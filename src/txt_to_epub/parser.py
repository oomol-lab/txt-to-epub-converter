import re
import logging
from typing import List, Optional
from .data_structures import Section, Chapter, Volume
from .parser_config import ParserConfig, DEFAULT_CONFIG

# Configure logging
logger = logging.getLogger(__name__)


class ChinesePatterns:
    """Regular expression patterns for Chinese books"""
    
    # Table of contents keywords
    TOC_KEYWORDS = ["目录"]
    
    # Preface keywords
    PREFACE_KEYWORDS = ["前言", "序", "序言"]
    
    # Volume/Part/Book patterns
    VOLUME_PATTERN = re.compile(r'(第([一二三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟萬]+|\d{1,3})[卷部篇]\s+[^\n]*)')
    
    # Chapter patterns - 宽进策略：章节号后面的标题文字可以为空
    # 匹配 "第X章" (X可以是中文数字或阿拉伯数字，包括带前导零的如007)，后面可选标题文字
    # 关键改进：
    # 1. \d{1,4} 支持最多4位数字（如0001、007）
    # 2. 标题文字可以为空，也可以有内容
    # 3. 宽进原则：先匹配，后面用 is_valid_chapter_title 来严格验证
    #
    # 标题格式支持：
    # - 第X章（只有章节号）
    # - 第X章 标题文字（有标题）
    # - 第X章：标题文字（冒号分隔）
    # - 第X章　标题文字（全角空格）
    CHAPTER_PATTERN = re.compile(
        r'(?:^|(?<=\n))'  # 必须在行首（\n 之后或文件开头）
        r'('  # 捕获组1：整个章节标题
            r'[ \t\r]*'  # 可选的前导空白（包括\r，支持Windows换行符）
            r'(?:'  # 非捕获组：章节类型
                # 普通章节：第X章 [标题]
                r'第([一二三四五六七八九十百千万壹贰叁肴伍陆柒捌玖拾佰仟萬]+|\d{1,4})章'  # 捕获组2：章节号
                r'(?:'  # 标题部分（可选）
                    r'(?:[ \t\u3000]+|：|:)'  # 分隔符：空格、制表符、全角空格、冒号
                    r'[^\r\n，。！？；:;,.!?]{0,50}'  # 标题文字（不包含换行和句子结束标点）
                r')?'
                r'|'  # 或者
                # 特殊章节
                r'(?:番外|番外篇|外传|特别篇|插话|后记|尾声|终章|楔子|序章)'
                r'(?:'
                    r'(?:[ \t\u3000]+|：|:)'
                    r'[^\r\n，。！？；:;,.!?]{0,50}'
                r')?'
            r')'
        r')'  # 捕获组1结束
        r'[ \t]*'  # 可选的尾随空白
        r'(?=\r?\n|$)',  # 后面必须是换行（支持\r\n或\n）或文件结束
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
    VOLUME_PATTERN = re.compile(r'(?:^|\n)(\s*(?:(?:Part|Book|Volume)\s+(?:I{1,3}V?|VI{0,3}|IX|X{1,2}|\d{1,2}|One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|Eleven|Twelve|Thirteen|Fourteen|Fifteen|Sixteen|Seventeen|Eighteen|Nineteen|Twenty)(?::\s*[^\n]+)?)\s*)(?=\n|$)', re.MULTILINE | re.IGNORECASE)
    
    # Chapter patterns
    CHAPTER_PATTERN = re.compile(r'(?:^|\n)(\s*(?:Chapter|Ch\.?|Chap\.?)\s+(?:I{1,3}V?|VI{0,3}|IX|X{1,2}L?|\d{1,2}|One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|Eleven|Twelve|Thirteen|Fourteen|Fifteen|Sixteen|Seventeen|Eighteen|Nineteen|Twenty|Thirty|Forty|Fifty)(?::\s*[^\n]+)?\s*)(?=\n|$)', re.MULTILINE | re.IGNORECASE)
    
    # Section patterns
    SECTION_PATTERN = re.compile(r'(?:^|\n)(\s*(?:Section|Sect\.?)\s+(?:\d{1,2}(?:\.\d+)?|One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|Eleven|Twelve|Thirteen|Fourteen|Fifteen|Sixteen|Seventeen|Eighteen|Nineteen|Twenty)(?::\s*[^\n]+)?\s*)(?=\n|$)', re.MULTILINE | re.IGNORECASE)
    
    # Numbered section patterns (e.g., 1.1, 2.3)
    NUMBERED_SECTION_PATTERN = re.compile(r'(?:^|\n)(\s*(\d+\.\d+)\s+[^\n]+\s*)(?=\n|$)', re.MULTILINE)


def detect_language(content: str) -> str:
    """
    Detect the main language of the text (Chinese or English)

    :param content: Text content
    :return: 'chinese' or 'english'
    """
    if not content or not content.strip():
        return 'chinese'  # Default to Chinese

    # Count Chinese characters
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
    # Count English letters
    english_chars = len(re.findall(r'[a-zA-Z]', content))

    # Check common Chinese chapter keywords
    chinese_keywords = ['第', '章', '节', '卷', '部', '篇', '序言', '前言', '目录']
    chinese_keyword_count = sum(content.count(kw) for kw in chinese_keywords)

    # Check common English chapter keywords
    english_keywords = ['Chapter', 'Section', 'Part', 'Book', 'Volume', 'Contents', 'Preface', 'Introduction']
    english_keyword_count = sum(content.lower().count(kw.lower()) for kw in english_keywords)

    # Decision logic
    if chinese_chars > english_chars * 0.5 or chinese_keyword_count > english_keyword_count:
        return 'chinese'
    else:
        return 'english'


def is_simple_chapter_title(title: str, language: str = 'chinese') -> bool:
    """
    判断章节标题是否过于简单（只有章节号，没有实质内容）

    :param title: 章节标题
    :param language: 语言类型
    :return: True 如果是简单的章节号，False 如果有实质内容
    """
    if not title:
        return True

    title = title.strip()

    if language == 'chinese':
        # 匹配只有"第X章"或"第X章 "的标题
        simple_patterns = [
            r'^第[一二三四五六七八九十百千万\d]+章\s*$',
            r'^第[一二三四五六七八九十百千万\d]+章\s+[\s\u3000]*$',  # 包含全角空格
            r'^\d+[\s\u3000]*$',  # 只有数字
            r'^第\d+章\s*$',
            r'^第\d+章\s+[\s\u3000]*$'
        ]

        for pattern in simple_patterns:
            if re.match(pattern, title):
                return True

        # 如果标题长度小于等于5个字符，且包含"第"和"章"，认为是简单标题
        if len(title) <= 5 and '第' in title and '章' in title:
            return True

    else:
        # 英文简单标题模式
        simple_patterns = [
            r'^Chapter\s+\d+\s*$',
            r'^Ch\.?\s+\d+\s*$',
            r'^Chapter\s+[IVXivx]+\s*$',
            r'^\d+\s*$'
        ]

        for pattern in simple_patterns:
            if re.match(pattern, title, re.IGNORECASE):
                return True

    return False


def extract_meaningful_title(chapter_content: str, language: str = 'chinese', max_length: int = 20) -> str:
    """
    从章节内容中提取有意义的标题

    :param chapter_content: 章节内容
    :param language: 语言类型
    :param max_length: 标题最大长度
    :return: 提取的标题
    """
    if not chapter_content or not chapter_content.strip():
        return ""

    content = chapter_content.strip()

    # 移除常见的开头词汇
    if language == 'chinese':
        # 移除"话说"、"且说"、"却说"等开头
        content = re.sub(r'^(话说|且说|却说|却说|正是|正所谓|古人云|俗语说)\s*', '', content)

        # 寻找第一个完整的句子
        sentences = re.split(r'[。！？；]', content)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) >= 5 and len(sentence) <= max_length * 2:  # 中文字符
                # 检查是否包含有意义的内容
                if re.search(r'[的之在了是]', sentence):  # 包含有意义的连接词
                    # 截取前max_length个字符
                    title = sentence[:max_length]
                    # 确保不以不完整词语结束
                    if len(title) < len(sentence):
                        # 尝试在标点或自然断点处结束
                        break_points = [',', '，', ':', '：', ' ', '\u3000']
                        for bp in break_points:
                            if bp in title:
                                title = title.rsplit(bp, 1)[0]
                                break
                    return title.strip()

        # 如果没有找到合适的句子，取前几个字符
        if len(content) >= 5:
            title = content[:max_length]
            # 避免切断词语
            if len(title) < len(content):
                # 寻找最后一个空格或标点
                for i in range(len(title)-1, 0, -1):
                    if title[i] in ' ，。！？；：':
                        title = title[:i]
                        break
            return title.strip()

    else:
        # 英文处理
        sentences = re.split(r'[.!?;]', content)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) >= 10 and len(sentence) <= max_length * 2:
                # 包含有意义的词
                if re.search(r'\b(the|a|an|is|are|was|were|in|on|at|to|for)\b', sentence, re.IGNORECASE):
                    title = sentence[:max_length]
                    # 在合适的位置截断
                    words = title.split()
                    if len(words) > 1:
                        title = ' '.join(words[:-1]) if len(' '.join(words)) > max_length else ' '.join(words)
                    return title.strip()

        #  fallback
        if len(content) >= 10:
            title = content[:max_length]
            words = title.split()
            if len(words) > 1:
                title = ' '.join(words[:-1])
            return title.strip()

    return ""


