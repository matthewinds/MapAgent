from __future__ import annotations

import concurrent.futures
import html
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PDF = Path(
    "/Users/matthew/Library/Containers/com.tencent.xinWeChat/Data/Documents/"
    "xwechat_files/wxid_6wbf1gf3wl5g22_7462/temp/drag/2026.findings-eacl.67.pdf"
)
WORK_DIR = ROOT / "tmp" / "pdfs"
CACHE_DIR = WORK_DIR / "mapagent_zh_pages"
IMAGE_DIR = WORK_DIR / "mapagent_source_pages"
OUTPUT_DIR = ROOT / "output" / "pdf"
OUTPUT_PDF = OUTPUT_DIR / "MapAgent_中文对照翻译版.pdf"
OUTPUT_MD = OUTPUT_DIR / "MapAgent_中文翻译.md"
FONT_PATH = Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")


def load_env(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def translate_page(page_number: int, source_text: str, config: dict[str, str]) -> str:
    cache_path = CACHE_DIR / f"page-{page_number:02d}.txt"
    if cache_path.exists() and cache_path.stat().st_size > 100:
        return cache_path.read_text(encoding="utf-8")

    system_prompt = """你是一名严谨的计算机科学论文翻译专家。请把提供的论文页面完整翻译为简体中文。
要求：
1. 不要总结、删减、扩写或评价，必须覆盖页面上的全部正文、标题、图注、表注、脚注、列表和附录内容。
2. 模型名、数据集名、框架名、API 名、代码、变量、公式、数字和引用编号保持原样。
3. 术语首次出现时使用“中文（English）”，之后可以使用中文；MapAgent、MapTool、Planner Agent 等专有名词可保留英文。
4. 表格使用清晰的 Markdown 表格；无法可靠重建的表格按行列顺序完整列出，绝不能省略数字。
5. 参考文献条目保持原文，不翻译作者、题名和出版信息。
6. 断行和连字符是 PDF 排版造成的，请还原为正常句子。
7. 只返回译文，不要加入“以下是翻译”等说明。"""
    payload = {
        "model": config.get("DEEPSEEK_MODEL", "deepseek-flash"),
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"原论文第 {page_number} 页内容如下：\n\n{source_text}",
            },
        ],
        "temperature": 0,
        "max_tokens": 8192,
        "thinking": {"type": "disabled"},
    }
    request_data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    base_url = config.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=request_data,
        headers={
            "Authorization": f"Bearer {config['DEEPSEEK_API_KEY']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    last_error: Exception | None = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                result = json.loads(response.read().decode("utf-8"))
            translated = result["choices"][0]["message"]["content"].strip()
            if len(translated) < max(100, int(len(source_text) * 0.22)):
                raise RuntimeError("translation output is unexpectedly short")
            cache_path.write_text(translated + "\n", encoding="utf-8")
            print(f"translated page {page_number}: {len(source_text)} -> {len(translated)} chars", flush=True)
            return translated
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, KeyError, RuntimeError) as exc:
            last_error = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"page {page_number} translation failed: {last_error}")


