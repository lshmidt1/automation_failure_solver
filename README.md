# automation_failure_solver

## Overview
The `automation_failure_solver` project is designed to handle failure events through a series of AWS Lambda functions. It ingests failure data, analyzes it, and triggers necessary actions based on the analysis. This project utilizes Terraform for infrastructure management and includes scripts for building and deploying the Lambda functions.

## Project Structure
```
automation_failure_solver
├── lambdas
│   ├── notify
│   │   ├── notify.py
│   │   ├── requirements.txt
│   │   └── events
│   │       └── notify_event.json
│   ├── solver
│   │   ├── handler.py
│   │   ├── requirements.txt
│   │   └── events
│   │       └── solver_event.json
│   ├── ingest_failure
│   │   ├── lambda_ingest_failure.py
│   │   └── requirements.txt
│   └── analyze_failure
│       ├── worker_analyze_failure.py
│       └── requirements.txt
├── terraform
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── modules
│       └── lambda
│           ├── main.tf
│           └── variables.tf
├── scripts
│   ├── build_lambda.sh
│   ├── package_lambda.sh
│   └── deploy.sh
├── tests
│   ├── unit
│   │   ├── test_notify.py
│   │   └── test_solver.py
│   └── integration
│       └── test_integration.py
├── events
│   ├── sample_notify_event.json
│   └── sample_solver_event.json
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup Instructions
1. **Clone the Repository**
   ```
   git clone <repository-url>
   cd automation_failure_solver
   ```

2. **Install Dependencies**
   Navigate to each Lambda function directory and install the required dependencies listed in the `requirements.txt` files.

3. **Configure Terraform**
   Update the `variables.tf` file with your specific configurations and run the following commands to set up the infrastructure:
   ```
   terraform init
   terraform apply
   ```

4. **Build Packages**
   Use the provided scripts to build and package the Lambda functions:
   ```
   ./scripts/build_packages.sh
   ```

5. **Deploy**
   Deploy the packaged Lambda functions using the deployment script:
   ```
   ./scripts/deploy.sh
   ```

## Usage
- The `ingest_failure` Lambda function processes incoming failure events.
- The `analyze_failure` Lambda function analyzes the data received from the `ingest_failure` function.
- The `notify` and `solver` functions handle notifications and further processing based on the analysis.

## Testing
Sample events for testing the Lambda functions are provided in the `events` directory. Use these events to simulate API Gateway and SQS events for testing purposes.

## Contribution
Feel free to contribute to this project by submitting issues or pull requests. Please ensure that your code adheres to the project's coding standards and includes appropriate tests.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.