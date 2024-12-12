import cv2
import boto3
import time
import numpy as np
import json
import signal
import sys

# Initialize AWS clients
kinesis_video = boto3.client('kinesisvideo', region_name='us-west-2')
stream_name = 'test-stream'
running = True

def signal_handler(sig, frame):
    global running
    print('\nStopping stream...')
    running = False

signal.signal(signal.SIGINT, signal_handler)

def stream_camera():
    global running
    cap = cv2.VideoCapture(0)
    
    try:
        # Get Kinesis Video Stream endpoint
        endpoint = kinesis_video.get_data_endpoint(
            StreamName=stream_name,
            APIName='PUT_MEDIA'
        )['DataEndpoint']
        
        # Create Kinesis Video client for PutMedia
        kvs_client = boto3.client(
            'kinesisvideo',
            endpoint_url=endpoint,
            region_name='us-west-2'
        )
        
        print("Streaming started. Press Ctrl+C to stop.")
        
        while running:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Convert frame to JPEG format
            _, buffer = cv2.imencode('.jpg', frame)
            data = buffer.tobytes()
            
            try:
                # Use PutMedia API directly
                kvs_client.put_media(
                    StreamName=stream_name,
                    Data=data,
                    ProducerTimestamp=int(time.time() * 1000),
                    FragmentNumber=str(int(time.time())),
                    ContainerFormat='JPEG'
                )
            except Exception as e:
                print(f"Error streaming: {e}")
                
            time.sleep(0.1)  # Reduce frame rate
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    stream_camera()