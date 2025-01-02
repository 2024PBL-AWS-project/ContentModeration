import boto3
import cv2
import json
import time

def test_moderation_pipeline():
    # Initialize clients
    kvs = boto3.client('kinesisvideo', region_name='us-west-2')
    dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
    table = dynamodb.Table('content-moderation-table')
    
    try:
        # Test video stream
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        if ret:
            print("✅ Camera access successful")
        
        # Test DynamoDB
        response = table.scan(Limit=1)
        print("✅ DynamoDB access successful")
        
        # Test CloudWatch Logs
        logs = boto3.client('logs', region_name='us-west-2')
        response = logs.describe_log_groups()
        print("✅ CloudWatch Logs access successful")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
    finally:
        if 'cap' in locals():
            cap.release()

if __name__ == "__main__":
    test_moderation_pipeline() 