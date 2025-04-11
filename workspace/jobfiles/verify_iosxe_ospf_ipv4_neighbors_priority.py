"""
Verify OSPF IPv4 Neighbors Priority Test Job
------------------------------------------
This job file verifies that all OSPF IPv4 neighbors on the device
have the expected priority values.

Can run in two modes:
- learning: Learn current OSPF neighbor priority values and save to parameters JSON file
- testing: Verify OSPF neighbor priority values against saved parameters
"""

import logging

from pyats import aetest
from utils.connectivity import (
    connect_to_testbed_devices,
    disconnect_from_testbed_devices,
    run_command_on_devices,
    verify_testbed_device_connectivity,
)
from utils.context import Context
from utils.parameters import (
    validate_parameters_directory_exists,
)
from utils.reports import generate_job_report
from utils.runner import handle_test_execution_mode
from utils.types import ResultStatus, RunningMode

logger = logging.getLogger(__name__)


DESCRIPTION = (
    "The purpose of this test case is to validate the priority values of "
    "IPv4 OSPF neighbors on one or more IOS-XE devices. "
    "This verification ensures that each OSPF neighbor has the expected priority, which is critical "
    "for proper DR/BDR election in broadcast and non-broadcast networks.\n"
    "\n"
    "OSPF (Open Shortest Path First) uses priority values to determine the election of Designated Router (DR) "
    "and Backup Designated Router (BDR) in a network segment. "
    "Verifying the OSPF neighbor priority values is important for ensuring proper network convergence "
    "and stability. Incorrect priority settings can lead to suboptimal DR/BDR elections, "
    "potentially causing network instability or inefficient routing. "
    "This test helps identify any discrepancies in priority configurations that could impact network performance."
)

SETUP = (
    "* All devices are connected as per the network topology.\n"
    "* All devices are powered up and operational.\n"
    "* SSH connectivity to the devices is established.\n"
    "* Authentication against the devices is successful.\n"
)

PROCEDURE = (
    "* Establish connections to all target devices\n"
    "* Verify device connectivity to ensure all devices are accessible\n"
    "* Execute the *show ip ospf neighbor* command on each device\n"
    "* Parse the command output to extract interface names with active OSPF adjacencies, the associated neighbor Router IDs, and each neighbor's priority value\n"
    "* For each device, compare the current OSPF neighbor information against the below expected parameters. Record pass/fail results for each verification point.\n"
    "\n"
    "{% for device, interfaces in parameters.items() %}"
    "    * Device {{ device }}:\n"
    "{% for interface, interface_data in interfaces.items() %}"
    "        * Interface {{ interface }}:\n"
    "{% for neighbor_id, neighbor_data in interface_data.get('neighbors', {}).items() %}"
    "            * Verify neighbor {{ neighbor_id }} has priority value \"{{ neighbor_data.get('priority') }}\"\n"
    "{% endfor %}"
    "{% endfor %}"
    "{% endfor %}"
)

PASS_FAIL_CRITERIA = (
    "**This test passes when all of the following conditions are met:**\n"
    "\n"
    "* SSH connectivity to each device is successful\n"
    "* Authentication against each device is successful\n"
    "* All expected OSPF interfaces are present on each device\n"
    "* All expected OSPF neighbors are present on each interface\n"
    "* Each OSPF neighbor has the correct priority value\n"
    "\n"
    "**This test fails if any of the following criteria are met:**\n"
    "\n"
    "* One or more devices are unreachable over the network\n"
    "* One or more devices are not responsive to SSH connections\n"
    "* Authentication against one or more devices is unsuccessful\n"
    "* An expected OSPF interface is missing on a device\n"
    "* An expected OSPF neighbor is missing on an interface\n"
    "* An OSPF neighbor has an incorrect priority value\n"
)


class CommonSetup(aetest.CommonSetup):
    """Setup for script."""

    @aetest.subsection
    def connect_to_devices(self, context: Context):
        """Connect to all devices in the testbed."""
        connect_to_testbed_devices(context.testbed_adapter)

    @aetest.subsection
    def verify_connected(self, context: Context):
        """Verify that all devices are connected."""
        verify_testbed_device_connectivity(context.testbed_adapter, self.failed)

    @aetest.subsection
    def ensure_parameters_directory_exists(self):
        """Create parameters directory if it doesn't exist."""
        validate_parameters_directory_exists(self.failed)


