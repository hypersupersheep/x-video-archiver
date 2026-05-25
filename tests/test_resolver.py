import pytest

from x_video_tool.resolver import (
    ResolveError,
    ResolverConfig,
    build_response,
    normalize_x_url,
)


def test_normalize_accepts_x_status_url():
    assert (
        normalize_x_url("x.com/example/status/12345?s=20#ignored")
        == "https://x.com/example/status/12345?s=20"
    )


def test_normalize_rejects_non_x_url():
    with pytest.raises(ResolveError):
        normalize_x_url("https://example.com/watch/123")


def test_build_response_prefers_highest_direct_mp4():
    info = {
        "id": "123",
        "title": "Sample Video",
        "formats": [
            {
                "format_id": "hls-720",
                "url": "https://video.example/playlist.m3u8",
                "ext": "mp4",
                "protocol": "m3u8_native",
                "height": 720,
                "tbr": 1500,
            },
            {
                "format_id": "http-360",
                "url": "https://video.example/360.mp4",
                "ext": "mp4",
                "protocol": "https",
                "height": 360,
                "tbr": 800,
            },
            {
                "format_id": "http-720",
                "url": "https://video.example/720.mp4",
                "ext": "mp4",
                "protocol": "https",
                "height": 720,
                "tbr": 1400,
            },
        ],
    }

    resolved = build_response("https://x.com/example/status/123", info, ResolverConfig())

    assert resolved["download_url"] == "https://video.example/720.mp4"
    assert resolved["videos"][0]["best"]["format_id"] == "http-720"


def test_build_response_rejects_long_video():
    info = {
        "id": "123",
        "title": "Long Video",
        "duration": 601,
        "formats": [
            {
                "format_id": "http-720",
                "url": "https://video.example/720.mp4",
                "ext": "mp4",
                "protocol": "https",
                "height": 720,
            }
        ],
    }

    with pytest.raises(ResolveError):
        build_response(
            "https://x.com/example/status/123",
            info,
            ResolverConfig(max_duration_seconds=600),
        )
