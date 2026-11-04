# 一句话，十二种我 · 高飞自述

基于高飞《用 Opus 5.5 做视频》互动 PPT 和十二支原片制作的第一人称视频。1920×1080，30 fps，H.264 + AAC，烧录中文字幕。

叙述从“我是高飞”和“这些画面讲的，都是我”展开，介绍我怎样提供资料、给 AI 创作自由、确认样片、尝试风格、提出反馈。画面主标题、方法卡和落款统一为第一人称。原片节选保留作品原文，并加“我的原片节选”标记，避免把 AI 对我说的话当成解说者的视角。

全片解说调用项目中已有的 ElevenLabs `gaofei` 克隆音色（`eleven_v3`），沿用原工程速度 1.2 与稳定度 0.5。用户已要求使用其本人音色；无需新建克隆、上传录音或修改账号。片头和片尾均披露“本人音色 AI 合成”，不称为本人现场录音。原片音轨全部静音，使用本工程单独合成的配乐与转场声，不混入女声或旧纪录片男声。

## 文件与本地保留

- `script.json`：21 段第一人称文案、画面标题、原片编号和截取位置，含用户已配置的音色 ID（不是密钥）。
- `导演稿.md`：与脚本一致的可读旁白稿。
- `make_voice.py`：按文字、音色和参数缓存配音，生成音频与服务返回的逐字时间戳。
- `render.py`：按实际音频重新计算镜头时长、字幕、动态标题及混音，输出成片。
- `capture_ppt.cjs`：用独立的无头浏览器截取 PPT 第 4、6、10 页，完成后关闭自身浏览器。
- `requirements.txt`：本地视频制作所需 Python 库；配音请求只使用 Python 标准库。
- `验收记录.md`：当前版本的成片和验证证据。
- `voice/`：上一版本已入库的通用男声缓存，保留既有路径；本次不使用，也不向此目录写入本人音色。

新的个人音色结果保存在被忽略的 `<build>/voice/`，每段一份 MP3 和一份包含文字、逐字时间及缓存指纹的 JSON。本地保留，避免二次调用费用；不提交到 Git。原始影片和人工素材仍位于用户原工作区，保持原路径，不批量移动或删除。`build/` 中还保留 ASS、混音、字幕、审查和画面缓存；`out/` 保留可直接使用的成片。

## 重新制作

使用现有 Python 环境（NumPy、SciPy、Pillow），以及 FFmpeg/FFprobe。中文字体默认为 macOS Hiragino Sans GB。给配音进程配置 `ELEVENLABS_API_KEY` 环境变量；脚本不读取密钥文件、不输出密钥。命中音频缓存后不调用配音服务。

```sh
python3 创作解说/make_voice.py --out /path/to/build/intro-film/voice

# 首次没有 PPT 截图时运行。需要 Playwright 与已有的 Chrome。
node 创作解说/capture_ppt.cjs /path/to/build/intro-film/assets

python3 创作解说/render.py \
  --media /path/to/original/out \
  --build /path/to/build/intro-film \
  --voice /path/to/build/intro-film/voice \
  --output /path/to/out/一句话十二种我-第一人称本人音色.mp4
```

`make_voice.py --only hook,title` 可先生成短样片；`--force --only <id>` 只重做审查未通过的段落。渲染的 `--only title,freedom` 只输出指定片段；`--remix-only` 在时长未变时复用画面。字幕直接使用服务返回的逐字时间。渲染会拒绝文案不匹配或音色不是 gaofei 的缓存。

配音接口依据：[ElevenLabs 带时间戳合成文档](https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps)。语义检查使用项目既有的 Scribe 工作流，自动转写不等同于本人对音色相似度的认可。

输出统一为 BT.709 limited range；混音目标约 -16 LUFS，编码前预留 -2.2 dBTP 余量。成片后再完整解码并测量实际 AAC 真峰值。
