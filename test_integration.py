import unittest
import boto3
import json
from app import app

class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.s3 = boto3.client('s3')
        self.rekognition = boto3.client('rekognition')
        self.dynamodb = boto3.resource('dynamodb')
        
    def test_end_to_end_flow(self):
        # Test video feed endpoint
        response = self.app.get('/video_feed')
        self.assertEqual(response.status_code, 200)
        
        # Test results endpoint
        response = self.app.get('/get_results')
        self.assertEqual(response.status_code, 200)
        
        # Test metrics endpoint
        response = self.app.get('/get_metrics')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
