"""Utilities for generating and managing customer-facing HTML test results."""

import logging

from .types import CommandExecution, ResultStatus

logger = logging.getLogger(__name__)


class TestResultCollector:
    """Collects and stores test results throughout test execution.

    This class provides methods to accumulate results without affecting test flow,
    similar to self.passed() and self.failed() but without controlling execution.
    Results are stored in the runtime object for access across test cases.
    """

    def __init__(self):
        """Initialize the result collector."""
        self.results = []
        self.command_executions: list[CommandExecution] = []

    @property
    def status(self) -> ResultStatus:
        """Get the overall status of the collected results.

        INFO results are ignored when determining the overall status.
        If all results are INFO or PASSED, the status is PASSED.
        Otherwise, returns the first non-PASSED, non-INFO status found.
        """
        for result in self.results:
            if (
                result["status"] != ResultStatus.PASSED
                and result["status"] != ResultStatus.INFO
            ):
                return result["status"]
        return ResultStatus.PASSED

    def add_result(self, status: ResultStatus, message: str):
        """Add a result to the collection.

        Args:
            status: Result status from ResultStatus enum (e.g., ResultStatus.PASSED)
            message: Detailed result message
        """
        logger.info("[RESULT][%s] %s", status, message)
        self.results.append(
            {
                "status": status,
                "message": message,
            }
        )

    def add_command_execution(
        self, device_name: str, command: str, output: str, data: dict | None = None
    ):
        """Add a command execution record to the collection.

        Args:
            device_name: Name of the device where the command was executed
            command: The command that was executed
            output: The output of the command execution
        """
        logger.debug("Recording command execution on %s: %s", device_name, command)
        self.command_executions.append(
            {
                "device_name": device_name,
                "command": command,
                "output": output,
                "data": data if data is not None else {},
            }
        )
