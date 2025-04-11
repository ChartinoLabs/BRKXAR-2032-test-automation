"""Contains utility functions used for generating customer-facing reports/deliverables."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import markdown
from utils import templates
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


def convert_markdown_to_html(markdown_text: str) -> str:
    """Convert markdown text to HTML.

    Args:
        markdown_text: Markdown-formatted text to convert

    Returns:
        HTML-formatted text
    """
    html = markdown.markdown(
        markdown_text,
        extensions=["extra", "codehilite", "tables", "fenced_code", "toc", "nl2br"],
    )
    return html


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

    # Render content with parameters as necessary
    if parameters:
        rendered_description = templates.render_string_template(
            description, parameters=parameters
        )
        rendered_setup = templates.render_string_template(setup, parameters=parameters)
        rendered_procedure = templates.render_string_template(
            procedure, parameters=parameters
        )
        rendered_criteria = templates.render_string_template(
            pass_fail_criteria, parameters=parameters
        )
    else:
        rendered_description = templates.render_string_template(description)
        rendered_setup = templates.render_string_template(setup)
        rendered_procedure = templates.render_string_template(procedure)
        rendered_criteria = templates.render_string_template(pass_fail_criteria)

    # Convert rendered markdown to HTML
    rendered_description_html = convert_markdown_to_html(rendered_description)
    rendered_setup_html = convert_markdown_to_html(rendered_setup)
    rendered_procedure_html = convert_markdown_to_html(rendered_procedure)
    rendered_criteria_html = convert_markdown_to_html(rendered_criteria)

    # Format results for the template
    formatted_results = []
    for result in results:
        formatted_results.append(
            {
                "message": result["message"],
                "status": "PASSED"
                if result["status"] == ResultStatus.PASSED
                else "FAILED",
            }
        )

    # Render the report using the template utility
    html_content = templates.render_template(
        "test_case/report.html.j2",
        title=title,
        description_html=rendered_description_html,
        setup_html=rendered_setup_html,
        procedure_html=rendered_procedure_html,
        criteria_html=rendered_criteria_html,
        results=formatted_results,
        passed=passed,
        generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

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


def aggregate_reports() -> Path:
    """Aggregate all individual test results into a single HTML report.

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
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

    # Format results for the template
    formatted_results = []
    for result in all_results:
        # Copy result file from current location to REPORT_RESULTS_DIR
        result_file = Path(result["result_file"])
        result_file_dest = REPORT_RESULTS_DIR / result_file.name
        result_file_dest.write_text(result_file.read_text())

        formatted_results.append(
            {
                "task_id": result["task_id"],
                "title": result["title"],
                "passed": result["passed"],
                "timestamp": result["timestamp"],
                "result_file_path": str(result_file_dest.relative_to(REPORT_DIR)),
            }
        )

    # Render the report using the template utility
    html_content = templates.render_template(
        "summary/report.html.j2",
        generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_tests=total_tests,
        passed_tests=passed_tests,
        success_rate=success_rate,
        results=formatted_results,
    )

    output_file = REPORT_DIR / AGGREGATED_REPORT_FILENAME
    output_file.write_text(html_content)

    return output_file
