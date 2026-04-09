#!/usr/bin/env python3
"""Download external images from all Obsidian notes to the local attachments folder.

Opens a pywebview UI to review images one by one. Press Download to save the image
to Zxtra/Assets/ and replace the markdown link with an Obsidian wikilink, or Skip
to leave it as-is. Navigate back with the ← button.
"""

import hashlib
import json
import mimetypes
import re
import threading
from pathlib import Path
from urllib.parse import urlparse

import requests
import webview

VAULT_PATH = Path(__file__).parent.parent
ATTACHMENTS_PATH = VAULT_PATH / "Zxtra" / "Assets"
STATE_PATH = Path(__file__).parent / ".download_images_state.json"

# Matches: ![alt text](https://...)
IMAGE_URL_PATTERN = re.compile(r'!\[([^\]]*)\]\((https?://[^\s)>]+)\)')

# Domains that are never direct image links (video sites, etc.)
EXCLUDED_DOMAINS = {"youtube.com", "www.youtube.com", "youtu.be"}


# ── Persisted state ──────────────────────────────────────────────────────────

def load_skipped() -> set[str]:
    if not STATE_PATH.exists():
        return set()
    data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return set(data.get("skipped", []))


def save_skipped(skipped: set[str]) -> None:
    STATE_PATH.write_text(
        json.dumps({"skipped": sorted(skipped)}, indent=2),
        encoding="utf-8",
    )


# ── Vault scanning ────────────────────────────────────────────────────────────

def find_remote_images(vault_path: Path) -> list[dict]:
    images = []
    for md_file in sorted(vault_path.rglob("*.md")):
        if ".obsidian" in md_file.parts or ".scripts" in md_file.parts or "Zxtra" in md_file.parts:
            continue
        content = md_file.read_text(encoding="utf-8")
        for match in IMAGE_URL_PATTERN.finditer(content):
            alt_text = match.group(1)
            url = match.group(2)
            domain = urlparse(url).netloc
            if domain in EXCLUDED_DOMAINS:
                continue
            # ID uses file + url only, not match offset — offset shifts when
            # earlier images in the same file are downloaded and their links replaced.
            image_id = hashlib.md5(f"{md_file}:{url}".encode()).hexdigest()[:10]
            images.append({
                "id": image_id,
                "note": str(md_file.relative_to(vault_path)),
                "note_abs": str(md_file),
                "url": url,
                "alt": alt_text,
                "full_match": match.group(0),
            })
    return images


# ── Download helpers ──────────────────────────────────────────────────────────

def derive_filename(url: str, content_type: str) -> str:
    url_filename = Path(urlparse(url).path).name
    if url_filename and "." in url_filename:
        return url_filename
    ext = mimetypes.guess_extension(content_type.split(";")[0].strip()) or ".bin"
    if ext == ".jpe":
        ext = ".jpg"
    return hashlib.md5(url.encode()).hexdigest()[:12] + ext


def unique_path(dest: Path) -> Path:
    if not dest.exists():
        return dest
    counter = 1
    while True:
        candidate = dest.with_stem(f"{dest.stem}_{counter}")
        if not candidate.exists():
            return candidate
        counter += 1


def download_and_replace(image: dict) -> dict:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
        response = requests.get(image["url"], timeout=30, headers=headers)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "application/octet-stream")
        filename = derive_filename(image["url"], content_type)

        ATTACHMENTS_PATH.mkdir(parents=True, exist_ok=True)
        dest = unique_path(ATTACHMENTS_PATH / filename)
        dest.write_bytes(response.content)

        rel_path = dest.relative_to(VAULT_PATH)
        wikilink = f"![[{rel_path}]]"

        note = Path(image["note_abs"])
        content = note.read_text(encoding="utf-8")
        updated = content.replace(image["full_match"], wikilink, 1)
        note.write_text(updated, encoding="utf-8")

        return {"ok": True, "saved_as": dest.name}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


# ── pywebview JS bridge ───────────────────────────────────────────────────────

