# filepath: c:\Users\lshmidt\source\repos\automation_failure_solver\lambdas\notify\notify.py
import json
import os
import requests

def lambda_handler(event, context):
    # Extract necessary information from the event
    message = event.get('Records')[0].get('Sns').get('Message')
    
    # Prepare the notification payload
    payload = {
        "text": f"Notification: {message}"
    }
    
    # Send notification to Slack
    slack_webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    response = requests.post(slack_webhook_url, json=payload)
    
    # Check for successful response
    if response.status_code != 200:
        raise ValueError(f"Request to Slack returned an error {response.status_code}, the response is:\n{response.text}")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Notification sent successfully!')
    }