def enhance_chapter_title(chapter_title: str, chapter_content: str, language: str = 'chinese', llm_assistant=None) -> str:
    """
    增强章节标题：如果标题过于简单，尝试使用 LLM 或从内容中提取有意义的标题

    :param chapter_title: 原始章节标题
    :param chapter_content: 章节内容
    :param language: 语言类型
    :param llm_assistant: LLM 助手实例（可选）
    :return: 增强后的标题
    """
    # 如果标题已经有实质内容，直接返回
    if not is_simple_chapter_title(chapter_title, language):
        return chapter_title

    # 提取章节号
    if language == 'chinese':
        chapter_num_match = re.search(r'(第[一二三四五六七八九十百千万\d]+章)', chapter_title)
        chapter_number = chapter_num_match.group(1) if chapter_num_match else chapter_title
    else:
        chapter_num_match = re.search(r'(Chapter\s+[\dIVXivx]+)', chapter_title, re.IGNORECASE)
        chapter_number = chapter_num_match.group(1) if chapter_num_match else chapter_title

    # 优先使用 LLM 生成标题
    if llm_assistant:
        try:
            logger.info(f"使用 LLM 生成章节标题: {chapter_number}")
            result = llm_assistant.generate_chapter_title(
                chapter_number=chapter_number,
                chapter_content=chapter_content,
                language=language,
                max_content_length=1000
            )

            # 如果 LLM 生成成功且置信度足够高
            if result.get('title') and result.get('confidence', 0) > 0.5:
                generated_title = result['title'].strip()
                if generated_title:
                    # 组合章节号和生成的标题
                    if language == 'chinese':
                        return f"{chapter_number} {generated_title}"
                    else:
                        return f"{chapter_number}: {generated_title}"
            else:
                logger.warning(f"LLM 生成标题置信度过低或为空: {result.get('confidence', 0):.2f}")
        except Exception as e:
            logger.warning(f"LLM 生成标题失败，回退到规则提取: {e}")

    # 回退方案：从内容中提取有意义的标题
    meaningful_title = extract_meaningful_title(chapter_content, language)

    if meaningful_title:
        # 保留原始章节号，添加实质内容
        if language == 'chinese':
            return f"{chapter_number} {meaningful_title}"
        else:
            return f"{chapter_number}: {meaningful_title}"

    # 如果无法提取有意义的内容，返回原始标题
    return chapter_title


