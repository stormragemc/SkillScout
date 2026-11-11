"""Local media evidence, sampled frames and optional Earshot measurements."""
import hashlib
import json
import shutil

from .config import handle
from .core import ScoutError, clean, digest, now
from .instagram import reel_identity, repo_links
from .security import command


def analyze(store, path, source, creator=None, transcript=None, frames=False, audio=False):
    path = path.expanduser()
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 100_000_000:
        raise ScoutError("Provide a local non-linked media file under 100 MB")
    path = path.resolve()
    if path.suffix.lower() not in {".mp4", ".m4v", ".mov", ".webm", ".mkv", ".avi"}:
        raise ScoutError("Use a supported video container; playlists and manifests are not accepted")
    source = reel_identity(source)
    media_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    mid = digest([source, media_hash])[:24]
    output = store.root / "media" / mid
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    evidence = {"id": mid, "source": source, "creator": handle(creator) if creator else None,
                "media_sha256": media_hash, "at": now(), "transcript": None, "frames": [],
                "audio": None, "limitations": [], "claims_verified": False, "github_candidates": []}
    if transcript:
        if transcript.is_symlink() or not transcript.is_file() or transcript.stat().st_size > 100_000:
            raise ScoutError("Transcript must be a local text file under 100 KB")
        text = transcript.read_text(encoding="utf-8")
        evidence.update(transcript=text, github_candidates=repo_links(text),
                        transcript_origin="User/host supplied; not independently verified")
    if frames:
        binary = shutil.which("ffmpeg")
        if not binary:
            evidence["limitations"].append("ffmpeg unavailable; no frames extracted")
        else:
            rc, _ = command([binary, "-nostdin", "-v", "error", "-threads", "1", "-protocol_whitelist", "file",
                             "-format_whitelist", "mov,matroska,webm,avi",
                             "-i", str(path), "-t", "60", "-vf", "fps=1/5,scale=640:-2", "-frames:v", "12",
                             "-y", str(output / "frame-%02d.jpg")], timeout=60)
            evidence["frames"] = [str(p) for p in sorted(output.glob("frame-*.jpg"))]
            if rc:
                evidence["limitations"].append("Frame extraction failed or was partial")
            evidence["limitations"].append("Sampled frames require actual host image inspection")
    if audio:
        binary = shutil.which("earshot")
        if not binary:
            evidence["limitations"].append("Earshot unavailable; no measurements performed")
        else:
            try:
                rc, raw = command([binary, "measure", str(path), "--json"], timeout=120)
                if rc:
                    raise ScoutError("Earshot failed")
                evidence["audio"] = json.loads(raw)
            except (ScoutError, ValueError):
                evidence["limitations"].append("Earshot failed; audio analysis not established")
    evidence["limitations"].append("No automatic ASR model download or cloud audio upload. Measurements are not transcription.")
    store.save("evidence", mid, evidence)
    return evidence


def draft(store, evidence_id, name, guidance):
    evidence = store.load("evidence", evidence_id)
    result = {"id": digest([evidence_id, name, guidance])[:24], "name": clean(name, 100),
              "guidance": guidance[:16000], "source": evidence["source"], "evidence_id": evidence_id,
              "status": "draft_only", "at": now(), "installable": False,
              "next": "Evaluate the technique, then prepare a separate scanned skill package."}
    store.save("drafts", result["id"], result)
    return result
