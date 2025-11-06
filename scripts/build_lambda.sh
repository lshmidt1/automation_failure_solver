#!/bin/bash
set -e

# Define the directories
LAMBDA_DIR="lambdas"
DIST_DIR="dist"

# Create the distribution directory if it doesn't exist
rm -rf $DIST_DIR
mkdir -p $DIST_DIR

# Function to package a Lambda function
package_lambda() {
    local lambda_name=$1
    local requirements_file="$LAMBDA_DIR/$lambda_name/requirements.txt"
    local temp_dir=$(mktemp -d)
    
    echo "Building $lambda_name..."
    
    # Install dependencies if requirements.txt exists
    if [ -f $requirements_file ]; then
        pip install -r $requirements_file -t $temp_dir
    fi
    
    # Copy the Lambda function code
    cp $LAMBDA_DIR/$lambda_name/*.py $temp_dir/
    
    # Create ZIP file
    (cd $temp_dir && zip -r $DIST_DIR/${lambda_name}.zip .)
    
    # Cleanup
    rm -rf $temp_dir
    
    echo "✓ Created ${lambda_name}.zip"
}

# Package each Lambda function
package_lambda "ingest_failure"
package_lambda "analyze_failure"

echo "Packaging complete. Zips located in $DIST_DIR/"
ls -lh $DIST_DIR/