def is_valid_chapter_title(match, content: str, language: str = 'chinese') -> bool:
    """
    Validate if a regex match is a genuine chapter title, not an inline reference.

    :param match: Regex match object
    :param content: Full text content
    :param language: Language type, 'chinese' or 'english'
    :return: True if valid chapter title, False if likely a reference
    """
    match_text = match.group(0).strip()
    match_start = match.start()
    match_end = match.end()

    # 1. Check if title is too long (likely not a real chapter title)
    if len(match_text) > 100:
        logger.debug(f"Rejected chapter title (too long): {match_text[:50]}...")
        return False

    # 2. Check context before the match
    context_before_start = max(0, match_start - 50)
    context_before = content[context_before_start:match_start]

    # Check if it's in the middle of a sentence (preceded by comma, etc.)
    if language == 'chinese':
        # Chinese: check for patterns like "在第X章", "如第X章", "见第X章"
        if re.search(r'[在如见到自从正前后于从到至]第.{0,5}章', context_before[-20:] + match_text[:10]):
            logger.debug(f"Rejected chapter title (inline reference): {match_text}")
            return False

        # Check if preceded by punctuation that suggests inline reference
        if re.search(r'[，,、；;]第.{0,5}章', context_before[-10:] + match_text[:10]):
            logger.debug(f"Rejected chapter title (after punctuation): {match_text}")
            return False
    else:
        # English: check for patterns like "in Chapter X", "see Chapter X"
        if re.search(r'(?:in|see|from|at|to|of|for)\s+Chapter\s+\w+', context_before[-30:] + match_text[:20], re.IGNORECASE):
            logger.debug(f"Rejected chapter title (inline reference): {match_text}")
            return False

    # 3. Check context after the match
    context_after_end = min(len(content), match_end + 50)
    context_after = content[match_end:context_after_end]

    if language == 'chinese':
        # Check for continuation phrases like "结束时", "中", "里"
        if re.match(r'^\s*[结结束时中里]', context_after):
            logger.debug(f"Rejected chapter title (continuation): {match_text}")
            return False

        # Check if followed by comma (inline reference pattern)
        if re.match(r'^\s*[，,]', context_after):
            logger.debug(f"Rejected chapter title (followed by comma): {match_text}")
            return False
    else:
        # English: check for continuation like "ends", "of the book"
        if re.match(r'^\s*(?:ends?|of|in|at)\s', context_after, re.IGNORECASE):
            logger.debug(f"Rejected chapter title (continuation): {match_text}")
            return False

    # 4. Check if the match is at the beginning of a line (real chapter titles usually are)
    # Allow some whitespace before the match
    line_start = content.rfind('\n', 0, match_start)
    if line_start == -1:
        line_start = 0
    else:
        line_start += 1

    text_before_match = content[line_start:match_start]
    if text_before_match.strip():  # Non-whitespace characters before match on same line
        # There's text before the chapter marker on the same line
        # This suggests it's not a standalone chapter title
        logger.debug(f"Rejected chapter title (not at line start): {match_text}")
        return False

    return True


