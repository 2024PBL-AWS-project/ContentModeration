import boto3

kinesis_video = boto3.client('kinesisvideo', region_name='us-west-2')

try:
    kinesis_video.create_stream(
        StreamName='test-stream',
        DataRetentionInHours=24,
        MediaType='video/h264'
    )
    print("Stream created successfully")
except kinesis_video.exceptions.ResourceInUseException:
    print("Stream already exists") 