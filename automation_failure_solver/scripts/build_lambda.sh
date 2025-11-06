#!/bin/bash

# This script builds the necessary packages for deployment, including packaging the Lambda functions and their dependencies.

set -e

# Define the directories
LAMBDA_DIR="lambdas"
DIST_DIR="dist"

# Create the distribution directory if it doesn't exist
mkdir -p $DIST_DIR

# Function to package a Lambda function
package_lambda() {
    local lambda_name=$1
    local requirements_file="$LAMBDA_DIR/$lambda_name/requirements.txt"
    local lambda_file="$LAMBDA_DIR/$lambda_name/*.py"

    # Install dependencies
    pip install -r $requirements_file -t $DIST_DIR/$lambda_name

    # Copy the Lambda function code
    cp $lambda_file $DIST_DIR/$lambda_name/
}

# Package each Lambda function
package_lambda "notify"
package_lambda "solver"

echo "Packaging complete. Lambda functions are located in the $DIST_DIR directory."