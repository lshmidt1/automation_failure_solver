# Automation Test Failure Root Cause Solver

An AI-powered system to automatically identify and classify root causes of failed automation tests, helping developers quickly understand and resolve test failures.

## Project Overview

This project explores using AI to analyze test failures and classify their root causes (e.g., production bugs, test bugs, environmental issues, flaky tests, etc.). By automatically identifying the underlying reason for test failures, we aim to significantly reduce the time developers spend on manual failure investigation.

## Project Evolution

### Hackathon Phase (Preliminary Work)

The initial exploration was developed during a hackathon and can be found in the **`Hackathon/`** folder. This early work focused primarily on:
- UI/UX design and user experience
- Basic proof of concept architecture
- AWS Lambda-based infrastructure with Terraform
- Initial workflow for ingesting and analyzing test failures

**Infrastructure Components:**
- `ingest_failure` Lambda: Processes incoming failure events
- `analyze_failure` Lambda: Analyzes failure data
- `notify` and `solver` Lambdas: Handle notifications and further processing
- Terraform configuration for infrastructure management
- Local web dashboard for visualization

For detailed setup instructions, see the hackathon folder's README.

### POC - Discovery Phase (Current Work)

We are now conducting a serious feasibility assessment to determine if this approach is viable for production use. This work can be found in the **`POC - Discovery/`** folder.

**Current Focus:**
- Evaluating AI accuracy in classifying test failure root causes
- Testing different AI approaches (basic vs. multi-node workflows)
- Measuring performance, cost, and ROI
- Working with real test failure data
- Assessing technical feasibility and limitations

**Status:** POC Complete - Initial feasibility has been proven. See [`POC - Discovery/README.md`](POC%20-%20Discovery/README.md) for detailed results.

## Root Cause Categories

The system classifies test failures into distinct categories:
- **Production Code Bug**: Bugs in the application code being tested
- **Test Code Bug**: Issues in the test code itself (assertions, setup, mocking, etc.)
- **Environmental Issues**: Missing dependencies, configuration problems, file system issues
- **Flaky Tests**: Timing issues, race conditions, non-deterministic behavior
- **Infrastructure**: Network failures, service unavailability, database timeouts
- **Data Issues**: Invalid test data, incorrect database state, missing fixtures
- **Breaking Changes**: API changes, deprecated functionality, interface modifications

## Project Structure

```
.
├── Hackathon/                    # Original hackathon work (preliminary)
│   └── automation_failure_solver/
│       ├── lambdas/              # AWS Lambda functions
│       │   ├── ingest_failure/
│       │   ├── analyze_failure/
│       │   ├── notify/
│       │   └── solver/
│       ├── local/                # Local development & UI dashboard
│       ├── terraform/            # Infrastructure as code
│       ├── scripts/              # Build and deployment scripts
│       └── tests/                # Unit and integration tests
│
└── POC - Discovery/              # Current feasibility assessment
    ├── notebooks/                # Jupyter notebooks for POC
    ├── docs/                     # Test failure data samples
    └── README.md                 # Detailed POC results & findings
```

## Quick Start

### For Hackathon Work
The hackathon phase implemented a Lambda-based infrastructure:

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd automation_failure_solver/Hackathon/automation_failure_solver
   ```

2. **Install Dependencies**
   Navigate to each Lambda function directory and install dependencies from `requirements.txt`

3. **Configure Terraform**
   ```bash
   cd terraform
   terraform init
   terraform apply
   ```

4. **Build & Deploy**
   ```bash
   ./scripts/build_packages.sh
   ./scripts/deploy.sh
   ```

### For POC Work
See [`POC - Discovery/README.md`](POC%20-%20Discovery/README.md) for:
- Setting up AWS Bedrock with Claude
- Running the Jupyter notebooks
- Understanding the different AI approaches tested
- Viewing POC results and conclusions

## Technology Stack

### Hackathon Phase
- AWS Lambda (Python)
- AWS Bedrock for LLM access
- Terraform for infrastructure
- Local web dashboard for visualization

### POC Phase
- Python 3.x
- AWS Bedrock with Claude 3 Sonnet
- LangGraph for multi-node workflows
- Jupyter notebooks for experimentation

## Current Status

**POC Phase: Complete**
- Initial accuracy results are promising

**Next Steps:**
- Test with larger dataset of real failures
- Integrate actual test source code (not dummy data)
- Measure accuracy against human expert classifications
- Calculate detailed ROI metrics
- Plan MVP architecture and integration with CI/CD pipelines

## Contributing

This is currently an internal exploratory project. For questions or contributions, please contact the project maintainers.

## License

Internal project - not for external distribution
