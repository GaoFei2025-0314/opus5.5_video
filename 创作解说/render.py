"""Edit the supplied films and PPT captures into a narrated 1080p explainer."""

import argparse
import concurrent.futures
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import signal
from scipy.io import wavfile

FPS, W, H, SR = 30, 1920, 1080, 48000
FONT = "Hiragino Sans GB"
FILES = {
    1: "在我眼里的你.mp4", 2: "在我眼里的你-v2-配音版.mp4",
    3: "在我眼里的你-v3-双声版.mp4", 4: "在我眼里的你-v4-男声版.mp4",
    5: "在我眼里的你-v5-点线面版.mp4", 6: "在我眼里的你-v6-宏伟版.mp4",
    7: "在我眼里的你-v7-字.mp4", 8: "在我眼里的你-v8-冒险.mp4",
    9: "在我眼里的你-v9-见字如面.mp4", 10: "在我眼里的你-v10-江城.mp4",
    11: "在我眼里的你-v11-快闪.mp4", 12: "在我眼里的你-v12-漫画.mp4",
}
NAMES = {1: "文字与配乐", 2: "女声旁白", 3: "双声", 4: "男声旁白", 5: "点线面体",
         6: "宏伟版", 7: "字", 8: "冒险", 9: "见字如面", 10: "江城", 11: "快闪", 12: "漫画"}


def run(args, **kwargs):
    result = subprocess.run([str(arg) for arg in args], capture_output=True, **kwargs)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors="replace")[-5000:])
    return result.stdout


def duration(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]))


def ass_time(seconds):
    centis = max(0, round(seconds * 100))
    return f"{centis // 360000}:{centis // 6000 % 60:02}:{centis // 100 % 60:02}.{centis % 100:02}"


def srt_time(seconds):
    millis = max(0, round(seconds * 1000))
    return f"{millis // 3600000:02}:{millis // 60000 % 60:02}:{millis // 1000 % 60:02},{millis % 1000:03}"


def text_escape(text):
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}").replace("\n", r"\N")


class Ass:
    def __init__(self):
        self.events = []

    def add(self, start, end, text, size=48, x=100, y=100, color="F1EEE7", bold=False,
            align=7, layer=1, animate=True, shadow=0, raw=False):
        # libass colors use BGR. All motion has explicit timeline-relative timing.
        bgr = color[4:6] + color[2:4] + color[0:2]
        tags = f"\\an{align}\\fn{FONT}\\fs{size}\\b{int(bold)}\\1c&H{bgr}&\\bord{2 if shadow else 0}\\shad{shadow}"
        if animate:
            tags += f"\\move({x},{y + 18},{x},{y},0,360)\\fad(180,180)"
        else:
            tags += f"\\pos({x},{y})"
        self.events.append(f"Dialogue: {layer},{ass_time(start)},{ass_time(end)},Default,,0,0,0,,{{{tags}}}{text if raw else text_escape(text)}")

    def caption(self, start, end, text):
        tags = f"\\an2\\fn{FONT}\\fs46\\b0\\1c&HF7F5F0&\\3c&H090B0A&\\bord2\\shad1\\pos(960,1020)\\fad(55,80)"
        self.events.append(f"Dialogue: 8,{ass_time(start)},{ass_time(end)},Default,,0,0,0,,{{{tags}}}{text_escape(text)}")

    def write(self, path):
        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{FONT},46,&H00F1EEE7,&H00F1EEE7,&H00090B0A,&H00090B0A,0,0,0,0,100,100,0,0,1,0,0,7,90,90,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        path.write_text(header + "\n".join(self.events) + "\n")


