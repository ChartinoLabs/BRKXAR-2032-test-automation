"""Contains constants used across pyATS test scripts."""

from pathlib import Path

# Save all parameters under the `parameters` directory at the root of the
# project.
PARAMETERS_DIR = Path(__file__).parent.parent.parent / "parameters"
