import os

files = {}

files["backend/utils/database.py"] = '''
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.config import get_settings
from backend.models.db_models import Base
from backend.logger import logger

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized.")

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
'''.strip()

files["backend/__init__.py"] = ""
files["backend/utils/__init__.py"] = ""
files["backend/routes/__init__.py"] = "from . import resume_routes, job_routes, ranking_routes, export_routes"
files["backend/services/__init__.py"] = ""
files["backend/models/__init__.py"] = "from .db_models import Base, JobProfile, Candidate, CandidateAnalysis"

for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Fixed: {path}")

print("All files fixed!")
