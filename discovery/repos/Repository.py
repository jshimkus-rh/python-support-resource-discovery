#
# SPDX-License-Identifier: GPL-2.0-only
#
# Copyright Red Hat
#
from __future__ import print_function

# Although the requests python package would simplify the processing slightly
# there is an Objective-C runtime error on macOS using it in an ansible
# context.  Thus we use httplib and urlparse.
import platform
if int(platform.python_version_tuple()[0]) < 3:
  import httplib
  import urlparse
else:
  from http import client as httplib
  from urllib import parse as urlparse

import argparse
import errno
import fcntl
import functools
import itertools
import json
import logging
import os
import socket
import subprocess
import sys
import time

from mill import defaults, factory
from discovery import architectures

log = logging.getLogger(__name__)

######################################################################
######################################################################
class Repository(factory.Factory, defaults.DefaultsFileInfo):
  # We cache the results of determining the various roots to avoid
  # having to constantly perform network queries.
  #
  # We start with None so that separate dictionaries are created per
  # subclass.
  #
  # All found roots with no distinction as to architecture.
  # Keyed by category.
  __agnosticRoots = None

  # Available roots; keyed by architecture.
  __cachedLatest = None
  __cachedNightly = None
  __cachedReleased = None

  # Cached contents to avoid multiple requests for the same data.
  __cachedUriContents = {}

  ####################################################################
  # Public methods
  ####################################################################
  def availableRoots(self, architecture = None):
    """Returns a dictionary with keys being the <major>.<minor> and the values
    the URI for the release repo.

    This method prioritizes released over latest over nightly versions.
    """
    available = self._cachedNightly(architecture)
    available.update(self._cachedLatest(architecture))
    available.update(self._cachedReleased(architecture))
    return available

  ####################################################################
  def availableLatestRoots(self, architecture = None):
    """Returns a dictionary with keys being the <major>.<minor> and the values
    the URI for the release repo.

    This method prioritizes latest over released over nightly versions.
    """
    available = self._cachedNightly(architecture)
    available.update(self._cachedReleased(architecture))
    available.update(self._cachedLatest(architecture))
    return available

  ####################################################################
  def availableNightlyRoots(self, architecture = None):
    """Returns a dictionary with keys being the <major>.<minor> and the values
    the URI for the release repo.

    This method prioritizes nightly over latest over released versions.
    """
    available = self._cachedReleased(architecture)
    available.update(self._cachedLatest(architecture))
    available.update(self._cachedNightly(architecture))
    return available

  ####################################################################
  # Overridden instance-behavior methods
  ####################################################################
  def __init__(self, args = None):
    if args is None:
      args = self._defaultArguments()
    self.__cacheRoot = None
    self.__cacheSubdir = None
    self.__cacheRefresh = None
    super(Repository, self).__init__(args)

  ####################################################################
  # Protected methods
  ####################################################################
  def _agnosticLatest(self, architecture):
    return self.__privateAgnosticRoots(self._categoryLatest(architecture),
                                       functools.partial(
                                        self._findAgnosticLatestRoots,
                                        architecture))

  ####################################################################
  def _agnosticNightly(self, architecture):
    return self.__privateAgnosticRoots(self._categoryNightly(architecture),
                                       functools.partial(
                                        self._findAgnosticNightlyRoots,
                                        architecture))

  ####################################################################
  def _agnosticReleased(self, architecture):
    return self.__privateAgnosticRoots(self._categoryReleased(architecture),
                                       functools.partial(
                                        self._findAgnosticReleasedRoots,
                                        architecture))

  ####################################################################
  def _availableLatest(self, architecture):
    return self.__privateAvailableRoots(self._categoryLatest(architecture),
                                        architecture,
                                        functools.partial(
                                          self. _filterNonExistentArchitecture,
                                          self._agnosticLatest(architecture),
                                          architecture))

  ####################################################################
  def _availableNightly(self, architecture):
    return self.__privateAvailableRoots(self._categoryNightly(architecture),
                                        architecture,
                                        functools.partial(
                                          self. _filterNonExistentArchitecture,
                                          self._agnosticNightly(architecture),
                                          architecture))

  ####################################################################
  def _availableReleased(self, architecture):
    return self.__privateAvailableRoots(self._categoryReleased(architecture),
                                        architecture,
                                        functools.partial(
                                          self. _filterNonExistentArchitecture,
                                          self._agnosticReleased(architecture),
                                          architecture))

  ####################################################################
  def _cachedLatest(self, architecture = None):
    if self.__cachedLatest is None:
      self.__cachedLatest = {}
    if architecture is None:
      architecture = architectures.Architecture.defaultChoice()
    if architecture not in self.__cachedLatest:
      self.__cachedLatest[architecture] = self._availableLatest(architecture)
    return self.__cachedLatest[architecture].copy()

  ####################################################################
  def _cachedNightly(self, architecture = None):
    if self.__cachedNightly is None:
      self.__cachedNightly = {}
    if architecture is None:
      architecture = architectures.Architecture.defaultChoice()
    if architecture not in self.__cachedNightly:
      self.__cachedNightly[architecture] = self._availableNightly(architecture)
    return self.__cachedNightly[architecture].copy()

  ####################################################################
  def _cachedReleased(self, architecture = None):
    if self.__cachedReleased is None:
      self.__cachedReleased = {}
    if architecture is None:
      architecture = architectures.Architecture.defaultChoice()
    if architecture not in self.__cachedReleased:
      self.__cachedReleased[architecture] = self._availableReleased(
                                                                architecture)
    return self.__cachedReleased[architecture].copy()

  ####################################################################
  def _categoryLatest(self, architecture):
    # What is returned must be suitable for use as a file name w/o special
    # handling (e.g., requiring quoting).
    return "latest"

  ####################################################################
  def _categoryNightly(self, architecture):
    # What is returned must be suitable for use as a file name w/o special
    # handling (e.g., requiring quoting).
    return "nightly"

  ####################################################################
  def _categoryReleased(self, architecture):
    # What is returned must be suitable for use as a file name w/o special
    # handling (e.g., requiring quoting).
    return "released"

  ####################################################################
  def _defaultArguments(self):
    return argparse.Namespace(forceScan = False)

  ####################################################################
  def _filterNonExistentArchitecture(self, repos, architecture):
    """Filters out the repos that don't have a subdir for the
    specified archtecture returning only those that do.
    """
    raise NotImplementedError

  ####################################################################
  def _findAgnosticLatestRoots(self, architecture):
    raise NotImplementedError

  ####################################################################
  def _findAgnosticNightlyRoots(self, architecture):
    raise NotImplementedError

  ####################################################################
  def _findAgnosticReleasedRoots(self, architecture):
    raise NotImplementedError

  ####################################################################
  def _host(self):
    return self._releasedHost()

  ####################################################################
  def _latestStartingPath(self, architecture = None):
    path = self.defaults([self.name().lower(), "paths", "latest"])
    if path is not None:
      path = "{0}{1}".format(self._startingPathPrefix(architecture), path)
    else:
      path = self._releasedStartingPath(architecture)
    return path

  ####################################################################
  def _nightlyStartingPath(self, architecture = None):
    path = self.defaults([self.name().lower(), "paths", "nightly"])
    if path is not None:
      path = "{0}{1}".format(self._startingPathPrefix(architecture), path)
    else:
      path = self._latestStartingPath(architecture)
    return path

  ####################################################################
  def _releasedHost(self):
    host = self.defaults([self.name().lower(), "hosts", "released"])
    return host

  ####################################################################
  def _releasedStartingPath(self, architecture = None):
    path = self.defaults([self.name().lower(), "paths", "released"])
    if path is not None:
      path = "{0}{1}".format(self._startingPathPrefix(architecture), path)
    return path

  ####################################################################
  def _path_contents(self, path = None):
    contents = ""
    if path is None:
      path = self._releasedStartingPath()
    if (path is not None) and (self._host() is not None):
      contents = self._uri_contents("http://{0}{1}".format(self._host(), path))
    return contents

  ####################################################################
  def _startingPathPrefix(self, architecture):
    return ""

  ####################################################################
  def _uri_contents(self, uri, retries = 3):
    if not uri.endswith("/"):
      uri = "{0}/".format(uri)
    if uri not in self.__cachedUriContents:
      log.debug("retrieving contents from uri: {0}".format(uri))
      parsed = urlparse.urlparse(uri)
      for iteration in range(retries):
        try:
          connection = httplib.HTTPConnection(parsed.netloc, timeout = 10)
          connection.request("GET", parsed.path)
          response = connection.getresponse()
          if response.status == 200:
            self.__cachedUriContents[uri] = response.read().decode("UTF-8")
            break
          log.debug("response status {0} on iteration {1}"
                      .format(response.status, iteration))
          if (iteration < (retries - 1)):
            sleep = min(5, 1 << iteration)
            log.debug("sleeping {0} second(s) before retrying".format(sleep))
            time.sleep(sleep)
        except (socket.gaierror, socket.timeout):
          log.debug("socket error on iteration {0}".format(iteration))
      else: # for
        # We log this at info level because some distributions don't
        # necessarily support all the architectures of potential interest.
        log.info("retries exhausted; caching empty contents for {0}"
                  .format(uri))
        self.__cachedUriContents[uri] = ""

    return self.__cachedUriContents[uri]

  ####################################################################
  # Private methods
  ####################################################################
  def __privateAgnosticFileName(self, category):
    return "agnostic.{0}.json".format(category)

  ####################################################################
  def __privateAgnosticRoots(self, category, finder):
    if self.__agnosticRoots is None:
      self.__agnosticRoots = {}
    if category not in self.__agnosticRoots:
      openFile = self.__privateOpenFile(
                  self.__privateAgnosticFileName(category))
      try:
        roots = self.__privateLoadFile(
                  openFile,
                  finder,
                  "Updating saved {0} {1} repos".format(self.className(),
                                                        category),
                  forceScan = self.args.forceScan)
        self.__agnosticRoots[category] = roots
      finally:
        openFile.close()
    return self.__agnosticRoots[category]

  ####################################################################
  def __privateAvailableFileName(self, category, architecture):
    return "available.{0}.{1}.json".format(category, architecture)

  ####################################################################
  def __privateAvailableRoots(self, category, architecture, finder):
    roots = None
    openFile = self.__privateOpenFile(
                 self.__privateAvailableFileName(category, architecture))
    try:
      with self.__privateOpenFile(
            self.__privateAgnosticFileName(category)) as f:
        mtime = self.__privateFileMtime(f)
      roots = self.__privateLoadFile(
                openFile,
                finder,
                "Updating saved {0} {1} {2} repos ".format(self.className(),
                                                           category,
                                                           architecture),
                mtime,
                forceScan = self.args.forceScan)
    finally:
      openFile.close()
    return roots

  ####################################################################
  @property
  def __privateCacheRefresh(self):
    if self.__cacheRefresh is None:
      try:
        self.__cacheRefresh = self.defaults(["cache", "refresh"])
      except defaults.DefaultsException as ex:
        log.warn("exception accessing defaults: {0}".format(ex))
        log.info("using default refresh: 1 day")

      if self.__cacheRefresh is None:
        self.__cacheRefresh = "1-0-0"

      refresh = self.__cacheRefresh.split("-")
      if len(refresh) > 3:
        log.warn("more than three refresh fields specified: {0}"
                  .format(self.__cacheRefresh))
        refresh = refresh[-3:]
        log.info("using rightmost fields as refresh: {0}"
                  .format("-".join(refresh)))

      try:
        refresh = list(map(lambda x: int(x), refresh))
      except ValueError:
        log.warn("could not convert one or more fields to integers: {0}"
                  .format("-".join(refresh)))
        log.info("using default refresh: 1 day")
        refresh = [1, 0, 0]

      refresh.reverse()
      refresh = dict(itertools.zip_longest(("minutes", "hours", "days"),
                                           refresh, fillvalue = 0))

      self.__cacheRefresh = ((refresh["days"] * 86400)
                              + (refresh["hours"] * 3600)
                              + (refresh["minutes"] * 60))
      if self.__cacheRefresh < 60:
        log.debug("forcing refresh minimum: 1 minute")
        self.__cacheRefresh = 60

    return self.__cacheRefresh

  ####################################################################
  @property
  def __privateCacheRoot(self):
    if self.__cacheRoot is None:
      try:
        self.__cacheRoot = self.defaults(["cache", "directories", "root"])
      except defaults.DefaultsException as ex:
        log.warn("exception accessing defaults: {0}".format(ex))
        log.info("using default root: {0}".format(os.environ["HOME"]))

      if self.__cacheRoot is None:
        self.__cacheRoot = os.environ["HOME"]
      self.__cacheRoot = os.path.expanduser(self.__cacheRoot)
      if not os.path.isabs(self.__cacheRoot):
        log.warn("root is not absolute path: {0}".format(self.__cacheRoot))
        log.info("using default root: {0}".format(os.environ["HOME"]))
        self.__cacheRoot = os.environ["HOME"]

    return self.__cacheRoot

  ####################################################################
  @property
  def __privateCacheSubdir(self):
    if self.__cacheSubdir is None:
      try:
        self.__cacheSubdir = self.defaults(["cache", "directories",
                                            "subdirectory"])
      except defaults.DefaultsException as ex:
        log.warn("exception accessing defaults: {0}".format(ex))
        log.info("using default subdirectory: .python-repos-cache")

      if self.__cacheSubdir is None:
        self.__cacheSubdir = ".python-repos-cache"

    return self.__cacheSubdir

  ####################################################################
  def __privateDirPath(self):
    return os.path.sep.join([self.__privateCacheRoot,
                             self.__privateCacheSubdir,
                             self.className()])

  ####################################################################
  def __privateFileMtime(self, openFile):
    stats = os.fstat(openFile.fileno())
    return stats.st_mtime

  ####################################################################
  def __privateLoadFile(self, openFile, finder, logMessage,
                        dependencyMtime = None, forceScan = False):
    roots = None
    stats = os.fstat(openFile.fileno())
    # Truncate the file if ...
    #   - we've been explicitly told to or
    #   - its dependency is more recent than the file itself or
    #   - it's been more than the cache refresh time since it was updated or
    #   - it contains no actual data; this is either because it's a newly
    #     created file or the previous check most likely encountered an error
    forceScan = (forceScan
                  or ((dependencyMtime is not None)
                      and (dependencyMtime > stats.st_mtime))
                  or ((time.time() - stats.st_mtime)
                      >= self.__privateCacheRefresh)
                  or (stats.st_size == 0))
    if not forceScan:
      roots = json.loads(openFile.read())
      forceScan = len(roots) == 0

    if forceScan:
      log.info(logMessage)
      openFile.truncate(0)
      openFile.seek(0)
      self.__privateSaveFile(openFile, finder())
      openFile.seek(0)
      roots = json.loads(openFile.read())

    return roots

  ####################################################################
  def __privateOpenFile(self, name):
    try:
      os.makedirs(self.__privateDirPath(), 0o700)
    except OSError as ex:
      if ex.errno != errno.EEXIST:
        raise
    try:
      fd = os.open(os.path.sep.join([self.__privateDirPath(), name]),
                   os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o640)
    except OSError as ex:
      if ex.errno != errno.EEXIST:
        raise
      fd = os.open(os.path.sep.join([self.__privateDirPath(), name]),
                   os.O_RDWR, 0o640)
    try:
      openFile = os.fdopen(fd, "r+")
      fcntl.flock(openFile, fcntl.LOCK_EX)
    except:
      os.close(fd)
    return openFile

  ####################################################################
  def __privateSaveFile(self, openFile, roots):
    openFile.write(json.dumps(roots))
    openFile.flush()
    os.fsync(openFile.fileno())
