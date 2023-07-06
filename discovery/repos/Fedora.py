#
# SPDX-License-Identifier: GPL-2.0-only
#
# Copyright Red Hat
#
import json
import re

from discovery import architectures
from .Repository import Repository

######################################################################
######################################################################
class Fedora(Repository):
  # Exclude any release prior to 28.
  __FEDORA_MINIMUM_MAJOR = 28

  # Available via Factory.
  _available = True

  ####################################################################
  # Overridden methods
  ####################################################################
  def _categoryLatest(self, architecture):
    return "{0}-{1}".format(
                    self._startingPathPrefix(architecture).replace("/", "-"),
                    super(Fedora, self)._categoryLatest(architecture))

  ####################################################################
  def _categoryNightly(self, architecture):
    # For Fedora latest is nightly.
    return self._categoryLatest(architecture)

  ####################################################################
  def _categoryReleased(self, architecture):
    return "{0}-{1}".format(
                    self._startingPathPrefix(architecture).replace("/", "-"),
                    super(Fedora, self)._categoryReleased(architecture))

  ####################################################################
  def _filterRepos(self, repos, architecture):
    repos = super(Fedora, self)._filterRepos(repos, architecture)

    repos = dict([ (key, value)
                      for (key, value) in repos.items()
                        if self._uri_contents(
                          "{0}/Everything/{1}"
                            .format(value, architecture)) != self.uriError ])
    return repos

  ####################################################################
  def _findAgnosticLatestRoots(self, architecture):
    return self._agnosticCommon(self._latestStartingPath(architecture))

  ####################################################################
  def _findAgnosticNightlyRoots(self, architecture):
    # For Fedora latest is nightly.
    # We could potentially make it 'rawhide', but that would require some
    # farther-reaching changes as the infrastructure is only set up to handle
    # numeric versions.
    return self._findAgnosticLatestRoots(architecture)

  ####################################################################
  def _findAgnosticReleasedRoots(self, architecture):
    return self._agnosticCommon(self._releasedStartingPath(architecture))

  ####################################################################
  def _startingPathPrefix(self, architecture):
    path = "/pub/fedora"
    if not architectures.Architecture.fedoraSecondary(architecture):
      path = "{0}/linux".format(path)
    else:
      path = "{0}-secondary".format(path)
    return path

  ####################################################################
  # Protected methods
  ####################################################################
  def _agnosticCommon(self, path):
    roots = {}
    if path is not None:
      data = self._path_contents("{0}/".format(path))

      if data == self.uriError:
        roots = self.uriErrorRoot
      else:
        # Find all the released versions greater than or equal to the Fedora
        # minimum major (limited to no less than 28, Fedora 28 being the
        # version first incorporating VDO).
        regex = r"(?i)<a\s+href=\"(\d+)/\">\1/</a>"
        roots = dict([
          (x,  self._availableUri(path, x))
            for x in filter(lambda x: int(x) >= self.__FEDORA_MINIMUM_MAJOR,
                            re.findall(regex, data)) ])

    return roots

  ####################################################################
  def _archivedHost(self):
    return self.defaults([self.name().lower(), "hosts", "archived"])

  ####################################################################
  def _availableUri(self, path, version):
    # If the version has a README file that indicates it has been moved to
    # the archive server.
    data = self._path_contents("{0}/{1}/".format(path, version))
    regex = r"(?i)<a\s+href=\"(README)\">\1</a>"
    host = self._host()
    match = re.search(regex, data)
    if match is not None:
      host = self._archivedHost()
      path = path.replace("/pub/", "/pub/archive/", 1)
    uri = None if host is None else "http://{0}{1}/{2}".format(host, path,
                                                               version)
    return uri
