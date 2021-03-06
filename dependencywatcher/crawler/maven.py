import logging, os
from dependencywatcher.crawler.xpath import XPathDetector
from dependencywatcher.crawler.utils import VersionUtil

logger = logging.getLogger(__name__)

class MavenDetector(XPathDetector):
    """ This detector gets newest information from a Maven repository """

    XPATHS = {
        "version": "/metadata/versioning/release/text()|/metadata/version/text()",
        "updatetime": "/metadata/versioning/lastUpdated/text()",
        "url": "/project/url/text()",
        "description": "/project/description/text()",
        "license": "/project/licenses/license/name/text()"
    }

    def get_repositories(self, options):
        try:
            return [options["repository"]]
        except KeyError:
            return ["http://central.maven.org/maven2/"]

    def get_urls(self, options, result):
        url_path = None
        try:
            # Search for Maven alias (such an alias will have a ':' separator):
            for alias in self.manifest["aliases"]:
                try:
                    s = alias.split(":")
                    if len(s) == 2:
                        group = s[0]
                        artifact = s[1]
                        url_path = "%s/%s" % (group.replace(".", "/"), artifact)
                        break
                except ValueError:
                    pass
        except KeyError:
            pass

        if url_path is None:
            raise Exception("No Maven alias was found!")

        urls = []
        for repo in self.get_repositories(options):
            urls.append(os.path.join(repo, url_path, "maven-metadata.xml"))
            try:
                urls.append(os.path.join(repo, url_path, result["version"], "%s-%s.pom" % (artifact, result["version"])))
            except KeyError:
                pass
        return urls

    def resolve(self, options, result):
        for url in self.get_urls(options, result):
            new_options = dict(options.items() + [("url", url)])
            r = super(MavenDetector, self).resolve(new_options, result)
            if r:
                return r

    def detect(self, what, options, result):
        if what == "version" or what == "stable_version":
            versions = self.resolve(dict(options.items() + [("xpath", "/metadata/versioning/versions/version/text()")]), result)
            if len(versions) > 0:
                result[what] = VersionUtil.find_latest(versions) if what == "version" else VersionUtil.find_stable(versions)
                return

        try:
            new_options = dict(options.items() + [("xpath", MavenDetector.XPATHS[what])])
            return super(MavenDetector, self).detect(what, new_options, result)
        except KeyError:
            return None

