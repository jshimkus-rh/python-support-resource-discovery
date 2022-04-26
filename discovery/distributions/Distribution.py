import errno
import logging
import os
import re
import string
import subprocess
import yaml

from mill import defaults, factory
from discovery import architectures

log = logging.getLogger(__name__)

########################################################################
########################################################################
class DistributionException(Exception):

  ####################################################################
  # Overridden methods
  ####################################################################
  def __init__(self, msg, *args, **kwargs):
    super(DistributionException, self).__init__(*args, **kwargs)
    self._msg = msg

  ######################################################################
  def __str__(self):
    return self._msg

######################################################################
######################################################################
class DistributionNoDefaultException(DistributionException):

  ####################################################################
  # Overridden methods
  ####################################################################
  def __init__(self, msg = "no distribution found for use as default",
               *args, **kwargs):
    super(DistributionNoDefaultException, self).__init__(msg, *args, **kwargs)

######################################################################
######################################################################
class DistributionUnknownCombinationException(DistributionException):

  ####################################################################
  # Overridden methods
  ####################################################################
  def __init__(self, msg = "unknown combination", *args, **kwargs):
    super(DistributionUnknownCombinationException, self).__init__(msg,
                                                                  *args,
                                                                  **kwargs)

########################################################################
########################################################################
class Distribution(factory.Factory, defaults.DefaultsFileInfo):
  """Factory for instantiating objects which represent OS distributions.
  """
  ####################################################################
  # Factory-behavior attributes.
  ####################################################################
  # These dictionaries are indexed by architecture.  Each such accessed
  # item is a dictionary, indexed by distribution, which contains the
  # distributions available for the architecture.
  __mappingLatest = None
  __mappingNightly = None
  __mappingReleased = None

  ####################################################################
  # Instance-behavior attributes.
  ####################################################################
  _majorVersion = None
  _minorVersion = None
  _repoRoot = None
  _architecture = None

  ####################################################################
  # Public factory-behavior methods
  ####################################################################
  @classmethod
  def categoryMappingChoices(cls):
    """Returns a dictionary mapping the names of the distribution categories to
    the methods that return the available choices.
    """
    return { cls.defaultCategory()  : cls.choices,
             "latest"               : cls.choicesLatest,
             "nightly"              : cls.choicesNightly }

  ####################################################################
  @classmethod
  def categoryMappingMakeItem(cls):
    """Returns a dictionary mapping the names of the distribution categories to
    the methods to use in creating instances of same.
    """
    return { cls.defaultCategory()  : cls.makeItem,
             "latest"               : cls.makeItemLatest,
             "nightly"              : cls.makeItemNightly }

  ####################################################################
  @classmethod
  def choicesLatest(cls, architecture = None):
    return super(Distribution, cls).choices(("latest", architecture))

  ####################################################################
  @classmethod
  def choicesNightly(cls, architecture = None):
    return super(Distribution, cls).choices(("nightly", architecture))

  ####################################################################
  @classmethod
  def defaultCategory(cls):
    """Returns the name of the default category of distributions.
    """
    return "released"

  ####################################################################
  @classmethod
  def defaultDistribution(cls):
    # The distribution to use for machines which operate as servers but
    # are not under test.
    return cls.defaultChoice()

  ####################################################################
  @classmethod
  def makeItemLatest(cls, itemName, args = None, architecture = None):
    return cls._makeItemCommon(itemName, args, ("latest", architecture))

  ####################################################################
  @classmethod
  def makeItemNightly(cls, itemName, args = None, architecture = None):
    return cls._makeItemCommon(itemName, args, ("nightly", architecture))

  ####################################################################
  # Public instance-behavior methods
  ####################################################################
  @property
  def architecture(self):
    return self._architecture

  ####################################################################
  @property
  def bootOptions(self):
    return self._distroDefault(self.defaults([self.versionName,
                                              "bootOptions"]))

  ####################################################################
  @property
  def buildTag(self):
    return "{0}".format(self.version)

  ####################################################################
  @property
  def family(self):
    return "{0}{1}".format(self._familyPrefix, self.majorVersion)

  ####################################################################
  @property
  def kickStart(self):
    return self._distroDefault(self.defaults([self.versionName, "kickStart"]))

  ####################################################################
  @property
  def mainRepo(self):
    return "{0}/{1}/$basearch/os".format(self.repoRoot, self.variant)

  ####################################################################
  @property
  def majorVersion(self):
    return self._majorVersion

  ####################################################################
  @property
  def minorVersion(self):
    return self._minorVersion

  ####################################################################
  @property
  def released(self):
    return self._repoRootReleasedIndicator in self.repoRoot

  ####################################################################
  @property
  def repoRoot(self):
    return self._repoRoot

  ####################################################################
  @property
  def specialRepos(self):
    return []

  ####################################################################
  @property
  def specialRepoRoots(self):
    return []

  ####################################################################
  @property
  def tags(self):
    return None

  ####################################################################
  @property
  def variant(self):
    raise NotImplementedError

  ####################################################################
  @property
  def version(self):
    version = "{0}-{1}".format(self.versionName.lower(),
                               self.majorVersion)
    if self.minorVersion is not None:
      version = "{0}.{1}".format(version, self.minorVersion)
    return version

  ####################################################################
  @property
  def versionName(self):
    return self._versionName()

  ####################################################################
  @property
  def versionNumber(self):
    number = "{0}".format(self.majorVersion)
    if self.minorVersion is not None:
      number = "{0}.{1}".format(number, self.minorVersion)
    return number

  ####################################################################
  @property
  def virtualBoxRepo(self):
    return "http://download.virtualbox.org" \
              "/virtualbox/rpm/{0}/$releasever/$basearch".format(
                                                            self.versionName)

  ####################################################################
  # Overridden factory-behavior methods
  ####################################################################
  @classmethod
  def choices(cls, architecture = None):
    return super(Distribution, cls).choices((None, architecture))

  ####################################################################
  @classmethod
  def _defaultChoice(cls):
    from . import Fedora

    defaultDistribution = cls.defaults(["distribution"])
    family = cls.defaults(["family"], defaultDistribution)
    family = "fedora" if family is None else family.lower()
    major = cls.defaults(["major"], defaultDistribution)
    minor = (None if family == "fedora"
                  else cls.defaults(["minor"], defaultDistribution))

    defaultChoice = "{0}{1}{2}".format(family,
                                       major,
                                       minor if minor is not None else "")

    if defaultChoice not in cls.choices():
      # The specified distribution was not available.
      # Use the most recent released member of the specified family or, if
      # not available, the most recent member of the specified family.
      defaultChoice = None

      instances = [cls.makeItem(choice) for choice in cls.choices()]
      familyInstances = dict([(float(instance.versionNumber), instance)
                              for instance in instances
                                if instance.versionName == family])
      releasedInstances = dict(filter(lambda x: x[1].released,
                                      familyInstances.items()))
      if len(releasedInstances) > 0:
        defaultChoice = releasedInstances[max(releasedInstances)].name()
      elif len(familyInstances) > 0:
        defaultChoice = familyInstances[max(familyInstances)].name()

      if defaultChoice is None:
        # Use the most recent released Fedora or, if not available, the most
        # recent Fedora.
        fedoraInstances = dict([(float(instance.versionNumber), instance)
                                for instance in instances
                                  if isinstance(instance, Fedora)])
        releasedInstances = dict(filter(lambda x: x[1].released,
                                        fedoraInstances.items()))
        if len(releasedInstances) > 0:
          defaultChoice = releasedInstances[max(releasedInstances)].name()
        elif len(fedoraInstances) > 0:
          defaultChoice = fedoraInstances[max(fedoraInstances)].name()

      if defaultChoice is None:
        raise DistributionNoDefaultException()

    return defaultChoice

  ####################################################################
  @classmethod
  def _mapping(cls, option = None):
    """'option', if present, is a tuple of (category, architecture) - both may
    be None - which indicates what mapping to utilize.

    A (category, architecture) of (None, None) is equivalent to not specifying
    an option, for which the default is to use the default category and
    architecture.
    """
    (category, architecture) = cls._decodeOption(option)

    mapping = { cls.defaultCategory() : cls._mappingReleased,
                "latest"              : cls._mappingLatest,
                "nightly"             : cls._mappingNightly }

    return mapping[category](architecture)

  ####################################################################
  @classmethod
  def makeItem(cls, itemName, args = None, architecture = None):
    return cls._makeItemCommon(itemName, args, (None, architecture))

  ####################################################################
  # Overridden instance-behavior methods
  ####################################################################
  def __init__(self, args):
    super(Distribution, self).__init__(args)

  ####################################################################
  # Protected factory-behavior methods
  ####################################################################
  @classmethod
  def _allowableRoots(cls, roots):
    """Filters out those roots whose versions are less than that specified in
    the defaults.
    """
    (major, minor) = cls._minimumVersion()
    minimumVersion = float(major if minor is None
                                  else "{0}.{1}".format(major, minor))

    roots = dict([(key, value) for (key, value) in roots.items()
                                if float(key) >= minimumVersion])
    return roots

  ####################################################################
  @classmethod
  def _decodeOption(cls, option):
    category = None
    architecture = None
    if option is not None:
      (category, architecture) = option
    if category is None:
      category = cls.defaultCategory()
    if architecture is None:
      architecture = architectures.Architecture.defaultChoice()
    return (category, architecture)

  ####################################################################
  @classmethod
  def _latestRoots(cls, architecture):
    """Returns the available latest roots for the specified architecture
    filtered by the limits specified in the defaults file.
    """
    return cls._allowableRoots(cls._repo().availableLatestRoots(architecture))

  ####################################################################
  @classmethod
  def _makeDistributionMapping(cls, architecture, roots):
    # Dynamically created classes are assigned to the module-space in which
    # they are created regardless of their base class.  As we have runtime
    # determination of the location of a module's defaults location based on
    # the installation of the module we need the dynamically created classes
    # to be assigned to the module-space of the subclass, if any, from which
    # the chain of methods that led here began.
    # Consequently the subclass (however far descended) must perform the actual
    # creation.  This is easily accomplished by copy/pasting this method,
    # _makeDistributionMapping, as part of the subclass.
    return dict([(name, type(params["className"],
                             params["baseClasses"],
                             params["attributes"]))
                  for (name, params)
                    in cls._makeDynamicClassParameters(architecture,
                                                       roots).items()])

  ####################################################################
  @classmethod
  def _makeDynamicClassParameters(cls, architecture, roots):
    parameters = {}

    for klass in roots:
      for (key, value) in roots[klass].items():
        splitKey = key.split(".", 1)
        major = int(splitKey[0])
        minor = None if len(splitKey) < 2 else int(splitKey[1])
        name = "{0}{1}{2}".format(klass.className().lower(),
                                  major,
                                  "" if minor is None else minor)
        parameters[name] = { "className": "{0}{1}{2}"
                                            .format(klass.className(),
                                                    major,
                                                    "" if minor is None
                                                       else minor),
                              "baseClasses": (klass,),
                              "attributes": dict(_available = True,
                                                 _majorVersion = major,
                                                 _minorVersion = minor,
                                                 _name = name,
                                                 _repoRoot = value,
                                                 _architecture = architecture)
                           }
    return parameters


  ####################################################################
  @classmethod
  def _makeItemCommon(cls, itemName, args = None, option = None):
    (category, architecture) = cls._decodeOption(option)
    try:
      item = super(Distribution, cls).makeItem(itemName,
                                               args,
                                               (category, architecture))
    except ValueError:
      raise DistributionUnknownCombinationException(
              "unknown {0} combination: {1}/{2}".format(cls.className(),
                                                        itemName,
                                                        architecture))
    return item

  ####################################################################
  @classmethod
  def _mappingLatest(cls, architecture):
    if cls.__mappingLatest is None:
      cls.__mappingLatest = {}

    if architecture not in cls.__mappingLatest:
      log.debug("creating {0} 'latest' classes".format(architecture))

      cls.__mappingLatest[architecture] = (
        cls._makeDistributionMapping(
                                architecture,
                                dict([(klass,
                                       klass._latestRoots(architecture))
                                      for klass in
                                        super(Distribution,
                                              cls)._mapping().values()])))
    return cls.__mappingLatest[architecture]

  ####################################################################
  @classmethod
  def _mappingNightly(cls, architecture):
    if cls.__mappingNightly is None:
      cls.__mappingNightly = {}

    if architecture not in cls.__mappingNightly:
      log.debug("creating {0} 'nightly' classes".format(architecture))

      cls.__mappingNightly[architecture] = (
        cls._makeDistributionMapping(
                                architecture,
                                dict([(klass,
                                       klass._nightlyRoots(architecture))
                                      for klass in
                                        super(Distribution,
                                              cls)._mapping().values()])))
    return cls.__mappingNightly[architecture]

  ####################################################################
  @classmethod
  def _mappingReleased(cls, architecture):
    if cls.__mappingReleased is None:
      cls.__mappingReleased = {}

    if architecture not in cls.__mappingReleased:
      log.debug("creating {0} 'released' classes".format(architecture))

      cls.__mappingReleased[architecture] = (
        cls._makeDistributionMapping(
                                architecture,
                                dict([(klass,
                                       klass._releasedRoots(architecture))
                                      for klass in
                                        super(Distribution,
                                              cls)._mapping().values()])))
    return cls.__mappingReleased[architecture]

  ####################################################################
  @classmethod
  def _minimumVersion(cls):
    return (cls.defaults([cls._versionName(), "minimum", "major"]), None)

  ####################################################################
  @classmethod
  def _nightlyRoots(cls, architecture):
    """Returns the available nightly roots for the specified architecture
    filtered by the limits specified in the defaults file.
    """
    return cls._allowableRoots(cls._repo().availableNightlyRoots(architecture))

  ####################################################################
  @classmethod
  def _releasedRoots(cls, architecture):
    """Returns the available released roots for the specified architecture
    filtered by the limits specified in the defaults file.
    """
    return cls._allowableRoots(cls._repo().availableRoots(architecture))

  ####################################################################
  @classmethod
  def _repo(cls):
    """Returns an instance of the repo class associated with the distribution.
    """
    return cls._repoClass()()

  ####################################################################
  @classmethod
  def _repoClass(cls):
    """Returns the repo class associated with the distribution."""
    raise NotImplementedError

  ####################################################################
  @classmethod
  def _versionName(cls):
    return cls.className().lower().rstrip(string.digits)

  ####################################################################
  # Protected instance-behavior methods
  ####################################################################
  def _distroDefault(self, sourceDictionary):
    """The input dictionary is dual-level structured akin to

      default: <default value>
      fedora2\d$:
        default: <fedora 2x default value>
        fedora28: <fedora 28 value>
        fedora29: <fedora 29 value>
      fedora3\d$:
        default: <fedora 3x default value>

    where the first-level keys are regexes to match all distributions with a
    specific prefix.
    """
    regexMatches = list(filter(lambda x: re.match(x, self.name()) is not None,
                               sourceDictionary.keys()))
    if len(regexMatches) > 1:
      raise defaults.DefaultsFileFormatException(
                                                "multiple regex matches found")

    default = None
    if len(regexMatches) == 0:
      default = self.defaults(["default"], sourceDictionary)
    else:
      distroMatches = list(
                        filter(lambda x: re.match(x, self.name()) is not None,
                               sourceDictionary[regexMatches[0]].keys()))
      if len(distroMatches) > 1:
        raise defaults.DefaultsFileFormatException(
                                        "multiple distribution matches found")
      if len(distroMatches) == 0:
        default = self.defaults(["default"], sourceDictionary[regexMatches[0]])
      else:
        default = sourceDictionary[regexMatches[0]][distroMatches[0]]

    return default

  ####################################################################
  @property
  def _familyPrefix(self):
    raise NotImplementedError

  ####################################################################
  @property
  def _repoRootReleasedIndicator(self):
    return "released"

  ####################################################################
  # Private factory-behavior methods
  ####################################################################

  ####################################################################
  # Private instance-behavior methods
  ####################################################################
