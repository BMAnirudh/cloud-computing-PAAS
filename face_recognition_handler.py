import json
import boto3
import os
from face_recognition_code import face_recognition_function

def lambda_handler(event, context):
    try:
        # S3 client setup
        s3_client = boto3.client('s3', region_name='us-east-1')

        # Extract bucket name and image file name from the event
        bucket_name = event['bucket_name']
        image_file_name = event['image_file_name']

        # Download image from S3
        local_image_path = f"/tmp/{image_file_name}"
        s3_client.download_file(bucket_name, image_file_name, local_image_path)

        # Process the image to detect and recognize faces
        recognized_name = face_recognition_function(local_image_path)
        
        # setting the required variables
        output_bucket = '1229729529-output'
        output_file_name = image_file_name.replace('.jpg', '.txt')
        output_txt_file_path = f"/tmp/{output_file_name}"
        
        # Save the recognized name to another S3 bucket
        s3_client.upload_file(output_txt_file_path, output_bucket, output_file_name)
        
        # Clean up the temporary files if needed
        os.remove(local_image_path)
        os.remove(output_txt_file_path)

        return {
            'statusCode': 200,
            'body': json.dumps('Face recognition processed successfully and pushed the result to output s3 bucket.')
        }

    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps('Error processing the image.')
        }
