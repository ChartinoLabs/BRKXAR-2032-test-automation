"""Contains utility functions for saving and loading parameter files."""

import json
import logging
from pathlib import Path
from typing import Callable

from utils.constants import PARAMETERS_DIR
from utils.types import ParameterData

logger = logging.getLogger(__name__)


def validate_parameters_directory_exists(
    failed_callable: Callable[[str], None],
) -> None:
    """Validate that the parameters directory exists."""
    if PARAMETERS_DIR.exists() is False:
        logger.info(f"Creating parameters directory: {PARAMETERS_DIR}")
        try:
            PARAMETERS_DIR.mkdir(parents=True, exist_ok=True)
            logger.info("Parameters directory created successfully")
        except Exception as e:
            logger.error(f"Failed to create parameters directory: {e}")
            failed_callable(f"Failed to create parameters directory: {e}")
            raise


def save_parameters_to_file(data: ParameterData, parameters_file: str | Path) -> bool:
    """
    Save test case parameters to a JSON file

    Args:
        data: Data structure with parameters to save
        parameters_file: Path to the JSON file where parameters will be saved

    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("Saving test case parameters to file '%s'", parameters_file)

    # Write parameters to JSON file
    try:
        with open(str(parameters_file), "w") as f:
            json.dump(data, f, indent=4)
            # Add newline to the end to make pre-commit hooks happy
            f.write("\n")
        logger.info("Successfully saved parameters to file '%s'", parameters_file)
        return True
    except Exception as e:
        logger.error("Failed to write parameters to file '%s': %s", e)
        raise


def load_parameters_from_file(parameters_file: str | Path) -> ParameterData:
    """
    Load test case parameters from JSON file

    Returns:
        ParameterData: Data structure with parameters loaded from file
    """
    logger.info("Loading OSPF parameters from file '%s'", parameters_file)

    true_parameters_file = (
        Path(parameters_file)
        if not isinstance(parameters_file, Path)
        else parameters_file
    )

    if true_parameters_file.exists() is False:
        logger.warning("Parameters file '%s' not found", parameters_file)
        return {}

    try:
        with open(str(true_parameters_file), "r") as f:
            parameters = json.load(f)
        logger.info(
            "Successfully loaded OSPF parameters from file '%s'", parameters_file
        )
        return parameters
    except Exception as e:
        logger.error("Failed to load parameters file '%s': %s", parameters_file, e)
        return {}
