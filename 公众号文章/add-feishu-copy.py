"""Add the self-contained Feishu copy toolbar to an exported article HTML."""

import argparse
from html import escape
from pathlib import Path
import re
from urllib.parse import urlparse


START = '<!-- feishu-copy:start -->'
END = '<!-- feishu-copy:end -->'
CSS = """
.feishu-tools{margin:22px 0 28px;padding:18px;border:1px solid #d8d2c4;border-radius:8px;background:#f5f3eb}
.feishu-actions{display:flex;align-items:center;flex-wrap:wrap;gap:12px}
.feishu-tools button,.feishu-manual button{font-family:inherit;font-size:16px;font-weight:600;line-height:1.5;border:1px solid #285e58;border-radius:5px;padding:11px 18px;cursor:pointer}
.feishu-tools button{font-family:inherit;background:#285e58;color:white}
.feishu-tools button:disabled{opacity:.65;cursor:wait}
.feishu-tools a{font-size:15px}.feishu-tools p{font-size:14px;line-height:1.7;margin:10px 0 0;color:#39453c}
.feishu-tools a:focus-visible,.feishu-manual button:focus-visible{outline:3px solid #a63e2d;outline-offset:3px}
.feishu-manual{width:min(900px,95vw);max-height:90dvh;padding:24px;border:1px solid #9aa89f;border-radius:8px;background:#fffefa;color:#17231e}
.feishu-manual::backdrop{background:#17211eaa}.feishu-manual button{font-family:inherit;margin:0 10px 18px 0;background:white;color:#244538}
.feishu-manual-content{max-height:65dvh;overflow:auto;border-top:1px solid #d8d2c4;padding:20px 0}
@media(max-width:700px){.feishu-tools{padding:16px}.feishu-actions{align-items:stretch;flex-direction:column}.feishu-actions a{text-align:center;padding:7px}}
@media print{.feishu-tools,.feishu-manual{display:none!important}}
"""


def update_html(source, url, script):
    parsed = urlparse(url)
    if parsed.scheme != 'https' or not parsed.hostname or not (
        parsed.hostname == 'feishu.cn' or parsed.hostname.endswith('.feishu.cn')
    ) or parsed.username or parsed.password:
        raise ValueError('目标地址必须是 https://…feishu.cn/ 下的飞书文档')
    if source.count(START) != source.count(END) or source.count(START) > 1:
        raise ValueError('HTML 中的复制工具栏标记不完整，未修改文件')
    source = re.sub(re.escape(START) + r'.*?' + re.escape(END), '', source, flags=re.S)
    main = re.search(r'<main\b[^>]*>.*?</h1>', source, re.S)
    if not main:
        raise ValueError('未找到 main 中的文章标题，未修改文件')
    block = (
        START + '<style>' + CSS + '</style>'
        '<aside class="feishu-tools" aria-label="复制文章到飞书">'
        '<div class="feishu-actions"><button type="button">复制到飞书</button>'
        f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">打开飞书文档 ↗</a></div>'
        '<p role="status" aria-live="polite">先复制图文，再打开飞书文档，点击正文位置，按 ⌘V / Ctrl+V 粘贴。</p>'
        '<p>包含正文、配图、12 版 GIF 和作品链接。粘贴后请检查 GIF 是否显示，图片较多需等待上传。</p>'
        '</aside><script>' + script + '</script>' + END
    )
    return source[:main.end()] + block + source[main.end():]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', type=Path, required=True, help='已导出的独立 HTML 文件，原地更新')
    parser.add_argument('--feishu-url', required=True, help='目标飞书文档 HTTPS 链接，仅写入本地 HTML')
    args = parser.parse_args()
    script = Path(__file__).with_name('copy-to-feishu.js').read_text(encoding='utf-8')
    source = args.html.read_text(encoding='utf-8')
    updated = update_html(source, args.feishu_url, script)
    if updated != source:
        args.html.write_text(updated, encoding='utf-8')
    print(f'已更新复制工具栏：{args.html}')


if __name__ == '__main__':
    main()
