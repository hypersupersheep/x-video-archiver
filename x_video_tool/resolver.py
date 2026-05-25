from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


ALLOWED_HOSTS = {
    "x.com",
    "www.x.com",
    "mobile.x.com",
    "twitter.com",
    "www.twitter.com",
    "mobile.twitter.com",
}


class ResolveError(Exception):
    """Raised when a post cannot be resolved into downloadable media."""


@dataclass(frozen=True)
class ResolverConfig:
    cookies_file: str | None = None
    cookies_from_browser: str | None = None
    max_duration_seconds: int = 600
    request_timeout_seconds: int = 45


def normalize_x_url(raw_url: str) -> str:
    """Return a clean X/Twitter URL or raise ResolveError.

    这里只接受 X/Twitter 的 post URL，避免这个服务被滥用成通用下载代理。
    """

    candidate = raw_url.strip()
    if not candidate:
        raise ResolveError("URL is empty.")

    if "://" not in candidate:
        candidate = f"https://{candidate}"

    parsed = urlparse(candidate)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"} or host not in ALLOWED_HOSTS:
        raise ResolveError("Only x.com/twitter.com post URLs are supported.")

    path_parts = [part for part in parsed.path.split("/") if part]
    is_status_url = "status" in path_parts or path_parts[:2] == ["i", "status"]
    if not is_status_url:
        raise ResolveError("The URL must point to an X/Twitter status post.")

    return parsed._replace(scheme="https", fragment="").geturl()


def resolve_video(raw_url: str, config: ResolverConfig) -> dict[str, Any]:
    url = normalize_x_url(raw_url)

    ydl_opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "socket_timeout": config.request_timeout_seconds,
        "extractor_args": {"twitter": {"api": ["graphql"]}},
    }

    if config.cookies_file:
        cookies_path = Path(config.cookies_file).expanduser()
        if not cookies_path.exists():
            raise ResolveError(f"Cookies file not found: {cookies_path}")
        ydl_opts["cookiefile"] = str(cookies_path)

    if config.cookies_from_browser:
        ydl_opts["cookiesfrombrowser"] = parse_cookies_from_browser(
            config.cookies_from_browser
        )

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except DownloadError as exc:
        raise ResolveError(str(exc)) from exc
    except Exception as exc:  # yt-dlp extractors can raise several concrete types.
        raise ResolveError(f"Unexpected extractor error: {exc}") from exc

    return build_response(url, info, config)


def parse_cookies_from_browser(raw_value: str) -> tuple[str, str | None, str | None, str | None]:
    """Parse a small subset of yt-dlp's browser cookie syntax.

    Accepted values:
    - chrome
    - safari
    - chrome:Profile 1
    - firefox:default-release::container
    """

    value = raw_value.strip()
    if not value:
        raise ResolveError("X_VIDEO_COOKIES_FROM_BROWSER is empty.")

    browser_and_profile, _, container = value.partition("::")
    browser_part, _, profile = browser_and_profile.partition(":")
    browser, _, keyring = browser_part.partition("+")

    browser = browser.strip().lower()
    if not browser:
        raise ResolveError("Browser name is missing in X_VIDEO_COOKIES_FROM_BROWSER.")

    return (
        browser,
        profile.strip() or None,
        keyring.strip().upper() or None,
        container.strip() or None,
    )


def build_response(source_url: str, info: dict[str, Any], config: ResolverConfig) -> dict[str, Any]:
    videos = []
    for entry in _video_entries(info):
        duration = entry.get("duration")
        if (
            config.max_duration_seconds > 0
            and duration is not None
            and duration > config.max_duration_seconds
        ):
            raise ResolveError(
                f"Video is {int(duration)}s; max allowed is {config.max_duration_seconds}s."
            )

        formats = [_format_payload(fmt) for fmt in entry.get("formats") or []]
        formats = [fmt for fmt in formats if fmt["url"]]
        mp4_formats = [fmt for fmt in formats if _is_direct_mp4(fmt)]

        if not mp4_formats:
            continue

        best = max(mp4_formats, key=_format_score)
        videos.append(
            {
                "id": entry.get("id") or info.get("id"),
                "title": entry.get("title") or info.get("title") or "x-video",
                "duration": duration,
                "thumbnail": entry.get("thumbnail") or info.get("thumbnail"),
                "best": best,
                "formats": sorted(mp4_formats, key=_format_score, reverse=True),
            }
        )

    if not videos:
        raise ResolveError("No direct mp4 video variants were found in this post.")

    first = videos[0]
    return {
        "source_url": source_url,
        "title": info.get("title") or first["title"],
        "extractor": info.get("extractor_key") or info.get("extractor"),
        "download_url": first["best"]["url"],
        "filename": _suggest_filename(first),
        "videos": videos,
    }


def _video_entries(info: dict[str, Any]) -> list[dict[str, Any]]:
    entries = info.get("entries")
    if isinstance(entries, list) and entries:
        return [entry for entry in entries if isinstance(entry, dict)]
    return [info]


def _format_payload(fmt: dict[str, Any]) -> dict[str, Any]:
    return {
        "format_id": fmt.get("format_id"),
        "url": fmt.get("url"),
        "ext": fmt.get("ext"),
        "protocol": fmt.get("protocol"),
        "height": fmt.get("height"),
        "width": fmt.get("width"),
        "fps": fmt.get("fps"),
        "tbr": fmt.get("tbr"),
        "filesize": fmt.get("filesize") or fmt.get("filesize_approx"),
        "format_note": fmt.get("format_note"),
    }


def _is_direct_mp4(fmt: dict[str, Any]) -> bool:
    url = fmt.get("url") or ""
    protocol = fmt.get("protocol") or ""
    return (
        fmt.get("ext") == "mp4"
        and url.startswith("http")
        and ".m3u8" not in url
        and "m3u8" not in protocol
    )


def _format_score(fmt: dict[str, Any]) -> tuple[int, float, int]:
    height = fmt.get("height") or 0
    bitrate = fmt.get("tbr") or 0.0
    filesize = fmt.get("filesize") or 0
    return (height, bitrate, filesize)


def _suggest_filename(video: dict[str, Any]) -> str:
    raw_title = video.get("title") or video.get("id") or "x-video"
    safe = "".join(char if char.isalnum() or char in "-_." else "_" for char in raw_title)
    safe = "_".join(part for part in safe.split("_") if part)[:80]
    return f"{safe or 'x-video'}.mp4"
