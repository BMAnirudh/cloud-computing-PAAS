#__copyright__   = "Copyright 2024, VISA Lab"
#__license__     = "MIT"

import boto3
from boto3 import client as boto3_client
import os
import tempfile
import logging
import subprocess
import math
import json

# loggin set up
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# initilaize s3 and lambda_client client
s3 = boto3.client('s3', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')       
    
    
def video_splitting_cmdline(video_filename):
    filename = os.path.basename(video_filename)
    outfile = os.path.splitext(filename)[0] + ".jpg"

    split_cmd = 'ffmpeg -i ' + video_filename + ' -vframes 1 ' + '/tmp/' + outfile
    try:
        subprocess.check_call(split_cmd, shell=True)
    except subprocess.CalledProcessError as e:
        print(e.returncode)
        print(e.output)

    fps_cmd = 'ffmpeg -i ' + video_filename + ' 2>&1 | sed -n "s/.*, \\(.*\\) fp.*/\\1/p"'
    fps = subprocess.check_output(fps_cmd, shell=True).decode("utf-8").rstrip("\n")
    return outfile
            

def lambda_handler(event, context):
    try:
        # input bucket and key info from s3 event
        s3_input_bucket = event['Records'][0]['s3']['bucket']['name']
        input_key = event['Records'][0]['s3']['object']['key']
        s3_stage_1_bucket = '1229729529-stage-1'
        
		# download the video file from input bucket
        temp_video_path = f"/tmp/{os.path.basename(input_key)}"
        s3.download_file(s3_input_bucket, input_key, temp_video_path)
        
		# split the downloaded video into frames
        output_frame_image = video_splitting_cmdline(temp_video_path)
        
        # Full path to the output image
        output_frame_path = f"/tmp/{output_frame_image}"

        # Upload the frame to the stage-1 bucket
        s3.upload_file(output_frame_path, s3_stage_1_bucket, output_frame_image)
        
        # Invocation parameters for the face-recognition Lambda function
        payload = {
            "bucket_name": s3_stage_1_bucket,
            "image_file_name": output_frame_image
        }
        
        # Invoke face-recognition Lambda function
        response = lambda_client.invoke(
            FunctionName='face-recognition',
            InvocationType='Event',
            Payload=json.dumps(payload)
        )

        # Clean up the temporary files if needed
        os.remove(temp_video_path)
        os.remove(output_frame_path)

        return {
            'statusCode': 200,
            'body': f'Successfully processed {input_key} and invoked face-recognition.'
        }
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': 'Error processing the video file.'
        }