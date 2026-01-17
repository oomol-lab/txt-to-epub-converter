from ebooklib import epub
from typing import Optional


def _get_watermark_html(watermark_text: str) -> str:
    """
    Generate watermark HTML.

    :param watermark_text: Watermark text content
    :return: HTML string for watermark
    """
    if not watermark_text:
        return ""

    return f'''
        <div style="position: fixed; bottom: 2rem; left: 50%; transform: translateX(-50%); width: 100%;">
            <p style="color: #95a5a6; font-size: 0.8em; text-align: center;">
                {watermark_text}
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

    # Determine unit name and decorative icon
    if "卷" in volume_title:
        unit_name = "卷"
        icon = "📖"
    elif "部" in volume_title:
        unit_name = "部"
        icon = "📚"
    elif "篇" in volume_title:
        unit_name = "篇"
        icon = "📜"
    else:
        unit_name = "卷"
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
        <title>{volume_title}</title>
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
            <h1 class="volume-title">{volume_title}</h1>
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
                       watermark_text: Optional[str] = None) -> epub.EpubHtml:
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

    # Generate watermark HTML
    watermark_html = _get_watermark_html(watermark_text) if watermark_text else ""

    # Create elegant chapter page content
    if chapter_content.strip():
        chapter_page.content = f'''
        <!DOCTYPE html>
        <html lang="zh">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{chapter_title}</title>
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
                <h1 class="chapter-title">{chapter_title}</h1>
                <div style="margin-top: 1.5rem; margin-bottom: 2rem;">
                    <pre>{chapter_content}</pre>
                </div>
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
            <title>{chapter_title}</title>
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
                <h1 class="chapter-title">{chapter_title}</h1>
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

    if section_title:
        section_page.content = f'''
        <!DOCTYPE html>
        <html lang="zh">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{section_title}</title>
            <link rel="stylesheet" type="text/css" href="style/nav.css"/>
        </head>
        <body class="chinese-text">
            <h2 class="section-title">{section_title}</h2>
            <div style="margin-top: 1rem;">
                <pre>{section_content}</pre>
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
                <pre>{section_content}</pre>
            </div>
        </body>
        </html>
        '''

    return section_page



def create_chapter(title: str, content: str, file_name: str) -> epub.EpubHtml:
    """
    Create EPUB chapter with modern design.
    """
    chapter = epub.EpubHtml(title=title, file_name=file_name, lang='zh')
    
    if content:
        chapter.content = f'''
        <!DOCTYPE html>
        <html lang="zh">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <link rel="stylesheet" type="text/css" href="style/nav.css"/>
        </head>
        <body class="chinese-text">
            <h1 class="chapter-title">{title}</h1>
            <div style="margin-top: 1.5rem;">
                <pre>{content}</pre>
            </div>
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
            <title>{title}</title>
            <link rel="stylesheet" type="text/css" href="style/nav.css"/>
        </head>
        <body class="chinese-text">
            <h1 class="chapter-title">{title}</h1>
        </body>
        </html>
        '''
    
    return chapter