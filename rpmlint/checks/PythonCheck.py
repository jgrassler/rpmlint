import os
import re
import requirements

from rpmlint.checks.AbstractCheck import AbstractFilesCheck

# Warning messages
WARNS = {
    "tests": "python-tests-in-package",
    "doc": "python-doc-in-package",
    "req-missing": "python-egginfo-require-not-in-spec",
    "src": "python-src-in-package"
  }

# Error messages
ERRS = {
    "egg-distutils": "python-egg-info-distutils-style",
    "tests": "python-tests-in-site-packages",
    "doc": "python-doc-in-site-packages",
    "src": "python-src-in-site-packages"
  }

# Paths that shouldn't be in any packages, ever, because they clobber global
# name space.
ERR_PATHS = {
    "/usr/lib[^/]*/python[^/]*/site-packages/tests?$": ERRS["tests"],
    "/usr/lib[^/]*/python[^/]*/site-packages/docs?$": ERRS["doc"],
    "/usr/lib[^/]*/python[^/]*/site-packages/src$": ERRS["src"]
  }

# Paths that shouldn't be in any packages, but might need to be under
# sufficiently special circumstances.
WARN_PATHS = {
    "/usr/lib[^/]*/python[^/]*/site-packages/[^/]+/tests?$": WARNS["tests"],
    "/usr/lib[^/]*/python[^/]*/site-packages/[^/]+/docs?$": WARNS["doc"],
    "/usr/lib[^/]*/python[^/]*/site-packages/[^/]+/src$": WARNS["src"]
  }

class PythonCheck(AbstractFilesCheck):
    def __init__(self, config, output):
        super().__init__(config, output, r'.*')

    def check_file(self, pkg, filename):
      egg_info_re = re.compile('.*egg-info$')

      if egg_info_re.match(filename):
        self.check_egginfo(pkg, filename)

      for path in WARN_PATHS:
        path_re = re.compile(path)

        if path_re.match(filename):
          self.output.add_info("W", pkg, WARN_PATHS[path], filename)

      for path in ERR_PATHS:
        path_re = re.compile(path)

        if path_re.match(filename):
          self.output.add_info("E", pkg, ERR_PATHS[path], filename)

    def check_egginfo(self, pkg, filename):
      """
      Check type of egg-info metadata and check Requires against egg-info
      metadata if applicable.
      """
      # Check for (deprecated) distutils style metadata.
      if os.path.isfile(pkg.dirName() + filename):
        self.output.add_info("E", pkg, ERRS["egg-distutils"], filename)
        # No need to proceed any further here since distutils style metadata
        # doesn't have requirements information.
        return

      # egg-info is a directory, check requires.txt against spec's Requires.
      # We will ignore packages that do not have a requires.txt here.
      requires_path = pkg.dirName() + filename + "/" + "requires.txt"
      if os.path.isfile(requires_path):
        self.compare_requires(pkg, requires_path)

    def compare_requires(self, pkg, requires_path):
      """
      Check whether each egg name from requirements.txt occurs in the spec's
      Requirements somewhere and output a warning if it's nowhere to be found.
      """
      from_egg = self.egg_requires(requires_path)
      from_spec = self.package_requires(pkg)

      for egg_require in from_egg:
        found = False
        for spec_require in from_spec:

          if egg_require in spec_require:
            found = True

        if not found:
          self.output.add_info("W", pkg, WARNS["req-missing"], requires_path, ":", egg_require)

    def egg_requires(self, requires_path):
      """
      Generate a flat list of unversioned, lowercase require names from an
      egg-info directory's requires.txt.
      """

      try:
        f = open(requires_path, 'r')
      except Exception:
        # Some .egg-info directories do not have a requires.txt, so this may
        # fail.
        return

      lines = ""
      requires = []

      for line in f.readlines():
        # FIXME: this code ignores conditional sections, such as
        #
        #   [:python_version < '3']
        #
        # It does this because requirements-parser cannot deal with these
        # sections, hence we just filter out the section header. The best
        # approach for fixing this would be submitting patch against
        # requirements-parser that adds the capability to deal with sections by
        # adding such conditionals to every require in that section as
        # environment markers. Once such a patch exists, we can filter such
        # markers here on a per-requirement basis.

        if line.startswith("["):
          continue
        lines += line

      requires_raw = requirements.parser.parse(lines)

      for r in requires_raw:
        requires.append(r.name.lower())

      f.close()

      return requires

    def package_requires(self, pkg):
      """
      Generate a flat list of unversioned, lowercase requirement names from the
      package's, spec.
      """

      requires_raw = pkg.requires
      requires = []

      for r in requires_raw:
        requires.append(r[0].lower())

      return requires