def remove_table_of_contents(content: str, language: str = None, llm_assistant=None, config: Optional[ParserConfig] = None) -> str:
    """
    Remove the table of contents section from the text to avoid interference with chapter recognition.
    Supports both Chinese and English table of contents recognition.

    Enhanced version: Detects TOC by identifying regions with dense chapter-like patterns.
    Optionally uses LLM for more accurate TOC identification.

    :param content: Original text content
    :param language: Language type, 'chinese' or 'english', auto-detect if None
    :param llm_assistant: Optional LLM assistant for intelligent TOC detection
    :param config: Parser configuration (optional, uses default if None)
    :return: Text content with table of contents removed
    """
    if config is None:
        config = DEFAULT_CONFIG

    print("\n" + "="*60)
    print("【目录检测】开始检测文档中是否存在目录页...")
    print("="*60)

    if not content or not content.strip():
        print("【目录检测】文档内容为空，跳过")
        return content

    # Auto-detect language
    if language is None:
        language = detect_language(content)

    print(f"【目录检测】检测到文档语言: {language}")

    # Try LLM-based TOC detection first if available
    if llm_assistant:
        try:
            print("【目录检测】尝试使用LLM智能识别目录...")
            logger.info("尝试使用LLM识别目录...")
            toc_result = llm_assistant.identify_table_of_contents(content[:5000], language)

            if toc_result.get('has_toc') and toc_result.get('confidence', 0) > config.llm_toc_detection_threshold:
                print(f"【目录检测】✓ LLM确认存在目录 (置信度: {toc_result['confidence']:.2f})")
                print(f"【目录检测】原因: {toc_result.get('reason', 'N/A')}")
                logger.info(f"LLM确认存在目录 (置信度: {toc_result['confidence']:.2f})")
                logger.info(f"原因: {toc_result.get('reason', 'N/A')}")

                # Use rule-based method to find and remove TOC, but with LLM confirmation
                # This provides a good balance between accuracy and robustness
                pass  # Continue to rule-based detection below
            else:
                print(f"【目录检测】✗ LLM判定: {'无目录' if not toc_result.get('has_toc') else '目录置信度低'} (置信度: {toc_result.get('confidence', 0):.2f})")
                logger.info(f"LLM未检测到目录或置信度较低 (has_toc={toc_result.get('has_toc')}, confidence={toc_result.get('confidence', 0):.2f})")
                # If LLM says no TOC with high confidence, skip TOC removal
                if not toc_result.get('has_toc') and toc_result.get('confidence', 0) > config.llm_no_toc_threshold:
                    print("【目录检测】LLM高置信度判定无目录，跳过目录移除")
                    print("="*60 + "\n")
                    logger.info("LLM高置信度判定无目录，跳过目录移除")
                    return content
        except Exception as e:
            print(f"【目录检测】⚠ LLM识别失败，回退到规则方法: {e}")
            logger.warning(f"LLM目录识别失败，回退到规则方法: {e}")
    else:
        print("【目录检测】使用规则方法检测目录...")

    # Select corresponding patterns
    if language == 'english':
        patterns = EnglishPatterns()
        toc_keywords = patterns.TOC_KEYWORDS
        preface_keywords = patterns.PREFACE_KEYWORDS
        chapter_patterns = [patterns.CHAPTER_PATTERN, patterns.VOLUME_PATTERN]
    else:
        patterns = ChinesePatterns()
        toc_keywords = patterns.TOC_KEYWORDS
        preface_keywords = patterns.PREFACE_KEYWORDS
        chapter_patterns = [patterns.CHAPTER_PATTERN, patterns.VOLUME_PATTERN]

    lines = content.split('\n')

    # Find table of contents start position
    toc_start = -1
    toc_end = -1

    # Method 1: Explicit TOC keyword detection
    for i, line in enumerate(lines):
        stripped_line = line.strip()

        # Identify table of contents start: standalone line with TOC keywords
        if stripped_line in toc_keywords or any(keyword.lower() == stripped_line.lower() for keyword in toc_keywords):
            toc_start = i
            print(f"【目录检测】✓ 方法1: 检测到目录关键词在第 {i+1} 行: '{stripped_line}'")
            logger.info(f"检测到目录标题在第 {i+1} 行: {stripped_line}")
            break

    # Method 2: Detect dense chapter pattern region (TOC without explicit keyword)
    if toc_start == -1:
        print("【目录检测】方法1未发现目录关键词，尝试方法2: 增强密集章节模式检测...")
        # Scan for regions with abnormally high density of chapter-like patterns
        window_size = 20  # Check 20 lines at a time
        max_score = 0
        max_score_start = -1
        candidate_info = None

        for i in range(0, min(len(lines), 500), 3):  # Only check first 500 lines, step by 3
            window_end = min(i + window_size, len(lines))
            window_lines = lines[i:window_end]

            # Count chapter-like patterns in window
            chapter_count = 0
            short_line_count = 0  # Count of short lines (typical of TOC)
            total_chars = 0
            consecutive_chapters = 0  # Consecutive chapter-pattern lines
            max_consecutive = 0
            has_page_numbers = False  # Check for page number patterns

            for j, line in enumerate(window_lines):
                stripped = line.strip()
                total_chars += len(stripped)

                # Check for short lines (TOC characteristic)
                if 5 < len(stripped) < 80:
                    short_line_count += 1

                # Check if line matches chapter pattern
                is_chapter_line = False
                for pattern in chapter_patterns:
                    if pattern.search(stripped):
                        # Check if it's a short line (TOC entry, not actual chapter with content)
                        if len(stripped) < 80:  # TOC entries are usually short
                            chapter_count += 1
                            is_chapter_line = True
                        break

                # Track consecutive chapter patterns
                if is_chapter_line:
                    consecutive_chapters += 1
                    max_consecutive = max(max_consecutive, consecutive_chapters)
                else:
                    consecutive_chapters = 0

                # Check for page number patterns (common in TOC)
                if re.search(r'\d{1,4}\s*$', stripped):  # Ends with numbers (page numbers)
                    has_page_numbers = True

            # Calculate multiple scoring factors
            score = 0

            # Factor 1: Chapter density (chapters per 1000 characters)
            if total_chars > 100:  # Ensure sufficient text
                density = (chapter_count * 1000) / total_chars
                if density > 100:  # High density
                    score += density * 0.5  # Weight 0.5

            # Factor 2: Absolute chapter count (at least 5 chapters)
            if chapter_count >= 5:
                score += chapter_count * 2  # Weight 2

            # Factor 3: Consecutive chapter patterns (strong indicator)
            if max_consecutive >= 3:
                score += max_consecutive * 10  # Weight 10

            # Factor 4: High ratio of short lines
            if len(window_lines) > 0:
                short_ratio = short_line_count / len(window_lines)
                if short_ratio > 0.6:  # More than 60% short lines
                    score += short_ratio * 20  # Weight 20

            # Factor 5: Presence of page numbers
            if has_page_numbers:
                score += 15  # Bonus points

            # Factor 6: Early position in document (TOC usually at beginning)
            position_bonus = max(0, 50 - i)  # Earlier lines get higher bonus
            score += position_bonus * 0.2

            # Update best candidate
            if score > max_score and score > config.toc_detection_score_threshold:  # Use configured threshold
                max_score = score
                max_score_start = i
                candidate_info = {
                    'chapters': chapter_count,
                    'density': density if total_chars > 100 else 0,
                    'consecutive': max_consecutive,
                    'short_ratio': short_ratio if len(window_lines) > 0 else 0,
                    'has_page_nums': has_page_numbers
                }

        # If found high-score region, consider it as TOC
        if max_score > config.toc_detection_score_threshold:  # Use configured threshold
            toc_start = max_score_start
            print(f"【目录检测】✓ 方法2: 检测到疑似目录区域从第 {toc_start+1} 行开始")
            print(f"【目录检测】综合评分: {max_score:.1f}")
            if candidate_info:
                print(f"【目录检测】特征: 章节数={candidate_info['chapters']}, 密度={candidate_info['density']:.1f}/1000字, "
                      f"连续章节={candidate_info['consecutive']}, 短行占比={candidate_info['short_ratio']:.1%}, "
                      f"含页码={candidate_info['has_page_nums']}")
            logger.info(f"检测到疑似目录区域从第 {toc_start+1} 行开始，综合评分: {max_score:.1f}")

    # Find TOC end
    if toc_start != -1:
        # Look for the end of TOC
        chapter_density_window = 10

        for i in range(toc_start + 1, len(lines)):
            stripped_line = lines[i].strip()

            # Check for long paragraph (main content)
            if len(stripped_line) > 100:
                # Check if it's NOT a chapter title
                is_chapter = False
                for pattern in chapter_patterns:
                    if pattern.search(stripped_line):
                        is_chapter = True
                        break

                if not is_chapter:
                    # Found long content paragraph
                    toc_end = i - 1
                    logger.info(f"目录结束于第 {toc_end+1} 行（检测到长段落正文）")
                    break

            # Check for consecutive empty lines followed by content
            if not stripped_line:
                # Look ahead for content
                next_content_idx = -1
                for j in range(i + 1, min(i + 5, len(lines))):
                    if lines[j].strip():
                        next_content_idx = j
                        break

                if next_content_idx != -1:
                    next_line = lines[next_content_idx].strip()
                    # If next is long content or preface
                    if len(next_line) > 50:
                        is_chapter = any(p.search(next_line) for p in chapter_patterns)
                        is_preface = any(keyword.lower() == next_line.lower() for keyword in preface_keywords)

                        if not is_chapter or is_preface:
                            toc_end = i
                            logger.info(f"目录结束于第 {toc_end+1} 行（空行后接正文）")
                            break

            # Safety: if scanned too far without finding end, limit TOC region
            if i - toc_start > config.toc_max_scan_lines:
                toc_end = i
                logger.warning(f"目录区域过长，强制在第 {toc_end+1} 行结束")
                break

    # Remove TOC if found
    if toc_start != -1 and toc_end != -1 and toc_end > toc_start:
        removed_lines = toc_end - toc_start + 1
        print(f"\n【目录移除】✓ 成功移除目录区域!")
        print(f"【目录移除】位置: 第 {toc_start+1} 行 到 第 {toc_end+1} 行")
        print(f"【目录移除】删除: 共 {removed_lines} 行")
        print("="*60 + "\n")
        logger.info(f"移除目录: 第 {toc_start+1} 行到第 {toc_end+1} 行，共 {removed_lines} 行")
        remaining_lines = lines[:toc_start] + lines[toc_end + 1:]
        return '\n'.join(remaining_lines)
    else:
        print("【目录检测】✗ 未检测到目录区域")
        print("="*60 + "\n")

    return content


