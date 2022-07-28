import repos
from .Distribution import (Distribution,
                           DistributionUnknownCombinationException)

########################################################################
class CentOS(Distribution):
  """Class for CentOS distributions.
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
  def specialRepoRoots(self):
    roots = super(CentOS, self).specialRepoRoots
    try:
      roots.append(self.makeItem(
                    self._distroDefault(
                      self.defaults([self.versionName, "specialRepos"])),
                    architecture = self.architecture).repoRoot)
    except DistributionUnknownCombinationException:
      # The defaults specifies a distribution that isn't available.
      pass
    return roots

  ####################################################################
  @property
  def variant(self):
    return "Server" if self.majorVersion < 8 else "BaseOS"

  ####################################################################
  @classmethod
  def _minimumVersion(cls):
    (major, _) = super(CentOS, cls)._minimumVersion()
    return (major, cls.defaults([cls._versionName(), "minimum", "minor"]))

  ####################################################################
  @classmethod
  def _repoClass(cls):
    return repos.CentOS

  ####################################################################
  @property
  def _familyPrefix(self):
    return "CentOSLinux"

  ####################################################################
  # Protected methods
  ####################################################################

  ####################################################################
  # Private methods
  ####################################################################
