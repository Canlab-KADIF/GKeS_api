import re
import json
import boto3
from fastapi import HTTPException, UploadFile

from core.databases import database
from core.models import filters
from core.models import filter_special_structures
from config import AWS

from utils.json_check.run_CheckUploadDatas import check

PRIMARY_KEY_REGEX = re.compile(r"^(?P<ts>\d{8}_\d{6})_(?P<session>[A-Z0-9]+)$")
FILENAME_REGEX = re.compile(
    r"^(?P<primary_key>\d{8}_\d{6}_[A-Z0-9]+)_(?P<datatype>meta|route|thumbnail|video_clip|raw)\.(?P<ext>json|jpg|jpeg|mp4|bag)$"
)

def extract_primary_key(file_name: str, expected_datatype: str, expected_exts: list[str]):
    match = FILENAME_REGEX.match(file_name)
    if not match:
        raise HTTPException(status_code=400, detail=f"Invalid filename format: {file_name}")
    
    if match.group("datatype") != expected_datatype:
        raise HTTPException(status_code=400, detail=f"{file.filename} has incorrect datatype. Expected '{expected_datatype}'.")
    
    if match.group("ext") not in expected_exts:
        raise HTTPException(status_code=400, detail=f"{file.filename} has incorrect extension. Allowed: {expected_exts}")
    
    return match.group("primary_key")

def check_primary_key(
    video_clip_file_name: str,
    thumbnail_file_name: str,
    meta_file_name: str,
    route_file_name: str,
    bag_file_name: str,
):
    pk_meta = extract_primary_key(meta_file_name, "meta", ["json"])
    pk_route = extract_primary_key(route_file_name, "route", ["json"])
    pk_thumb = extract_primary_key(thumbnail_file_name, "thumbnail", ["jpg", "jpeg"])
    pk_video = extract_primary_key(video_clip_file_name, "video_clip", ["mp4"])
    pk_bag = extract_primary_key(bag_file_name, "raw", ["bag"])

    if len(set([pk_meta, pk_route, pk_thumb, pk_video])) != 1:
        raise HTTPException(status_code=400, detail="All files must have the same primary_key prefix.")

    if not PRIMARY_KEY_REGEX.match(pk_meta):
        raise HTTPException(status_code=400, detail=f"Primary key format is invalid: {pk_meta}")
    
    return pk_meta

def check_json(meta_data: dict, route_data: dict):

    extra_meta_keys_in_check, missing_meta_keys_in_check, extra_route_keys_in_check, missing_route_keys_in_check = check(meta_data, route_data)

    error_messages = []
    if extra_meta_keys_in_check:
        error_messages.append(f"Unexpected metadata keys found: {','.join(extra_meta_keys_in_check)}")
    if missing_meta_keys_in_check:
        error_messages.append(f"Required metadata keys are missing: {','.join(missing_meta_keys_in_check)}")
    if extra_route_keys_in_check:
        error_messages.append(f"Unexpected route keys found: {','.join(extra_route_keys_in_check)}")
    if missing_route_keys_in_check:
        error_messages.append(f"Required route keys are missing: {','.join(missing_route_keys_in_check)}")

    if error_messages:
        raise HTTPException(status_code=400, detail=error_messages)

    return meta_data, route_data

async def check_db(pk_meta: str):
    query_check = filters.select().where(filters.c.id == pk_meta)
    existing = await database.fetch_one(query_check)
    if existing:
        raise HTTPException(status_code=400, detail=f"{pk_meta} already exists")

async def insert_db(pk_meta: str, meta_data: dict, route_data: dict):
    triggered_idx = meta_data.get("screen", {}).get("triggered_position", {}).get("idx")

    matched_data = next(
        (item for item in route_data.get("data", []) if item.get("idx") == triggered_idx),
        None
    )

    if triggered_idx is None:
        raise HTTPException(status_code=400, detail="No triggered index found in metadata.")

    if matched_data is None:
        raise HTTPException(status_code=400, detail="No route data found matching the triggered index from metadata.")

    # 1) filters 테이블에 insert
    environment = meta_data.get("scene_context", {}).get("environmental_conditions")
    scenery = matched_data.get("scenery")
    junctions = scenery.get("junctions")

    values_dict = {
        "id": pk_meta,
        "datetime": meta_data.get("datetime"),
        "driving_mode": meta_data.get("driving_mode"),
        "cloudness": environment.get("cloudness"),
        "illuminance": environment.get("illuminance"),
        "rainfall": environment.get("rainfall"),
        "snowfall": environment.get("snowfall"),
        "wind": environment.get("wind"),
        "triggered_cause": meta_data.get("triggered_cause", {}).get("cause"),
        "intersections": junctions.get("intersections"),
        "roundabouts": junctions.get("roundabouts"),
        "road_types": scenery.get("road_types"),
        "zones": scenery.get("zones"),
    }

    try:
        query_insert = filters.insert().values(**values_dict)
        await database.execute(query_insert)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error inserting data to filters table: {e}")

    # 2) filter_special_structures 테이블에 여러 개 insert
    special_structures = scenery.get("special_structures", [])

    if special_structures:
        values_for_special = [
            {"filter_id": pk_meta, "structure_code": code}
            for code in special_structures
        ]
        try:
            query_insert_special = filter_special_structures.insert()
            await database.execute_many(query_insert_special, values_for_special)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error inserting data to filter_special_structures table: {e}")

async def validation_and_insert(
    video_clip_file_name: str,
    thumbnail_file_name: str,
    meta_file_name: str,
    route_file_name: str,
    bag_file_name: str,

    meta_data: dict,
    route_data: dict,
):
    primary_key = check_primary_key(video_clip_file_name, thumbnail_file_name, meta_file_name, route_file_name, bag_file_name)
    print(1)
    meta_data, route_data = check_json(meta_data, route_data)
    print(2)
    await check_db(primary_key)
    print(3)
    await insert_db(primary_key, meta_data, route_data)
    print(4)

    return primary_key