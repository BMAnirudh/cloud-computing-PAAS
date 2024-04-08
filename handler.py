#__copyright__   = "Copyright 2024, VISA Lab"
#__license__     = "MIT"

import boto3
from boto3 import client as boto3_client
import os
import tempfile
from decouple import config
import logging
import video_splitting_cmdline

# loggin set up
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load AWS credentials from environment variables
aws_access_key_id = config('AWS_ACCESS_KEY_ID')
aws_secret_access_key = config('AWS_SECRET_ACCESS_KEY')

# initilaize s3 client
s3 = boto3.client('s3', region_name='us-east-1', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)


def upload_folder(local_dir, bucket_name, s3_key):
    try:
        # uploads the entire folder to s3 bucket as a folder
        for root, dirs, files in os.walk(local_dir):
            for file in files:
                local_frame_path = os.path.join(root, file)
                relative_frame_path = os.path.relpath(local_frame_path, local_dir)
                s3_object_key = os.path.join(s3_key, relative_frame_path)
                s3.upload_file(local_frame_path, bucket_name, s3_object_key)
    except Exception as e:
        logger.error(f"Error uploading {s3_key} to bucket {bucket_name}: {e}")
        return False           
            

def handler(event, context):
    try:
        # input bucket and key info from s3 event
        s3_input_bucket = event['Records'][0]['s3']['bucket']['name']
        input_key = event['Records'][0]['s3']['object']['key']
        s3_stage_1_bucket = '1229729529-stage-1'
        
		
		# download the video file from input bucket
        temp_vedio_path = f"/tmp/{os.path.basename(input_key)}"
        
        print('before download')
        s3.download_file(s3_input_bucket, input_key, temp_vedio_path)
        print('after download')
        print('befor func call')
		# split the downloaded video into frames
        output_frames_dir = video_splitting_cmdline.video_splitting_cmdline(temp_vedio_path)
        print('after func call')
		
		# upload frames to stage-1 s3 bucket
        folder_name = os.path.basename(output_frames_dir)
        print('befor upload')
        upload_folder(output_frames_dir, s3_stage_1_bucket, folder_name)
        print('after upload')
        return True
    
    except Exception as e:
        logger.error(f"Error downloading {input_key} from bucket {s3_input_bucket}: {e}")
        return False