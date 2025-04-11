"""Contains the execution context for pyATS test scripts.

This module houses a Context class, which is created by the pyATS/EasyPy
jobfile runner and passed into each individual test script. It provides a
centralized point of access for the testbed adapter, corresponding device
adapters, and test script results.
"""

from utils.adapters import TestbedAdapter
from utils.results import TestResultCollector
from utils.types import RunningMode


class Context:
    """Execution context for pyATS test scripts.

    This class provides access to the testbed adapter, device adapters,
    and results for the test scripts.

    This *could* probably be a dataclass, but for now, we'll keep it
    as a class to facilitate future extensability and helper methods.
    """

    def __init__(
        self,
        test_case_identifier: str,
        test_case_title: str,
        task_id: str,
        mode: RunningMode,
        testbed_adapter: TestbedAdapter,
        test_result_collector: TestResultCollector,
        parameters_file: str,
    ) -> None:
        """Instantiates a new Context object."""
        self.test_case_identifier = test_case_identifier
        self.test_case_title = test_case_title
        self.task_id = task_id
        self.mode = mode
        self.testbed_adapter = testbed_adapter
        self.test_result_collector = test_result_collector
        self.parameters_file = parameters_file
