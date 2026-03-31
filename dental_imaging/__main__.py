"""Allow ``python -m dental_imaging`` from the repository root."""

import sys

from dental_imaging.main import main

if __name__ == "__main__":
    sys.exit(main())
