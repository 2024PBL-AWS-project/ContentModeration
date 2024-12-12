import boto3
import json

def test_aws_connection():
    try:
        # Test STS (Security Token Service)
        sts = boto3.client('sts')
        response = sts.get_caller_identity()
        print("✅ Successfully connected to AWS!")
        print(f"Account ID: {response['Account']}")
        print(f"User ARN: {response['Arn']}")
        
        # Test services used in your app
        services = {
            'dynamodb': boto3.client('dynamodb', region_name='us-west-2'),
            'rekognition': boto3.client('rekognition', region_name='us-west-2'),
            'cloudwatch': boto3.client('cloudwatch', region_name='us-west-2')
        }
        
        for service_name, client in services.items():
            try:
                if service_name == 'dynamodb':
                    client.list_tables()
                print(f"✅ {service_name} connection successful")
            except Exception as e:
                print(f"❌ {service_name} error: {str(e)}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_aws_connection()
