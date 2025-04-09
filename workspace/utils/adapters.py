"""Contains adapter classes for pyATS objects to improve IDE support.

These adapter classes wrap pyATS objects to provide better type hints and
docstring information, making it easier to work with them in IDEs that
support code completion and type checking.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterator, List, Optional, Union, cast

from pyats.topology.device import Device as PyatsDevice
from pyats.topology.testbed import Testbed as PyatsTestbed

logger = logging.getLogger(__name__)


class DeviceAdapter:
    """Adapter for pyATS Device objects.

    Provides typed access to common Device methods with better IDE integration.

    Attributes:
        name (str): The device name
        os (str): The operating system of the device
        type (str): The device type (e.g., 'router', 'switch')
        connected (bool): Whether the device is currently connected
        device (PyatsDevice): The underlying pyATS Device object
    """

    def __init__(self, device: PyatsDevice):
        """Initialize the device adapter.

        Args:
            device: The pyATS Device object to adapt
        """
        self.device = device

    @property
    def name(self) -> str:
        """Get the device name."""
        return cast(str, self.device.name)

    @property
    def os(self) -> str:
        """Get the device operating system."""
        return cast(str, self.device.os)

    @property
    def type(self) -> str:
        """Get the device type."""
        return cast(str, self.device.type)

    @property
    def connected(self) -> bool:
        """Return whether the device is connected."""
        return cast(bool, self.device.connected)

    def connect(self, *, log_stdout: bool = True) -> None:
        """Connect to the device.

        Args:
            log_stdout: Whether to log output to stdout
        """
        self.device.connect(log_stdout=log_stdout)

    def disconnect(self) -> None:
        """Disconnect from the device."""
        self.device.disconnect()

    def execute(self, command: str) -> str:
        """Execute a command on the device.

        Args:
            command: The command to execute

        Returns:
            The command output as a string
        """
        return cast(str, self.device.execute(command))

    def parse(self, command: str, output: Optional[str] = None) -> Dict[str, Any]:
        """Parse the output of a command using the appropriate parser.

        Args:
            command: The command to parse
            output: Optional pre-collected output to parse; if None, the command will be executed

        Returns:
            A dictionary containing the parsed output
        """
        if output is None:
            return cast(Dict[str, Any], self.device.parse(command))
        return cast(Dict[str, Any], self.device.parse(command, output=output))

    def configure(self, commands: Union[str, List[str]]) -> str:
        """Configure the device with one or more commands.

        Args:
            commands: A single command string or list of command strings

        Returns:
            The configuration output
        """
        return cast(str, self.device.configure(commands))

    def __getattr__(self, name: str) -> Any:
        """Pass through any other attributes to the underlying device object."""
        return getattr(self.device, name)

    def __repr__(self) -> str:
        """Return a string representation of the device."""
        return f"DeviceAdapter(name='{self.name}', os='{self.os}', connected={self.connected})"


class TestbedAdapter:
    """Adapter for pyATS Testbed objects.

    Provides typed access to common Testbed methods with better IDE integration.

    Attributes:
        name (str): The testbed name
        devices (Dict[str, DeviceAdapter]): Dictionary of device adapters keyed by device name
        testbed (PyatsTestbed): The underlying pyATS Testbed object
    """

    def __init__(self, testbed: PyatsTestbed):
        """Initialize the testbed adapter.

        Args:
            testbed: The pyATS Testbed object to adapt
        """
        self.testbed = testbed
        self._device_adapters: Dict[str, DeviceAdapter] = {}

    @property
    def name(self) -> str:
        """Get the testbed name."""
        return cast(str, self.testbed.name)

    @property
    def devices(self) -> Dict[str, DeviceAdapter]:
        """Get a dictionary of device adapters."""
        # Lazily create device adapters as needed
        for device_name, device in self.testbed.devices.items():
            if device_name not in self._device_adapters:
                self._device_adapters[device_name] = DeviceAdapter(device)
        return self._device_adapters

    def get_device(self, device_name: str) -> DeviceAdapter:
        """Get a device adapter by name.

        Args:
            device_name: The name of the device

        Returns:
            A DeviceAdapter for the specified device

        Raises:
            KeyError: If the device is not found in the testbed
        """
        if device_name not in self.devices:
            raise KeyError(f"Device {device_name} not found in testbed")
        return self.devices[device_name]

    def connect_device(self, device_name: str, *, log_stdout: bool = True) -> None:
        """Connect to a specific device.

        Args:
            device_name: The name of the device to connect to
            log_stdout: Whether to log output to stdout

        Raises:
            KeyError: If the device is not found in the testbed
        """
        self.get_device(device_name).connect(log_stdout=log_stdout)

    def disconnect_device(self, device_name: str) -> None:
        """Disconnect from a specific device.

        Args:
            device_name: The name of the device to disconnect from

        Raises:
            KeyError: If the device is not found in the testbed
        """
        self.get_device(device_name).disconnect()

    def __iter__(self) -> Iterator[DeviceAdapter]:
        """Iterate over device adapters in the testbed."""
        for device_name in self.testbed.devices:
            yield self.devices[device_name]

    def __len__(self) -> int:
        """Return the number of devices in the testbed."""
        return len(self.testbed.devices)

    def __getitem__(self, key: str) -> DeviceAdapter:
        """Get a device adapter by name."""
        return self.get_device(key)

    def __getattr__(self, name: str) -> Any:
        """Pass through any other attributes to the underlying testbed object."""
        return getattr(self.testbed, name)

    def __repr__(self) -> str:
        """Return a string representation of the testbed."""
        return (
            f"TestbedAdapter(name='{self.name}', devices={list(self.devices.keys())})"
        )


def adapt_testbed(testbed: PyatsTestbed) -> TestbedAdapter:
    """Create a TestbedAdapter from a pyATS Testbed object.

    Args:
        testbed: The pyATS Testbed object to adapt

    Returns:
        A TestbedAdapter for the testbed
    """
    return TestbedAdapter(testbed)


def adapt_device(device: PyatsDevice) -> DeviceAdapter:
    """Create a DeviceAdapter from a pyATS Device object.

    Args:
        device: The pyATS Device object to adapt

    Returns:
        A DeviceAdapter for the device
    """
    return DeviceAdapter(device)
