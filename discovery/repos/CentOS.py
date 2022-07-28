import re

from .Repository import Repository

######################################################################
######################################################################
class CentOS(Repository):
  # Exclude any release prior to the combined minimum major and minor.
  __CENTOS_MINIMUM_MAJOR = 8
  __CENTOS_MINIMUM_MINOR = 3

  # Available via Factory.
  _available = True

  ####################################################################
  # Overridden methods
  ####################################################################
  def _filterNonExistentArchitecture(self, repos, architecture):
    regex = re.compile(r"(?i)<a\s+href=\"({0}/)\">\1</a>".format(architecture))

    return dict([ (key, value)
      for (key, value) in repos.items()
        if re.search(regex,
                     self._uri_contents(
                      "{0}/{1}".format(value, "BaseOS"))) is not None ])

  ####################################################################
  def _findAgnosticLatestRoots(self, architecture):
    return self._findAgnosticReleasedRoots(architecture)

  ####################################################################
  def _findAgnosticNightlyRoots(self, architecture):
    return self._findAgnosticReleasedRoots(architecture)

  ####################################################################
  def _findAgnosticReleasedRoots(self, architecture):
    roots = {}
    path = self._releasedStartingPath()
    if path is not None:
      data = self._path_contents("{0}/".format(path))

      # Find all the released versions greater than or equal to the CentOS
      # minimum major and then find their minors.
      regex = r"(?i)<a\s+href=\"(centos-(\d+))/\">\1/</a>"
      for release in filter(
                      lambda x: int(x[1]) >= self.__CENTOS_MINIMUM_MAJOR,
                      re.findall(regex, data)):
        roots.update(self._availableReleasedMinors(
                        "{0}/centos-{1}".format(path, release[1]),
                        int(release[1])))
    return roots

  ####################################################################
  # Protected methods
  ####################################################################
  def _availableReleasedMinors(self, path, major):
    data = self._path_contents("{0}/".format(path))

    regex = r"(?i)<a\s+href=\"({0}\.(\d+)(|\.\d+))/\">\1/</a>".format(major)
    matches = re.findall(regex, data)
    if major == self.__CENTOS_MINIMUM_MAJOR:
      matches = filter(lambda x: int(x[1]) >= self.__CENTOS_MINIMUM_MINOR,
                       matches)
    # Convert the minor/zStream to integers.
    matches = [(x[0],
                int(x[1]),
                int(x[2].lstrip(".")) if x[2] != "" else 0) for x in matches]

    available = {}
    minors = [x[1] for x in matches]
    if len(minors) > 0:
      for minor in range(min(minors), max(minors) + 1):
        minorMatches = list(filter(lambda x: x[1] == minor, matches))
        if len(minorMatches) > 0:
          maxZStream = max([x[2] for x in minorMatches])
          maxMatch = list(filter(lambda x: x[2] == maxZStream, minorMatches))
          maxMatch = maxMatch[0]
          available["{0}.{1}".format(major, maxMatch[1])] = (
            "http://{0}{1}/{2}".format(self._host(), path, maxMatch[0]))
    return available
