"""Contains utility functions used for generating customer-facing reports/deliverables."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import BaseLoader, Environment, StrictUndefined
from utils.constants import (
    AGGREGATED_REPORT_FILENAME,
    REPORT_ASSETS_DIR,
    REPORT_DIR,
    REPORT_RESULTS_DIR,
    TEST_RESULTS_DIR,
)
from utils.types import Result, ResultStatus


def ensure_results_dirs():
    """Create the necessary directories for storing results if they don't exist."""
    for directory in [
        TEST_RESULTS_DIR,
        REPORT_DIR,
        REPORT_ASSETS_DIR,
        REPORT_RESULTS_DIR,
    ]:
        directory.mkdir(parents=True, exist_ok=True)


def generate_job_report(
    task_id: str,
    title: str,
    description: str,
    setup: str,
    procedure: str,
    pass_fail_criteria: str,
    results: list[Result],
    status: ResultStatus,
    parameters: dict[str, Any],
) -> Path:
    """Generate an HTML report for a specific job execution.

    Args:
        task_id: Unique identifier for the task execution
        title: Test title
        description: Test description (from DESCRIPTION template)
        setup: Setup information (from SETUP template)
        procedure: Test procedure (from PROCEDURE template)
        pass_fail_criteria: Pass/fail criteria (from PASS_FAIL_CRITERIA template)
        results: Detailed results of the test execution
        passed: Whether the test passed or failed
        parameters: Test parameters used for template rendering

    Returns:
        Path to the generated HTML report file
    """
    ensure_results_dirs()

    passed = status == ResultStatus.PASSED

    jinja_environment = Environment(
        loader=BaseLoader,
        extensions=["jinja2.ext.do"],
        trim_blocks=True,
        lstrip_blocks=True,
        undefined=StrictUndefined,
    )

    # Prepare templates
    description_template = jinja_environment.from_string(description)
    setup_template = jinja_environment.from_string(setup)
    procedure_template = jinja_environment.from_string(procedure)
    pass_fail_criteria_template = jinja_environment.from_string(pass_fail_criteria)

    # Render with parameters as necessary
    if parameters:
        rendered_description = description_template.render(parameters=parameters)
        rendered_setup = setup_template.render(parameters=parameters)
        rendered_procedure = procedure_template.render(parameters=parameters)
        rendered_criteria = pass_fail_criteria_template.render(parameters=parameters)
    else:
        rendered_description = description_template.render()
        rendered_setup = setup_template.render()
        rendered_procedure = procedure_template.render()
        rendered_criteria = pass_fail_criteria_template.render()

    # Construct HTML variant of results.
    html_results = ""
    for result in results:
        # Font color should be a legible red if failed, and be a normal black if passed
        color = "#dc3545" if result["status"] != ResultStatus.PASSED else "#000000"
        html_results += f"""
            <div style="color: {color};">
                {result["message"]}
            </div>
            <br />
"""

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title} - Test Results</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .result-{{ 'pass' if passed else 'fail' }} {{
                color: {{ '#28a745' if passed else '#dc3545' }};
                font-weight: bold;
            }}
            section {{ margin-bottom: 30px; }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <div class="result-{"pass" if passed else "fail"}">
            Test Status: {"PASSED" if passed else "FAILED"}
        </div>

        <section>
            <h2>Description</h2>
            {rendered_description}
        </section>

        <section>
            <h2>Setup</h2>
            {rendered_setup}
        </section>

        <section>
            <h2>Procedure</h2>
            {rendered_procedure}
        </section>

        <section>
            <h2>Pass/Fail Criteria</h2>
            {rendered_criteria}
        </section>

        <section>
            <h2>Results</h2>
            {html_results}
        </section>

        <footer>
            <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </footer>
    </body>
    </html>
    """

    output_file = TEST_RESULTS_DIR / f"{task_id}_results.html"
    output_file.write_text(html_content)

    # Save metadata for aggregation
    metadata = {
        "task_id": task_id,
        "title": title,
        "passed": passed,
        "timestamp": datetime.now().isoformat(),
        "result_file": str(output_file),
    }
    metadata_file = TEST_RESULTS_DIR / f"{task_id}_metadata.json"
    metadata_file.write_text(json.dumps(metadata, indent=2))

    return output_file


def aggregate_reports(archive_path: Path | None = None) -> Path:
    """Aggregate all individual test results into a single HTML report.

    Args:
        archive_path: Optional path to the pyATS archive zip file to include

    Returns:
        Path to the aggregated report
    """
    metadata_files = list(TEST_RESULTS_DIR.glob("*_metadata.json"))
    all_results = []

    for metadata_file in metadata_files:
        metadata = json.loads(metadata_file.read_text())
        all_results.append(metadata)

    # Sort results by timestamp
    all_results.sort(key=lambda x: x["timestamp"])

    # Calculate summary statistics
    total_tests = len(all_results)
    passed_tests = sum(1 for result in all_results if result["passed"])

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Results Summary</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .summary {{ margin: 20px 0; padding: 20px; background: #f8f9fa; }}
            .test-result {{ margin: 10px 0; }}
            .pass {{ color: #28a745; }}
            .fail {{ color: #dc3545; }}
        </style>
    </head>
    <body>
        <h1>Test Results Summary</h1>

        <div class="summary">
            <h2>Executive Summary</h2>
            <p>Total Tests: {total_tests}</p>
            <p>Passed: {passed_tests}</p>
            <p>Failed: {total_tests - passed_tests}</p>
            <p>Success Rate: {(passed_tests / total_tests) * 100:.1f}%</p>
        </div>

        <h2>Test Results</h2>
        <div class="test-results">
    """

    for result in all_results:
        status_class = "pass" if result["passed"] else "fail"

        # Copy result file from current location to REPORT_RESULTS_DIR
        result_file = Path(result["result_file"])
        result_file_dest = REPORT_RESULTS_DIR / result_file.name
        result_file_dest.write_text(result_file.read_text())

        html_content += f"""
            <div class="test-result">
                <h3>{result["title"]}</h3>
                <p class="{status_class}">Status: {"PASSED" if result["passed"] else "FAILED"}</p>
                <p><a href="{result_file_dest.relative_to(REPORT_DIR)}">
                    View Detailed Results
                </a></p>
            </div>
        """

    if archive_path:
        html_content += f"""
        <div class="artifacts">
            <h2>Test Artifacts</h2>
            <p><a href="{archive_path.name}">Download Complete Test Archive</a></p>
        </div>
        """

    html_content += """
        </div>
    </body>
    </html>
    """

    output_file = REPORT_DIR / AGGREGATED_REPORT_FILENAME
    output_file.write_text(html_content)

    return output_file