def parse_hierarchical_content(content: str, config: Optional[ParserConfig] = None, llm_assistant=None, skip_toc_removal: bool = False, context=None, resume_state=None) -> List[Volume]:
    """
    Split text content into three-level hierarchical structure: volumes, chapters, sections.
    Supports both Chinese and English book formats.
    Optimized version using finditer() for better performance.

    :param content: Text content
    :param config: Parser configuration (optional, uses default if None)
    :param llm_assistant: Optional LLM assistant for intelligent TOC detection
    :param skip_toc_removal: If True, skip table of contents removal (useful when content already processed)
    :return: List of volumes containing complete hierarchical structure
    """
    if config is None:
        config = DEFAULT_CONFIG

    if not content or not content.strip():
        # If content is empty, return a volume with empty chapter
        return [Volume(title=None, chapters=[Chapter(title="Empty Content", content="This document is empty or cannot be parsed.", sections=[])])]

    # Detect language
    language = detect_language(content)

    # Preprocessing: remove table of contents to avoid interference with content parsing
    if not skip_toc_removal:
        content = remove_table_of_contents(content, language, llm_assistant, config)

    # Select corresponding patterns based on language
    if language == 'english':
        patterns = EnglishPatterns()
        volume_pattern = patterns.VOLUME_PATTERN
    else:
        patterns = ChinesePatterns()
        volume_pattern = patterns.VOLUME_PATTERN

    # Optimized: Use finditer() instead of split() for better performance
    volume_matches = list(volume_pattern.finditer(content))

    volumes = []

    if not volume_matches:
        # No volumes, only chapters
        chapters = parse_chapters_from_content(content, language, config, llm_assistant, context, resume_state)
        # Validate and merge short chapters if enabled
        if config.enable_length_validation:
            chapters = validate_and_merge_chapters(chapters, language, config.min_chapter_length)
        if chapters:
            volumes.append(Volume(title=None, chapters=chapters))
        else:
            # If no chapters detected, treat entire content as one chapter
            default_title = "正文" if language == 'chinese' else "Content"
            volumes.append(Volume(title=None, chapters=[Chapter(title=default_title, content=content.strip(), sections=[])]))
    else:
        # Handle first part (possibly preface, content without volume title)
        first_volume_start = volume_matches[0].start()
        if first_volume_start > 0 and content[:first_volume_start].strip():
            pre_content = content[:first_volume_start]
            pre_chapters = parse_chapters_from_content(pre_content, language, config, llm_assistant, context, resume_state)
            # Validate and merge short chapters if enabled
            if config.enable_length_validation:
                pre_chapters = validate_and_merge_chapters(pre_chapters, language, config.min_chapter_length)
            if pre_chapters:
                volumes.append(Volume(title=None, chapters=pre_chapters))
            else:
                # If first part has no chapter structure, treat as preface chapter
                preface_title = "序言" if language == 'chinese' else "Preface"
                volumes.append(Volume(title=None, chapters=[Chapter(title=preface_title, content=pre_content.strip(), sections=[])]))

        # Handle parts with volume titles
        seen_volume_titles = set()  # Track seen volume titles
        for i, match in enumerate(volume_matches):
            volume_title = match.group(1).strip()

            # Get volume content (from end of current match to start of next match, or end of text)
            volume_start = match.end()
            volume_end = volume_matches[i + 1].start() if i + 1 < len(volume_matches) else len(content)
            volume_content = content[volume_start:volume_end]

            # Check for duplicate volume titles, skip if duplicate
            if volume_title and volume_title not in seen_volume_titles:
                seen_volume_titles.add(volume_title)
                chapters = parse_chapters_from_content(volume_content, language, config, llm_assistant, context, resume_state)
                # Validate and merge short chapters if enabled
                if config.enable_length_validation:
                    chapters = validate_and_merge_chapters(chapters, language, config.min_chapter_length)
                if chapters:
                    volumes.append(Volume(title=volume_title, chapters=chapters))
                elif volume_content.strip():  # If has content but no chapter structure
                    # Treat entire volume content as one chapter
                    default_title = "正文" if language == 'chinese' else "Content"
                    volumes.append(Volume(title=volume_title, chapters=[Chapter(title=default_title, content=volume_content.strip(), sections=[])]))

    # Ensure at least one volume
    if not volumes:
        error_title = "未知内容" if language == 'chinese' else "Unknown Content"
        error_content = "无法解析文档结构，请检查文档格式。" if language == 'chinese' else "Unable to parse document structure. Please check document format."
        volumes.append(Volume(title=None, chapters=[Chapter(title=error_title, content=error_content, sections=[])]))

    return volumes


