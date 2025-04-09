"""Contains type definitions for pyATS test scripts."""

from enum import Enum
from typing import Any


class RunningMode(str, Enum):
    """The mode under which pyATS test scripts are running."""

    LEARNING = "learning"
    TESTING = "testing"


ParameterData = dict[str, Any]