def captions(scene, voice_dir):
    if not scene["text"]:
        return []
    metadata = [json.loads(line) for line in (voice_dir / f"{scene['id']}.jsonl").read_text().splitlines()]
    char_times = []
    for word in metadata:
        if word["type"] != "WordBoundary":
            continue
        letters = re.sub(r"[\s，。！？：；、]", "", word["text"])
        if not letters:
            continue
        a, d = word["offset"] / 1e7, word["duration"] / 1e7
        char_times.extend((a + i * d / len(letters), a + (i + 1) * d / len(letters)) for i in range(len(letters)))
    clean = re.sub(r"[\s，。！？：；、]", "", scene["text"])
    if len(clean) != len(char_times):
        raise ValueError(f"Timing character mismatch in {scene['id']}: {len(clean)} != {len(char_times)}")
    groups = []
    for phrase in re.split(r"[，。！？：；]", scene["text"]):
        phrase = phrase.strip()
        if phrase:
            groups.extend(phrase[i:i + 22] for i in range(0, len(phrase), 22))
    result, cursor = [], 0
    for group in groups:
        count = len(re.sub(r"[\s、]", "", group))
        start = char_times[cursor][0] + scene["lead"]
        end = char_times[cursor + count - 1][1] + scene["lead"] + 0.12
        group = group.replace("奥普斯五点五", "Opus 5.5").replace("克劳德代码工具", "Claude Code")
        result.append([start, min(end, scene["duration"] - 0.05), group])
        cursor += count
    return result


def graphics(scene, ass):
    d = scene["duration"]
    kind = scene.get("graphic")
    if kind == "title":
        ass.add(0, d, "OPUS 5.5 / VIDEO EXPERIMENT", 28, 110, 180, "EC503C")
        ass.add(0.25, d, "一句话，", 132, 100, 290, bold=True)
        ass.add(0.6, d, "十二种「我」。", 132, 100, 455, "EC503C", True)
        ass.add(1.0, d, "高飞的 AI 视频创作实录", 38, 110, 685)
    elif kind == "freedom":
        ass.add(0, d, "时长、画面、声音、配乐、音效", 70, 115, 165, bold=True)
        ass.add(0.65, d, "都由你决定", 120, 110, 290, "EC503C", True)
        ass.add(3.8, d, "技术完全自由", 94, 110, 500, bold=True)
        ass.add(4.4, d, "Shader / Canvas / Three.js / CSS 手绘 / Remotion", 37, 115, 640, "A8AEA4")
        ass.add(6.2, d, "需要什么库自己装。", 65, 115, 750, bold=True)
    elif kind == "styles":
        ass.add(0, d, "风格，是一套贯穿全片的规则", 68, 90, 70, bold=True)
        for index, label in enumerate(["字", "像素冒险", "手账书信", "水墨江城", "快闪", "黑白漫画"]):
            x = 90 + index % 3 * 590
            y = 450 + index // 3 * 390
            ass.add(index * 0.12, d, label, 32, x, y, bold=True)
    elif kind == "feedback":
        ass.add(0, d, "让反馈，变成下一步动作", 76, 110, 160, bold=True)
        rows = [("“冲击不够”", "先改 15 秒，检查节奏与音乐"),
                ("“画面看不清”", "减少元素，让观众一眼看懂"),
                ("“配音读错”", "逐句转写，只重做没通过的句子")]
        for index, (quote, action) in enumerate(rows):
            y, start = 350 + index * 170, index * d / 4
            ass.add(start, d, quote, 48, 110, y, "EC503C", True)
            ass.add(start + 0.25, d, "→  " + action, 44, 640, y + 4)
    elif kind == "method":
        ass.add(0, d, "把这套方法，带回去", 38, 115, 130, "A8AEA4")
        for index, label in enumerate(["真实素材", "创作自由", "明确反馈"]):
            ass.add(index * 1.2 + 0.3, d, label, 115, 110, 240 + index * 190,
                    "EC503C" if index == 1 else "F1EEE7", True)
        ass.add(5, d, "你负责判断\n「像不像你」", 63, 1130, 490, "F1EEE7", True)
    elif kind == "endcard":
        ass.add(0, d, "把想法做出来", 132, 960, 400, "EC503C", True, align=5)
        ass.add(0.35, d, "高飞 / Opus 5.5 视频创作实录", 36, 960, 590, align=5)
        ass.add(0.5, d, "原片与资料：高飞  ·  旁白：AI 合成", 27, 960, 760, "A8AEA4", align=5)
    elif not scene.get("ppt"):
        ass.add(0.15, min(d, 3.6), scene["headline"], 53, 90, 125, bold=True, shadow=2)
    # A restrained, consistent chapter line survives every visual style.
    ass.add(0, d, scene["chapter"], 26, 88, 42, "C6C8C0", animate=False)
    ass.add(0, d, "高飞 / OPUS 5.5", 24, 1835, 42, "C6C8C0", align=9, animate=False)


