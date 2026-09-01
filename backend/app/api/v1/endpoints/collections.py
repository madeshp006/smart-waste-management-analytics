from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException, status
import psycopg2
import psycopg2.extras
from app.core.security import get_current_user, require_roles, get_db_connection
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
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

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
        params.append(start_date)
    if end_date:
        where_clauses.append("r.collection_date <= %s")
        params.append(end_date)

    where_str = " AND ".join(where_clauses)

    # Count total
    count_sql = f"SELECT COUNT(*) as cnt FROM public.waste_collection_records r WHERE {where_str};"
    cursor.execute(count_sql, params)
    total = cursor.fetchone()["cnt"]

    # Offset & Limit
    offset = (page - 1) * size
    query_sql = f"""
        SELECT 
            r.id, r.collection_date, r.ward_id, w.name as ward_name, w.zone,
            cp.name as collection_point_name,
            wt.name as waste_type_name, wt.category as waste_category,
            v.registration_number as vehicle_registration,
            CAST(r.weight_kg AS FLOAT) as weight_kg,
            r.created_at
        FROM public.waste_collection_records r
        JOIN public.wards w ON r.ward_id = w.id
        JOIN public.waste_types wt ON r.waste_type_id = wt.id
        JOIN public.vehicles v ON r.vehicle_id = v.id
        LEFT JOIN public.collection_points cp ON r.collection_point_id = cp.id
        WHERE {where_str}
        ORDER BY r.collection_date DESC, r.id DESC
        LIMIT %s OFFSET %s;
    """
    params.extend([size, offset])
    cursor.execute(query_sql, params)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    items = [dict(r) for r in rows]

    return {
        "total": total,
        "page": page,
        "size": size,
        "items": items
    }

@router.post("/collections", response_model=CollectionRecordOut, status_code=status.HTTP_201_CREATED)
def create_collection_record(
    record: CollectionRecordCreate,
    current_user: dict = Depends(require_roles(["Admin", "Ward_Officer"]))
):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        INSERT INTO public.waste_collection_records
        (collection_date, ward_id, collection_point_id, waste_type_id, vehicle_id, weight_kg, collected_by_user_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
    """, (
        record.collection_date, record.ward_id, record.collection_point_id,
        record.waste_type_id, record.vehicle_id, record.weight_kg, current_user["id"]
    ))
    new_id = cursor.fetchone()["id"]
    conn.commit()

    # Fetch created record details
    cursor.execute("""
        SELECT 
            r.id, r.collection_date, r.ward_id, w.name as ward_name, w.zone,
            cp.name as collection_point_name,
            wt.name as waste_type_name, wt.category as waste_category,
            v.registration_number as vehicle_registration,
            CAST(r.weight_kg AS FLOAT) as weight_kg,
            r.created_at
        FROM public.waste_collection_records r
        JOIN public.wards w ON r.ward_id = w.id
        JOIN public.waste_types wt ON r.waste_type_id = wt.id
        JOIN public.vehicles v ON r.vehicle_id = v.id
        LEFT JOIN public.collection_points cp ON r.collection_point_id = cp.id
        WHERE r.id = %s;
    """, (new_id,))
    created_record = cursor.fetchone()
    cursor.close()
    conn.close()

    return dict(created_record)
