from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import settings
from .resolver import ResolveError, ResolverConfig, normalize_x_url, resolve_video


STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="X Video Archiver",
    description="Private X/Twitter video resolver for iPhone Shortcuts.",
    version="0.1.0",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ResolveRequest(BaseModel):
    url: str = Field(..., min_length=1)


def require_token(
    authorization: str | None = Header(default=None),
    x_api_token: str | None = Header(default=None),
) -> None:
    if not settings.app_token:
        return

    bearer = None
    if authorization and authorization.lower().startswith("bearer "):
        bearer = authorization.split(" ", 1)[1].strip()

    if settings.app_token not in {bearer, x_api_token}:
        raise HTTPException(status_code=401, detail="Missing or invalid API token.")


def resolver_config() -> ResolverConfig:
    return ResolverConfig(
        cookies_file=settings.cookies_file,
        max_duration_seconds=settings.max_duration_seconds,
        request_timeout_seconds=settings.request_timeout_seconds,
    )


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/resolve", dependencies=[Depends(require_token)])
def api_resolve(payload: ResolveRequest) -> dict:
    try:
        return resolve_video(payload.url, resolver_config())
    except ResolveError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/download", dependencies=[Depends(require_token)])
def download(url: str = Query(..., min_length=1)) -> RedirectResponse:
    """Resolve a post URL and redirect to the best direct mp4 variant."""

    try:
        normalized = normalize_x_url(url)
        resolved = resolve_video(normalized, resolver_config())
    except ResolveError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return RedirectResponse(resolved["download_url"], status_code=302)
