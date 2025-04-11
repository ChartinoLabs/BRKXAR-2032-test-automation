"""Contains the adapter/facade for pyATS testbed objects."""

from typing import Any, Iterator, cast

from pyats.topology.testbed import Testbed as PyatsTestbed
from utils.adapters.device import DeviceAdapter
from utils.results import TestResultCollector
from utils.types import ParameterData


class TestbedAdapter:
    """Adapter for pyATS Testbed objects.

    Provides typed access to common Testbed methods with better IDE integration.

    Attributes:
        name (str): The testbed name
        devices (Dict[str, DeviceAdapter]): Dictionary of device adapters keyed by device name
        testbed (PyatsTestbed): The underlying pyATS Testbed object
        results: TestResultCollector for recording test results
    """

    def __init__(self, testbed: PyatsTestbed):
        """Initialize the testbed adapter.

        Args:
            testbed: The pyATS Testbed object to adapt
        """
        self.testbed = testbed
        self._device_adapters: dict[str, DeviceAdapter] = {}
        self.result_collector = TestResultCollector()
        self.parameters: ParameterData = {}

    @property
    def name(self) -> str:
        """Get the testbed name."""
        return cast(str, self.testbed.name)

    @property
    def devices(self) -> dict[str, DeviceAdapter]:
        """Get a dictionary of device adapters."""
        # Lazily create device adapters as needed
        for device_name, device in self.testbed.devices.items():
            if device_name not in self._device_adapters:
                self._device_adapters[device_name] = DeviceAdapter(device, self)
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
