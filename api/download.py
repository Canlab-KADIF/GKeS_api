import boto3
from config import AWS_OLD, AWS
from config import OpenSearchConfig
from fastapi import APIRouter, Request, HTTPException
import requests
import json
import zipfile
import datetime
import os

s3 = boto3.client('s3', aws_access_key_id=AWS_OLD.ACCESS_KEY_ID, aws_secret_access_key=AWS_OLD.SECRET_ACCESS_KEY, region_name=AWS_OLD.REGION)

download_router = APIRouter()

@download_router.get("/download_file_list")
def download_file_list(
    request: Request,
    target_key: str
):

    response = s3.list_objects_v2(Bucket=AWS.BUCKET, Prefix=AWS.FOLDER + "/" + target_key + "/")
    if "Contents" not in response:
        raise HTTPException(status_code=400, detail=f"{AWS.BUCKET} 버킷이 비어 있습니다.")

    files = []
    for content in response["Contents"]:
        path = content["Key"]
        url = "https://" + AWS.BUCKET + ".s3.ap-northeast-2.amazonaws.com/" + path
        files.append(url)

    return {"files": files}