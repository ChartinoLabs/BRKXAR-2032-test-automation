"""Contains constants used across pyATS test scripts."""

from pathlib import Path

# Save all parameters under the `parameters` directory at the root of the
# project.
PARAMETERS_DIR = Path(__file__).parent.parent.parent / "parameters"

# Customer-facing results directories
TEST_RESULTS_DIR = Path(__file__).parent.parent.parent / "test_results"
REPORT_DIR = Path(__file__).parent.parent.parent / "test_report"
REPORT_ASSETS_DIR = REPORT_DIR / "assets"
REPORT_RESULTS_DIR = REPORT_DIR / "results"
AGGREGATED_REPORT_FILENAME = "test_results_summary.html"

# Template names for job files
TEMPLATE_NAMES = {
    "description": "DESCRIPTION",
    "setup": "SETUP",
    "procedure": "PROCEDURE",
    "pass_fail_criteria": "PASS_FAIL_CRITERIA",
}