def make_styles_grid(root, output):
    canvas = Image.new("RGB", (W, H), "#101411")
    for index, version in enumerate([7, 8, 9, 10, 11, 12]):
        image = Image.open(root / "分享演示" / "assets" / f"v{version}.jpg").convert("RGB")
        image = image.resize((550, 309), Image.Resampling.LANCZOS)
        canvas.paste(image, (90 + index % 3 * 590, 165 + index // 3 * 390))
    canvas.save(output)


def prepare(script, args):
    elapsed, timeline = 0.0, []
    for source in script["scenes"]:
        scene = dict(source)
        scene["lead"] = 0.24 if scene["text"] else 0
        scene["speechDuration"] = duration(args.root / "voice" / f"{scene['id']}.mp3") if scene["text"] else 0
        frames = round(scene.get("duration", scene["speechDuration"] + scene["lead"] + 0.26 + scene.get("extra", 0)) * FPS)
        scene.update(frames=frames, duration=frames / FPS, start=elapsed)
        elapsed += scene["duration"]
        if scene.get("graphic") == "title":
            scene["shots"] = [[11, 39]]
        scene["captions"] = captions(scene, args.root / "voice")
        if scene["id"] == "hook":
            scene["shotStarts"] = [0] + [next(a for a, _, text in scene["captions"] if text.startswith(phrase))
                                          for phrase in ["水墨长卷", "黑白漫画", "还有冲进屏幕"]]
        ass = Ass()
        graphics(scene, ass)
        if scene["id"] in ["voices", "visual"]:
            count = len(scene["shots"])
            for i, (version, _) in enumerate(scene["shots"]):
                ass.add(i * scene["duration"] / count, (i + 1) * scene["duration"] / count,
                        f"V{version} / {NAMES[version]}", 28, 1825, 100, align=9, shadow=2)
        for start, end, text in scene["captions"]:
            ass.caption(start, end, text)
        ass.write(args.build / "shots" / f"{scene['id']}.ass")
        timeline.append(scene)
    (args.build / "timeline.json").write_text(json.dumps({"duration": elapsed, "scenes": timeline}, ensure_ascii=False, indent=2))
    srt, cue = [], 1
    for scene in timeline:
        for a, b, text in scene["captions"]:
            srt.append(f"{cue}\n{srt_time(a + scene['start'])} --> {srt_time(b + scene['start'])}\n{text}\n")
            cue += 1
    (args.build / "captions.srt").write_text("\n".join(srt))
    return timeline


def render_scene(scene, args):
    output = args.build / "shots" / f"{scene['id']}.mp4"
    ass = args.build / "shots" / f"{scene['id']}.ass"
    fingerprint = hashlib.sha256((json.dumps(scene, sort_keys=True) + ass.read_text() + Path(__file__).read_text()).encode()).hexdigest()
    cache = output.with_suffix(".sha256")
    if output.exists() and cache.exists() and cache.read_text() == fingerprint:
        print(f"cached picture {scene['id']}", flush=True)
        return
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    filters = []
    if scene.get("shots"):
        n = len(scene["shots"])
        left = scene["frames"]
        for i, (version, start) in enumerate(scene["shots"]):
            if scene.get("shotStarts") and i < n - 1:
                frames = round(scene["shotStarts"][i + 1] * FPS) - round(scene["shotStarts"][i] * FPS)
            else:
                frames = left if i == n - 1 else scene["frames"] // n
            left -= frames
            source = args.media / FILES[version]
            command += ["-ss", str(start), "-t", str(frames / FPS + 0.2), "-i", str(source)]
            sizing = f"scale=1680:945:flags=lanczos,pad={W}:{H}:120:0:color=0x101411" if version in [8, 9, 10, 12] else f"scale={W}:{H}:flags=lanczos"
            filters.append(f"[{i}:v]trim=duration={frames / FPS},setpts=PTS-STARTPTS,fps={FPS},{sizing},setsar=1,format=yuv420p[v{i}]")
        filters.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[base]")
    elif scene.get("ppt") and scene.get("graphic") != "feedback":
        image = args.build / "assets" / f"ppt{scene['ppt']}.png"
        command += ["-loop", "1", "-framerate", str(FPS), "-i", str(image)]
        filters.append(f"[0:v]scale={W}:{H},setsar=1,format=yuv420p[base]")
    elif scene.get("graphic") == "styles":
        command += ["-loop", "1", "-framerate", str(FPS), "-i", str(args.build / "assets" / "styles.png")]
        filters.append("[0:v]setsar=1,format=yuv420p[base]")
    else:
        command += ["-f", "lavfi", "-i", f"color=c=0x101411:s={W}x{H}:r={FPS}:d={scene['duration']}"]
        filters.append("[0:v]setsar=1,format=yuv420p[base]")
    if scene.get("graphic") == "title":
        filters.append("[base]eq=brightness=-0.25:saturation=0.45,drawbox=x=0:y=0:w=1920:h=1080:color=black@0.3:t=fill[dim]")
        current = "dim"
    else:
        current = "base"
    # Clear top/bottom bands protect captions from text already present in source films.
    filters.append(f"[{current}]drawbox=x=0:y=0:w=1920:h=91:color=black@0.82:t=fill,drawbox=x=0:y=936:w=1920:h=144:color=black@0.91:t=fill,ass=filename='{ass.as_posix()}'[video]")
    command += ["-filter_complex", ";".join(filters), "-map", "[video]", "-an", "-frames:v", str(scene["frames"]),
                "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
                "-threads", "4", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", str(output)]
    run(command)
    cache.write_text(fingerprint)
    print(f"picture {scene['id']} · {scene['duration']:.1f}s", flush=True)


def read_audio(path, start=None, seconds=None):
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error"]
    if start is not None:
        command += ["-ss", str(start)]
    command += ["-i", str(path)]
    if seconds is not None:
        command += ["-t", str(seconds)]
    command += ["-f", "f32le", "-ac", "2", "-ar", str(SR), "-"]
    return np.frombuffer(run(command), np.float32).reshape(-1, 2).copy()


def mix_audio(timeline, args):
    total = sum(scene["duration"] for scene in timeline)
    length = round(total * SR)
    voice = np.zeros((length, 2), np.float32)
    original = np.zeros_like(voice)
    music = np.zeros_like(voice)
    rng = np.random.default_rng(20261029)

    def put(track, seconds, sound, gain=1):
        start = max(0, round(seconds * SR))
        count = min(len(sound), length - start)
        if sound.ndim == 1:
            sound = np.column_stack([sound, sound])
        if count > 0:
            track[start:start + count] += sound[:count] * gain

    # An original restrained score: warm plucks, low pulse and light percussion.
    beat = 60 / 108
    chords = [[50, 53, 57], [46, 50, 53], [53, 57, 60], [48, 52, 55]]
    for tick in range(math.ceil(total / (beat / 2))):
        at = tick * beat / 2
        chord = chords[(tick // 16) % 4]
        midi = chord[tick % 3] + 12
        t = np.arange(round(1.5 * SR)) / SR
        frequency = 440 * 2 ** ((midi - 69) / 12)
        envelope = (1 - np.exp(-t * 60)) * np.exp(-t * 3.8)
        pluck = (np.sin(2 * np.pi * frequency * t) + 0.23 * np.sin(4 * np.pi * frequency * t)) * envelope
        put(music, at, pluck, 0.032)
        if tick % 4 == 0:
            t = np.arange(round(0.32 * SR)) / SR
            kick = np.sin(2 * np.pi * (46 * t + 42 * (1 - np.exp(-t * 35)) / 35)) * np.exp(-t * 17)
            put(music, at, kick, 0.055)
        if tick % 2:
            noise = rng.normal(0, 1, round(0.06 * SR))
            noise = np.concatenate([[0], np.diff(noise)]) * np.exp(-np.arange(len(noise)) / (0.012 * SR))
            put(music, at, noise, 0.007)
    for scene in timeline:
        start = scene["start"]
        if scene["text"]:
            sound = read_audio(args.root / "voice" / f"{scene['id']}.mp3")
            rms = math.sqrt(float(np.mean(sound ** 2)))
            sound *= min(3.0, 0.115 / max(rms, 1e-6))
            sound = np.clip(sound, -0.82, 0.82)
            put(voice, start + scene["lead"], sound)
        if scene.get("originalAudio") or scene.get("musicSource"):
            version, source_start = scene.get("musicSource", scene["shots"][0])
            sound = read_audio(args.media / FILES[version], source_start, scene["duration"])
            times = np.arange(len(sound)) / SR
            speech_end = scene["speechDuration"] + scene["lead"]
            gain = np.interp(times, [0, 0.2, speech_end, speech_end + 0.4, scene["duration"] - 0.2, scene["duration"]], [0, 0.16, 0.16, 0.65, 0.65, 0])
            put(original, start, sound * gain[:, None])
            a, b = round(start * SR), round((start + scene["duration"]) * SR)
            music[a:b] *= 0.08
        if scene["id"] in ["title", "freedom", "rules", "feedback", "method", "endcard"]:
            t = np.arange(round(0.42 * SR)) / SR
            air = rng.normal(0, 1, len(t))
            air = signal.lfilter(*signal.butter(2, 0.13), air)
            envelope = np.sin(np.pi * t / max(t[-1], 1e-6)) ** 2
            put(music, start, air * envelope, 0.045)
    energy = np.abs(voice).mean(axis=1)
    activity = signal.lfilter([1 / 1200] * 1200, [1], energy)
    duck = 1 - np.clip(activity * 12, 0, 0.58)
    music *= duck[:, None]
    fade = np.ones(length)
    fade[:SR] = np.linspace(0, 1, SR)
    fade[-2 * SR:] = np.linspace(1, 0, 2 * SR)
    mixed = voice + (music + original) * fade[:, None]
    peak = float(np.abs(mixed).max())
    if peak > 0.96:
        mixed *= 0.96 / peak
    wavfile.write(args.build / "mix.wav", SR, mixed.astype(np.float32))
    wavfile.write(args.build / "narration.wav", SR, voice.astype(np.float32))
    print(f"audio mix · {total:.2f}s · raw peak {peak:.3f}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--media", type=Path, required=True, help="Directory containing the twelve original MP4 films")
    parser.add_argument("--build", type=Path, required=True, help="Task-local build directory; assets/pptN.png must be present")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--only", help="Render selected scene pictures only, comma separated")
    parser.add_argument("--remix-only", action="store_true", help="Reuse pictures after audio-only edits; scene lengths must still match")
    parser.add_argument("--jobs", type=int, default=3)
    args = parser.parse_args()
    args.root = Path(__file__).resolve().parent
    args.media, args.build, args.output = args.media.resolve(), args.build.resolve(), args.output.resolve()
    (args.build / "shots").mkdir(parents=True, exist_ok=True)
    script = json.loads((args.root / "script.json").read_text())
    make_styles_grid(args.root.parent, args.build / "assets" / "styles.png")
    timeline = prepare(script, args)
    selected = [scene for scene in timeline if not args.only or scene["id"] in args.only.split(",")]
    print(f"Timeline: {sum(s['duration'] for s in timeline):.2f}s, {len(timeline)} scenes", flush=True)
    if args.remix_only:
        for scene in timeline:
            picture = args.build / "shots" / f"{scene['id']}.mp4"
            if not picture.exists() or abs(duration(picture) - scene["duration"]) > 1 / FPS:
                raise ValueError(f"Picture duration changed for {scene['id']}; render pictures again")
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            list(pool.map(lambda scene: render_scene(scene, args), selected))
    if args.only:
        return
    mix_audio(timeline, args)
    listing = args.build / "concat.txt"
    listing.write_text("\n".join(f"file '{(args.build / 'shots' / (s['id'] + '.mp4')).as_posix()}'" for s in timeline))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", listing,
         "-i", args.build / "mix.wav", "-map", "0:v", "-map", "1:a",
         "-vf", "scale=1920:1080:in_range=auto:out_range=tv,setparams=range=limited",
         "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-color_range", "tv",
         "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-c:a", "aac", "-b:a", "256k",
         "-af", "loudnorm=I=-16:TP=-2.2:LRA=9", "-ar", "48000", "-movflags", "+faststart", "-shortest", args.output])
    print(f"FINAL {args.output}", flush=True)


if __name__ == "__main__":
    main()