class Api:
    def __init__(self, images: list[dict]):
        self._images_by_id = {img["id"]: img for img in images}
        self._all_images = images
        self._skipped = load_skipped()
        self.window: webview.Window | None = None

    def get_images(self) -> list[dict]:
        # Strip internal-only fields before sending to JS; include persisted skip flag.
        return [
            {
                **{k: v for k, v in img.items() if k not in ("note_abs", "full_match")},
                "previously_skipped": img["id"] in self._skipped,
            }
            for img in self._all_images
        ]

    def download_one(self, image_id: str) -> dict:
        image = self._images_by_id.get(image_id)
        if image is None:
            return {"ok": False, "error": "Unknown image id"}
        result = download_and_replace(image)
        # Remove from skipped state if it was there
        if result["ok"] and image_id in self._skipped:
            self._skipped.discard(image_id)
            save_skipped(self._skipped)
        return result

    def save_skip(self, image_id: str) -> None:
        self._skipped.add(image_id)
        save_skipped(self._skipped)

    def close(self) -> None:
        # Destroy must not block the JS bridge thread or it deadlocks on macOS.
        if self.window:
            threading.Thread(target=self.window.destroy, daemon=True).start()


# ── HTML UI ───────────────────────────────────────────────────────────────────

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Download Remote Images</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 13px;
    background: #1a1a1a;
    color: #d4d4d4;
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
    user-select: none;
  }

  /* ── Top bar ── */
  .topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 18px;
    border-bottom: 1px solid #2e2e2e;
    flex-shrink: 0;
  }
  .topbar .progress { color: #888; font-size: 12px; }
  .topbar .note {
    flex: 1;
    text-align: center;
    font-size: 12px;
    color: #aaa;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    padding: 0 16px;
  }
  .topbar .stats { font-size: 12px; color: #666; }

  /* ── Image area ── */
  .image-area {
    height: 380px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    position: relative;
    background: #141414;
  }
  .image-area img {
    max-width: 100%;
    max-height: 380px;
    object-fit: contain;
    display: block;
  }
  .placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    color: #555;
  }
  .placeholder .icon { font-size: 48px; }
  .placeholder .msg { font-size: 12px; }

  /* ── Status overlay (downloaded / error) ── */
  .overlay {
    position: absolute;
    top: 12px; right: 12px;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
  }
  .overlay.ok  { background: #1a3d1a; color: #6fcf6f; }
  .overlay.err { background: #3d1a1a; color: #cf6f6f; }

  /* ── Meta row ── */
  .meta {
    padding: 10px 18px;
    border-top: 1px solid #2e2e2e;
    display: flex;
    flex-direction: column;
    gap: 3px;
    flex-shrink: 0;
  }
  .meta .url {
    font-size: 11px;
    color: #7ca9f7;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .meta .alt { font-size: 11px; color: #666; }

  /* ── Action bar ── */
  .actions {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 18px;
    border-top: 1px solid #2e2e2e;
    flex-shrink: 0;
  }

  button {
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    border: none;
    transition: background 0.1s, opacity 0.1s;
  }
  button:disabled { opacity: 0.35; cursor: default; }

  .btn-nav {
    background: #2a2a2a;
    color: #aaa;
    border: 1px solid #3a3a3a;
    padding: 8px 12px;
  }
  .btn-nav:not(:disabled):hover { background: #333; }

  .spacer { flex: 1; }

  .btn-skip {
    background: #2a2a2a;
    color: #bbb;
    border: 1px solid #3a3a3a;
  }
  .btn-skip:not(:disabled):hover { background: #333; }

  .btn-download {
    background: #7c6af7;
    color: #fff;
    min-width: 130px;
  }
  .btn-download:not(:disabled):hover { background: #6a59e0; }

  .btn-close {
    background: transparent;
    color: #666;
    border: 1px solid #333;
  }
  .btn-close:hover { background: #222; color: #aaa; }

  /* ── Empty / done screens ── */
  .screen {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 14px;
    color: #666;
  }
  .screen .icon { font-size: 40px; }
  .screen h2 { font-size: 16px; font-weight: 600; color: #aaa; }
  .screen p  { font-size: 13px; color: #666; }
</style>
</head>
<body>

<!-- populated by JS -->
<div id="root"></div>

<script>
let images = [];
// decisions[id] = { status: "downloaded"|"skipped"|"error", label: string }
const decisions = {};
let index = 0;

// ── Init ──────────────────────────────────────────────────────────────────────

async function init() {
  images = await pywebview.api.get_images();

  // Restore persisted skip decisions and advance past them to the first pending image
  for (const img of images) {
    if (img.previously_skipped) {
      decisions[img.id] = { status: "skipped", label: "Skipped" };
    }
  }
  index = images.findIndex(img => !decisions[img.id]);
  if (index === -1) index = images.length; // all skipped → go to done screen

  render();
}

// ── Rendering ─────────────────────────────────────────────────────────────────

function render() {
  const root = document.getElementById("root");

  if (images.length === 0) {
    root.innerHTML = `
      <div class="screen">
        <div class="icon">🔍</div>
        <h2>No remote images found</h2>
        <p>All images in the vault are already local.</p>
        <button class="btn-close" onclick="close_()">Close</button>
      </div>`;
    return;
  }

  const pendingCount = images.filter(img => !decisions[img.id] || decisions[img.id].status === "skipped").length;
  const downloadedCount = images.filter(img => decisions[img.id]?.status === "downloaded").length;

  if (index >= images.length) {
    // All reviewed
    root.innerHTML = `
      <div class="screen">
        <div class="icon">✅</div>
        <h2>All done</h2>
        <p>${downloadedCount} downloaded · ${images.length - downloadedCount} skipped</p>
        <button class="btn-close" onclick="close_()">Close</button>
      </div>`;
    return;
  }

  const img = images[index];
  const decision = decisions[img.id];
  const isDownloaded = decision?.status === "downloaded";

  const overlayHtml = decision
    ? `<div class="overlay ${decision.status === "downloaded" ? "ok" : decision.status === "error" ? "err" : ""}">
         ${decision.label}
       </div>`
    : "";

  const statsText = `${downloadedCount} downloaded · ${images.length - downloadedCount - index > 0 ? images.length - index - downloadedCount : 0} remaining`;

  root.innerHTML = `
    <div class="topbar">
      <span class="progress">${index + 1} / ${images.length}</span>
      <span class="note" title="${escHtml(img.note)}">${escHtml(img.note)}</span>
      <span class="stats">${downloadedCount} downloaded</span>
    </div>

    <div class="image-area">
      <img id="img-preview" src="${escHtml(img.url)}"
        onerror="this.style.display='none'; document.getElementById('img-placeholder').style.display='flex'">
      <div id="img-placeholder" class="placeholder" style="display:none">
        <div class="icon">🖼️</div>
        <div class="msg">Image failed to load</div>
      </div>
      ${overlayHtml}
    </div>

    <div class="meta">
      <div class="url" title="${escHtml(img.url)}">${escHtml(img.url)}</div>
      ${img.alt ? `<div class="alt">alt: ${escHtml(img.alt)}</div>` : ""}
    </div>

    <div class="actions">
      <button class="btn-nav" onclick="go(-1)" ${index === 0 ? "disabled" : ""}>←</button>
      <div class="spacer"></div>
      <button class="btn-close" onclick="close_()">Close</button>
      <button class="btn-skip" onclick="skip()" ${isDownloaded ? "disabled" : ""}>Skip</button>
      <button class="btn-download" id="btn-dl" onclick="download()" ${isDownloaded ? "disabled" : ""}>
        ${isDownloaded ? "✓ Downloaded" : "Download"}
      </button>
    </div>`;
}

// ── Actions ───────────────────────────────────────────────────────────────────

function go(delta) {
  index = Math.max(0, Math.min(images.length - 1, index + delta));
  render();
}

function skip() {
  const img = images[index];
  if (!decisions[img.id] || decisions[img.id].status !== "downloaded") {
    decisions[img.id] = { status: "skipped", label: "Skipped" };
    pywebview.api.save_skip(img.id); // fire-and-forget
  }
  index++;
  render();
}

async function download() {
  const img = images[index];
  const btn = document.getElementById("btn-dl");
  btn.disabled = true;
  btn.textContent = "Downloading…";

  const result = await pywebview.api.download_one(img.id);

  if (result.ok) {
    decisions[img.id] = { status: "downloaded", label: `✓ ${result.saved_as}` };
    index++;
  } else {
    decisions[img.id] = { status: "error", label: `✗ ${result.error}` };
  }
  render();
}

function close_() {
  pywebview.api.close();
}

// Keyboard shortcuts
document.addEventListener("keydown", e => {
  if (e.key === "ArrowRight") skip();
  if (e.key === "ArrowLeft")  go(-1);
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    const img = images[index];
    if (img && (!decisions[img.id] || decisions[img.id].status !== "downloaded")) download();
  }
  if (e.key === "Escape") close_();
});

function escHtml(str) {
  return str.replace(/&/g,"&amp;").replace(/</g,"&lt;")
            .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

window.addEventListener("pywebviewready", init);
</script>
</body>
</html>
"""


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    print("Scanning vault for remote images…")
    images = find_remote_images(VAULT_PATH)
    print(f"Found {len(images)} remote image(s).")

    api = Api(images)
    window = webview.create_window(
        "Download Remote Images",
        html=HTML,
        js_api=api,
        width=800,
        height=620,
        min_size=(560, 440),
    )
    api.window = window
    webview.start()


if __name__ == "__main__":
    main()
