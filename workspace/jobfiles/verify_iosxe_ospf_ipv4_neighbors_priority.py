"""Verify OSPF IPv4 neighbor priority values on Cisco IOS-XE devices."""

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
            context=context,
        )

        # Collect OSPF data from all devices
        for device in context.testbed_adapter.devices.values():
            execution_result = parsed_data.get(device.name)
            if execution_result is None:
                msg = (
                    f"The test was unable to retrieve OSPF neighbor data from device "
                    f"{device.name}. This could indicate that OSPF is not configured "
                    f"on the device, the device is unreachable, or there is an issue "
                    f"with the command execution. This behavior is unexpected, so this "
                    f"test case must fail."
                )
                context.test_result_collector.add_result(
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
                context.test_result_collector.add_result(
                    status=ResultStatus.INFO,
                    message=(
                        f"On device {device.name}, the output of the *show ip ospf "
                        f"neighbor* command indicates that there are no OSPF interfaces "
                        f"with active neighbors. This may be normal if OSPF is not "
                        f"configured or if no neighbor relationships have been "
                        f"established on this device."
                    ),
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
                    context.test_result_collector.add_result(
                        status=ResultStatus.INFO,
                        message=(
                            f"On device {device.name}, the output of the *show ip ospf "
                            f"neighbor* command indicates that interface {interface_name} "
                            f"has an OSPF neighbor with router ID {neighbor_id} with a "
                            f"priority value of {neighbor_data.get('priority', '')}. The "
                            f"priority value is used in DR/BDR election and is significant "
                            f"for network topology stability."
                        ),
                    )

            all_devices_data[device.name] = device_ospf_data
            context.test_result_collector.add_result(
                status=ResultStatus.PASSED,
                message=(
                    f"The test successfully gathered OSPF neighbor priority information "
                    f"from device {device.name} using the *show ip ospf neighbor* "
                    f"command. All data was retrieved and parsed correctly. This behavior "
                    f"is as expected for this test phase."
                ),
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
                    f"The test expected to find device {expected_device_name} in the "
                    f"current network state, but the device was not found or was not "
                    f"accessible. This could indicate that the device is offline, has "
                    f"been renamed, or is not properly configured in the testbed. This "
                    f"behavior is unexpected, so this test case must fail."
                )
                context.test_result_collector.add_result(
                    status=ResultStatus.FAILED, message=msg
                )
                self.failed(msg)
                continue

            logger.info(
                f"Found expected device {expected_device_name} in current state"
            )
            context.test_result_collector.add_result(
                status=ResultStatus.PASSED,
                message=(
                    f"The test successfully verified that device {expected_device_name} "
                    f"exists in the current network state and is accessible. This behavior "
                    f"is as expected."
                ),
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
                        f"The test expected to find interface {interface_name} on device "
                        f"{expected_device_name}, but this interface was not present in "
                        f"the current state or does not have any active OSPF neighbors. "
                        f"This could indicate a configuration change, interface shutdown, "
                        f"or OSPF process issue on this interface. This behavior is "
                        f"unexpected, so this test case must fail."
                    )
                    context.test_result_collector.add_result(
                        status=ResultStatus.FAILED, message=msg
                    )
                    self.failed(msg)
                    continue

                logger.info(
                    f"Found expected interface {interface_name} in current state for device "
                    f"{expected_device_name}"
                )
                context.test_result_collector.add_result(
                    status=ResultStatus.PASSED,
                    message=(
                        f"On device {expected_device_name}, the test verified that "
                        f"interface {interface_name} exists and has active OSPF neighbors. "
                        f"This confirms the interface is operational and participating in "
                        f"the OSPF process. This behavior is as expected."
                    ),
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
                context.test_result_collector.add_result(
                    status=ResultStatus.INFO,
                    message=(
                        f"On device {expected_device_name}, interface {interface_name} "
                        f"currently has {len(actual_neighbors)} OSPF neighbors, while the "
                        f"expected number of neighbors is {len(expected_neighbors)}. This "
                        f"information will be used for detailed comparison."
                    ),
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
                            f"On device {expected_device_name}, interface {interface_name} "
                            f"is missing an expected OSPF neighbor with router ID "
                            f"{neighbor_id}. This could indicate a connectivity issue, "
                            f"OSPF configuration change, or that the neighbor router is "
                            f"down. This behavior is unexpected, so this test case must fail."
                        )
                        context.test_result_collector.add_result(
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
                            f"On device {expected_device_name}, interface {interface_name}, "
                            f"the OSPF neighbor with router ID {neighbor_id} has a priority "
                            f"value of {current_neighbor_priority}, which does not match the "
                            f"expected priority value of {expected_neighbor_priority}. This "
                            f"could indicate a configuration change on the neighbor router or "
                            f"an issue with the OSPF process. Incorrect priority values can "
                            f"affect DR/BDR election and network stability. This behavior is "
                            f"unexpected, so this test case must fail."
                        )
                        context.test_result_collector.add_result(
                            status=ResultStatus.FAILED, message=msg
                        )
                        self.failed(msg)
                    else:
                        logger.info(
                            f"The current priority of neighbor {neighbor_id} on interface "
                            f"{interface_name} is {current_neighbor_priority}, which matches the "
                            f"expected priority of this neighbor which is {expected_neighbor_priority}"
                        )
                        context.test_result_collector.add_result(
                            status=ResultStatus.PASSED,
                            message=(
                                f"On device {expected_device_name}, interface {interface_name}, "
                                f"the OSPF neighbor with router ID {neighbor_id} has the expected "
                                f"priority value of {current_neighbor_priority}. This confirms "
                                f"that the DR/BDR election process is working with the correct "
                                f"configuration parameters. This behavior is as expected."
                            ),
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
                results=context.test_result_collector.results,
                command_executions=context.test_result_collector.command_executions,
                status=context.test_result_collector.status,
                parameters=context.testbed_adapter.parameters,
            )

    @aetest.subsection
    def disconnect_from_devices(self, context: Context):
        """Disconnect from all devices in the testbed."""
        disconnect_from_testbed_devices(context.testbed_adapter)
