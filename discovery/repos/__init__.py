#
# SPDX-License-Identifier: GPL-2.0-only
#
# Copyright Red Hat
#
from .CentOS import CentOS
from .Fedora import Fedora
from .ReposCommand import ReposCommand
from .Repository import Repository
from .RHEL import RHEL

from mill import command
def repos():
  command.CommandShell(ReposCommand).run()
