from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.core.config import get_settings
from app.db.session import Base, engine

settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts_list)

if settings.enforce_https:
    app.add_middleware(HTTPSRedirectMiddleware)

app.add_middleware(GZipMiddleware, minimum_size=settings.gzip_minimum_size)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=settings.cors_origin_regex_value,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)


app.include_router(health_router)
app.include_router(documents_router, prefix=settings.api_prefix)
