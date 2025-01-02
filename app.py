import sys
print("Python path:", sys.path)

from flask import Flask, render_template, Response, jsonify
import cv2
import boto3
from datetime import datetime, timedelta
import logging
import uuid
from decimal import Decimal
import watchtower
import sys
import json
import atexit
import os
from dotenv import load_dotenv
from boto3 import client

# Load environment variables
load_dotenv()

# Debug logging
print("AWS Access Key:", os.getenv('AWS_ACCESS_KEY_ID', 'Not found'))
print("AWS Secret Key:", os.getenv('AWS_SECRET_ACCESS_KEY', 'Not found')[:5] + '...' if os.getenv('AWS_SECRET_ACCESS_KEY') else 'Not found')

try:
    # Test AWS credentials
    sts = boto3.client('sts')
    identity = sts.get_caller_identity()
    print(f"AWS Identity Check: {identity['Arn']}")
except Exception as e:
    print(f"AWS Credentials Error: {e}")

# Configure AWS credentials
boto3.setup_default_session(
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name='us-west-2'
)

app = Flask(__name__, static_folder='static')

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
rekognition = boto3.client('rekognition', region_name='us-west-2')
table = dynamodb.Table('content-moderation-table')
cloudwatch_logs = boto3.client('logs', region_name='us-west-2')
cloudwatch = client('cloudwatch')

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

try:
    sts = boto3.client('sts')
    identity = sts.get_caller_identity()
    logger.info(f"AWS Identity Check: {identity['Arn']}")
except Exception as e:
    logger.error(f"AWS Credentials Error: {e}")

try:
    # Check if table exists
    table.table_status
