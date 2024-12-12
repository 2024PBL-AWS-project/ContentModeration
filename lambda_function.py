import boto3
import json
import logging
from botocore.exceptions import ClientError
from datetime import datetime
import time
from decimal import Decimal
import uuid

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Initialize AWS clients
rekognition = boto3.client('rekognition', region_name='us-west-2')
kinesis_video = boto3.client('kinesisvideo', region_name='us-west-2')
sns = boto3.client('sns', region_name='us-west-2')

def lambda_handler(event, context):
    """Lambda handler to process video streams through Rekognition Content Moderation"""
    logger.info("Received event: %s", json.dumps(event))
    
    try:
        # Extract stream name from the event
        stream_name = event['detail']['requestParameters']['StreamName']
        
        # Get stream endpoint
        endpoint = kinesis_video.get_data_endpoint(
            StreamName=stream_name,
            APIName='GET_MEDIA'
        )['DataEndpoint']
        
        # Create Kinesis Video Media client
        kvs_client = boto3.client('kinesis-video-media', 
                                endpoint_url=endpoint,
                                region_name='us-west-2')
        
        # Get the media stream
        stream = kvs_client.get_media(
            StreamName=stream_name,
            StartSelector={'StartSelectorType': 'NOW'}
        )
        
        # Process frames through Rekognition
        response = rekognition.detect_moderation_labels(
            Image={'Bytes': stream['Payload'].read()},
            MinConfidence=80.0
        )
        
        # Process moderation results
        if response['ModerationLabels']:
            dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
            table = dynamodb.Table('content-moderation-table')
            
            # Format labels
            formatted_labels = [{
                'Name': label['Name'],
                'Confidence': Decimal(str(label['Confidence']))
            } for label in response['ModerationLabels']]
            
            # Store in DynamoDB
            table.put_item(Item={
                'ImageId': str(uuid.uuid4()),
                'stream_name': stream_name,
                'timestamp': datetime.now().isoformat(),
                'labels': formatted_labels,
                'status': 'flagged'
            })
            
            # Send SNS notification
            sns.publish(
                TopicArn='arn:aws:sns:us-west-2:794038244518:content-moderation-alerts',
                Message=json.dumps({
                    'stream_name': stream_name,
                    'labels': formatted_labels,
                    'timestamp': datetime.now().isoformat()
                })
            )
            
        return {
            'statusCode': 200,
            'body': json.dumps('Content moderation completed')
        }
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise