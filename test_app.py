import unittest
from app import app
import json
import boto3
from moto import mock_dynamodb, mock_rekognition, mock_cloudwatch

class TestContentModeration(unittest.TestCase):
    @mock_dynamodb
    def setUp(self):
        """Set up test database"""
        self.dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
        
        # Create test table
        self.table = self.dynamodb.create_table(
            TableName='content-moderation-table',
            KeySchema=[
                {'AttributeName': 'ImageId', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'ImageId', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        
        self.app = app.test_client()

    @mock_rekognition
    def test_moderation_detection(self):
        """Test content moderation detection"""
        # Mock test event
        test_event = {
            "Records": [{
                "ImageId": "test-image-1",
                "ModerationLabels": [{
                    "Name": "Explicit Content",
                    "Confidence": 85.5
                }]
            }]
        }
        
        response = self.app.post('/process_image',
                               data=json.dumps(test_event),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
    @mock_cloudwatch
    def test_metrics(self):
        """Test metrics endpoint"""
        response = self.app.get('/get_metrics')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('processed_frames', data)
        self.assertIn('flagged_content', data)

if __name__ == '__main__':
    unittest.main()