except Exception as e:
    logger.info("Creating DynamoDB table...")
    table = dynamodb.create_table(
        TableName='content-moderation-table',
        KeySchema=[
            {'AttributeName': 'ImageId', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'ImageId', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'TimestampIndex',
                'KeySchema': [
                    {'AttributeName': 'timestamp', 'KeyType': 'HASH'},
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )
    table.wait_until_exists()

def setup_cloudwatch_logging():
    try:
        LOG_GROUP_NAME = '/aws/content-moderation-dashboard'
        stream_name = f'app-logs-{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}'
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Set up CloudWatch handler with modified config
        cloudwatch_handler = watchtower.CloudWatchLogHandler(
            log_group=LOG_GROUP_NAME,  # Changed from log_group_name
            stream_name=stream_name,
            boto3_client=cloudwatch_logs,
            use_queues=False,
            send_interval=1,
            create_log_group=True
        )
        
        # Add console handler for local debugging
        console_handler = logging.StreamHandler(sys.stdout)
        
        # Set formatter for both handlers
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        cloudwatch_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add both handlers
        logger.addHandler(cloudwatch_handler)
        logger.addHandler(console_handler)
        
        print(f"Log stream name: {stream_name}")
        logger.info("Application starting...")
        
        return cloudwatch_handler
    except Exception as e:
        print(f"Failed to set up CloudWatch logging: {e}")
        return None

# Set up logging before running the app
cloudwatch_handler = setup_cloudwatch_logging()

def put_metric_data(metric_name, value, unit='Count'):
    try:
        cloudwatch.put_metric_data(
            Namespace='ContentModerationDashboard',
            MetricData=[{
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'StorageResolution': 1
            }]
        )
    except Exception as e:
        logger.error(f"Error putting metric data: {e}")

def process_frame(frame):
    try:
        logger.info("Starting to process new frame")
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        
        response = rekognition.detect_moderation_labels(
            Image={'Bytes': frame_bytes},
            MinConfidence=20.0
        )
        
        logger.debug(f"Rekognition Response: {response}")
        put_metric_data("FlaggedContent",1)
        formatted_labels = [
            {
                'Name': label['Name'],
                'Confidence': Decimal(str(label['Confidence']))
            }
            for label in response['ModerationLabels']
        ]
        
        for label in formatted_labels:
            logger.debug(f"Found label: {label['Name']} with confidence {label['Confidence']}")

        is_flagged = len(formatted_labels) > 0
        
        # Store in DynamoDB
        try:
            current_time = datetime.now().isoformat()
            table.put_item(Item={
                'ImageId': str(uuid.uuid4()),
                'timestamp': current_time,
                'created_at': current_time,
                'labels': formatted_labels,
                'status': 'flagged' if is_flagged else 'ok'
            })
            logger.info(f"Successfully stored results in DynamoDB (flagged: {is_flagged})")
        except Exception as e:
            logger.error(f"DynamoDB error: {e}")
            
        if is_flagged:
            send_moderation_metrics(response['ModerationLabels'])
            
    except Exception as e:
        logger.error(f"Error processing frame: {str(e)}")

def generate_frames():
    try:
        if not hasattr(generate_frames, 'cap'):
            # Try different camera indices if 0 doesn't work
            for camera_index in range(3):  # Try indices 0, 1, 2
                generate_frames.cap = cv2.VideoCapture(camera_index)
                if generate_frames.cap.isOpened():
                    logger.info(f"Camera opened successfully on index {camera_index}")
                    break
            
            if not generate_frames.cap.isOpened():
                logger.error("Failed to open camera on any index")
                return
            
            # Set camera properties
            generate_frames.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            generate_frames.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            generate_frames.cap.set(cv2.CAP_PROP_FPS, 30)
            generate_frames.frame_count = 0
        
        while True:
            ret, frame = generate_frames.cap.read()
            if not ret:
                logger.error("Failed to read frame")
                # Try to reinitialize camera
                generate_frames.cap.release()
                generate_frames.cap = cv2.VideoCapture(0)
                continue
                
            if generate_frames.frame_count % 30 == 0:
                process_frame(frame)
            
            generate_frames.frame_count += 1
            
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                   
    except Exception as e:
        logger.error(f"Camera error: {str(e)}")
        yield b''

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering template: {e}")
        return str(e), 500

@app.route('/video_feed')
def video_feed():
    try:
        return Response(generate_frames(),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    except Exception as e:
        logger.error(f"Video feed error: {str(e)}")
        return "Camera error", 500

@app.route('/get_results')
def get_results():
    try:
        # 현재 시간부터 과거 방향으로 검색
        current_time = datetime.now().isoformat()
        one_day_ago = (datetime.now() - timedelta(days=1)).isoformat()
        
        # 먼저 scan으로 시도
        response = table.scan(
            FilterExpression='#ts BETWEEN :start_ts AND :end_ts',
            ExpressionAttributeNames={
                '#ts': 'timestamp'
            },
            ExpressionAttributeValues={
                ':start_ts': one_day_ago,
                ':end_ts': current_time
            }
        )
        
        items = response.get('Items', [])
        
        # 시간순 정렬
        items.sort(key=lambda x: x['timestamp'], reverse=True)
        items = items[:10]  # 최근 10개만
        
        # Decimal을 float로 변환
        for item in items:
            if 'labels' in item:
                for label in item['labels']:
                    if 'Confidence' in label:
                        label['Confidence'] = float(label['Confidence'])
        
        return jsonify(items)
    except Exception as e:
        logger.error(f"Error in get_results: {e}")
        return jsonify([])

@app.route('/dashboard')
def dashboard():
    try:
        cloudwatch_url = cloudwatch.get_dashboard(
            DashboardName='ContentModerationDashboard'
        )['DashboardArn']
        return jsonify({'dashboard_url': cloudwatch_url})
    except Exception as e:
        logger.error(f"Error fetching dashboard: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_metrics')
def get_metrics():
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(seconds=30)  # Last 30 seconds
        
        metrics = cloudwatch.get_metric_data(
            MetricDataQueries=[
                {
                    'Id': 'processed',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'ContentModerationDashboard',
                            'MetricName': 'ProcessedFrames'
                        },
                        'Period': 30,
                        'Stat': 'Sum'
                    }
                },
                {
                    'Id': 'flagged',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'ContentModerationDashboard',
                            'MetricName': 'FlaggedContent'
                        },
                        'Period': 30,
                        'Stat': 'Sum'
                    }
                }
            ],
            StartTime=start_time,
            EndTime=end_time
        )
        
        return jsonify({
            'processed_frames': sum(point for point in metrics['MetricDataResults'][0]['Values']),
            'flagged_content': sum(point for point in metrics['MetricDataResults'][1]['Values'])
        })
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({'error': str(e)}), 500

def cleanup():
    logger.info("Application shutting down...")
    try:
        # Release video capture if it exists
        if hasattr(generate_frames, 'cap'):
            generate_frames.cap.release()
            cv2.destroyAllWindows()
        # Kill any existing processes on port 5000
        kill_existing_process(5000)
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

def kill_existing_process(port):
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                connections = proc.connections()
                for conn in connections:
                    if conn.laddr.port == port:
                        logger.info(f"Killing process {proc.pid} using port {port}")
                        proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except ImportError:
        logger.warning("psutil not installed, cannot check for existing processes")

def send_moderation_metrics(labels):
    """Send moderation metrics to CloudWatch"""
    timestamp = datetime.utcnow()
    
    for label in labels:
        cloudwatch.put_metric_data(
            Namespace='ContentModeration',
            MetricData=[
                {
                    'MetricName': f'Confidence_{label["Name"].replace(" ", "_")}',
                    'Value': label['Confidence'],
                    'Unit': 'Percent',
                    'Timestamp': timestamp
                }
            ]
        )

if __name__ == '__main__':
    app.run(debug=True) 