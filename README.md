# X Video Archiver

A small private helper for saving authorized videos from X posts to an iPhone.

The iPhone shortcut handles the share flow and file saving. A tiny FastAPI service does the part Shortcuts is bad at: resolving an X post into the best direct MP4 variant.

This is meant for personal archiving: your own posts, videos you have permission to save, or material that is clearly licensed for offline use.

## How It Works

```text
X post URL
-> iPhone Shortcut
-> FastAPI service
-> yt-dlp extracts MP4 variants
-> Shortcut downloads the selected MP4
-> Files or Photos
```

Shortcuts can make HTTP requests and save files, but it is not a reliable X parser. X pages depend on JavaScript, internal APIs, guest tokens, and sometimes cookies. Keeping that logic on a small backend is simpler and easier to fix.

## Run Locally

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn x_video_tool.server:app --host 0.0.0.0 --port 8000
```

Open the local web UI:

```text
http://127.0.0.1:8000
```

For iPhone use, replace `127.0.0.1` with your Mac's LAN address. On macOS:

```bash
ipconfig getifaddr en0
```

Then use:

```text
http://<mac-lan-ip>:8000
```

## Shortcut Setup

The easiest first version uses the clipboard.

1. Copy an X post URL.
2. Get Clipboard.
3. POST it to `http://<server-host>:8000/api/resolve` as JSON:

```json
{
  "url": "Clipboard"
}
```

4. Read `download_url` from the JSON response.
5. Get Contents of URL for that `download_url`.
6. Save the file to Files or Photos.

More detailed steps are in [docs/iphone-shortcut.md](docs/iphone-shortcut.md).

## API

Resolve a post:

```bash
curl -X POST http://127.0.0.1:8000/api/resolve \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://x.com/TwitterDev/status/1304102743196356610"}'
```

The important field is:

```json
{
  "download_url": "https://video.twimg.com/..."
}
```

Redirect straight to the best MP4:

```text
http://127.0.0.1:8000/download?url=<x-post-url>
```

## Public Deployment

If the service is reachable from the internet, protect it:

```bash
export X_VIDEO_APP_TOKEN="<long-random-string>"
```

Send it from the shortcut:

```text
Authorization: Bearer <long-random-string>
```

If you add a cookies file for posts that need login context, keep it local and never commit it:

```bash
export X_VIDEO_COOKIES_FILE="/path/to/browser-cookies-file"
```

You can also let `yt-dlp` read cookies from a local browser profile:

```bash
export X_VIDEO_COOKIES_FROM_BROWSER="chrome"
```

The browser account does not need to match the phone account. It only needs permission to view the post. Keep this mode private: any caller using your API may indirectly use that browser session for resolution.

The default maximum duration is 600 seconds. Set it to `0` to disable that guardrail:

```bash
export X_VIDEO_MAX_DURATION_SECONDS=0
```

## Tests

```bash
.venv/bin/pytest -q
```

Current coverage checks URL validation, MP4 selection, and the short-video guardrail.

## Notes

- This is not a public downloader service.
- Do not commit tokens, cookies, or real deployment URLs.
- Public deployments should add rate limiting before regular use.
