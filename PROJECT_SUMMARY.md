# Project Summary

`x-video-archiver` is a small iPhone workflow project.

The shortcut sends an X post URL to a FastAPI service. The service uses `yt-dlp` to read the available MP4 variants and returns the best direct video URL. The shortcut downloads that URL and saves the file.

What is included:

- FastAPI API and web UI
- X/Twitter URL validation
- MP4 variant selection
- optional API token for public deployments
- optional cookies file support for authenticated context
- iPhone Shortcut setup notes
- focused tests for resolver behavior

What is intentionally not included:

- no real tokens
- no cookies
- no personal IP addresses
- no hosted endpoint
- no bulk downloading workflow
