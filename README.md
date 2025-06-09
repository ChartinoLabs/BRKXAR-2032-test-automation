# BRKXAR-2032 Test Automation

This project serves as a repository of test automation developed by Generative AI as part of Cisco Live 2025 session "Turbocharging Automated Network Testing with Generative AI" (BRKXAR-2032).

## Quick Start

### Install Dependencies

This project uses the [uv](https://github.com/astral-sh/uv) dependency manager for fast and reliable Python dependency management. Once uv is installed, you can install all dependencies for this project using the following command:

```sh
uv sync
```

### Testbed Configuration

The `testbed.yaml` file at the root of this project currently contains access details for a testbed internal to Cisco. This testbed is not accessible to the public through the Internet; however, you can modify the access details in this file to point to your own testbed.

The testbed used to develop the test automation in this project consists of four Catalyst 8000v routers running in Cisco Modeling Labs (CML). We recommend getting started with a similar testbed setup of at least four IOS-XE routers configured with OSPF between them.

### Command Line Usage

There are two execution modes for the test automation in this project: a **learning mode** and a **testing mode**. Both are detailed below.

#### Learning Mode

```bash
uv run pyats run job workspace/runner.py --testbed-file testbed.yaml --mode learning
```

#### Testing Mode

```bash
uv run pyats run job workspace/runner.py --testbed-file testbed.yaml --mode testing
```

### Test Results

After executing the test automation in the testing mode, human-friendly test results will be stored under the `test_report` directory. The main index page for the test report is the `test_results_summary.html` file, which contains an overview of all test cases that were executed, the status of their execution, and links to detailed test case results for each test case.

The quickest way to view the test results is to start a local web server on your development machine using Python's built-in HTTP server:

```bash
python -m http.server --directory test_report 9999
```

Then, open your web browser and navigate to `http://localhost:9999/test_results_summary.html` to view the test results.

> **Note**: If you leverage remote development environments, you will need to adjust `localhost` in the above URL to point to the IP address or FQDN (Fully Qualified Domain Name) of your remote development environment.
