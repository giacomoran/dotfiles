#!/usr/bin/env python3
"""Download an X (Twitter) video, transcribe it, and write an Obsidian note.

Usage:
    python create_x_video_note.py <x_url> <title>

Example:
    python create_x_video_note.py https://x.com/Ultraroboticsco/status/123 "Ultra - 2026, Introducing Operator (OP1)"

The note is written to "📘 Sources - Videos/<title>.md" in the vault.
"""

import argparse
import getpass
import json
import re
import subprocess
import tempfile
import warnings
from pathlib import Path

# torchcodec ships broken dylibs on macOS; suppress its warning — whisperx never
# uses it (it loads audio via soundfile/librosa directly).
warnings.filterwarnings("ignore", module=r"pyannote\.audio\.core\.io")

import mlx_whisper
import torch
import whisperx
from whisperx.diarize import DiarizationPipeline

VAULT_PATH = Path(__file__).parent.parent
VIDEOS_PATH = VAULT_PATH / "📘 Sources - Videos"
HF_TOKEN_PATH = Path(__file__).parent / ".hf_token"

WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"
_TORCH_DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"

_diarize_model = None


def load_hf_token() -> str:
    """Load HuggingFace token from disk, prompting once if not yet stored."""
    if HF_TOKEN_PATH.exists():
        return HF_TOKEN_PATH.read_text(encoding="utf-8").strip()
    token = getpass.getpass("HuggingFace token (for pyannote diarization): ").strip()
    assert token, "HuggingFace token is required"
    HF_TOKEN_PATH.write_text(token, encoding="utf-8")
    return token


def get_diarize_model(hf_token: str):
    global _diarize_model
    if _diarize_model is None:
        _diarize_model = DiarizationPipeline(token=hf_token, device=_TORCH_DEVICE)
    return _diarize_model


def sanitize_filename(name: str) -> str:
    sanitized = re.sub(r'[/\\:*?"<>|]', "-", name)
    return sanitized.strip(" .")


def _run_ytdlp(args: list[str]) -> subprocess.CompletedProcess:
    result = subprocess.run(
        ["yt-dlp"] + args,
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        error_line = next(
            (l.removeprefix("ERROR: ") for l in result.stderr.splitlines() if l.startswith("ERROR:")),
            result.stderr.strip(),
        )
        print(result.stderr.strip())
        raise RuntimeError(error_line)
    return result


def download_audio(url: str, dest_dir: Path) -> Path:
    _run_ytdlp(["--no-playlist", "-f", "bestaudio",
                "--extract-audio", "--audio-format", "wav",
                "-o", str(dest_dir / "audio.%(ext)s"), url])
    return dest_dir / "audio.wav"


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
    result = mlx_whisper.transcribe(
        str(audio_path), path_or_hf_repo=WHISPER_MODEL,
        hallucination_silence_threshold=2.0,
    )

    audio = whisperx.load_audio(str(audio_path))

    result["segments"] = [s for s in result["segments"] if s.get("text", "").strip()]

    align_model, metadata = whisperx.load_align_model(
        language_code=result["language"], device=_TORCH_DEVICE,
    )
    result = whisperx.align(
        result["segments"], align_model, metadata, audio,
        device=_TORCH_DEVICE, return_char_alignments=False,
    )

    diarize = get_diarize_model(hf_token)
    diarize_segments = diarize(audio)
    result = whisperx.assign_word_speakers(diarize_segments, result)

    return format_transcript(result["segments"])


def write_note(url: str, title: str, transcript: str) -> Path:
    VIDEOS_PATH.mkdir(parents=True, exist_ok=True)
    filename = sanitize_filename(title) + ".md"
    note_path = VIDEOS_PATH / filename
    content = (
        f"**Source:** {url}\n\n"
        f"## Transcript\n\n"
        f"{transcript}\n"
    )
    note_path.write_text(content, encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an Obsidian note for an X (Twitter) video.")
    parser.add_argument("url", help="X post URL containing a video")
    parser.add_argument("title", help="Note title (used as the filename)")
    args = parser.parse_args()

    hf_token = load_hf_token()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        print("Downloading audio…")
        audio_path = download_audio(args.url, tmp_path)
        print("Transcribing…")
        transcript = transcribe_audio(audio_path, hf_token)

    print("Writing note…")
    note_path = write_note(args.url, args.title, transcript)
    print(f"Created: {note_path.relative_to(VAULT_PATH)}")


if __name__ == "__main__":
    main()
