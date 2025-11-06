#!/bin/bash

# This script packages the Lambda functions and their dependencies.

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
    local package_dir="$DIST_DIR/$lambda_name"

    # Create package directory for the Lambda function
    mkdir -p $package_dir

    # Install dependencies
    if [ -f $requirements_file ]; then
        pip install -r $requirements_file -t $package_dir
    fi

    # Copy the Lambda function code
    cp $lambda_file $package_dir/

    echo "Packaged $lambda_name successfully."
}

# Package each Lambda function
package_lambda "notify"
package_lambda "solver"

echo "All Lambda functions packaged successfully."