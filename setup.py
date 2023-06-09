#!/usr/bin/env python

import functools
import os
import platform
import setuptools
import sys
import yaml

package_name = "resource-discovery"
package_prefix = "discovery"
subpackages = [{"name": "architectures", "entry": "arches"},
               {"name": "distributions", "entry": "distros"},
               {"name": "repos", "entry": "repos"}]
config_file_name = "config.yml"

def readFile(path):
  with open(path) as f:
    return f.read()

def prefixed(src):
  if ("bdist_wheel" not in sys.argv) or ("--universal" not in sys.argv):
    src = python_prefixed(src)
  return src

def python_prefixed(src):
  return "{0}-{1}".format(versioned("python"), src)

def versioned(src):
  python_version = platform.python_version_tuple()[0]
  if ("bdist_wheel" in sys.argv) and ("--universal" in sys.argv):
    python_version = ""
  return "{0}{1}".format(src, python_version)

console_scripts = ["{0} = {1}.{2}:{3}".format(versioned(subpackage["entry"]),
                                              package_prefix,
                                              subpackage["name"],
                                              subpackage["entry"])
                    for subpackage in subpackages]

# Establish the installation requirements based on being invoked as part of
# building an RPM.
#
# If building an RPM specifying installation requirements here results in
# dependencies that are not met.  Working around this requires that the RPM
# .spec file specifies dependencies itself.
install_requires = ["{0} >= 1.0.0".format(python_prefixed("utility-mill"))]
try:
  os.environ["RPM_PACKAGE_NAME"]
  install_requires = []
except KeyError:
  pass

setup = functools.partial(
          setuptools.setup,
          name = python_prefixed(package_name),
          version = "1.0.12",
          description = python_prefixed(package_name),
          author = "Joe Shimkus",
          author_email = "jshimkus@redhat.com",
          packages = setuptools.find_packages(exclude = []),
          entry_points = {
            "console_scripts" : console_scripts
          },
          install_requires = install_requires,
          zip_safe = False,
          classifiers = [
            "License :: OSI Approved :: GNU General Public License v2 (GPLv2)"
          ],
          license = readFile(os.path.join(package_prefix, "LICENSE.txt"))
        )

package_data = {}
data_files = []

for subpackage in subpackages:
  with open(os.path.join(package_prefix,
                         subpackage["name"],
                         config_file_name)) as f:
    defaults = yaml.safe_load(f)["config"]["defaults"]
    defaultsFileName = defaults["name"]
    defaultsInstallDir = defaults["install-dir"]

    # If there is a defaults file we need to install it in the correct location.
    package_data_files = [config_file_name]
    if defaultsFileName is not None:
      # If the install directory is None the defaults file is installed as part
      # of the subpackage.  If not, that's where the defaults is to be
      # installed.
      if defaultsInstallDir is None:
        package_data_files.append(defaultsFileName)
      else:
        data_files.append((defaultsInstallDir,
                            [os.path.join(package_prefix, subpackage["name"],
                                          defaultsFileName)]))

    package_data[".".join([package_prefix,
                           subpackage["name"]])] = package_data_files

# Execute setup.
setup(package_data = package_data, data_files = data_files)