class VerifyOSPFNeighborsPriority(aetest.Testcase):
    """
    Verify OSPF IPv4 Neighbors Priority Values
    """

    @aetest.setup
    def setup(self, context: Context):
        """
        Set test mode: learning or testing
        """
        self.mode = context.mode
        logger.info(f"Running in {self.mode} mode")

    def gather_current_state(self, context: Context) -> dict:
        """Gather the current state of each device."""
        all_devices_data = {}

        # Collect OSPF data from all devices using 'show ip ospf neighbor'
        parsed_data = run_command_on_devices(
            command="show ip ospf neighbor",
            testbed=context.testbed_adapter,
        )

        # Collect OSPF data from all devices
        for device in context.testbed_adapter.devices.values():
            execution_result = parsed_data.get(device.name)
            if execution_result is None:
                msg = f"No OSPF data found for device {device.name}"
                context.testbed_adapter.result_collector.add_result(
                    status=ResultStatus.FAILED,
                    message=msg,
                )
                self.failed(msg)
                continue

            data = execution_result.data

            # Check if there are any OSPF interfaces and neighbors
            if "interfaces" not in data or not data["interfaces"]:
                logger.warning(f"No OSPF interfaces found on {device.name}")
                all_devices_data[device.name] = {}
                context.testbed_adapter.result_collector.add_result(
                    status=ResultStatus.INFO,
                    message=f"No OSPF interfaces found on {device.name}",
                )
                continue

            # Process OSPF neighbors
            device_ospf_data = {}
            for interface_name, interface_data in data["interfaces"].items():
                if "neighbors" not in interface_data or not interface_data["neighbors"]:
                    continue

                if interface_name not in device_ospf_data:
                    device_ospf_data[interface_name] = {"neighbors": {}}

                # Process each neighbor
                for neighbor_id, neighbor_data in interface_data["neighbors"].items():
                    device_ospf_data[interface_name]["neighbors"][neighbor_id] = {
                        "priority": neighbor_data.get("priority", ""),
                    }
                    context.testbed_adapter.result_collector.add_result(
                        status=ResultStatus.INFO,
                        message=f"Found neighbor {neighbor_id} with priority {neighbor_data.get('priority', '')}",
                    )

            all_devices_data[device.name] = device_ospf_data
            context.testbed_adapter.result_collector.add_result(
                status=ResultStatus.PASSED,
                message=f"Successfully gathered OSPF data from {device.name}",
            )

        return all_devices_data

    def compare_expected_parameters_to_current_state(
        self,
        current_state: dict,
        expected_parameters: dict,
        context: Context,
    ) -> None:
        """Compare the current state of each device to the expected parameters for each device."""
        logger.info("Validating current state of devices against expected parameters")
        for expected_device_name, expected_device_data in expected_parameters.items():
            logger.info("Checking current state of device %s", expected_device_name)
            if expected_device_name not in current_state:
                msg = (
                    f"Expected device {expected_device_name} not found in current state"
                )
                context.testbed_adapter.result_collector.add_result(
                    status=ResultStatus.FAILED, message=msg
                )
                self.failed(msg)
                continue

            logger.info(
                f"Found expected device {expected_device_name} in current state"
            )
            context.testbed_adapter.result_collector.add_result(
                status=ResultStatus.PASSED,
                message=f"Found expected device {expected_device_name} in current state",
            )

            # Compare each interface and neighbor
            for interface_name, interface_data in expected_device_data.items():
                logger.info(
                    "Checking current state of interface %s on device %s",
                    interface_name,
                    expected_device_name,
                )
                if interface_name not in current_state[expected_device_name]:
                    msg = (
                        f"Interface {interface_name} not found in current state for device "
                        f"{expected_device_name}"
                    )
                    context.testbed_adapter.result_collector.add_result(
                        status=ResultStatus.FAILED, message=msg
                    )
                    self.failed(msg)
                    continue

                logger.info(
                    f"Found expected interface {interface_name} in current state for device "
                    f"{expected_device_name}"
                )
                context.testbed_adapter.result_collector.add_result(
                    status=ResultStatus.PASSED,
                    message=f"Found expected interface {interface_name}",
                )

                expected_neighbors = interface_data.get("neighbors", {})
                actual_neighbors = current_state[expected_device_name][
                    interface_name
                ].get("neighbors", {})

                logger.info(
                    "Comparing %d expected neighbors against %d current neighbors for interface "
                    "%s on device %s",
                    len(expected_neighbors),
                    len(actual_neighbors),
                    interface_name,
                    expected_device_name,
                )
                context.testbed_adapter.result_collector.add_result(
                    status=ResultStatus.INFO,
                    message=f"Found {len(actual_neighbors)} neighbors, expecting {len(expected_neighbors)}",
                )

                # Compare each expected neighbor
                for neighbor_id, expected_neighbor_data in expected_neighbors.items():
                    logger.info(
                        "Checking current state of neighbor %s on interface %s of device %s",
                        neighbor_id,
                        interface_name,
                        expected_device_name,
                    )
                    if neighbor_id not in actual_neighbors:
                        msg = (
                            f"Neighbor {neighbor_id} on interface {interface_name} not found in "
                            f"current state for device {expected_device_name}"
                        )
                        context.testbed_adapter.result_collector.add_result(
                            status=ResultStatus.FAILED, message=msg
                        )
                        self.failed(msg)
                        continue

                    logger.info(
                        f"Found expected neighbor {neighbor_id} on interface {interface_name} "
                        f"for device {expected_device_name}"
                    )
                    current_neighbor_data = actual_neighbors[neighbor_id]
                    current_neighbor_priority = current_neighbor_data.get("priority")
                    expected_neighbor_priority = expected_neighbor_data.get("priority")

                    logger.info(
                        "Comparing current priority '%s' of neighbor %s on interface %s of device %s "
                        "against expected priority '%s'",
                        current_neighbor_priority,
                        neighbor_id,
                        interface_name,
                        expected_device_name,
                        expected_neighbor_priority,
                    )
                    if current_neighbor_priority != expected_neighbor_priority:
                        msg = (
                            f"The current priority of neighbor {neighbor_id} on interface "
                            f"{interface_name} is {current_neighbor_priority}, which does not match "
                            "the expected priority of this neighbor which is "
                            f"{expected_neighbor_priority}"
                        )
                        context.testbed_adapter.result_collector.add_result(
                            status=ResultStatus.FAILED, message=msg
                        )
                        self.failed(msg)
                    else:
                        logger.info(
                            f"The current priority of neighbor {neighbor_id} on interface "
                            f"{interface_name} is {current_neighbor_priority}, which matches the "
                            f"expected priority of this neighbor which is {expected_neighbor_priority}"
                        )
                        context.testbed_adapter.result_collector.add_result(
                            status=ResultStatus.PASSED,
                            message=f"Neighbor {neighbor_id} priority matches expected: {current_neighbor_priority}",
                        )

    @aetest.test
    def verify_ospf_neighbors_priority(self, context: Context):
        """
        Learning mode: Learn OSPF neighbor priority values and save to parameters file
        Testing mode: Verify OSPF neighbor priority values against parameters file
        """
        handle_test_execution_mode(
            context,
            self.gather_current_state,
            self.compare_expected_parameters_to_current_state,
            self.mode,
            context.parameters_file,
            self.passed,
            self.failed,
        )


class CommonCleanup(aetest.CommonCleanup):
    """Cleanup for script."""

    @aetest.subsection
    def add_results_to_report(self, context: Context):
        """Add accumulated results to the HTML report."""
        if context.mode == RunningMode.TESTING:
            generate_job_report(
                task_id="ospf_neighbors_priority_detailed",
                title="OSPF IPv4 Neighbors Priority",
                description=DESCRIPTION,
                setup=SETUP,
                procedure=PROCEDURE,
                pass_fail_criteria=PASS_FAIL_CRITERIA,
                results=context.testbed_adapter.result_collector.results,
                command_executions=context.testbed_adapter.result_collector.command_executions,
                status=context.testbed_adapter.result_collector.status,
                parameters=context.testbed_adapter.parameters,
            )

    @aetest.subsection
    def disconnect_from_devices(self, context: Context):
        """Disconnect from all devices in the testbed."""
        disconnect_from_testbed_devices(context.testbed_adapter)
