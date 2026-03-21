"""
routes/export_routes.py - GET /export_shortlist endpoint.
Returns CSV or JSON download of all analyzed candidates for a job profile.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.db_models import JobProfile
from backend.services.export_service import export_service
from backend.utils.database import get_db
from backend.logger import logger

router = APIRouter(prefix="/api", tags=["Export"])


@router.get("/export_shortlist")
async def export_shortlist(
    job_profile_id: str = Query(..., description="Job profile ID to export"),
    format: str = Query(default="csv", description="Export format: csv or json"),
    db: AsyncSession = Depends(get_db),
):
    """
    Export all analyzed candidates for a job profile as CSV or JSON.
    Includes rank, score, skills, experience, shortlist status.
    """
    # Validate job profile
    result = await db.execute(
        select(JobProfile).where(JobProfile.id == job_profile_id)
    )
    job_profile = result.scalar_one_or_none()
    if not job_profile:
        raise HTTPException(status_code=404, detail="Job profile not found.")

    format = format.lower()
    try:
        if format == "json":
            content = await export_service.export_json(job_profile_id, db)
            return Response(
                content=content,
                media_type="application/json",
                headers={
                    "Content-Disposition": f'attachment; filename="candidates_{job_profile_id[:8]}.json"'
                },
            )
        else:  # default: csv
            content = await export_service.export_csv(job_profile_id, db)
            return Response(
                content=content,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f'attachment; filename="candidates_{job_profile_id[:8]}.csv"'
                },
            )
    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
