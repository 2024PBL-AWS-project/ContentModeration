import boto3
import json

cloudwatch = boto3.client('cloudwatch')

dashboard_body = {
    "widgets": [
        {
            "type": "metric",
            "x": 0,
            "y": 0,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    ["ContentModeration", "Confidence_Non_Explicit_Nudity", {"label": "Non-Explicit Nudity"}],
                    ["ContentModeration", "Confidence_Explicit", {"label": "Explicit Content"}]
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": "us-west-2",
                "period": 1,
                "stat": "Average",
                "title": "Content Moderation Confidence Levels"
            }
        },
        {
            "type": "metric",
            "x": 0,
            "y": 6,
            "width": 12,
            "height": 3,
            "properties": {
                "metrics": [
                    ["ContentModeration", "ProcessedFrames", {"label": "Frames Processed"}]
                ],
                "view": "singleValue",
                "region": "us-west-2",
                "period": 60,
                "stat": "Sum",
                "title": "Total Frames Processed"
            }
        }
    ]
}

try:
    response = cloudwatch.put_dashboard(
        DashboardName='ContentModerationDashboard',
        DashboardBody=json.dumps(dashboard_body)
    )
    print("Dashboard created successfully")
except Exception as e:
    print(f"Error creating dashboard: {e}") 