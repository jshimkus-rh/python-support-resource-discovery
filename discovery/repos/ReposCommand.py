from __future__ import print_function

import argparse
import yaml

from mill import command
from discovery import architectures
from .Repository import Repository

########################################################################
class ReposCommand(command.Command):
  """Command class for command line utility.
  """

  ####################################################################
  # Public factory-behavior methods
  ####################################################################

  ####################################################################
  # Public instance-behavior methods
  ####################################################################

  ####################################################################
  # Overridden factory-behavior methods
  ####################################################################
  @classmethod
  def parserParents(cls):
    parser = argparse.ArgumentParser(add_help = False)

    parser.add_argument("--force-scan",
                        help = "force a scan for available repos" \
                                "; by default scan results are cached and" \
                                " updated when at least one day has passed" \
                                " since the last scan" \
                                "; specifying this option will force a scan" \
                                " for available repos",
                        action = "store_true",
                        dest = "forceScan")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--latest",
                       help = "report only the available latest repos",
                       action = "store_true")
    group.add_argument("--nightly",
                       help = "report only the available nightly repos",
                       action = "store_true")
    group.add_argument("--released",
                       help = "report only the available latest repos",
                       action = "store_true")

    parents = super(ReposCommand, cls).parserParents()
    parents.append(parser)
    return parents

  ####################################################################
  # Overridden instance-behavior methods
  ####################################################################
  def run(self):
    all = not (self.args.latest or self.args.nightly or self.args.released)

    for choice in Repository.choices():
      instance = Repository.makeItem(choice, self.args)
      for architecture in architectures.Architecture.choices():
        if all or self.args.released:
          print("{0} {1} released roots:".format(instance.name(),
                                                 architecture))
          print(yaml.safe_dump(instance.availableRoots(architecture),
                               default_flow_style = False))
        if all or self.args.latest:
          print("{0} {1} latest roots:".format(instance.name(),
                                               architecture))
          print(yaml.safe_dump(instance.availableLatestRoots(architecture),
                               default_flow_style = False))
        if all or self.args.nightly:
          print("{0} {1} nightly roots:".format(instance.name(),
                                                architecture))
          print(yaml.safe_dump(instance.availableNightlyRoots(architecture),
                               default_flow_style = False))

  ####################################################################
  # Protected factory-behavior methods
  ####################################################################

  ####################################################################
  # Protected instance-behavior methods
  ####################################################################

  ####################################################################
  # Private factory-behavior methods
  ####################################################################

  ####################################################################
  # Private instance-behavior methods
  ####################################################################
