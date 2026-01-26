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

    # Volume/Part/Book patterns (improved with better boundary detection)
    VOLUME_PATTERN = re.compile(
        r'(?:^|(?<=\n))'  # Line start
        r'[ \t]*'
        r'(第([一二三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟萬]+|\d{1,3})[卷部篇]'
        r'(?:[ \t\u3000]+[^\r\n]{0,40})?)'  # Optional title (max 40 chars)
        r'[ \t]*'
        r'(?=\r?\n|$)',  # Line end
        re.MULTILINE
    )

    # Chapter patterns
    CHAPTER_PATTERN = re.compile(
        r'(?:^|(?<=\n))'
        r'('
            r'[ \t\r]*'
            r'(?:\d{1,4}[\.、])?'  # Optional numeric prefix: "001."
            r'[ \t]*'
            r'[【\[]?'  # Optional decorative brackets
            r'(?:'
                r'第([一二三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟萬]+|\d{1,3})章'
                r'[】\]]?'  # Closing bracket right after chapter number
                r'(?:'
                    r'(?:[ \t\u3000]+|：|:)?'  # Optional separator (made optional)
                    r'[^\r\n，。！？；]{1,50}'  # Title content (at least 1 char)
                    r'(?:[（\(][上中下前后][）\)])?'  # Optional part markers: (上)
                r')?'
                r'|'
                r'[【\[]?'  # Bracket for special chapter types
                r'(?:番外|番外篇|外传|特别篇|插话|后记|尾声|终章|楔子|序章)'
                r'[】\]]?'  # Closing bracket
                r'(?:'
                    r'(?:[ \t\u3000]+|：|:)?'  # Optional separator
                    r'[^\r\n，。！？；]{1,50}'
                r')?'
            r')'
        r')'
        r'[ \t]*'
        r'(?=\r?\n|$)',
        re.MULTILINE
    )

    # Section patterns (improved)
    SECTION_PATTERN = re.compile(
        r'(?:^|(?<=\n))'
        r'[ \t]*'
        r'(第([一二三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟萬]+|\d{1,3})节'
        r'(?:[ \t\u3000]+[^\r\n]{0,40})?)'
        r'[ \t]*'
        r'(?=\r?\n|$)',
        re.MULTILINE
    )


class EnglishPatterns:
    """Regular expression patterns for English books"""

    # Table of contents keywords
    TOC_KEYWORDS = ["Contents", "Table of Contents", "TOC"]

    # Preface keywords
    PREFACE_KEYWORDS = ["Preface", "Foreword", "Introduction", "Prologue"]

    # Extended word to number mapping (1-100)
    WORD_TO_NUM = {
        'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
        'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
        'eleven': '11', 'twelve': '12', 'thirteen': '13', 'fourteen': '14', 'fifteen': '15',
        'sixteen': '16', 'seventeen': '17', 'eighteen': '18', 'nineteen': '19', 'twenty': '20',
        'thirty': '30', 'forty': '40', 'fifty': '50', 'sixty': '60', 'seventy': '70',
        'eighty': '80', 'ninety': '90', 'hundred': '100'
    }

    # Extended Roman numeral mapping (1-100)
    ROMAN_TO_NUM = {
        'I': '1', 'II': '2', 'III': '3', 'IV': '4', 'V': '5',
        'VI': '6', 'VII': '7', 'VIII': '8', 'IX': '9', 'X': '10',
        'XI': '11', 'XII': '12', 'XIII': '13', 'XIV': '14', 'XV': '15',
        'XVI': '16', 'XVII': '17', 'XVIII': '18', 'XIX': '19', 'XX': '20',
        'XXI': '21', 'XXX': '30', 'XL': '40', 'L': '50',
        'LX': '60', 'LXX': '70', 'LXXX': '80', 'XC': '90', 'C': '100'
    }

    # Complete Roman numeral pattern (1-100): supports I, II, III, IV, V...C
    ROMAN_PATTERN = r'(?:C|XC|L?X{0,3})(?:IX|IV|V?I{0,3})'

    # Number word pattern (supports "One", "Two", etc.)
    NUMBER_WORD_PATTERN = r'(?:One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|Eleven|Twelve|Thirteen|Fourteen|Fifteen|Sixteen|Seventeen|Eighteen|Nineteen|Twenty|Thirty|Forty|Fifty|Sixty|Seventy|Eighty|Ninety|Hundred)'

    # Volume/Part/Book patterns (improved with extended Roman numerals support)
    VOLUME_PATTERN = re.compile(
        r'(?:^|(?<=\n))'
        r'[ \t]*'
        r'((?:Part|Book|Volume)\s+'
        r'(?:' + ROMAN_PATTERN + r'|\d{1,3}|' + NUMBER_WORD_PATTERN + r')'
        r'(?::\s*[^\r\n]{0,60})?)'
        r'[ \t]*'
        r'(?=\r?\n|$)',
        re.MULTILINE | re.IGNORECASE
    )

    # Chapter patterns (improved with extended Roman numerals and better formatting)
    CHAPTER_PATTERN = re.compile(
        r'(?:^|(?<=\n))'
        r'[ \t]*'
        r'((?:Chapter|Ch\.?|Chap\.?)\s+'
        r'(?:' + ROMAN_PATTERN + r'|\d{1,3}|' + NUMBER_WORD_PATTERN + r')'
        r'(?:[:\.]\s*[^\r\n]{0,60})?)'
        r'[ \t]*'
        r'(?=\r?\n|$)',
        re.MULTILINE | re.IGNORECASE
    )

    # Section patterns (improved)
    SECTION_PATTERN = re.compile(
        r'(?:^|(?<=\n))'
        r'[ \t]*'
        r'((?:Section|Sect\.?)\s+'
        r'(?:\d{1,3}(?:\.\d+)?|' + NUMBER_WORD_PATTERN + r')'
        r'(?:[:\.]\s*[^\r\n]{0,60})?)'
        r'[ \t]*'
        r'(?=\r?\n|$)',
        re.MULTILINE | re.IGNORECASE
    )

    # Numbered section patterns
    NUMBERED_SECTION_PATTERN = re.compile(r'(?:^|\n)(\s*(\d+\.\d+)\s+[^\n]+\s*)(?=\n|$)', re.MULTILINE)
