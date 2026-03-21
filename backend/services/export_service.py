"""
services/export_service.py - Generate CSV and JSON exports.
"""
import csv, io, json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.models.db_models import Candidate
from backend.logger import logger


class ExportService:

    async def export_csv(self, job_profile_id: str, db: AsyncSession) -> bytes:
        rows = await self._fetch_rows(job_profile_id, db)
        output = io.StringIO()
        fieldnames = ["Rank","Name","Email","Phone","Score (1-10)","Match %","Shortlisted",
                      "Skills","Experience (Years)","Education","Companies","Strengths",
                      "Weaknesses","ATS Missing Keywords","ATS Suggestions","File Name"]
        writer = csv.DictWriter(output, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "Rank": row.get("rank",""),
                "Name": row.get("name",""),
                "Email": row.get("email",""),
                "Phone": row.get("phone",""),
                "Score (1-10)": row.get("score",""),
                "Match %": row.get("match_percentage",""),
                "Shortlisted": "Yes" if row.get("shortlisted") else "No",
                "Skills": "; ".join(row.get("skills") or []),
                "Experience (Years)": row.get("experience_years",""),
                "Education": "; ".join(row.get("education") or []),
                "Companies": "; ".join(row.get("companies") or []),
                "Strengths": "; ".join(row.get("strengths") or []),
                "Weaknesses": "; ".join(row.get("weaknesses") or []),
                "ATS Missing Keywords": "; ".join(row.get("ats_missing_keywords") or []),
                "ATS Suggestions": "; ".join(row.get("ats_suggestions") or []),
                "File Name": row.get("file_name",""),
            })
        logger.info(f"CSV export: {len(rows)} rows")
        return output.getvalue().encode("utf-8-sig")

    async def export_json(self, job_profile_id: str, db: AsyncSession) -> bytes:
        rows = await self._fetch_rows(job_profile_id, db)
        payload = {
            "exported_at": datetime.utcnow().isoformat(),
            "job_profile_id": job_profile_id,
            "total_candidates": len(rows),
            "shortlisted_count": sum(1 for r in rows if r.get("shortlisted")),
            "candidates": rows,
        }
        return json.dumps(payload, indent=2, default=str).encode("utf-8")

    async def _fetch_rows(self, job_profile_id: str, db: AsyncSession) -> list[dict]:
        result = await db.execute(
            select(Candidate)
            .where(Candidate.job_profile_id == job_profile_id)
            .options(selectinload(Candidate.analysis))
        )
        candidates = result.scalars().all()
        rows = []
        for c in candidates:
            a = c.analysis
            rows.append({
                "candidate_id": c.id, "file_name": c.file_name,
                "name": c.name, "email": c.email, "phone": c.phone,
                "skills": c.skills or [], "experience_years": c.experience_years,
                "education": c.education or [], "companies": c.companies or [],
                "certifications": c.certifications or [],
                "rank": a.rank if a else None,
                "score": a.score if a else None,
                "match_percentage": a.match_percentage if a else None,
                "shortlisted": a.shortlisted if a else False,
                "reasoning": a.reasoning if a else "",
                "strengths": a.strengths if a else [],
                "weaknesses": a.weaknesses if a else [],
                "ats_missing_keywords": a.ats_missing_keywords if a else [],
                "ats_suggestions": a.ats_suggestions if a else [],
            })
        rows.sort(key=lambda r: r.get("rank") or 9999)
        return rows

export_service = ExportService()
