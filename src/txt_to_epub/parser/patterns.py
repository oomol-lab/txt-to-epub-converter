"""
Regular expression patterns for Chinese and English books
"""
import re


class ChinesePatterns:
    """Regular expression patterns for Chinese books"""

    # Table of contents keywords
    TOC_KEYWORDS = ["目录"]

    # Preface keywords
    PREFACE_KEYWORDS = ["前言", "序", "序言"]

    # Volume/Part/Book patterns
    VOLUME_PATTERN = re.compile(r'(第([一二三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟萬]+|\d{1,3})[卷部篇]\s+[^\n]*)')

    # Chapter patterns
    CHAPTER_PATTERN = re.compile(
        r'(?:^|(?<=\n))'
        r'('
            r'[ \t\r]*'
            r'(?:'
                r'第([一二三四五六七八九十百千万壹贰叁肴伍陆柒捌玖拾佰仟萬]+|\d{1,4})章'
                r'(?:'
                    r'(?:[ \t\u3000]+|：|:)'
                    r'[^\r\n，。！？；:;,.!?]{0,50}'
                r')?'
                r'|'
                r'(?:番外|番外篇|外传|特别篇|插话|后记|尾声|终章|楔子|序章)'
                r'(?:'
                    r'(?:[ \t\u3000]+|：|:)'
                    r'[^\r\n，。！？；:;,.!?]{0,50}'
                r')?'
            r')'
        r')'
        r'[ \t]*'
        r'(?=\r?\n|$)',
        re.MULTILINE
    )

    # Section patterns
    SECTION_PATTERN = re.compile(r'(第([一二三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟萬]+|\d{1,3})节\s+[^\n]*)')


class EnglishPatterns:
    """Regular expression patterns for English books"""

    # Table of contents keywords
    TOC_KEYWORDS = ["Contents", "Table of Contents", "TOC"]

    # Preface keywords
    PREFACE_KEYWORDS = ["Preface", "Foreword", "Introduction", "Prologue"]

    # Word to number mapping
    WORD_TO_NUM = {
        'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
        'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
        'eleven': '11', 'twelve': '12', 'thirteen': '13', 'fourteen': '14', 'fifteen': '15',
        'sixteen': '16', 'seventeen': '17', 'eighteen': '18', 'nineteen': '19', 'twenty': '20'
    }

    # Roman numeral mapping
    ROMAN_TO_NUM = {
        'I': '1', 'II': '2', 'III': '3', 'IV': '4', 'V': '5',
        'VI': '6', 'VII': '7', 'VIII': '8', 'IX': '9', 'X': '10',
        'XI': '11', 'XII': '12', 'XIII': '13', 'XIV': '14', 'XV': '15',
        'XVI': '16', 'XVII': '17', 'XVIII': '18', 'XIX': '19', 'XX': '20'
    }

    # Volume/Part/Book patterns
    VOLUME_PATTERN = re.compile(
        r'(?:^|\n)(\s*(?:(?:Part|Book|Volume)\s+(?:I{1,3}V?|VI{0,3}|IX|X{1,2}|\d{1,2}|One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|Eleven|Twelve|Thirteen|Fourteen|Fifteen|Sixteen|Seventeen|Eighteen|Nineteen|Twenty)(?::\s*[^\n]+)?)\s*)(?=\n|$)',
        re.MULTILINE | re.IGNORECASE
    )

    # Chapter patterns
    CHAPTER_PATTERN = re.compile(
        r'(?:^|\n)(\s*(?:Chapter|Ch\.?|Chap\.?)\s+(?:I{1,3}V?|VI{0,3}|IX|X{1,2}L?|\d{1,2}|One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|Eleven|Twelve|Thirteen|Fourteen|Fifteen|Sixteen|Seventeen|Eighteen|Nineteen|Twenty|Thirty|Forty|Fifty)(?::\s*[^\n]+)?\s*)(?=\n|$)',
        re.MULTILINE | re.IGNORECASE
    )

    # Section patterns
    SECTION_PATTERN = re.compile(
        r'(?:^|\n)(\s*(?:Section|Sect\.?)\s+(?:\d{1,2}(?:\.\d+)?|One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|Eleven|Twelve|Thirteen|Fourteen|Fifteen|Sixteen|Seventeen|Eighteen|Nineteen|Twenty)(?::\s*[^\n]+)?\s*)(?=\n|$)',
        re.MULTILINE | re.IGNORECASE
    )

    # Numbered section patterns
    NUMBERED_SECTION_PATTERN = re.compile(r'(?:^|\n)(\s*(\d+\.\d+)\s+[^\n]+\s*)(?=\n|$)', re.MULTILINE)
