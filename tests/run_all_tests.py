"""
StenoVision - Master Test Suite Runner
======================================
Convenience entry point executing the central modular master test suite runner.
"""

import sys
from pathlib import Path

# Add tests directory to path
tests_dir = Path(__file__).resolve().parent
if str(tests_dir) not in sys.path:
    sys.path.insert(0, str(tests_dir))

from run_master_suite import main

if __name__ == "__main__":
    main()
