#!/bin/bash

# This script deploys the Lambda functions and associated resources using Terraform.

set -e

# Navigate to the terraform directory
cd ../terraform

# Initialize Terraform
terraform init

# Plan the deployment
terraform plan

# Apply the deployment
terraform apply -y

# Navigate back to the scripts directory
cd ../scripts

echo "Deployment completed successfully."