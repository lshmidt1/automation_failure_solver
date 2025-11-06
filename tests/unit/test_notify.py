# File: automation_failure_solver/tests/unit/test_notify.py

import json
import pytest
from lambdas.notify.notify import lambda_handler

def test_lambda_handler_success():
    event = {
        "key": "value"  # Replace with actual event structure
    }
    context = {}  # Mock context if needed
    response = lambda_handler(event, context)
    assert response['statusCode'] == 200
    assert 'body' in response

def test_lambda_handler_failure():
    event = {
        "key": "invalid_value"  # Replace with actual event structure that causes failure
    }
    context = {}  # Mock context if needed
    response = lambda_handler(event, context)
    assert response['statusCode'] == 400
    assert 'error' in response['body']