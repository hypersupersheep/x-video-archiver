# iPhone Shortcut Setup

This version starts with the clipboard because it is easy to debug.

## Before You Start

Run the service:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn x_video_tool.server:app --host 0.0.0.0 --port 8000
```

Find the Mac's LAN address:

```bash
ipconfig getifaddr en0
```

The shortcut should call:

```text
http://<mac-lan-ip>:8000/api/resolve
```

Do not use `localhost` on the iPhone. On the phone, `localhost` means the phone itself, not the Mac.

## Actions

Create a new shortcut.

1. `Get Clipboard`
2. `Get Contents of URL`
   - URL: `http://<server-host>:8000/api/resolve`
   - Method: `POST`
   - Header: `Content-Type = application/json`
   - Request Body: `JSON`
   - JSON field: `url = Clipboard`
3. `Get Dictionary Value`
   - Key: `download_url`
   - Input: result from the first `Get Contents of URL`
4. `Get Contents of URL`
   - URL: the `download_url` dictionary value
5. `Save File` or `Save to Photo Album`

If the last step saves the wrong thing, set a variable after the second URL request:

```text
Video File = Contents of URL
```

Then save `Video File`. Shortcuts reuses vague names like `Contents of URL`, so naming the video output avoids confusion.

## Public Server

For a server exposed to the internet, set an app token:

```bash
export X_VIDEO_APP_TOKEN="<long-random-string>"
```

Add this header to the first `Get Contents of URL` action:

```text
Authorization: Bearer <long-random-string>
```

For posts that need browser login context, start the backend with:

```bash
X_VIDEO_COOKIES_FROM_BROWSER=chrome .venv/bin/uvicorn x_video_tool.server:app --host 0.0.0.0 --port 8000
```

For long videos, disable the default 600-second limit:

```bash
X_VIDEO_MAX_DURATION_SECONDS=0 .venv/bin/uvicorn x_video_tool.server:app --host 0.0.0.0 --port 8000
```

Both can be combined:

```bash
X_VIDEO_COOKIES_FROM_BROWSER=chrome X_VIDEO_MAX_DURATION_SECONDS=0 .venv/bin/uvicorn x_video_tool.server:app --host 0.0.0.0 --port 8000
```

## Common Failures

- `401 Missing or invalid API token`: the server expects a token and the shortcut did not send it.
- `No direct mp4 video variants`: the post has no direct MP4 variant, or it is not a video post.
- `Cookies file not found`: `X_VIDEO_COOKIES_FILE` points to a file that does not exist.
- `Video is ... max allowed`: the post is longer than the configured duration limit.
- The iPhone cannot connect: the Mac and iPhone are not on the same network, the server is not running, or macOS blocked incoming connections.
