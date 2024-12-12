import boto3
from datetime import datetime
from decimal import Decimal
import uuid

dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
table = dynamodb.Table('content-moderation-table')

# Insert test record
table.put_item(
    Item={
        'ImageId': str(uuid.uuid4()),
        'stream_name': 'test-stream',
        'timestamp': datetime.now().isoformat(),
        'labels': [
            {
                'Name': 'Test Label',
                'Confidence': Decimal('95.0')
            }
        ],
        'status': 'flagged'
    }
)
print("Test record inserted") 