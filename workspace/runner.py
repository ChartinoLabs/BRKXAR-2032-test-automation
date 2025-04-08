"""Primary entrypoint for pyATS job execution."""

import logging
from pathlib import Path

import yaml
from pyats.easypy import run
from utils.cli import define_parser

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def main(runtime):
    """
    Main entry point for job file

    Args:
        runtime: runtime object provided by pyATS
    """
    # Parse command-line arguments
    args, unknown = define_parser().parse_known_args()

    logger.info(f"Running in {str(args.mode)} mode")

    # Validate provided test plan path exists
    raw_test_plan_path = args.test_plan
    test_plan_path = Path(raw_test_plan_path).resolve()
    logger.info("Test plan filepath provided is '%s'", test_plan_path)
    if not test_plan_path.exists():
        logger.error("Test plan file does not exist: %s", test_plan_path)
        raise FileNotFoundError(f"Test plan file does not exist: {test_plan_path}")

    # Load test plan from YAML file
    with open(test_plan_path, "r") as f:
        test_plan = yaml.safe_load(f)

    base_jobfile_directory = Path(test_plan["jobfile_directory"]).resolve()

    for test_case_identifier, test_case_data in test_plan["test_cases"].items():
        # Construct task ID
        task_id = f"{test_case_identifier} - {test_case_data['title']}"
        # Construct full jobfile path relative to the base jobfile directory
        jobfile_path = base_jobfile_directory / test_case_data["jobfile"]

        logger.info(
            "Executing test case '%s' tied to jobfile at '%s'", task_id, jobfile_path
        )

        run(
            testscript=str(jobfile_path),
            runtime=runtime,
            mode=args.mode,
            task_id=task_id,
        )


if __name__ == "__main__":
    main()
