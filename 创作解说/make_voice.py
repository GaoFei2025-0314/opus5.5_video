"""Create and cache scene narration with word timing for the explainer film."""

import argparse
import asyncio
import hashlib
import json
import sys
from pathlib import Path


async def generate(args):
    if args.libs:
        sys.path.insert(0, str(args.libs.resolve()))
    import edge_tts

    script = json.loads(args.script.read_text())
    args.out.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(2)

    async def synthesize(scene):
        if not scene["text"]:
            return
        config = {"text": scene["text"], "voice": script["voice"], "rate": "+3%", "pitch": "-2Hz"}
        fingerprint = hashlib.sha256(json.dumps(config, ensure_ascii=False).encode()).hexdigest()
        mp3 = args.out / f"{scene['id']}.mp3"
        timing = args.out / f"{scene['id']}.jsonl"
        manifest = args.out / f"{scene['id']}.json"
        if manifest.exists() and mp3.exists() and timing.exists():
            if json.loads(manifest.read_text()).get("fingerprint") == fingerprint:
                print(f"cached {scene['id']}", flush=True)
                return
        async with semaphore:
            for attempt in range(3):
                try:
                    communicator = edge_tts.Communicate(**config, boundary="WordBoundary")
                    await communicator.save(str(mp3), str(timing))
                    if mp3.stat().st_size < 1000:
                        raise RuntimeError("No usable speech audio returned")
                    manifest.write_text(json.dumps({**config, "fingerprint": fingerprint,
                                                   "provider": "Microsoft Edge online TTS",
                                                   "disclosure": "AI-generated narration"},
                                                  ensure_ascii=False, indent=2))
                    print(f"ready {scene['id']}", flush=True)
                    return
                except Exception:
                    if attempt == 2:
                        raise
                    await asyncio.sleep(1 + attempt)

    await asyncio.gather(*(synthesize(scene) for scene in script["scenes"]))


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", type=Path, default=root / "script.json")
    parser.add_argument("--out", type=Path, default=root / "voice")
    parser.add_argument("--libs", type=Path, help="Optional task-local edge-tts install directory")
    asyncio.run(generate(parser.parse_args()))
