"""Contains utility functions used for flow control in test cases."""

import logging
from typing import Callable

from utils.context import Context
from utils.parameters import (
    load_parameters_from_file,
    save_parameters_to_file,
)
from utils.types import ParameterData, ResultStatus, RunningMode

logger = logging.getLogger(__name__)


def handle_test_execution_mode(
    context: Context,
    current_state_callable: Callable[[Context], dict],
    comparison_callable: Callable[[dict, ParameterData, Context], None],
    mode: RunningMode,
    parameters_file: str,
    passing_callable: Callable[[str], None],
    failing_callable: Callable[[str], None],
) -> None:
    """Handles the flow control of test execution based upon provided mode."""
    current_state = current_state_callable(context)

    # LEARNING MODE: Save the collected data to parameters file
    if mode == "learning":
        if save_parameters_to_file(current_state, parameters_file):
            result_msg = "Successfully learned parameters and saved to file"
            passing_callable(result_msg)
            context.testbed_adapter.result_collector.add_result(
                status=ResultStatus.PASSED, message=result_msg
            )
        else:
            result_msg = "Failed to save parameters to file"
            failing_callable(result_msg)
            context.testbed_adapter.result_collector.add_result(
                status=ResultStatus.FAILED, message=result_msg
            )
    # TESTING MODE: Verify against parameters file
    else:
        # Load expected parameters
        expected_parameters = load_parameters_from_file(parameters_file)
        context.testbed_adapter.parameters = expected_parameters
        if not expected_parameters:
            result_msg = "No expected parameters found. Run in learning mode first."
            failing_callable(result_msg)
            context.testbed_adapter.result_collector.add_result(
                status=ResultStatus.FAILED, message=result_msg
            )
            return

        logger.info("Comparing current state to expected parameters")
        try:
            comparison_callable(current_state, expected_parameters, context)
            result_msg = (
                "The current state of the device has been successfully "
                "validated against the expected parameters."
            )
            passing_callable(result_msg)
            context.testbed_adapter.result_collector.add_result(
                status=ResultStatus.PASSED, message=result_msg
            )
        except Exception as e:
            result_msg = str(e)
            failing_callable(result_msg)
            context.testbed_adapter.result_collector.add_result(
                status=ResultStatus.FAILED, message=result_msg
            )
