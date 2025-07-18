from fastapi import APIRouter, HTTPException
from fastapi.responses import ORJSONResponse
from supabase_client import supabase
from datetime import datetime, timedelta

router = APIRouter(default_response_class=ORJSONResponse)


@router.get("/recent")
async def get_recent_logs():
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not configured.")

    try:
        ten_minutes_ago = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
        response = (
            supabase.table("function_log")
            .select("*")
            .gte("created_at", ten_minutes_ago)
            .execute()
        )
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch recent logs from Supabase: {e}"
        )
