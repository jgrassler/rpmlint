import re

from os import path

from rpm import expandMacro
from rpmlint.checks.AbstractCheck import AbstractFilesCheck
from rpmlint.helpers import byte_to_string

# Warning messages
WARNS = {
    "tests": "python-tests-in-site-packages",
    "doc": "python-doc-in-site-packages",
    "src": "python-src-in-site-packages"
  }

# Errorr messages
ERRS = {
    "egg-distutils": "python-egg-info-distutils-style",
    "bad-requires": "python-requires-egg-info-mismatch"
  }


WARN_PATHS = {
    "/usr/lib*/python*/site-packages/test": WARNS["tests"],
    "/usr/lib*/python*/site-packages/tests": WARNS["tests"],
    "/usr/lib*/python*/site-packages/doc": WARNS["doc"],
    "/usr/lib*/python*/site-packages/docs": WARNS["doc"],
    "/usr/lib*/python*/site-packages/src": WARNS["src"]
  }

class PythonFileCheck(AbstractFilesCheck):
    def __init__(self, config, output):
        super().__init__(config, output, r'.*')

    def check_file(self, pkg, filename):
      egg_info_re = r'.*egg-info$'

      if egg_info_re.match(filename):
        self.check_egginfo(pkg, filename)

      # Output warnings for paths that shouldn't be in any packages, but might
      # need to be under sufficiently special circumstances.
      for path in WARN_PATHS:
        path_re = re.compile(path)

        if path_re.match(filename):
          self.output.add_info("W", pkg, WARN_PATHS[path])

    def check_egginfo(self, pkg, filename):
      """
      Check type of egg-info metadata and check Requires against egg-info
      metadata if applicable.
      """
      # Check for (deprecated) distutils style metadata.
      if os.path.isfile(pkg.dirName() + filename):
        self.output.add_info("E", pkg, ERRS["egg-distutils"])
        # No need to proceed any further here since distutils style metadata
        # doesn't have requirements information.
        return

      # egg-info is a directory, check requires.txt against spec's Requires.
      # We will ignore packages that do not have a requires.txt here.
      requires_file = pkg.dirName() + filename + "requires.txt"
      if os.path.isfile(requires_path):
        self.compare_requires(pkg, requires_path)

    def check_egginfo_requires(self, pkg, requires_path):
      from_egg = egg_requires(requires_path)

    def egg_requires(self, requires_path):
      """
      Generate a dictionary of requires/versions from an egg-info directory's
      requires.txt.
      """
      raise NotImplementedError

    def package_requires(self, pkg):
      """
      Generate a dictionary of requires/versions from the package's specs.
      """
      raise NotImplementedError
