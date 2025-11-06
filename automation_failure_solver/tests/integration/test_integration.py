# filepath: automation_failure_solver/automation_failure_solver/tests/integration/test_integration.py

import unittest
from lambdas.notify.notify import lambda_handler  # Adjust the import based on your actual handler function
from lambdas.solver.handler import lambda_handler as solver_handler  # Adjust the import based on your actual handler function

class TestIntegration(unittest.TestCase):

    def test_notify_integration(self):
        # Sample event for notify Lambda function
        event = {
            "key": "value"  # Replace with actual event structure
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 200)  # Adjust based on expected response

    def test_solver_integration(self):
        # Sample event for solver Lambda function
        event = {
            "key": "value"  # Replace with actual event structure
        }
        response = solver_handler(event, None)
        self.assertEqual(response['statusCode'], 200)  # Adjust based on expected response

if __name__ == '__main__':
    unittest.main()