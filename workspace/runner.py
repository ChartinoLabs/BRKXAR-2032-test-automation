"""Primary entrypoint for pyATS job execution."""

import argparse
import logging

from pyats.easypy import run
from utils.types import RunningMode

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

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


def main(runtime):
    """
    Main entry point for job file

    Args:
        runtime: runtime object provided by pyATS
    """
    # Parse command-line arguments
    args, unknown = parser.parse_known_args()

    logger.info(f"Running in {str(args.mode)} mode")

    # Execute test script with selected mode
    run(
        testscript="workspace/jobfiles/verify_iosxe_ospf_ipv4_neighbors_status.py",
        runtime=runtime,
        mode=args.mode,
    )


if __name__ == "__main__":
    main()
