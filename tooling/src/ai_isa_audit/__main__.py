"""Module entry: ``python -m ai_isa_audit``."""

# pylint: disable=invalid-name
# __main__ is the standard Python convention for module-style invocation.

import sys

from ai_isa_audit.cli import main

if __name__ == "__main__":
    sys.exit(main())
