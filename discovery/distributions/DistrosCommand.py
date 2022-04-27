#
# SPDX-License-Identifier: GPL-2.0-only
#
# Copyright Red Hat
#
from __future__ import print_function

import argparse

from mill import command
from discovery import architectures
from .Distribution import Distribution, DistributionUnknownCombinationException

########################################################################
class DistrosCommand(command.Command):
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

    # Class of distro to report.
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--latest",
                       help = "report only the available latest distros",
                       action = "store_true")
    group.add_argument("--nightly",
                       help = "report only the available nightly distros",
                       action = "store_true")
    group.add_argument("--released",
                       help = "report only the available latest distros",
                       action = "store_true")

    # Architecture to use.
    names = sorted(architectures.Architecture.choices())
    default = architectures.Architecture.defaultChoice()
    parser.add_argument("--arch",
                        help = "report on available distributions" \
                                " for architecture; DEFAULT = {0}".format(
                                  default),
                        dest = "architecture",
                        choices = names,
                        default = default)


    parents = super(DistrosCommand, cls).parserParents()
    parents.append(parser)
    return parents

  ####################################################################
  # Overridden instance-behavior methods
  ####################################################################
  def run(self):
    all = not (self.args.latest or self.args.nightly or self.args.released)

    root = self._distributionRoot

    command.CommandShell(root).printChoices()

    print("\nDefault distribution: {0}".format(
          root.defaultDistribution()))

    print("\nRoots {0}:".format(self.args.architecture))

    if all or self.args.released:
      print("\tDefault ({0}):".format(root.defaultCategory()))
      for choice in root.choices():
        try:
          instance = root.makeItem(choice, self.args, self.args.architecture)
          print("\t\t{0}: {1}".format(instance.name(), instance.repoRoot))
        except DistributionUnknownCombinationException:
          pass

    if all or self.args.latest:
      print("\n\tLatest:")
      for choice in root.choicesLatest():
        try:
          instance = root.makeItemLatest(choice,
                                         self.args,
                                         self.args.architecture)
          print("\t\t{0}: {1}".format(instance.name(), instance.repoRoot))
        except DistributionUnknownCombinationException:
          pass

    if all or self.args.nightly:
      print("\n\tNightly:")
      for choice in root.choicesNightly():
        try:
          instance = root.makeItemNightly(choice,
                                          self.args,
                                          self.args.architecture)
          print("\t\t{0}: {1}".format(instance.name(), instance.repoRoot))
        except DistributionUnknownCombinationException:
          pass

    print("\nSpecial Roots {0}:".format(self.args.architecture))
    for choice in root.choices():
      try:
        instance = root.makeItem(choice,
                                 self.args,
                                 self.args.architecture)
        print("\t\t{0}: {1}".format(instance.name(),
                                    instance.specialRepoRoots))
      except DistributionUnknownCombinationException:
        pass

    print("\nBoot Options {0}:".format(self.args.architecture))
    for choice in root.choices():
      try:
        instance = root.makeItem(choice,
                                 self.args,
                                 self.args.architecture)
        print("\t\t{0}: {1}".format(instance.name(),
                                    instance.bootOptions))
      except DistributionUnknownCombinationException:
        pass

  ####################################################################
  # Protected factory-behavior methods
  ####################################################################

  ####################################################################
  # Protected instance-behavior methods
  ####################################################################
  @property
  def _distributionRoot(self):
    return Distribution

  ####################################################################
  # Private factory-behavior methods
  ####################################################################

  ####################################################################
  # Private instance-behavior methods
  ####################################################################
