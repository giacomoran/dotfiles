#!/usr/bin/env python3
"""Create Obsidian notes for YouTube links found in the vault.

Opens a pywebview UI to review each YouTube link one by one. Press Create to
download the audio, transcribe with WhisperX (faster-whisper + pyannote), and
write a note under "📘 Sources - Videos/" containing a YouTube embed and a
speaker-diarized transcript. Press Skip to leave the link as-is. Navigate back
with ←.
"""

import getpass
import json
import os
import re
import subprocess
import tempfile
import threading
import traceback
import warnings
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# torchcodec ships broken dylibs on macOS; suppress its warning — whisperx never
# uses it (it loads audio via soundfile/librosa directly).
warnings.filterwarnings("ignore", module=r"pyannote\.audio\.core\.io")

import mlx_whisper
import requests
import torch
import webview
import whisperx
from whisperx.diarize import DiarizationPipeline

VAULT_PATH = Path(__file__).parent.parent
VIDEOS_PATH = VAULT_PATH / "📘 Sources - Videos"
STATE_PATH = Path(__file__).parent / ".create_video_notes_state.json"
HF_TOKEN_PATH = Path(__file__).parent / ".hf_token"

# mlx-whisper runs on MPS/ANE via Apple's MLX framework.
WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"
# Alignment and diarization are PyTorch-based; use MPS where available.
_TORCH_DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"

# Matches !?[text](youtube_url) — group 1 is full match, group 2 is the URL
_MD_LINK_RE = re.compile(
    r'(!?\[[^\]]*\])'
    r'\((https?://(?:www\.)?(?:youtube\.com/watch\?[^\s)>]*v=[^\s)>&]+|youtu\.be/[^\s)>?]+)[^\s)>]*)\)'
)

# Matches bare YouTube URLs not preceded by "(" (i.e., not already inside a markdown link)
_BARE_URL_RE = re.compile(
    r'(?<!\()(https?://(?:www\.)?(?:youtube\.com/watch\?[^\s)>\]]*v=[^\s)>&\]]+|youtu\.be/[^\s)>\]?]+)[^\s)>\]]*)'
)


# ── URL helpers ───────────────────────────────────────────────────────────────

def extract_video_id(url: str) -> str | None:
    parsed = urlparse(url)
    netloc = parsed.netloc.removeprefix("www.")
    if netloc == "youtube.com" and parsed.path == "/watch":
        ids = parse_qs(parsed.query).get("v", [])
        return ids[0] if ids else None
    if netloc == "youtu.be":
        vid = parsed.path.lstrip("/").split("?")[0]
        return vid or None
    return None


def canonical_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def thumbnail_url(video_id: str) -> str:
    return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"


# ── State persistence ─────────────────────────────────────────────────────────

def load_state() -> dict:
    if not STATE_PATH.exists():
        return {"skipped": [], "created": []}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def load_hf_token() -> str:
    """Load HuggingFace token from disk, prompting once if not yet stored."""
    if HF_TOKEN_PATH.exists():
        return HF_TOKEN_PATH.read_text(encoding="utf-8").strip()
    token = getpass.getpass("HuggingFace token (for pyannote diarization): ").strip()
    assert token, "HuggingFace token is required"
    HF_TOKEN_PATH.write_text(token, encoding="utf-8")
    return token


# ── Vault scanning ────────────────────────────────────────────────────────────

def find_youtube_links(vault_path: Path) -> list[dict]:
    """Return one entry per unique video ID, collecting all occurrences across notes."""
    by_video_id: dict[str, dict] = {}

    for md_file in sorted(vault_path.rglob("*.md")):
        if any(part in (".obsidian", ".scripts", "Zxtra") for part in md_file.parts):
            continue
        content = md_file.read_text(encoding="utf-8")

        # Collect (full_match, url) pairs — markdown links first, then bare URLs.
        # _BARE_URL_RE won't match URLs already inside markdown link parens
        # because of the (?<!\() lookbehind, so there is no overlap.
        pairs: list[tuple[str, str]] = []
        for m in _MD_LINK_RE.finditer(content):
            pairs.append((m.group(0), m.group(2)))
        for m in _BARE_URL_RE.finditer(content):
            pairs.append((m.group(0), m.group(1)))

        for full_match, url in pairs:
            video_id = extract_video_id(url)
            if not video_id:
                continue
            occurrence = {
                "note": str(md_file.relative_to(vault_path)),
                "note_abs": str(md_file),
                "full_match": full_match,
            }
            if video_id not in by_video_id:
                by_video_id[video_id] = {
                    "video_id": video_id,
                    "url": canonical_url(video_id),
                    "thumbnail": thumbnail_url(video_id),
                    "occurrences": [],
                }
            by_video_id[video_id]["occurrences"].append(occurrence)

    return list(by_video_id.values())


