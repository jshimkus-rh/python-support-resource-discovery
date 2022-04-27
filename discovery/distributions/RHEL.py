#
# SPDX-License-Identifier: GPL-2.0-only
#
# Copyright Red Hat
#
from discovery import repos
from .CentOS import CentOS

########################################################################
class RHEL(CentOS):
  """Class for RHEL distributions.
  """
  # Available for use.
  _available = True

  ####################################################################
  # Public methods
  ####################################################################

  ####################################################################
  # Overridden methods
  ####################################################################
  @property
  def buildTag(self):
    return ("{0}-candidate".format(self.version)
              if self.majorVersion < 8 else "{0}-build".format(self.version))

  ####################################################################
  @property
  def tags(self):
    tags = super(RHEL, self).tags
    if (((self.majorVersion > 7)
          or ((self.majorVersion == 7) and (self.minorVersion > 5)))
        and self._released):
      tags = "{0}{1}".format("" if tags is None else "{0} ".format(tags),
                             "RELEASED")
    return tags

  ####################################################################
  @classmethod
  def _repoClass(cls):
    return repos.RHEL

  ####################################################################
  @property
  def _familyPrefix(self):
    return "RedHatEnterpriseLinux"

  ####################################################################
  # Protected methods
  ####################################################################
  @property
  def _released(self):
    return ("/released/RHEL-{0}/{0}.{1}".format(self.majorVersion,
                                                self.minorVersion)
            in self.repoRoot)

  ####################################################################
  # Private methods
  ####################################################################