def parse_chapters_from_content(content: str, language: str = 'chinese', config: Optional[ParserConfig] = None, llm_assistant=None, context=None, resume_state=None) -> List[Chapter]:
    """
    Split chapters and sections from given content.
    Supports both Chinese and English chapter formats.
    Optimized version using finditer() for better performance.
    Validates chapter titles to filter out inline references.

    :param content: Text content
    :param language: Language type, 'chinese' or 'english'
    :param config: Parser configuration (optional)
    :param llm_assistant: LLM assistant for title enhancement
    :param context: Context for progress reporting
    :param resume_state: Resume state for checkpoint resume
    :return: Chapter list, each chapter contains title, content and section list
    """
    if config is None:
        config = DEFAULT_CONFIG

    if not content or not content.strip():
        return []

    # Select corresponding patterns based on language
    if language == 'english':
        patterns = EnglishPatterns()
        chapter_pattern = patterns.CHAPTER_PATTERN
        preface_keywords = patterns.PREFACE_KEYWORDS
    else:
        patterns = ChinesePatterns()
        chapter_pattern = patterns.CHAPTER_PATTERN
        preface_keywords = patterns.PREFACE_KEYWORDS

    # Optimized: Use finditer() instead of split()
    all_matches = list(chapter_pattern.finditer(content))

    # Validate matches to filter out inline references (if enabled)
    if config.enable_chapter_validation:
        chapter_matches = [match for match in all_matches if is_valid_chapter_title(match, content, language)]
        if len(all_matches) != len(chapter_matches):
            logger.info(f"Filtered out {len(all_matches) - len(chapter_matches)} inline chapter references")
    else:
        chapter_matches = all_matches

    chapter_list = []

    # If no chapter titles found, return empty list (let parent function handle)
    if not chapter_matches:
        return chapter_list

    # Process first part (possibly preface content without chapter title)
    first_chapter_start = chapter_matches[0].start()
    if first_chapter_start > 0 and content[:first_chapter_start].strip():
        preface_content = content[:first_chapter_start].strip()
        sections = parse_sections_from_content(preface_content, language)
        preface_title = "前言" if language == 'chinese' else "Preface"
        if sections:
            chapter_list.append(Chapter(title=preface_title, content="", sections=sections))
        else:
            chapter_list.append(Chapter(title=preface_title, content=preface_content, sections=[]))

    # Process each matched chapter
    seen_titles = set()  # Track seen chapter titles
    total_chapters = len(chapter_matches)

    # 设置断点续传的总章节数
    if resume_state:
        resume_state.set_total_chapters(total_chapters)

    # 记录开始处理章节
    if llm_assistant:
        logger.info(f"开始使用 LLM 生成章节标题，共 {total_chapters} 个章节")
        print(f"\n{'='*60}")
        print(f"开始智能生成章节标题（共 {total_chapters} 章）")
        if resume_state and resume_state.get_processed_count() > 0:
            print(f"断点续传：已处理 {resume_state.get_processed_count()} 章，继续处理...")
        print(f"{'='*60}")

    # 【优化】批量收集需要 LLM 增强的章节
    chapters_to_enhance = []
    chapter_data = []  # 存储章节的元数据

    for i, match in enumerate(chapter_matches):
        chapter_title = match.group(1).strip()

        # 断点续传：跳过已处理的章节
        if resume_state and resume_state.is_chapter_processed(chapter_title):
            if llm_assistant:
                print(f"[{i+1}/{total_chapters}] 跳过已处理章节: {chapter_title[:20]}...")
            continue

        # Get chapter content (from end of current match to start of next match, or end of text)
        chapter_start = match.end()
        chapter_end = chapter_matches[i + 1].start() if i + 1 < len(chapter_matches) else len(content)
        chapter_content = content[chapter_start:chapter_end].strip('\n\r')

        if chapter_title and chapter_title not in seen_titles:  # Ensure title is not empty and not duplicate
            # 存储章节数据
            chapter_data.append({
                'index': i,
                'title': chapter_title,
                'content': chapter_content,
                'is_simple': is_simple_chapter_title(chapter_title, language)
            })

            # 收集需要增强的章节
            if is_simple_chapter_title(chapter_title, language):
                # 提取章节号
                if language == 'chinese':
                    chapter_num_match = re.search(r'(第[一二三四五六七八九十百千万\d]+章)', chapter_title)
                    chapter_number = chapter_num_match.group(1) if chapter_num_match else chapter_title
                else:
                    chapter_num_match = re.search(r'(Chapter\s+[\dIVXivx]+)', chapter_title, re.IGNORECASE)
                    chapter_number = chapter_num_match.group(1) if chapter_num_match else chapter_title

                chapters_to_enhance.append({
                    'index': i,
                    'number': chapter_number,
                    'content': chapter_content
                })

    # 【优化】批量调用 LLM 生成标题
    enhanced_titles = {}
    if llm_assistant and chapters_to_enhance:
        try:
            logger.info(f"批量生成 {len(chapters_to_enhance)} 个简单章节的标题...")
            print(f"\n批量生成 {len(chapters_to_enhance)} 个章节标题...")

            batch_results = llm_assistant.generate_chapter_titles_batch(
                chapters_to_enhance,
                language=language,
                max_content_length=400
            )

            # 构建索引到标题的映射
            for result in batch_results:
                idx = result.get('index')
                if idx is not None:
                    idx = idx - 1  # 转换为0-based索引
                    if result.get('title') and result.get('confidence', 0) > 0.5:
                        enhanced_titles[idx] = result['title']
                        logger.info(f"[{idx+1}] 生成标题: {result['title']} (置信度: {result['confidence']:.2f})")

            print(f"✓ 批量生成完成: {len(enhanced_titles)}/{len(chapters_to_enhance)} 个标题成功")

        except Exception as e:
            logger.warning(f"批量生成标题失败，回退到规则提取: {e}")
            print(f"⚠ 批量生成失败，使用规则提取: {e}")

    # 处理所有章节，应用增强的标题
    for ch_data in chapter_data:
        i = ch_data['index']
        chapter_title = ch_data['title']
        chapter_content = ch_data['content']

        # 计算并上报进度：5% 到 95% 之间（生成目录阶段占 90%）
        progress_percent = int((i + 1) / total_chapters * 100)
        if context:
            # 将章节处理进度映射到 5% - 95% 区间
            mapped_progress = 5 + int((i + 1) / total_chapters * 90)
            context.report_progress(mapped_progress)

        # 打印进度
        print(f"[{i+1}/{total_chapters}] ({progress_percent}%) 处理章节: {chapter_title[:20]}...")

        # 应用增强的标题（如果有）
        if i in enhanced_titles:
            # 提取章节号
            if language == 'chinese':
                chapter_num_match = re.search(r'(第[一二三四五六七八九十百千万\d]+章)', chapter_title)
                chapter_number = chapter_num_match.group(1) if chapter_num_match else chapter_title
                enhanced_title = f"{chapter_number} {enhanced_titles[i]}"
            else:
                chapter_num_match = re.search(r'(Chapter\s+[\dIVXivx]+)', chapter_title, re.IGNORECASE)
                chapter_number = chapter_num_match.group(1) if chapter_num_match else chapter_title
                enhanced_title = f"{chapter_number}: {enhanced_titles[i]}"

            logger.info(f"[{i+1}/{total_chapters}] Enhanced: '{chapter_title}' -> '{enhanced_title}'")
            print(f"  ✓ 应用标题: {enhanced_title}")
            final_title = enhanced_title
        elif ch_data['is_simple'] and not llm_assistant:
            # 如果没有 LLM，回退到规则提取
            meaningful_title = extract_meaningful_title(chapter_content, language)
            if meaningful_title:
                if language == 'chinese':
                    chapter_num_match = re.search(r'(第[一二三四五六七八九十百千万\d]+章)', chapter_title)
                    chapter_number = chapter_num_match.group(1) if chapter_num_match else chapter_title
                    final_title = f"{chapter_number} {meaningful_title}"
                else:
                    chapter_num_match = re.search(r'(Chapter\s+[\dIVXivx]+)', chapter_title, re.IGNORECASE)
                    chapter_number = chapter_num_match.group(1) if chapter_num_match else chapter_title
                    final_title = f"{chapter_number}: {meaningful_title}"
                print(f"  - 规则提取标题: {meaningful_title}")
            else:
                final_title = chapter_title
                print(f"  - 保留原标题")
        else:
            final_title = chapter_title
            print(f"  - 保留原标题")

        seen_titles.add(final_title)

        # Further analyze chapter content for sections
        sections = parse_sections_from_content(chapter_content, language)
        if sections:
            # If has sections, chapter content is empty (all content is in sections)
            chapter_list.append(Chapter(title=final_title, content="", sections=sections))
        else:
            # If no sections, chapter directly contains content
            if not chapter_content.strip():
                empty_content = "此章节内容为空。" if language == 'chinese' else "This chapter is empty."
                chapter_content = empty_content
            chapter_list.append(Chapter(title=final_title, content=chapter_content, sections=[]))

        # 断点续传：标记章节已处理
        if resume_state:
            resume_state.mark_chapter_processed(chapter_title)

    # 完成日志
    if llm_assistant:
        print(f"{'='*60}")
        print(f"✓ 章节标题生成完成！共处理 {total_chapters} 个章节")
        print(f"{'='*60}\n")
        logger.info(f"章节标题生成完成，共处理 {total_chapters} 个章节")

    return chapter_list


