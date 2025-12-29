from fastapi import APIRouter, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import sqlalchemy
from sqlalchemy import and_, or_, distinct, func
from core import models
from core.databases import database

search_router = APIRouter()

class SearchResult(BaseModel):
    pages: Dict[str, int]
    datas: List[Dict[str, Any]]

@search_router.get("/search", response_model=SearchResult)
async def search_filters(
    driving_mode: Optional[List[int]] = Query(None),
    datetime: Optional[List[int]] = Query(None),
    triggered_cause: Optional[List[int]] = Query(None),
    zones: Optional[List[int]] = Query(None),
    road_types: Optional[List[int]] = Query(None),
    intersections: Optional[List[int]] = Query(None),
    roundabouts: Optional[List[int]] = Query(None),
    cloudness: Optional[List[int]] = Query(None),
    wind: Optional[List[int]] = Query(None),
    rainfall: Optional[List[int]] = Query(None),
    snowfall: Optional[List[int]] = Query(None),
    illuminance: Optional[List[int]] = Query(None),
    special_structures: Optional[List[int]] = Query(None),
    page: int = Query(1, ge=1),
):

    filters = {
        "driving_mode": driving_mode,
        "datetime": datetime,
        "triggered_cause": triggered_cause,
        "zones": zones,
        "road_types": road_types,
        "intersections": intersections,
        "roundabouts": roundabouts,
        "cloudness": cloudness,
        "wind": wind,
        "rainfall": rainfall,
        "snowfall": snowfall,
        "illuminance": illuminance,
    }
    return await query_filters(filters, special_structures, page)
    

async def query_filters(filters: dict, special_structures: Optional[List[int]] = None, page: int = 1):
    conditions = []
    PAGE_SIZE = 40

    all_values_map = {
        "driving_mode": [0, 1],
        "datetime": [0, 1, 2],
        "triggered_cause": [0, 1, 2, 3, 4, 5],
        "zones": [0, 1],
        "road_types": [0, 1, 2, 3],
        "intersections": [0, 1, 2],
        "roundabouts": [0, 1],
        "cloudness": [0, 1, 2],
        "wind": [0, 1, 2, 3],
        "rainfall": [0, 1, 2, 3],
        "snowfall": [0, 1, 2, 3],
        "illuminance": [0, 1, 2],
    }

    for attr, selected_values in filters.items():
        if selected_values is None:
            continue

        col = getattr(models.filters.c, attr)

        all_values = all_values_map.get(attr)
        if all_values is None:
            continue

        selected_set = set(selected_values)
        all_set = set(all_values)

        if selected_set == all_set:
            # 모든 값 선택 시 NULL 포함 허용 → 조건 패스
            continue

        # 기본 조건: 값 중 하나 포함 AND NULL 아님
        conditions.append(
            and_(
                col.in_(selected_values),
                col.isnot(None)
            )
        )

    # roundabouts + intersections 종속성 처리
    all_special_structures = [0, 1, 2, 3, 4, 5]

    join = False
    if special_structures and set(special_structures) != set(all_special_structures):
        # 모든 값을 선택했으면 special_structures 조건 무시
        join = True

    base_query = sqlalchemy.select(models.filters)
    if join:
        join_condition = models.filters.c.id == models.filter_special_structures.c.filter_id
        base_query = base_query.select_from(
            models.filters.join(models.filter_special_structures, join_condition)
        ).where(
            and_(
                and_(*conditions),
                models.filter_special_structures.c.structure_code.in_(special_structures)
            )
        ).distinct()
    else:
        base_query = base_query.where(and_(*conditions))

    # 1) 페이지 처리 하면서 filters 먼저 가져오고
    count_query = base_query.with_only_columns(func.count(distinct(models.filters.c.id))).order_by(None)
    total_items = await database.fetch_val(count_query)
    total_pages = (total_items + PAGE_SIZE - 1) // PAGE_SIZE

    paginated_query = base_query.limit(PAGE_SIZE).offset((page - 1) * PAGE_SIZE)
    results = await database.fetch_all(paginated_query)


    # 2) filter ids 리스트로 뽑아서
    filter_ids = [row.id for row in results]

    # 3) 그 ids로 special_structures 조회
    special_query = (
        sqlalchemy.select(models.filter_special_structures)
        .where(models.filter_special_structures.c.filter_id.in_(filter_ids))
    )

    special_rows = await database.fetch_all(special_query)

    # 4) filter_id별로 묶기
    special_map = {}
    for row in special_rows:
        special_map.setdefault(row.filter_id, []).append(row.structure_code)

    # 5) 결과에 붙이기
    processed_results = []
    for row in results:
        row_dict = dict(row)
        row_dict['special_structures'] = special_map.get(row.id, [])
        processed_results.append({
            "filters": row_dict,
            "data_paths": return_data_path(row.id),
        })

    return {
        "pages": {
            "total_pages": total_pages,
            "current_page": page,
            "page_size": PAGE_SIZE,
            "total_items": total_items,
        },
        "datas": processed_results,
    }