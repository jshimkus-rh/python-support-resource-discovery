import re

from .Repository import Repository

######################################################################
######################################################################
class RHEL(Repository):
  # Exclude any release prior to the combined minimum major and minor.
  __RHEL_MINIMUM_MAJOR = 7
  __RHEL_MINIMUM_MINOR = 5

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
                      "{0}/{1}".format(value,
                                       "Server" if float(key) < 8
                                                else "BaseOS"))) is not None ])

  ####################################################################
  def _findAgnosticLatestRoots(self, architecture):
    # Find all the latest versions greater than or equal to the RHEL
    # minimum major and then find their minors.
    roots = {}
    path = self._latestStartingPath()
    if path is not None:
      for rhel in self._findMajorRhels(path,
                                      r"<a\s+href=\"(rhel-(\d+))/\">\1/</a>"):
        roots.update(self._availableLatestMinors(
                "{0}/{1}/rel-eng/{2}".format(path, rhel[0], rhel[0].upper())))
    return roots

  ####################################################################
  def _findAgnosticNightlyRoots(self, architecture):
    # Find all the nightly versions greater than or equal to the RHEL
    # minimum major and then find their minors.
    roots = {}
    path = self._nightlyStartingPath()
    if path is not None:
      for rhel in self._findMajorRhels(path,
                                      r"<a\s+href=\"(rhel-(\d+))/\">\1/</a>"):
        roots.update(self._availableNightlyMinors(
                "{0}/{1}/nightly/{2}".format(path, rhel[0], rhel[0].upper())))
    return roots

  ####################################################################
  def _findAgnosticReleasedRoots(self, architecture):
    roots = {}
    # Find all the released versions greater than or equal to the RHEL
    # minimum major and then find their minors.
    path = self._releasedStartingPath()
    if path is not None:
      for rhel in self._findMajorRhels(
                              path, r"<a\s+href=\"(RHEL-(\d+))/\">\1/</a>"):
        roots.update(self._availableReleasedMinors(
                        "{0}/{1}".format(path, rhel[0]), int(rhel[1])))
    return roots

  ####################################################################
  # Protected methods
  ####################################################################
  def _availableLatestMinors(self, path):
    data = self._path_contents("{0}/".format(path))

    # Find all the latest greater than or equal to the RHEL minimum major.
    regex = r"(?i)<a\s+href=\"(latest-RHEL-(\d+)\.(\d+)(|\.\d+))/\">\1/</a>"
    matches = filter(lambda x: int(x[1]) >= self.__RHEL_MINIMUM_MAJOR,
                     re.findall(regex, data))
    # Convert the major/minor/zStream to integers.
    matches = [(x[0],
                int(x[1]),
                int(x[2]),
                int(x[3].lstrip(".")) if x[3] != "" else 0) for x in matches]
    # Exclude any minimum major versions that have a minor less than the
    # minimum minor.
    matches = filter(lambda x: not ((x[1] == self.__RHEL_MINIMUM_MAJOR)
                                    and (x[2] < self.__RHEL_MINIMUM_MINOR)),
                     matches)
    matches = list(matches)

    available = {}
    majors = [x[1] for x in matches]
    if len(majors) > 0:
      for major in range(min(majors), max(majors) + 1):
        majorMatches = list(filter(lambda x: x[1] == major, matches))
        minors = [x[2] for x in majorMatches]
        if len(minors) > 0:
          for minor in range(min(minors), max(minors) + 1):
            minorMatches = list(filter(lambda x: x[2] == minor, majorMatches))
            if len(minorMatches) > 0:
              maxZStream = max([x[3] for x in minorMatches])
              maxMatch = list(filter(lambda x: x[3] == maxZStream,
                                     minorMatches))
              maxMatch = maxMatch[0]
              available["{0}.{1}".format(maxMatch[1], maxMatch[2])] = (
                "http://{0}{1}/{2}/compose".format(self._host(), path,
                                                   maxMatch[0]))

    return available

  ####################################################################
  def _availableNightlyMinors(self, path):
    return self._availableLatestMinors(path)

  ####################################################################
  def _availableReleasedMinors(self, path, major):
    data = self._path_contents("{0}/".format(path))

    regex = r"<a\s+href=\"({0}\.(\d+)(|\.\d+))/\">\1/</a>".format(major)
    matches = re.findall(regex, data)
    if major == self.__RHEL_MINIMUM_MAJOR:
      matches = filter(lambda x: int(x[1]) >= self.__RHEL_MINIMUM_MINOR,
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

  ####################################################################
  def _findMajorRhels(self, path, regex):
    data = self._path_contents("{0}/".format(path))

    # Find all the released versions greater than or equal to the RHEL
    # minimum major.
    return filter(lambda x: int(x[1]) >= self.__RHEL_MINIMUM_MAJOR,
                  re.findall(regex, data))
