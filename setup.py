#!/usr/bin/env python

import functools
import os
import platform
import setuptools
import sys
import yaml

# package_version and the rpm .spec version are to be kept in sync.
package_version = {"major": 1, "minor": 0, "patch": 13, "release": 2}
package_name = "resource-discovery"
# Subdirectory containg packages.
package_subdir = "discovery"

subpackages = [{"name": "architectures", "entry": "arches"},
               {"name": "distributions", "entry": "distros"},
               {"name": "repos", "entry": "repos"}]

config_file_name = "config.yml"

###############################################################################
def readFile(path):
  with open(path) as f:
    return f.read()

###############################################################################
def prefixed(src):
  if ("bdist_wheel" not in sys.argv) or ("--universal" not in sys.argv):
    src = python_prefixed(src)
  return src

###############################################################################
def python_prefixed(src):
  return "{0}-{1}".format(versioned("python"), src)

###############################################################################
def versioned(src):
  python_version = platform.python_version_tuple()[0]
  if ("bdist_wheel" in sys.argv) and ("--universal" in sys.argv):
    python_version = ""
  return "{0}{1}".format(src, python_version)

###############################################################################
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

# Meta configuration.
with open(os.path.join("meta-config.yml")) as f:
  meta_config = yaml.safe_load(f)["config"]

console_scripts = ["{0} = {1}.{2}:{3}".format(versioned(subpackage["entry"]),
                                              package_subdir,
                                              subpackage["name"],
                                              subpackage["entry"])
                    for subpackage in subpackages
                      if subpackage["entry"] is not None]

setup = functools.partial(
          setuptools.setup,
          name = python_prefixed(package_name),
          version = "{0}.{1}.{2}.{3}".format(package_version["major"],
                                             package_version["minor"],
                                             package_version["patch"],
                                             package_version["release"]),
          description = python_prefixed(package_name),
          author = "Joe Shimkus",
          author_email = "jshimkus@redhat.com",
          packages = setuptools.find_packages(exclude = []),
          entry_points = {
            "console_scripts" : console_scripts
          },
          install_requires = install_requires,
          zip_safe = False,
          classifiers = ([] if meta_config["classifiers"] is None
                            else meta_config["classifiers"]),
          license = (None if meta_config["license-file"] is None
                          else readFile(meta_config["license-file"]))
        )

# Individual package data.
package_data = {}
data_files = []

for subpackage in subpackages:
  with open(os.path.join(package_subdir,
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
                            [os.path.join(package_subdir, subpackage["name"],
                                          defaultsFileName)]))

    package_data[".".join([package_subdir,
                           subpackage["name"]])] = package_data_files

# Execute setup.
setup(package_data = package_data, data_files = data_files)
