from fastapi import APIRouter
from core.data_schema import *
import time

filter_router = APIRouter()

@filter_router.get("/filter_list", description='ui 필터 리스트')
def get():
    return [
        {"db_column": "driving_mode", "enum": driving_mode_enum},
        {"db_column": "datetime", "enum": datetime_enum},
        {"db_column": "triggered_cause", "enum": triggered_cause_enum},
        {"db_column": "zones", "enum": scenery_zones_enum},
        {"db_column": "road_types", "enum": scenery_road_types_enum},
        {"db_column": "intersections", "enum": scenery_junctions_intersections_enum},
        {"db_column": "roundabouts", "enum": scenery_junctions_roundabouts_enum},
        {"db_column": "cloudness", "enum": environmental_conditions_cloudness_enum},
        {"db_column": "wind", "enum": environmental_conditions_intensity_enum},
        {"db_column": "rainfall", "enum": environmental_conditions_intensity_enum},
        {"db_column": "snowfall", "enum": environmental_conditions_intensity_enum},
        {"db_column": "illuminance", "enum": environmental_conditions_illuminance_enum},
        {"db_column": "special_structures", "enum": scenery_special_structures_enum},
    ]