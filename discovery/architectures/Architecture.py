#
# SPDX-License-Identifier: GPL-2.0-only
#
# Copyright Red Hat
#
import logging
import os
import platform

from mill import defaults, factory

log = logging.getLogger(__name__)

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
  @property
  def virtualizationFlag(self):
    return None

  ####################################################################
  # Overridden methods
  ####################################################################
  @classmethod
  def _defaultChoice(cls):
    default = platform.machine().lower()
    # Differing systems may use different values for 'machine'.
    # At present the only such known case is for ARM on Linux vs
    # Darwin.
    if default.startswith("arm"):
      # Presumably Darwin; convert to the value used by Linux.
      if default.endswith("64"):
        default = "aarch64"
      else:
        default = "armhfp"

    if not cls._isItemAvailable(default):
      log.info("your machine's architecture '{0}' is unknown".format(default))
      default = cls.defaults(["architecture"]).lower()

      if not cls._isItemAvailable(default):
        raise ValueError("default architecture '{0}' not known"
                          .format(default))

    return default

  ####################################################################
  # Protected methods
  ####################################################################

  ####################################################################
  # Private methods
  ####################################################################