def parse_sections_from_content(content: str, language: str = 'chinese') -> List[Section]:
    """
    Split sections from given chapter content.
    Supports both Chinese and English section formats.
    Optimized version using finditer() for better performance.

    :param content: Chapter content
    :param language: Language type, 'chinese' or 'english'
    :return: Section list, each section contains title and content
    """
    if not content or not content.strip():
        return []

    # Select corresponding patterns based on language
    if language == 'english':
        patterns = EnglishPatterns()
        # Try multiple section patterns for English
        section_patterns = [patterns.SECTION_PATTERN, patterns.NUMBERED_SECTION_PATTERN]
    else:
        patterns = ChinesePatterns()
        section_patterns = [patterns.SECTION_PATTERN]

    section_list = []
    section_matches = None
    active_pattern = None

    # Try different section patterns
    for pattern in section_patterns:
        matches = list(pattern.finditer(content))
        if matches:  # Found matching pattern
            section_matches = matches
            active_pattern = pattern
            break

    # If no section pattern found, return empty list
    if not section_matches:
        return section_list

    # Handle first part (chapter preface, content without section title)
    first_section_start = section_matches[0].start()
    if first_section_start > 0 and content[:first_section_start].strip():
        preface_title = "章节序言" if language == 'chinese' else "Chapter Preface"
        section_list.append(Section(title=preface_title, content=content[:first_section_start].strip()))

    # Process each matched section
    seen_titles = set()  # Track seen section titles
    for i, match in enumerate(section_matches):
        section_title = match.group(1).strip()

        # Get section content (from end of current match to start of next match, or end of text)
        section_start = match.end()
        section_end = section_matches[i + 1].start() if i + 1 < len(section_matches) else len(content)
        section_content = content[section_start:section_end].strip('\n\r')

        if section_title and section_title not in seen_titles:  # Ensure title is not empty and not duplicate
            seen_titles.add(section_title)
            # Ensure section content is not empty
            if not section_content.strip():
                empty_content = "此节内容为空。" if language == 'chinese' else "This section is empty."
                section_content = empty_content
            section_list.append(Section(title=section_title, content=section_content))

    return section_list


