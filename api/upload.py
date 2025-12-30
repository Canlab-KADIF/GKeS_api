from fastapi import APIRouter, File, UploadFile, HTTPException
from urllib.parse import quote
import json
import zipfile
import tempfile
import os
from pathlib import Path
import boto3

from core.databases import database
from core.models import filters, filter_special_structures
from utils import upload as upload_utils
from config import AWS


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
    # bag: UploadFile = File(...),
):
    print("1. UPLOAD")




    # TODO: 파일 업로드 로직 처리




    # JSON 파일 Dictionary 형태로 변환
    meta_content = await meta.read()
    route_content = await route.read()
    try:
        meta_data = json.loads(meta_content)
        route_data = json.loads(route_content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in meta or route files.")

    print("2. VALIDATION AND INSERT")

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

    print("3. UPLOAD TO S3")

    # 파일 포인터 초기화
    meta.file.seek(0)
    route.file.seek(0)

    # S3에 파일 업로드
    primary_key = quote(primary_key)
    s3.upload_fileobj(video_clip.file, AWS.BUCKET, f"{AWS.FOLDER}/{primary_key}/{quote(video_clip.filename)}")
    s3.upload_fileobj(thumbnail.file, AWS.BUCKET, f"{AWS.FOLDER}/{primary_key}/{quote(thumbnail.filename)}")
    s3.upload_fileobj(meta.file, AWS.BUCKET, f"{AWS.FOLDER}/{primary_key}/{quote(meta.filename)}")
    s3.upload_fileobj(route.file, AWS.BUCKET, f"{AWS.FOLDER}/{primary_key}/{quote(route.filename)}")
    s3.upload_fileobj(bag.file, AWS.BUCKET, f"{AWS.FOLDER}/{primary_key}/{quote(bag.filename)}")

    print("4. COMPLETE")

    return {"message": "All files uploaded successfully", "primary_key": primary_key}

@upload_router.post("/upload_zip")
async def upload_zip(zip_file: UploadFile = File(...)):
    print("1. UPLOAD ZIP")

    print("2. UNZIP")

    # 임시 디렉토리에 압축파일 저장 및 압축 해제
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, zip_file.filename)

        # 압축파일 저장
        with open(zip_path, "wb") as f:
            f.write(await zip_file.read())

        # 압축 해제
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="Invalid ZIP file format.")

        print("3. CHECK FILES")

        # 압축 해제된 디렉토리 내 파일 리스트
        all_files = list(Path(tmpdir).glob("**/*"))
        all_files = [f for f in all_files if f.is_file()]

        # 파일명 접미사 기준으로 매칭
        suffix_patterns = {
            "video_clip": "_video_clip.mp4",
            "thumbnail": "_thumbnail.jpg",
            "meta": "_meta.json",
            "route": "_route.json",
            "bag": "_raw.bag"
        }

        extracted_paths = {}

        for key, suffix in suffix_patterns.items():
            matched = [f for f in all_files if f.name.endswith(suffix)]
            if not matched:
                raise HTTPException(status_code=400, detail=f"Missing required file ending with: {suffix}")
            if len(matched) > 1:
                raise HTTPException(status_code=400, detail=f"Multiple files found ending with: {suffix}")
            extracted_paths[key] = matched[0]

        print("4. READ JSON")

        # JSON 파일 읽기
        try:
            with open(extracted_paths["meta"], "r", encoding="utf-8") as f:
                meta_data = json.load(f)
            with open(extracted_paths["route"], "r", encoding="utf-8") as f:
                route_data = json.load(f)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in meta or route files.")

        print("5. VALIDATION AND INSERT")

        # DB 등록 및 유효성 검사
        primary_key = await upload_utils.validation_and_insert(
            extracted_paths["video_clip"].name,
            extracted_paths["thumbnail"].name,
            extracted_paths["meta"].name,
            extracted_paths["route"].name,
            extracted_paths["bag"].name,
            meta_data,
            route_data
        )

        print("6. UPLOAD TO S3")
        primary_key = quote(primary_key)

        # S3에 각 파일 업로드
        for key, path in extracted_paths.items():
            with open(path, "rb") as f:
                s3.upload_fileobj(f, AWS.BUCKET, f"{AWS.FOLDER}/{primary_key}/{quote(path.name)}")

        print("7. UPLOAD ZIP")

        # ZIP 파일 자체도 업로드
        with open(zip_path, "rb") as f:
            s3.upload_fileobj(f, AWS.BUCKET, f"{AWS.FOLDER}/{primary_key}/{quote(zip_file.filename)}")

    print("8. COMPLETE")

    return {"message": "Zip and contents uploaded successfully", "primary_key": primary_key}