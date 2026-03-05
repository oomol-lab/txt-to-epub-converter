import html
import re
from ebooklib import epub
from typing import Optional


def _escape_text(text: Optional[str], *, quote: bool = False) -> str:
    """Escape plain text for safe HTML insertion."""
    return html.escape(text or "", quote=quote)


def _render_text_blocks(content: str) -> str:
    """
    Render plain text content as standard paragraph HTML.

    The previous implementation wrapped whole chapters in one large <pre>,
    which is prone to rendering differences across EPUB readers.
    """
    normalized = (content or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return ""

    paragraphs = []
    blocks = re.split(r"\n\s*\n+", normalized)
    for block in blocks:
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if not lines:
            continue
        escaped_lines = [_escape_text(line) for line in lines]
        paragraphs.append(f"<p>{'<br/>'.join(escaped_lines)}</p>")
    return "\n".join(paragraphs)


def _get_illustration_blocks(
    illustration_href: Optional[str],
    illustration_caption: Optional[str],
    illustration_position: str = "head"
) -> tuple[str, str]:
    """
    Generate illustration HTML blocks for chapter pages.

    :return: (head_block, tail_block)
    """
    if not illustration_href:
        return "", ""

    safe_caption = _escape_text(illustration_caption) if illustration_caption else ""
    caption_html = f'<p class="duokan-note">{safe_caption}</p>' if safe_caption else ""
    safe_alt = _escape_text(illustration_caption or "chapter illustration", quote=True)
    safe_href = _escape_text(illustration_href, quote=True)
    block = (
        f'<div class="duokan-image-single">'
        f'<img class="duokan-image" src="{safe_href}" alt="{safe_alt}"/>'
        f'{caption_html}'
        f'</div>'
    )
    normalized_pos = (illustration_position or "head").strip().lower()
    if normalized_pos not in {"head", "tail"}:
        normalized_pos = "head"
    if normalized_pos == "tail":
        return "", block
    return block, ""


def _get_watermark_html(watermark_text: str) -> str:
    """
    Generate watermark HTML.

    :param watermark_text: Watermark text content
    :return: HTML string for watermark
    """
    if not watermark_text:
        return ""

    safe_watermark = _escape_text(watermark_text)
    return f'''
        <div style="position: fixed; bottom: 2rem; left: 50%; transform: translateX(-50%); width: 100%;">
            <p style="color: #95a5a6; font-size: 0.8em; text-align: center;">
                {safe_watermark}
            </p>
        </div>'''


def create_volume_page(volume_title: str, file_name: str, chapter_count: int,
                      watermark_text: Optional[str] = None) -> epub.EpubHtml:
    """
    Create volume/part/book page with modern design.

    :param volume_title: Volume title
    :param file_name: File name
    :param chapter_count: Chapter count
    :param watermark_text: Watermark text (None to disable watermark)
    :return: EpubHtml object
    """
    volume_page = epub.EpubHtml(title=volume_title, file_name=file_name, lang='zh')
    safe_volume_title = _escape_text(volume_title)

    # Determine decorative icon
    if "卷" in volume_title:
        icon = "📖"
    elif "部" in volume_title:
        icon = "📚"
    elif "篇" in volume_title:
        icon = "📜"
    else:
        icon = "📖"

    # Generate watermark HTML
    watermark_html = _get_watermark_html(watermark_text) if watermark_text else ""

    # Create concise volume page content
    volume_page.content = f'''
    <!DOCTYPE html>
    <html lang="zh">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{safe_volume_title}</title>
        <link rel="stylesheet" type="text/css" href="style/nav.css"/>
        <style>
            body {{
                height: 100vh;
                margin: 0;
                padding: 2rem;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                page-break-after: always;
                box-sizing: border-box;
            }}
            .volume-content {{
                text-align: center;
                max-width: 80%;
            }}
        </style>
    </head>
    <body class="chinese-text">
        <div class="volume-content">
            <h1 class="volume-title">{safe_volume_title}</h1>
            <div style="margin-top: 2rem;">
                <div style="font-size: 3em; margin-bottom: 1.5rem;">{icon}</div>
                <p style="color: #2c3e50; font-size: 1.3em; font-weight: 500; margin-bottom: 2rem;">
                </p>
            </div>
        </div>{watermark_html}
    </body>
    </html>
    '''
    
    return volume_page



def create_chapter_page(chapter_title: str, chapter_content: str, file_name: str, section_count: int,
                       watermark_text: Optional[str] = None, illustration_href: Optional[str] = None,
                       illustration_caption: Optional[str] = None,
                       illustration_position: str = "head") -> epub.EpubHtml:
    """
    Create chapter page (for chapters with sections) with modern design.

    :param chapter_title: Chapter title
    :param chapter_content: Chapter content (usually empty, as content is in sections)
    :param file_name: File name
    :param section_count: Section count
    :param watermark_text: Watermark text (None to disable watermark)
    :return: EpubHtml object
    """
    chapter_page = epub.EpubHtml(title=chapter_title, file_name=file_name, lang='zh')
    safe_chapter_title = _escape_text(chapter_title)
    rendered_chapter_content = _render_text_blocks(chapter_content)

    # Generate watermark HTML
    watermark_html = _get_watermark_html(watermark_text) if watermark_text else ""
    illustration_head, illustration_tail = _get_illustration_blocks(
        illustration_href=illustration_href,
        illustration_caption=illustration_caption,
        illustration_position=illustration_position
    )

    # Create elegant chapter page content
    if rendered_chapter_content:
        chapter_page.content = f'''
        <!DOCTYPE html>
        <html lang="zh">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{safe_chapter_title}</title>
            <link rel="stylesheet" type="text/css" href="style/nav.css"/>
            <style>
                body {{
                    height: 100vh;
                    margin: 0;
                    padding: 2rem;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    page-break-after: always;
                    box-sizing: border-box;
                }}
                .chapter-content {{
                    text-align: center;
                    max-width: 80%;
                    margin: 0 auto;
                }}
            </style>
        </head>
        <body class="chinese-text">
            <div class="chapter-content">
                <h1 class="chapter-title">{safe_chapter_title}</h1>
                {illustration_head}
                <div style="margin-top: 1.5rem; margin-bottom: 2rem;">
                    {rendered_chapter_content}
                </div>
                {illustration_tail}
                <div style="margin-top: 2rem;">
                    <div style="font-size: 3em; margin-bottom: 1.5rem;">📚</div>
                    <p style="color: #2c3e50; font-size: 1.3em; font-weight: 500;">
                    </p>
                </div>
            </div>{watermark_html}
        </body>
        </html>
        '''
    else:
        chapter_page.content = f'''
        <!DOCTYPE html>
        <html lang="zh">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{safe_chapter_title}</title>
            <link rel="stylesheet" type="text/css" href="style/nav.css"/>
            <style>
                body {{
                    height: 100vh;
                    margin: 0;
                    padding: 2rem;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    page-break-after: always;
                    box-sizing: border-box;
                }}
                .chapter-content {{
                    text-align: center;
                    max-width: 80%;
                }}
            </style>
        </head>
        <body class="chinese-text">
            <div class="chapter-content">
                <h1 class="chapter-title">{safe_chapter_title}</h1>
                {illustration_head}
                {illustration_tail}
                <div style="margin-top: 2rem;">
                    <div style="font-size: 3em; margin-bottom: 1.5rem;">📚</div>
                    <p style="color: #2c3e50; font-size: 1.3em; font-weight: 500;">
                    </p>
                </div>
            </div>{watermark_html}
        </body>
        </html>
        '''
    
    return chapter_page



def create_section_page(section_title: str, section_content: str, file_name: str) -> epub.EpubHtml:
    """
    Create section page with modern design.

    :param section_title: Section title
    :param section_content: Section content
    :param file_name: File name
    :return: EpubHtml object
    """
    section_page = epub.EpubHtml(title=section_title, file_name=file_name, lang='zh')
    safe_section_title = _escape_text(section_title)
    rendered_section_content = _render_text_blocks(section_content)

    if section_title:
        section_page.content = f'''
        <!DOCTYPE html>
        <html lang="zh">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{safe_section_title}</title>
            <link rel="stylesheet" type="text/css" href="style/nav.css"/>
        </head>
        <body class="chinese-text">
            <h2 class="section-title">{safe_section_title}</h2>
            <div style="margin-top: 1rem;">
                {rendered_section_content}
            </div>
        </body>
        </html>
        '''
    else:
        # Untitled section (chapter preface)
        section_page.content = f'''
        <!DOCTYPE html>
        <html lang="zh">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Chapter Preface</title>
            <link rel="stylesheet" type="text/css" href="style/nav.css"/>
        </head>
        <body class="chinese-text">
            <div style="margin-top: 1rem;">
                {rendered_section_content}
            </div>
        </body>
        </html>
        '''

    return section_page



def create_chapter(title: str, content: str, file_name: str, illustration_href: Optional[str] = None,
                   illustration_caption: Optional[str] = None,
                   illustration_position: str = "head") -> epub.EpubHtml:
    """
    Create EPUB chapter with modern design.
    """
    chapter = epub.EpubHtml(title=title, file_name=file_name, lang='zh')
    safe_title = _escape_text(title)
    rendered_content = _render_text_blocks(content)
    illustration_head, illustration_tail = _get_illustration_blocks(
        illustration_href=illustration_href,
        illustration_caption=illustration_caption,
        illustration_position=illustration_position
    )
    
    if rendered_content:
        chapter.content = f'''
        <!DOCTYPE html>
        <html lang="zh">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{safe_title}</title>
            <link rel="stylesheet" type="text/css" href="style/nav.css"/>
        </head>
        <body class="chinese-text">
            <h1 class="chapter-title">{safe_title}</h1>
            {illustration_head}
            <div style="margin-top: 1.5rem;">
                {rendered_content}
            </div>
            {illustration_tail}
        </body>
        </html>
        '''
    else:
        chapter.content = f'''
        <!DOCTYPE html>
        <html lang="zh">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{safe_title}</title>
            <link rel="stylesheet" type="text/css" href="style/nav.css"/>
        </head>
        <body class="chinese-text">
            <h1 class="chapter-title">{safe_title}</h1>
            {illustration_head}
            {illustration_tail}
        </body>
        </html>
        '''
    
    return chapter