def clean_markdown(text: str) -> str:
    text = re.sub(r"^```(?:markdown|text)?\s*", "", text.strip(), flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def add_translation(story: list, text: str, styles: dict[str, ParagraphStyle]) -> None:
    blocks = re.split(r"\n\s*\n", clean_markdown(text))
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        first = block.splitlines()[0].strip()
        if first.startswith("#### "):
            style = styles["h4"]
            block = block[5:]
        elif first.startswith("### "):
            style = styles["h3"]
            block = block[4:]
        elif first.startswith("## "):
            style = styles["h2"]
            block = block[3:]
        elif first.startswith("# "):
            style = styles["h1"]
            block = block[2:]
        elif all(line.lstrip().startswith("|") for line in block.splitlines()):
            style = styles["table"]
        elif first.startswith(("- ", "* ", "• ")) or re.match(r"^\d+[.)]\s", first):
            style = styles["list"]
        else:
            style = styles["body"]

        # Large multi-line Paragraph objects can split poorly at an A4 page
        # boundary.  Keep semantic blocks, but divide them into modest chunks
        # so every continuation starts inside the configured top margin.
        lines = block.splitlines()
        chunks: list[str] = []
        current: list[str] = []
        current_length = 0
        for line in lines:
            if current and (len(current) >= 10 or current_length + len(line) > 850):
                chunks.append("\n".join(current))
                current = []
                current_length = 0
            current.append(line)
            current_length += len(line)
        if current:
            chunks.append("\n".join(current))

        for chunk in chunks:
            safe = html.escape(chunk)
            safe = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", safe)
            safe = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", safe)
            safe = safe.replace("\n", "<br/>")
            story.append(Paragraph(safe, style))
            story.append(Spacer(1, 1.8 * mm))


def build_pdf(translations: list[str], source_images: list[Path]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pdfmetrics.registerFont(TTFont("CJK", str(FONT_PATH)))
    styles_base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "ChineseTitle", parent=styles_base["Title"], fontName="CJK", fontSize=24,
            leading=34, alignment=TA_CENTER, textColor=colors.HexColor("#17365D"),
        ),
        "subtitle": ParagraphStyle(
            "ChineseSubtitle", parent=styles_base["Normal"], fontName="CJK", fontSize=12,
            leading=20, alignment=TA_CENTER, textColor=colors.HexColor("#555555"),
        ),
        "page_title": ParagraphStyle(
            "PageTitle", parent=styles_base["Heading1"], fontName="CJK", fontSize=16,
            leading=23, spaceAfter=8, keepWithNext=0, textColor=colors.HexColor("#17365D"),
        ),
        "h1": ParagraphStyle("H1", fontName="CJK", fontSize=15, leading=22, spaceBefore=6, spaceAfter=5, keepWithNext=0, textColor=colors.HexColor("#17365D")),
        "h2": ParagraphStyle("H2", fontName="CJK", fontSize=13, leading=20, spaceBefore=5, spaceAfter=4, keepWithNext=0, textColor=colors.HexColor("#244A73")),
        "h3": ParagraphStyle("H3", fontName="CJK", fontSize=11.5, leading=18, spaceBefore=4, spaceAfter=3, keepWithNext=0, textColor=colors.HexColor("#365F91")),
        "h4": ParagraphStyle("H4", fontName="CJK", fontSize=10.5, leading=17, spaceBefore=3, spaceAfter=2, keepWithNext=0, textColor=colors.HexColor("#444444")),
        "body": ParagraphStyle("Body", fontName="CJK", fontSize=9.6, leading=16, alignment=TA_JUSTIFY, splitLongWords=True, textColor=colors.HexColor("#202020")),
        "list": ParagraphStyle("List", fontName="CJK", fontSize=9.4, leading=15.5, leftIndent=5 * mm, firstLineIndent=-3 * mm, textColor=colors.HexColor("#202020")),
        "table": ParagraphStyle("TableText", fontName="CJK", fontSize=7.2, leading=11, backColor=colors.HexColor("#F3F5F7"), borderPadding=5, textColor=colors.HexColor("#111111")),
    }

    doc = SimpleDocTemplate(
        str(OUTPUT_PDF), pagesize=A4, rightMargin=16 * mm, leftMargin=16 * mm,
        topMargin=15 * mm, bottomMargin=16 * mm,
        title="MapAgent：面向地理空间推理的动态地图工具集成分层智能体 - 中文对照翻译版",
        author="原作者；中文翻译由 AI 辅助生成",
    )
    story: list = []
    story.append(Spacer(1, 42 * mm))
    story.append(Paragraph("MapAgent：面向地理空间推理的<br/>动态地图工具集成分层智能体", styles["title"]))
    story.append(Spacer(1, 12 * mm))
    story.append(Paragraph("中文对照翻译版", styles["subtitle"]))
    story.append(Spacer(1, 28 * mm))
    story.append(Paragraph("阅读说明", styles["h1"]))
    story.append(Paragraph(
        "本文件按原 PDF 页码制作：每张原文页面后紧跟对应的完整中文译文，以保留图表、公式、颜色标注和版面信息。模型名、数据集名、代码、公式与参考文献保留原文。译文由 AI 辅助生成，正式引用时应以英文原文为准。",
        styles["body"],
    ))
    story.append(PageBreak())

    for index, (translation, source_image) in enumerate(zip(translations, source_images), start=1):
        image = Image(str(source_image))
        max_w = A4[0] - 32 * mm
        max_h = A4[1] - 72 * mm
        scale = min(max_w / image.imageWidth, max_h / image.imageHeight)
        image.drawWidth = image.imageWidth * scale
        image.drawHeight = image.imageHeight * scale
        story.append(KeepTogether([
            Paragraph(f"原文第 {index} 页", styles["page_title"]),
            Spacer(1, 2 * mm),
            image,
        ]))
        story.append(PageBreak())
        story.append(KeepTogether([
            Paragraph(f"中文翻译 - 对应原文第 {index} 页", styles["page_title"]),
            Spacer(1, 2 * mm),
        ]))
        add_translation(story, translation, styles)
        if index != len(translations):
            story.append(PageBreak())

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont("CJK", 8)
        canvas.setFillColor(colors.HexColor("#777777"))
        canvas.drawCentredString(A4[0] / 2, 8 * mm, f"MapAgent 中文对照翻译版  |  {document.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def main() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config = load_env(ROOT / ".env")
    if not config.get("DEEPSEEK_API_KEY"):
        raise RuntimeError("DEEPSEEK_API_KEY is missing from .env")

    reader = PdfReader(str(SOURCE_PDF))
    source_pages = [(page.extract_text() or "").strip() for page in reader.pages]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(translate_page, i, text, config): i
            for i, text in enumerate(source_pages, start=1)
        }
        for future in concurrent.futures.as_completed(futures):
            future.result()

    translations = [
        (CACHE_DIR / f"page-{i:02d}.txt").read_text(encoding="utf-8").strip()
        for i in range(1, len(source_pages) + 1)
    ]
    md_parts = [
        "# MapAgent：面向地理空间推理的动态地图工具集成分层智能体\n",
        "> 中文翻译版。正式引用请以英文原文为准。\n",
    ]
    for i, translated in enumerate(translations, start=1):
        md_parts.append(f"\n---\n\n## 对应原文第 {i} 页\n\n{translated}\n")
    OUTPUT_MD.write_text("".join(md_parts), encoding="utf-8")

    source_images = [IMAGE_DIR / f"page-{i:02d}.png" for i in range(1, len(source_pages) + 1)]
    missing = [path for path in source_images if not path.exists()]
    if missing:
        raise RuntimeError(f"source page images are missing, first missing: {missing[0]}")
    build_pdf(translations, source_images)
    print(f"wrote {OUTPUT_PDF}", flush=True)
    print(f"wrote {OUTPUT_MD}", flush=True)


if __name__ == "__main__":
    main()
