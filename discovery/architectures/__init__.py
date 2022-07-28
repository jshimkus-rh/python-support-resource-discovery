from __future__ import print_function

from .Architecture import Architecture
from .ARM import AArch64, Armhfp
from .PPC import PPC64, PPC64LE
from .S390 import S390X
from .X86 import I386, X86_64

from mill import factory
def arches():
  factory.FactoryShell(Architecture).printChoices()
  print("Default choice: {0}".format(Architecture.defaultChoice()))
