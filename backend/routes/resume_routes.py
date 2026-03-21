import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.config import get_settings
from backend.logger import logger
from backend.models.db_models import Candidate
from backend.models.schemas import UploadResumeResponse, UploadedFile
from backend.utils.database import get_db

router = APIRouter(prefix="/api", tags=["Resume Upload"])
settings = get_settings()


@router.post("/upload_resume", response_model=UploadResumeResponse)
async def upload_resume(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    form = await request.form()
    files = form.getlist("files")

    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    uploaded = []

    for file in files:
        if not hasattr(file, "filename") or not file.filename:
            continue

        filename = file.filename
        suffix = Path(filename).suffix.lower().lstrip(".")

        if suffix not in ["pdf", "docx"]:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported file type '{suffix}'. Allowed: pdf, docx",
            )

        content = await file.read()

        if len(content) == 0:
            raise HTTPException(status_code=400, detail=f"File '{filename}' is empty.")

        file_id = str(uuid.uuid4())
        dest_path = upload_dir / f"{file_id}.{suffix}"
        dest_path.write_bytes(content)

        candidate = Candidate(
            id=file_id,
            file_name=filename,
            file_path=str(dest_path),
            file_type=suffix,
        )
        db.add(candidate)
        uploaded.append(UploadedFile(file_id=file_id, file_name=filename, file_type=suffix))
        logger.info(f"Uploaded: {filename} -> {dest_path}")

    if not uploaded:
        raise HTTPException(status_code=400, detail="No valid files were uploaded.")

    return UploadResumeResponse(uploaded=uploaded, total=len(uploaded))