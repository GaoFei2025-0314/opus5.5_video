# 一句话，十二种我

基于高飞《用 Opus 5.5 做视频》互动 PPT 和 12 支原片制作的中文创作解说。

成片约 3 分 19 秒，1920×1080，30 fps，H.264 + AAC，含烧录字幕。旁白采用自然中文男声，明确标注为 AI 合成。片头借用快闪原曲建立节奏，保留了水墨、漫画和快闪片段的原音乐与音效，其余段落使用单独合成的配乐。

剪辑围绕一个问题展开：同一句话为什么能做出十二种不同表达。先展示作品，再讲真实素材、创作自由、样片、声音与画面的逐轮迭代、反馈和可复用的方法。核心提示词在画面完整展示，技术名称保留正式拼写。

## 文件

- `导演稿.md`：中文旁白与创作意图。
- `script.json`：21 个段落的旁白、标题、原片编号和截取位置。
- `voice/`：20 段已生成的配音、词级时间标记与缓存信息，便于离线重剪。
- `make_voice.py`：仅在文字或音色改动后重新生成对应旁白；当前为 `zh-CN-YunxiNeural`。
- `capture_ppt.cjs`：截取原演示第 4、6、10 页的画布。
- `render.py`：按实际配音长度建立时间轴，剪辑原片、加入动态文字与字幕，混音并输出 MP4。

最终视频与字幕输出到用户工程的 `out/`，原片与视频中间文件不重复提交到仓库。原项目的代码、原片与演示稿均保持原样。

## 重新制作

需要 Python 3（NumPy、SciPy、Pillow），FFmpeg/FFprobe，以及可用的中文字体。当前导出使用 macOS 的 Hiragino Sans GB，换系统时可修改 `render.py` 的 `FONT`。首次生成配音需要网络和 `edge-tts`；使用本目录缓存配音渲染时不需要配音服务。PPT 截图使用 Playwright，可使用已有 Chrome。

从仓库根目录运行，按实际位置填写原片目录和构建目录：

```sh
# 在任务的独立 Python 环境中安装 requirements.txt，或使用已有可用环境。
python3 创作解说/make_voice.py

# Playwright 未安装到 Node 的正常搜索路径时，设置 PLAYWRIGHT_MODULE 指向已有包。
# 使用已有 Chrome 时，可设置 CHROME_PATH 指向其可执行文件。
node 创作解说/capture_ppt.cjs /path/to/build/intro-film/assets

python3 创作解说/render.py \
  --media /path/to/original/out \
  --build /path/to/build/intro-film \
  --output /path/to/out/一句话十二种我-Opus5.5创作解说.mp4
```

构建目录包含 `timeline.json`、`captions.srt`、逐段的 ASS 动态文字、画面片段、旁白声轨与混音。`--only title,freedom,comic` 可先出指定片段检查画面，`--jobs` 控制同时编码的段数。

旁白通过服务返回的词级时间建立字幕，而非按字数平均分配。音量检查目标为约 -16 LUFS，真峰值不高于 -1.5 dBTP；编码前保留 -2.2 dBTP 的余量，避免 AAC 编码产生的峰值过冲。最后统一编码为 BT.709、limited range，避免原片和 PPT 截图的色彩范围不同导致播放器反复切换。

## 内容依据与边界

所有作品片段、截图、头像和创作过程均来自用户提供的工程及 PPT。叙述为项目复盘，没有加入制作耗时、收益、模型性能或“一句话必然生成成片”等未经核实的承诺。使用 AI 旁白介绍高飞的创作，不将合成声音标为本人录音。

旁白使用可用的中文神经网络男声。已将本片的配音结果与时间标记缓存到 voice/，无需配音账户密钥即可离线重剪。
