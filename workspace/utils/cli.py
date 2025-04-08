"""Contains the CLI definition for the main pyATS jobfile runner."""

import argparse

from utils.types import RunningMode


def define_parser() -> argparse.Namespace:
    """Creates the argparse Namespace for the command line interface."""

    parser = argparse.ArgumentParser(description="OSPF Neighbor Validation")
    parser.add_argument(
        "--mode",
        type=RunningMode,
        choices=list(RunningMode),
        default=RunningMode.TESTING,
        help=(
            "Mode to run: learning (update test case parameters) or testing "
            "(validate against test case parameters)"
        ),
    )
    parser.add_argument(
        "--test-plan",
        type=str,
        default="test_plan.yaml",
        help="Path to the test plan YAML file",
    )
    return parser
