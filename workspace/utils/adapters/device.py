"""Contains the adapter/facade for pyATS device objects."""

from typing import TYPE_CHECKING, Any, cast

from pyats.topology.device import Device as PyatsDevice

if TYPE_CHECKING:
    from utils.adapters import TestbedAdapter


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

    def __init__(self, device: PyatsDevice, testbed_adapter: "TestbedAdapter"):
        """Initialize the device adapter.

        Args:
            device: The pyATS Device object to adapt
        """
        self.device = device
        self.testbed_adapter = testbed_adapter

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

    def parse(self, command: str, output: str | None = None) -> dict[str, Any]:
        """Parse the output of a command using the appropriate parser.

        Args:
            command: The command to parse
            output: Optional pre-collected output to parse; if None, the command will be executed

        Returns:
            A dictionary containing the parsed output
        """
        if output is None:
            return cast(dict[str, Any], self.device.parse(command))
        return cast(dict[str, Any], self.device.parse(command, output=output))

    def configure(self, commands: str | list[str]) -> str:
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