def validate_and_merge_chapters(chapters: List[Chapter], language: str = 'chinese', min_length: int = 500) -> List[Chapter]:
    """
    Validate chapter structure and merge chapters that are too short (likely misidentified).

    :param chapters: List of chapters to validate
    :param language: Language type, 'chinese' or 'english'
    :param min_length: Minimum chapter length in characters
    :return: Validated and merged chapter list
    """
    if not chapters:
        return chapters

    valid_chapters = []
    accumulated_content = ""
    accumulated_title = None

    for i, chapter in enumerate(chapters):
        # Calculate total content length (chapter content + all sections)
        total_content = chapter.content
        for section in chapter.sections:
            total_content += section.content

        content_length = len(total_content.strip())

        # Check if chapter is too short
        if content_length < min_length:
            logger.warning(f"Chapter '{chapter.title}' is too short ({content_length} chars), may be misidentified")

            # First chapter or no previous accumulated content
            if not valid_chapters and not accumulated_content:
                # Store this chapter for potential merging
                accumulated_title = chapter.title
                accumulated_content = f"{chapter.title}\n\n{chapter.content}"
            else:
                # Merge into previous chapter or accumulated content
                if valid_chapters:
                    # Merge into last valid chapter
                    last_chapter = valid_chapters[-1]
                    merged_content = last_chapter.content
                    if merged_content:
                        merged_content += f"\n\n{chapter.title}\n{chapter.content}"
                    else:
                        merged_content = f"{chapter.title}\n{chapter.content}"

                    # Keep the original chapter structure but update content
                    valid_chapters[-1] = Chapter(
                        title=last_chapter.title,
                        content=merged_content,
                        sections=last_chapter.sections
                    )
                    logger.info(f"Merged short chapter '{chapter.title}' into '{last_chapter.title}'")
                else:
                    # Add to accumulated content
                    accumulated_content += f"\n\n{chapter.title}\n{chapter.content}"
        else:
            # Chapter is long enough, it's valid
            if accumulated_content:
                # First, add the accumulated content as a chapter
                preface_title = accumulated_title or ("前言" if language == 'chinese' else "Preface")
                valid_chapters.append(Chapter(
                    title=preface_title,
                    content=accumulated_content.strip(),
                    sections=[]
                ))
                accumulated_content = ""
                accumulated_title = None

            # Then add current chapter
            valid_chapters.append(chapter)

    # Handle any remaining accumulated content
    if accumulated_content:
        preface_title = accumulated_title or ("前言" if language == 'chinese' else "Preface")
        valid_chapters.append(Chapter(
            title=preface_title,
            content=accumulated_content.strip(),
            sections=[]
        ))

    logger.info(f"Chapter validation complete: {len(chapters)} -> {len(valid_chapters)} chapters")
    return valid_chapters
