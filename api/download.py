import boto3
from config import AWS_OLD, AWS
from config import OpenSearchConfig
from fastapi import APIRouter, Request, HTTPException
import requests
import json
import zipfile
import datetime
import os
import tempfile
from pathlib import Path

s3 = boto3.client('s3', aws_access_key_id=AWS_OLD.ACCESS_KEY_ID, aws_secret_access_key=AWS_OLD.SECRET_ACCESS_KEY, region_name=AWS_OLD.REGION)

download_router = APIRouter()

@download_router.get("/download_file_list")
def download_file_list(
    request: Request,
    target_key: str
):

    response = s3.list_objects_v2(Bucket=AWS.BUCKET, Prefix=f"{AWS.FOLDER}/{target_key}/")
    if "Contents" not in response:
        raise HTTPException(status_code=400, detail=f"{AWS.BUCKET} 버킷이 비어 있습니다.")

    files = []
    for content in response["Contents"]:
        path = content["Key"]
        url = "https://" + AWS.BUCKET + ".s3.ap-northeast-2.amazonaws.com/" + path
        files.append(url)

    return {"files": files}

@download_router.get("/packaging_and_download")
def packaging_and_download(
    request: Request,
    target_key: str
):
    print("1. START")


    # S3에서 해당 key로 시작하는 파일 목록 가져오기
    response = s3.list_objects_v2(Bucket=AWS.BUCKET, Prefix=f"{AWS.FOLDER}/{target_key}/")
    if "Contents" not in response or not response["Contents"]:
        raise HTTPException(status_code=404, detail="S3에 해당 key로 시작하는 파일이 없습니다.")

    print("2. TEMPORARY DIRECTORY")

    # 임시 디렉토리 생성
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        zip_file_path = tmpdir_path / f"{target_key}.zip"

        print("3. ZIP FILE")
        print(f"tmpdir_path: {tmpdir_path}")

        # zip 파일 생성
        with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for obj in response["Contents"]:
                s3_key = obj["Key"]
                filename = s3_key.split("/")[-1]
                local_path = tmpdir_path / filename

                # S3에서 파일 다운로드
                s3.download_file(Bucket=AWS.BUCKET, Key=s3_key, Filename=str(local_path))

                # zip에 추가
                zipf.write(local_path, arcname=filename)

        print("4. ZIP FILE")

        # 압축 완료 후 S3에 업로드할 key 설정
        packaged_key = f"{AWS.FOLDER}/{target_key}/{target_key}.zip"

        print("5. ZIP FILE")

        # zip 파일을 다시 S3에 업로드
        with open(zip_file_path, "rb") as f:
            s3.upload_fileobj(f, AWS.BUCKET, packaged_key)


    # S3 URL 반환
    zip_url = f"https://{AWS.BUCKET}.s3.ap-northeast-2.amazonaws.com/{packaged_key}"
    
    print("6. COMPLETE")

    return {"url": zip_url}