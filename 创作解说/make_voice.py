"""Synthesize the owner's existing gaofei voice with character timing; keep audio local."""

import argparse
import base64
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path


def synthesize(args):
    script = json.loads(args.script.read_text())
    voice = script["voice"]
    key = os.environ.get("ELEVENLABS_API_KEY")
    args.out.mkdir(parents=True, exist_ok=True)
    for scene in script["scenes"]:
        if not scene["text"] or (args.only and scene["id"] not in args.only.split(",")):
            continue
        config = {"text": scene["text"], "model_id": voice["model"], "language_code": "zh",
                  "seed": 930, "voice_settings": voice["settings"]}
        fingerprint = hashlib.sha256(json.dumps([voice["id"], config], ensure_ascii=False).encode()).hexdigest()
        mp3 = args.out / f"{scene['id']}.mp3"
        manifest = mp3.with_suffix(".json")
        if mp3.exists() and manifest.exists() and not args.force:
            if json.loads(manifest.read_text()).get("fingerprint") == fingerprint:
                print(f"cached {scene['id']}", flush=True)
                continue
        if not key:
            raise RuntimeError("Set ELEVENLABS_API_KEY in the runtime environment; no key is stored in the project")
        request = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice['id']}/with-timestamps?output_format=mp3_44100_128",
            data=json.dumps(config, ensure_ascii=False).encode(),
            headers={"xi-api-key": key, "Content-Type": "application/json"})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    result = json.load(response)
                break
            except urllib.error.HTTPError as error:
                if (error.code == 429 or error.code >= 500) and attempt < 2:
                    time.sleep(2 * (attempt + 1))
                    continue
                raise RuntimeError(f"Speech synthesis for {scene['id']} failed: HTTP {error.code}") from None
        audio = base64.b64decode(result["audio_base64"], validate=True)
        alignment = result["alignment"]
        if len(audio) < 1000 or "".join(alignment["characters"]) != scene["text"]:
            raise ValueError(f"Invalid audio or character alignment for {scene['id']}")
        mp3.write_bytes(audio)
        manifest.write_text(json.dumps({"fingerprint": fingerprint, "voice": voice["name"],
            "provider": voice["provider"], "model": voice["model"], "text": scene["text"],
            "alignment": alignment, "disclosure": "Owner-authorized AI voice synthesis"},
            ensure_ascii=False, indent=2) + "\n")
        print(f"ready {scene['id']}", flush=True)


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", type=Path, default=root / "script.json")
    parser.add_argument("--out", type=Path, default=root.parent / "build/intro-film/voice")
    parser.add_argument("--only", help="Comma-separated scene IDs for a short voice preview")
    parser.add_argument("--force", action="store_true", help="Regenerate selected scenes after a failed speech audit")
    synthesize(parser.parse_args())
