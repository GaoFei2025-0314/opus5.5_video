"""Package this local deck, including its video clips, as one offline HTML file."""

import argparse
import base64
import mimetypes
import re
from pathlib import Path


def build(output: Path) -> None:
    root = Path(__file__).resolve().parent
    html = (root / "index.html").read_text(encoding="utf-8")
    data = (root / "data.js").read_text(encoding="utf-8")
    css = (root / "styles.css").read_text(encoding="utf-8")
    app = (root / "app.js").read_text(encoding="utf-8")
    for asset in sorted((root / "assets").iterdir()):
        if not asset.is_file():
            continue
        mime = mimetypes.guess_type(asset.name)[0] or "application/octet-stream"
        encoded = base64.b64encode(asset.read_bytes()).decode("ascii")
        uri = f"data:{mime};base64,{encoded}"
        relative = f"assets/{asset.name}"
        html = html.replace(f'src="{relative}"', f'src="{uri}"')
        html = html.replace(f'poster="{relative}"', f'poster="{uri}"')
        data = data.replace(f'"{relative}"', f'"{uri}"')
    html = html.replace('<link rel="stylesheet" href="styles.css">', f"<style>{css}</style>")
    safe_data = re.sub(r"</script", r"<\\/script", data, flags=re.IGNORECASE)
    safe_app = re.sub(r"</script", r"<\\/script", app, flags=re.IGNORECASE)
    html = html.replace('<script src="data.js" defer></script>', f"<script>{safe_data}</script>")
    html = html.replace('<script src="app.js" defer></script>', "")
    html = html.replace("</body>", f"<script>{safe_app}</script>\n</body>")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    print(f"Created {output.resolve()} ({output.stat().st_size / 1024 / 1024:.1f} MiB)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Destination HTML file")
    args = parser.parse_args()
    build(args.output)
