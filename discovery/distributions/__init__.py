#
# SPDX-License-Identifier: GPL-2.0-only
#
# Copyright Red Hat
#
from __future__ import print_function

from .CentOS import CentOS
from .Fedora import Fedora
from .RHEL import RHEL
from .Distribution import (Distribution,
                           DistributionNoDefaultException,
                           DistributionUnknownCombinationException)
from .DistrosCommand import DistrosCommand

from mill import command
def distros():
  command.CommandShell(DistrosCommand).run()
