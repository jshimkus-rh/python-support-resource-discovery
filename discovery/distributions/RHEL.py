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
    if ((self.majorVersion > 7)
        or ((self.majorVersion == 7) and (self.minorVersion > 5))):
      tags = "{0}{1}".format(
                "" if tags is None else "{0} ".format(tags),
                "RTT_ACCEPTED" if self._accepted else "RTT_PASSED")
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
  def _accepted(self):
    return ("/nightly-rhel-{0}".format(self.majorVersion)
            not in self.repoRoot)

  ####################################################################
  # Private methods
  ####################################################################
