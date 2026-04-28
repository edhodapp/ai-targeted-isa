"""Module entry: ``python -m ai_targeted_isa_ontology``."""

# pylint: disable=invalid-name
# __main__ is the standard Python convention for module-style invocation.

import sys

from ai_targeted_isa_ontology.build import main

if __name__ == "__main__":
    sys.exit(main())
