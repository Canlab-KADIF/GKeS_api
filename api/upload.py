from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
import json
import re

from core.databases import database
from core.models import filters, filter_special_structures
from utils import upload as upload_utils
from config import AWS
import boto3

upload_router = APIRouter()

# AWS S3 client 설정
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS.ACCESS_KEY_ID,
    aws_secret_access_key=AWS.SECRET_ACCESS_KEY,
    region_name=AWS.REGION
)

@upload_router.post("/upload")
async def upload(
    video_clip: UploadFile = File(...), 
    thumbnail: UploadFile = File(...),
    meta: UploadFile = File(...),
    route: UploadFile = File(...),
    bag: UploadFile = File(...),
):



    # TODO: 파일 업로드 로직 처리




    # JSON 파일 Dictionary 형태로 변환
    meta_content = await meta.read()
    route_content = await route.read()
    try:
        meta_data = json.loads(meta_content)
        route_data = json.loads(route_content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in meta or route files.")

    # 파일 유효성 검사 DB에 태그 등록
    primary_key = await upload_utils.validation_and_insert(
        video_clip.filename,              # String
        thumbnail.filename,               # String
        meta.filename,                    # String
        route.filename,                   # String
        bag.filename,                     # String

        meta_data,                        # Dict
        route_data,                       # Dict
    )

    # 파일 포인터 초기화
    meta.file.seek(0)
    route.file.seek(0)

    # S3에 파일 업로드
    s3.upload_fileobj(video_clip.file, AWS.BUCKET, f"{AWS.FOLDER}/{primary_key}/{video_clip.filename}")
    s3.upload_fileobj(thumbnail.file, AWS.BUCKET, f"{AWS.FOLDER}/{primary_key}/{thumbnail.filename}")
    s3.upload_fileobj(meta.file, AWS.BUCKET, f"{AWS.FOLDER}/{primary_key}/{meta.filename}")
    s3.upload_fileobj(route.file, AWS.BUCKET, f"{AWS.FOLDER}/{primary_key}/{route.filename}")
    s3.upload_fileobj(bag.file, AWS.BUCKET, f"{AWS.FOLDER}/{primary_key}/{bag.filename}")

    return {"message": "All files uploaded successfully", "primary_key": primary_key}