"""Contains helper functions working with device connectivity.

These are often used as part of pyATS test script setup and teardown sections.
"""

import concurrent.futures
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Iterable

from utils.adapters import DeviceAdapter, TestbedAdapter

logger = logging.getLogger(__name__)


def connect_to_device(device: DeviceAdapter) -> None:
    """Connect to a device in a testbed."""
    logger.info("Connecting to device %s", device.name)
    start_time = time.time()
    device.connect(log_stdout=False)
    total_time = time.time() - start_time
    logger.info(
        "Successfully connected to device %s in %.2f seconds",
        device.name,
        total_time,
    )


def connect_to_testbed_devices(testbed: TestbedAdapter) -> None:
    """Connect to devices within a testbed."""
    logger.info("Connecting to devices in testbed")

    device_list = list(testbed)

    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=len(device_list)
    ) as executor:
        # Submit all device connection tasks to the executor
        futures = [executor.submit(connect_to_device, device) for device in device_list]

        # Wait for all tasks to complete
        concurrent.futures.wait(futures)

    total_time = time.time() - start_time
    logger.info(
        "Successfully connected to all devices in testbed in %.2f seconds", total_time
    )


def verify_testbed_device_connectivity(
    testbed: TestbedAdapter, failed_callable: Callable[[str], None]
) -> None:
    """Validate that all devices in the testbed are marked as connected."""
    logger.info("Verifying connection to all devices")
    for device in testbed:
        logger.info("Verifying connection to device %s", device.name)
        if not device.connected:
            failed_callable(f"Failed to connect to device {device.name}")
        else:
            logger.info("Device %s is connected", device.name)


@dataclass
class CommandExecutionResult:
    """Represents the result of executing a command on a device."""

    device: DeviceAdapter
    command: str
    output: str
    data: dict[str, Any]


def run_command_on_device(
    command: str, device: DeviceAdapter
) -> CommandExecutionResult:
    """Runs a command on a device and parses the output."""
    output = device.execute(command)
    logger.info(
        "Output of command '%s' from device %s:\n\n%s\n", command, device.name, output
    )
    data = device.parse(command, output=output)
    logger.info(
        "Parsed data resulting from output of command '%s' from device %s:\n\n%s\n",
        command,
        device.name,
        json.dumps(data, indent=4),
    )

    # Record this command execution
    device.testbed_adapter.result_collector.add_command_execution(
        device_name=device.name,
        command=command,
        output=output,
        data=data,
    )

    return CommandExecutionResult(
        device=device,
        command=command,
        output=output,
        data=data,
    )


def run_command_on_devices(
    command: str,
    testbed: TestbedAdapter | None = None,
    device: DeviceAdapter | None = None,
    devices: list[DeviceAdapter] | None = None,
) -> dict[str, CommandExecutionResult]:
    """Runs a command on one or more devices and parses the output."""
    target_devices: Iterable[DeviceAdapter] = []
    if testbed is not None:
        target_devices = list(testbed)
    elif device is not None:
        target_devices = [device]
    elif devices is not None:
        target_devices = devices
    else:
        raise ValueError(
            f"No target devices specified to execute command '{command}' against"
        )

    logger.info("Running command '%s' on devices: %d", command, len(target_devices))

    results = {}
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=len(target_devices)
    ) as executor:
        # Create a dictionary mapping futures to device names for result tracking
        future_to_device = {
            executor.submit(run_command_on_device, command, device): device
            for device in target_devices
        }

        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_device):
            device = future_to_device[future]
            try:
                result = future.result()
                results[device.name] = result
            except Exception as exc:
                logger.error(f"Device {device.name} generated an exception: {exc}")
                results[device.name] = None

    total_time = time.time() - start_time
    logger.info(
        "Successfully executed command '%s' on all devices in %.2f seconds",
        command,
        total_time,
    )

    return results


def disconnect_single_device(device: DeviceAdapter) -> None:
    """Helper function to disconnect from a single device."""
    logger.info(
        "Checking to see if we're currently connected to device %s", device.name
    )
    if device.connected:
        logger.info(
            "Currently connected to device %s, disconnecting now...",
            device.name,
        )
        start_time = time.time()
        device.disconnect()
        total_time = time.time() - start_time
        logger.info(
            "Successfully disconnected from device %s in %.2f seconds",
            device.name,
            total_time,
        )
    else:
        logger.info("Not currently connected to device %s", device.name)


def disconnect_from_testbed_devices(testbed: TestbedAdapter) -> None:
    """Disconnect from devices within a testbed using thread pool."""
    logger.info("Disconnecting from all devices")
    device_list = list(testbed)
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=len(device_list)
    ) as executor:
        # Submit all device disconnection tasks to the executor
        futures = [
            executor.submit(disconnect_single_device, device) for device in device_list
        ]

        # Wait for all tasks to complete
        concurrent.futures.wait(futures)

    total_time = time.time() - start_time
    logger.info("All device disconnections completed in %.2f seconds", total_time)
