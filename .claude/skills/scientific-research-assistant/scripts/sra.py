#!/usr/bin/env python3
"""Entry point: python sra.py <command> [options]. Run with --help for commands."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sra.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
