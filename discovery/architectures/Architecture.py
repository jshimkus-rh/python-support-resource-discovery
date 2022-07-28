import os

from mill import defaults, factory

########################################################################
class Architecture(factory.Factory, defaults.DefaultsFileInfo):
  ####################################################################
  # Public methods
  ####################################################################
  @classmethod
  def fedoraSecondary(cls, architecture):
    return cls.makeItem(architecture).isFedoraSecondary

  ####################################################################
  @property
  def is32Bit(self):
    return NotImplementedError

  ####################################################################
  @property
  def is64Bit(self):
    return NotImplementedError

  ####################################################################
  @property
  def isFedoraSecondary(self):
    return False

  ####################################################################
  @property
  def lacksHardwareData(self):
    return False

  ####################################################################
  @property
  def requiresExternalStorage(self):
    return False

  ####################################################################
  # Overridden methods
  ####################################################################
  @classmethod
  def _defaultChoice(cls):
    defaultArchitecture = cls.defaults(["architecture"]).lower()

    if not cls._isItemAvailable(defaultArchitecture):
      raise ValueError("default architecture '{0}' not known"
                        .format(defaultArchitecture))

    return defaultArchitecture

  ####################################################################
  # Protected methods
  ####################################################################

  ####################################################################
  # Private methods
  ####################################################################

