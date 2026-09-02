from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException, status
from app.core.security import get_current_user, require_roles
from app.db.connection import get_db, execute_query
from app.schemas.schemas import CollectionRecordCreate, CollectionRecordOut, PaginatedCollectionRecords

router = APIRouter()

@router.get("/collections", response_model=PaginatedCollectionRecords)
def list_collections(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    ward_id: Optional[int] = None,
    waste_type_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(get_current_user)
):
    conn, engine_type = get_db()
    rec_table = "public.waste_collection_records" if engine_type == "postgres" else "waste_collection_records"
    wards_table = "public.wards" if engine_type == "postgres" else "wards"
    wt_table = "public.waste_types" if engine_type == "postgres" else "waste_types"
    v_table = "public.vehicles" if engine_type == "postgres" else "vehicles"
    cp_table = "public.collection_points" if engine_type == "postgres" else "collection_points"

    where_clauses = ["1=1"]
    params = []

    if ward_id:
        where_clauses.append("r.ward_id = %s")
        params.append(ward_id)
    if waste_type_id:
        where_clauses.append("r.waste_type_id = %s")
        params.append(waste_type_id)
    if start_date:
        where_clauses.append("r.collection_date >= %s")
        params.append(str(start_date))
    if end_date:
        where_clauses.append("r.collection_date <= %s")
        params.append(str(end_date))

    where_str = " AND ".join(where_clauses)

    count_sql = f"SELECT COUNT(*) as cnt FROM {rec_table} r WHERE {where_str};"
    count_row = execute_query(count_sql, tuple(params), fetch="one")
    total = count_row["cnt"] if count_row else 0

    offset = (page - 1) * size
    query_sql = f"""
        SELECT 
            r.id, r.collection_date, r.ward_id, w.name as ward_name, w.zone,
            cp.name as collection_point_name,
            wt.name as waste_type_name, wt.category as waste_category,
            v.registration_number as vehicle_registration,
            r.weight_kg,
            r.created_at
        FROM {rec_table} r
        JOIN {wards_table} w ON r.ward_id = w.id
        JOIN {wt_table} wt ON r.waste_type_id = wt.id
        JOIN {v_table} v ON r.vehicle_id = v.id
        LEFT JOIN {cp_table} cp ON r.collection_point_id = cp.id
        WHERE {where_str}
        ORDER BY r.collection_date DESC, r.id DESC
        LIMIT %s OFFSET %s;
    """
    exec_params = list(params)
    exec_params.extend([size, offset])
    rows = execute_query(query_sql, tuple(exec_params), fetch="all")

    items = [
        {
            "id": r["id"],
            "collection_date": str(r["collection_date"]),
            "ward_id": r["ward_id"],
            "ward_name": r["ward_name"],
            "zone": r["zone"],
            "collection_point_name": r["collection_point_name"],
            "waste_type_name": r["waste_type_name"],
            "waste_category": r["waste_category"],
            "vehicle_registration": r["vehicle_registration"],
            "weight_kg": float(r["weight_kg"]),
            "created_at": str(r["created_at"])
        }
        for r in rows
    ]

    return {"total": total, "page": page, "size": size, "items": items}

@router.post("/collections", response_model=CollectionRecordOut, status_code=status.HTTP_201_CREATED)
def create_collection_record(
    record: CollectionRecordCreate,
    current_user: dict = Depends(require_roles(["Admin", "Ward_Officer"]))
):
    conn, engine_type = get_db()
    rec_table = "public.waste_collection_records" if engine_type == "postgres" else "waste_collection_records"
    wards_table = "public.wards" if engine_type == "postgres" else "wards"
    wt_table = "public.waste_types" if engine_type == "postgres" else "waste_types"
    v_table = "public.vehicles" if engine_type == "postgres" else "vehicles"
    cp_table = "public.collection_points" if engine_type == "postgres" else "collection_points"

    insert_sql = f"""
        INSERT INTO {rec_table}
        (collection_date, ward_id, collection_point_id, waste_type_id, vehicle_id, weight_kg, collected_by_user_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
    """
    new_id = execute_query(insert_sql, (
        str(record.collection_date), record.ward_id, record.collection_point_id,
        record.waste_type_id, record.vehicle_id, record.weight_kg, current_user["id"]
    ), fetch="commit")

    query_sql = f"""
        SELECT 
            r.id, r.collection_date, r.ward_id, w.name as ward_name, w.zone,
            cp.name as collection_point_name,
            wt.name as waste_type_name, wt.category as waste_category,
            v.registration_number as vehicle_registration,
            r.weight_kg,
            r.created_at
        FROM {rec_table} r
        JOIN {wards_table} w ON r.ward_id = w.id
        JOIN {wt_table} wt ON r.waste_type_id = wt.id
        JOIN {v_table} v ON r.vehicle_id = v.id
        LEFT JOIN {cp_table} cp ON r.collection_point_id = cp.id
        WHERE r.id = %s;
    """
    created = execute_query(query_sql, (new_id,), fetch="one")
    return {
        "id": created["id"],
        "collection_date": str(created["collection_date"]),
        "ward_id": created["ward_id"],
        "ward_name": created["ward_name"],
        "zone": created["zone"],
        "collection_point_name": created["collection_point_name"],
        "waste_type_name": created["waste_type_name"],
        "waste_category": created["waste_category"],
        "vehicle_registration": created["vehicle_registration"],
        "weight_kg": float(created["weight_kg"]),
        "created_at": str(created["created_at"])
    }
