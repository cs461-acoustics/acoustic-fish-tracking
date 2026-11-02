import os
import sys
import boto3
from botocore import UNSIGNED
from botocore.config import Config

def download_raw_folder(bucket_name, s3_prefix, local_dir):
    s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    s3_prefix = s3_prefix.lstrip('/')
    if s3_prefix and not s3_prefix.endswith('/'):
        s3_prefix += '/'
    
    paginator = s3.get_paginator('list_objects_v2')
    
    pages = paginator.paginate(Bucket=bucket_name, Prefix=s3_prefix)
    for page in pages:
        if 'Contents' not in page:
            print("No files found matching that prefix.")
            return
        for obj in page['Contents']:
            s3_key = obj['Key']
            
            if s3_key.endswith('/'):
                continue
            
            relative_path = os.path.relpath(s3_key, s3_prefix)
            local_file_path = os.path.join(local_dir, relative_path)
            
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            
            print(f"Downloading: s3://{bucket_name}/{s3_key}")
            s3.download_file(bucket_name, s3_key, local_file_path)
                
def main():
    if len(sys.argv) < 4:
        print("Correct command is: python3 download_raws.py <bucket> <prefix> <destination_directory>")
        sys.exit(1)
        
    bucket = sys.argv[1]
    prefix = sys.argv[2]
    dest_dir = sys.argv[3]
    
    download_raw_folder(bucket, prefix, dest_dir)
    
if __name__ == "__main__":
    main()