# ── Processing helpers ────────────────────────────────────────────────────────

def sanitize_filename(name: str) -> str:
    sanitized = re.sub(r'[/\\:*?"<>|]', "-", name)
    return sanitized.strip(" .")


def _run_ytdlp(args: list[str]) -> subprocess.CompletedProcess:
    result = subprocess.run(
        ["yt-dlp"] + args,
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        # Extract the first ERROR line for a compact message; log full stderr for debugging
        error_line = next(
            (l.removeprefix("ERROR: ") for l in result.stderr.splitlines() if l.startswith("ERROR:")),
            result.stderr.strip(),
        )
        print(result.stderr.strip())
        raise RuntimeError(error_line)
    return result


def fetch_metadata(url: str) -> dict:
    result = _run_ytdlp(["--dump-json", "--no-playlist", url])
    data = json.loads(result.stdout)
    upload_date = data.get("upload_date", "0000")  # YYYYMMDD
    return {
        "title": data["title"],
        "uploader": data.get("uploader") or data.get("channel") or "Unknown",
        "year": upload_date[:4],
        "duration": data.get("duration_string", ""),
    }


def download_audio(url: str, dest_dir: Path) -> Path:
    # whisperx.load_audio handles resampling; just get the best available audio
    _run_ytdlp(["--no-playlist", "-f", "bestaudio",
                "--extract-audio", "--audio-format", "wav",
                "-o", str(dest_dir / "audio.%(ext)s"), url])
    return dest_dir / "audio.wav"


# Lazily loaded so startup is fast and the model is only fetched on first use
_diarize_model = None


def get_diarize_model(hf_token: str):
    global _diarize_model
    if _diarize_model is None:
        _diarize_model = DiarizationPipeline(token=hf_token, device=_TORCH_DEVICE)
    return _diarize_model


def format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def format_transcript(segments: list[dict]) -> str:
    """Group consecutive same-speaker segments and render with timestamps."""
    lines: list[str] = []
    current_speaker: str | None = None
    current_texts: list[str] = []
    current_start: float = 0.0

    for seg in segments:
        speaker = seg.get("speaker") or "SPEAKER_?"
        text = seg["text"].strip()
        if not text:
            continue
        if speaker != current_speaker:
            if current_texts and current_speaker is not None:
                lines.append(f"**{current_speaker}** · {format_timestamp(current_start)}")
                lines.append(" ".join(current_texts))
                lines.append("")
            current_speaker = speaker
            current_texts = [text]
            current_start = seg.get("start", 0.0)
        else:
            current_texts.append(text)

    if current_texts and current_speaker is not None:
        lines.append(f"**{current_speaker}** · {format_timestamp(current_start)}")
        lines.append(" ".join(current_texts))

    return "\n".join(lines)


def transcribe_audio(audio_path: Path, hf_token: str) -> str:
    # Transcribe on MPS/ANE via MLX — handles long-form natively.
    # hallucination_silence_threshold suppresses repetition loops on silent regions.
    result = mlx_whisper.transcribe(
        str(audio_path), path_or_hf_repo=WHISPER_MODEL,
        hallucination_silence_threshold=2.0,
    )

    # Load audio as numpy array for the alignment and diarization steps
    audio = whisperx.load_audio(str(audio_path))

    # Drop empty segments before alignment — whisperx warns and skips them anyway,
    # but filtering here keeps the logs clean.
    result["segments"] = [s for s in result["segments"] if s.get("text", "").strip()]

    # Align to get word-level timestamps (required for diarization assignment)
    align_model, metadata = whisperx.load_align_model(
        language_code=result["language"], device=_TORCH_DEVICE,
    )
    result = whisperx.align(
        result["segments"], align_model, metadata, audio,
        device=_TORCH_DEVICE, return_char_alignments=False,
    )

    # Assign speaker labels via pyannote
    diarize = get_diarize_model(hf_token)
    diarize_segments = diarize(audio)
    result = whisperx.assign_word_speakers(diarize_segments, result)

    return format_transcript(result["segments"])


def note_filename(uploader: str, year: str, title: str) -> str:
    return f"{sanitize_filename(uploader)}, {year} - {sanitize_filename(title)}.md"


def write_note(video_id: str, metadata: dict, transcript: str) -> Path:
    VIDEOS_PATH.mkdir(parents=True, exist_ok=True)
    filename = note_filename(metadata["uploader"], metadata["year"], metadata["title"])
    note_path = VIDEOS_PATH / filename
    content = (
        f"![](https://www.youtube.com/watch?v={video_id})\n\n"
        f"**Channel:** {metadata['uploader']}\n"
        f"**Year:** {metadata['year']}\n"
        f"**URL:** https://www.youtube.com/watch?v={video_id}\n\n"
        f"## Transcript\n\n"
        f"{transcript}\n"
    )
    note_path.write_text(content, encoding="utf-8")
    return note_path


def replace_in_source_notes(occurrences: list[dict], wikilink: str) -> None:
    for occ in occurrences:
        note = Path(occ["note_abs"])
        content = note.read_text(encoding="utf-8")
        updated = content.replace(occ["full_match"], wikilink, 1)
        note.write_text(updated, encoding="utf-8")


# ── pywebview JS bridge ───────────────────────────────────────────────────────

class Api:
    def __init__(self, videos: list[dict], hf_token: str):
        self._videos_by_id = {v["video_id"]: v for v in videos}
        self._all_videos = videos
        state = load_state()
        self._skipped: set[str] = set(state.get("skipped", []))
        self._created: set[str] = set(state.get("created", []))
        self._hf_token = hf_token
        self._info_cache: dict[str, dict] = {}
        self.window: webview.Window | None = None

    def fetch_video_info(self, video_id: str) -> dict:
        if video_id in self._info_cache:
            return self._info_cache[video_id]
        try:
            url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            data = requests.get(url, timeout=10).json()
            info = {"title": data["title"], "author": data["author_name"]}
        except Exception:
            traceback.print_exc()
            info = {"title": "Unknown", "author": "Unknown"}
        self._info_cache[video_id] = info
        return info

    def _push_status(self, message: str) -> None:
        if self.window:
            safe = message.replace("\\", "\\\\").replace("'", "\\'")
            self.window.evaluate_js(f"updateStatus('{safe}')")

    def get_videos(self) -> list[dict]:
        return [
            {
                "video_id": v["video_id"],
                "url": v["url"],
                "thumbnail": v["thumbnail"],
                "note_titles": [Path(occ["note"]).stem for occ in v["occurrences"]],
                "previously_skipped": v["video_id"] in self._skipped,
                "already_created": v["video_id"] in self._created,
            }
            for v in self._all_videos
        ]

    def create_one(self, video_id: str) -> dict:
        video = self._videos_by_id.get(video_id)
        if video is None:
            return {"ok": False, "error": "Unknown video id"}
        try:
            self._push_status("Fetching metadata…")
            metadata = fetch_metadata(video["url"])

            with tempfile.TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                self._push_status("Downloading audio…")
                audio_path = download_audio(video["url"], tmp_path)
                self._push_status("Transcribing…")
                transcript = transcribe_audio(audio_path, self._hf_token)
                # audio_path is deleted when the TemporaryDirectory context exits

            self._push_status("Writing note…")
            note_path = write_note(video_id, metadata, transcript)
            note_title = note_path.stem

            wikilink = f"[[📘 Sources - Videos/{note_title}]]"
            replace_in_source_notes(video["occurrences"], wikilink)

            self._created.add(video_id)
            self._skipped.discard(video_id)
            save_state({"skipped": sorted(self._skipped), "created": sorted(self._created)})

            return {"ok": True, "note_title": note_title}
        except Exception as exc:
            traceback.print_exc()
            return {"ok": False, "error": str(exc)}

    def save_skip(self, video_id: str) -> None:
        self._skipped.add(video_id)
        save_state({"skipped": sorted(self._skipped), "created": sorted(self._created)})

    def close(self) -> None:
        if self.window:
            threading.Thread(target=self.window.destroy, daemon=True).start()


# ── HTML UI ───────────────────────────────────────────────────────────────────

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Create Video Notes</title>
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

  /* ── Thumbnail area ── */
  .thumb-area {
    height: 320px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    position: relative;
    background: #141414;
  }
  .thumb-area img {
    max-width: 100%;
    max-height: 320px;
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
  .placeholder .msg  { font-size: 12px; }

  /* ── Status overlay ── */
  .overlay {
    position: absolute;
    top: 12px; right: 12px;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
  }
  .overlay.ok      { background: #1a3d1a; color: #6fcf6f; }
  .overlay.err     { background: #3d1a1a; color: #cf6f6f; }
  .overlay.working { background: #1a2e3d; color: #6faecf; }

  /* ── Meta row ── */
  .meta {
    padding: 10px 18px;
    border-top: 1px solid #2e2e2e;
    display: flex;
    flex-direction: column;
    gap: 3px;
    flex-shrink: 0;
  }
  .meta .title {
    font-size: 13px;
    font-weight: 500;
    color: #d4d4d4;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .meta .author { font-size: 12px; color: #888; }
  .meta .refs   { font-size: 11px; color: #666; }

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

  .btn-create {
    background: #7c6af7;
    color: #fff;
    min-width: 130px;
  }
  .btn-create:not(:disabled):hover { background: #6a59e0; }

  .btn-copy {
    background: #2a2a2a;
    color: #bbb;
    border: 1px solid #3a3a3a;
  }
  .btn-copy:not(:disabled):hover { background: #333; }
  .btn-copy.copied { color: #6fcf6f; border-color: #6fcf6f44; }

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

<div id="root"></div>

<script>
let videos = [];
// decisions[video_id] = { status: "created"|"skipped"|"error"|"working", label: string }
const decisions = {};
let index = 0;

// ── Init ──────────────────────────────────────────────────────────────────────

async function init() {
  videos = await pywebview.api.get_videos();

  for (const v of videos) {
    if (v.already_created) {
      decisions[v.video_id] = { status: "created", label: "Already created" };
    } else if (v.previously_skipped) {
      decisions[v.video_id] = { status: "skipped", label: "Skipped" };
    }
  }
  index = videos.findIndex(v => !decisions[v.video_id]);
  if (index === -1) index = videos.length;

  render();
}

// ── Video info (title / author via oEmbed) ────────────────────────────────────

// Cache so navigating back doesn't re-fetch
const infoCache = {};

async function fetchInfo(video_id) {
  if (!infoCache[video_id]) {
    infoCache[video_id] = pywebview.api.fetch_video_info(video_id);
  }
  const info = await infoCache[video_id];
  // Only update DOM if this video is still the one being shown
  const v = videos[index];
  if (!v || v.video_id !== video_id) return;
  const titleEl  = document.getElementById("meta-title");
  const authorEl = document.getElementById("meta-author");
  if (titleEl)  titleEl.textContent  = info.title;
  if (authorEl) authorEl.textContent = info.author;
}

// ── Status push from Python ───────────────────────────────────────────────────

function updateStatus(message) {
  const v = videos[index];
  if (!v) return;
  decisions[v.video_id] = { status: "working", label: message };
  renderOverlay();
}

function renderOverlay() {
  const el = document.getElementById("status-overlay");
  if (!el) return;
  const v = videos[index];
  const d = decisions[v?.video_id];
  if (!d) { el.style.display = "none"; return; }
  el.style.display = "";
  el.className = "overlay " + d.status;
  el.textContent = d.label;
}

// ── Rendering ─────────────────────────────────────────────────────────────────

function render() {
  const root = document.getElementById("root");

  if (videos.length === 0) {
    root.innerHTML = `
      <div class="screen">
        <div class="icon">🔍</div>
        <h2>No YouTube links found</h2>
        <p>All videos in the vault already have notes, or there are no links.</p>
        <button class="btn-close" onclick="close_()">Close</button>
      </div>`;
    return;
  }

  const createdCount = videos.filter(v => decisions[v.video_id]?.status === "created").length;

  if (index >= videos.length) {
    root.innerHTML = `
      <div class="screen">
        <div class="icon">✅</div>
        <h2>All done</h2>
        <p>${createdCount} note${createdCount !== 1 ? "s" : ""} created · ${videos.length - createdCount} skipped</p>
        <button class="btn-close" onclick="close_()">Close</button>
      </div>`;
    return;
  }

  const v = videos[index];
  const decision = decisions[v.video_id];
  const isDone = decision?.status === "created";
  const isWorking = decision?.status === "working";

  const overlayDisplay = decision ? "" : "display:none";
  const overlayClass = decision ? `overlay ${decision.status}` : "overlay";
  const overlayText = decision?.label ?? "";

  const refsText = v.note_titles.map(t => escHtml(t)).join(" · ");

  root.innerHTML = `
    <div class="topbar">
      <span class="progress">${index + 1} / ${videos.length}</span>
      <span class="note">${escHtml(v.url)}</span>
      <span class="stats">${createdCount} created</span>
    </div>

    <div class="thumb-area">
      <img src="${escHtml(v.thumbnail)}"
        onerror="this.style.display='none'; document.getElementById('thumb-placeholder').style.display='flex'">
      <div id="thumb-placeholder" class="placeholder" style="display:none">
        <div class="icon">▶️</div>
        <div class="msg">Thumbnail unavailable</div>
      </div>
      <div id="status-overlay" class="${overlayClass}" style="${overlayDisplay}">${escHtml(overlayText)}</div>
    </div>

    <div class="meta">
      <div class="title" id="meta-title">Loading…</div>
      <div class="author" id="meta-author"></div>
      <div class="refs">${refsText}</div>
    </div>

    <div class="actions">
      <button class="btn-nav" onclick="go(-1)" ${index === 0 ? "disabled" : ""}>←</button>
      <div class="spacer"></div>
      <button class="btn-copy" id="btn-copy" onclick="copyLink()">Copy link</button>
      <button class="btn-close" onclick="close_()">Close</button>
      <button class="btn-skip" onclick="skip()" ${isWorking ? "disabled" : ""}>
        ${isDone ? "Next →" : "Skip"}
      </button>
      <button class="btn-create" id="btn-create" onclick="create()" ${isDone || isWorking ? "disabled" : ""}>
        ${isDone ? "✓ Created" : "Create"}
      </button>
    </div>`;

  // Fetch title/author asynchronously after rendering the skeleton
  fetchInfo(v.video_id);
}

// ── Actions ───────────────────────────────────────────────────────────────────

function go(delta) {
  index = Math.max(0, Math.min(videos.length - 1, index + delta));
  render();
}

function skip() {
  const v = videos[index];
  if (decisions[v.video_id]?.status !== "created") {
    decisions[v.video_id] = { status: "skipped", label: "Skipped" };
    pywebview.api.save_skip(v.video_id);
  }
  index++;
  render();
}

async function create() {
  const v = videos[index];
  const btn = document.getElementById("btn-create");
  btn.disabled = true;
  btn.textContent = "Working…";
  decisions[v.video_id] = { status: "working", label: "Starting…" };
  renderOverlay();

  const result = await pywebview.api.create_one(v.video_id);

  if (result.ok) {
    decisions[v.video_id] = { status: "created", label: `✓ ${result.note_title}` };
    index++;
  } else {
    decisions[v.video_id] = { status: "error", label: `✗ ${result.error}` };
  }
  render();
}

function copyLink() {
  const v = videos[index];
  if (!v) return;
  navigator.clipboard.writeText(v.url);
  const btn = document.getElementById("btn-copy");
  if (!btn) return;
  btn.textContent = "Copied!";
  btn.classList.add("copied");
  setTimeout(() => { btn.textContent = "Copy link"; btn.classList.remove("copied"); }, 1500);
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
    const v = videos[index];
    const d = decisions[v?.video_id];
    if (v && d?.status !== "created" && d?.status !== "working") create();
  }
  if (e.key === "Escape") close_();
});

function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

window.addEventListener("pywebviewready", init);
</script>
</body>
</html>
"""


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    hf_token = load_hf_token()
    print("Scanning vault for YouTube links…")
    videos = find_youtube_links(VAULT_PATH)
    print(f"Found {len(videos)} unique video(s).")

    api = Api(videos, hf_token)
    window = webview.create_window(
        "Create Video Notes",
        html=HTML,
        js_api=api,
        width=800,
        height=640,
        min_size=(560, 460),
    )
    api.window = window
    webview.start()
    os._exit(0)


if __name__ == "__main__":
    main()
