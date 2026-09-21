import os
import boto3
from botocore.exceptions import ClientError
from datetime import datetime

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "DigitanoProjects")

dynamodb = boto3.resource(
    "dynamodb",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

table = dynamodb.Table(TABLE_NAME)

def save_project_prd(user_id: str, project_id: str, prompt: str, generated_prd: dict) -> dict:
    """
    Saves or updates a project PRD in Amazon DynamoDB using Single-Table Design.
    PK: USER#<user_id>
    SK: PROJECT#<project_id>
    """
    item = {
        "PK": f"USER#{user_id}",
        "SK": f"PROJECT#{project_id}",
        "projectId": project_id,
        "userId": user_id,
        "originalPrompt": prompt,
        "prdData": generated_prd,
        "updatedAt": datetime.utcnow().isoformat(),
        "status": "COMPLETED"
    }

    try:
        table.put_item(Item=item)
        return {"status": "success", "projectId": project_id}
    except ClientError as e:
        print(f"DynamoDB PutItem Error: {e.response['Error']['Message']}")
        return {"status": "error", "message": e.response['Error']['Message']}

def get_project_prd(user_id: str, project_id: str) -> dict:
    """
    Fetches a single project PRD from DynamoDB.
    """
    try:
        response = table.get_item(
            Key={
                "PK": f"USER#{user_id}",
                "SK": f"PROJECT#{project_id}"
            }
        )
        item = response.get("Item")
        if not item:
            return {"status": "not_found", "message": f"Project {project_id} not found."}
        return {"status": "success", "data": item}
    except ClientError as e:
        print(f"DynamoDB GetItem Error: {e.response['Error']['Message']}")
        return {"status": "error", "message": e.response['Error']['Message']}
