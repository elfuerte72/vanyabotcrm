"""One-off: upload funnel photos to a public Supabase Storage bucket.

The bot sends funnel photos from local files in ``bot/media/photos/`` and now
records their filenames in ``user_events.media``. The CRM (a separate service
with no access to those files) renders them from Supabase Storage, so this
script mirrors the local photos into a public bucket once. Re-running it is
safe — uploads use upsert and the bucket is created only if missing.

Usage:
    SUPABASE_URL=https://<project>.supabase.co \\
    SUPABASE_SERVICE_KEY=<service_role_key> \\
    uv run python -m scripts.upload_funnel_media

The service_role key is required (it bypasses RLS for bucket/object writes).
Find it in Supabase → Project Settings → API → service_role secret.
"""

from __future__ import annotations

import mimetypes
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

_BOT_DIR = Path(__file__).resolve().parent.parent
# Credentials live in the repo-root .env (preferred), with bot/.env as a fallback.
load_dotenv(_BOT_DIR.parent / ".env")
load_dotenv(_BOT_DIR / ".env")

BUCKET = os.environ.get("FUNNEL_MEDIA_BUCKET", "funnel-media")
PHOTOS_DIR = _BOT_DIR / "media" / "photos"


def _headers(service_key: str) -> dict[str, str]:
    return {"apikey": service_key, "Authorization": f"Bearer {service_key}"}


def _ensure_bucket(client: httpx.Client, base_url: str, service_key: str) -> None:
    resp = client.post(
        f"{base_url}/storage/v1/bucket",
        headers=_headers(service_key),
        json={"id": BUCKET, "name": BUCKET, "public": True},
    )
    if resp.status_code in (200, 201):
        print(f"✓ bucket '{BUCKET}' created (public)")
    elif resp.status_code in (400, 409) and "exist" in resp.text.lower():
        print(f"• bucket '{BUCKET}' already exists")
    else:
        raise SystemExit(f"Failed to create bucket: {resp.status_code} {resp.text}")


def _upload(client: httpx.Client, base_url: str, service_key: str, path: Path) -> None:
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    with path.open("rb") as fh:
        data = fh.read()
    resp = client.post(
        f"{base_url}/storage/v1/object/{BUCKET}/{path.name}",
        headers={**_headers(service_key), "Content-Type": content_type, "x-upsert": "true"},
        content=data,
    )
    if resp.status_code not in (200, 201):
        raise SystemExit(f"Failed to upload {path.name}: {resp.status_code} {resp.text}")
    print(f"  ↑ {path.name} ({len(data) // 1024} KB)")


def main() -> None:
    base_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not base_url or not service_key:
        raise SystemExit("Set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables.")

    if not PHOTOS_DIR.is_dir():
        raise SystemExit(f"Photos dir not found: {PHOTOS_DIR}")

    files = sorted(p for p in PHOTOS_DIR.iterdir() if p.is_file() and not p.name.startswith("."))
    if not files:
        raise SystemExit(f"No photos found in {PHOTOS_DIR}")

    print(f"Uploading {len(files)} files to {base_url}/storage/v1/object/{BUCKET}/ …")
    with httpx.Client(timeout=60) as client:
        _ensure_bucket(client, base_url, service_key)
        for path in files:
            _upload(client, base_url, service_key, path)

    print(
        f"\n✓ Done. Public URL pattern:\n"
        f"  {base_url}/storage/v1/object/public/{BUCKET}/<filename>"
    )


if __name__ == "__main__":
    sys.exit(main())
