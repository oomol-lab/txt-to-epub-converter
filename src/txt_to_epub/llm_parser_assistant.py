"""
LLM-assisted parser for ambiguous chapter detection
大模型辅助解析器 - 使用 OpenAI SDK 实现

支持的模型:
- GPT-4 系列 (推荐): gpt-4-turbo, gpt-4
- GPT-3.5 系列 (经济): gpt-3.5-turbo
- 其他兼容 OpenAI API 的模型
"""
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChapterCandidate:
    """候选章节数据结构"""
    text: str
    position: int
    line_number: int
    confidence: float
    context_before: str
    context_after: str
    pattern_type: str
    issues: List[str] = None

    def __post_init__(self):
        if self.issues is None:
            self.issues = []


@dataclass
class LLMDecision:
    """LLM决策结果数据结构"""
    is_chapter: bool
    confidence: float
    reason: str
    suggested_title: Optional[str] = None
    suggested_position: Optional[int] = None


class LLMParserAssistant:
    """LLM辅助解析器 - OpenAI 实现"""

    def __init__(self, api_key: str = None, model: str = "gpt-4-turbo",
                 base_url: str = None, organization: str = None):
        """
        初始化LLM助手

        :param api_key: OpenAI API密钥 (如果为None,将从环境变量读取)
        :param model: 使用的模型
        :param base_url: API基础URL (用于兼容其他服务)
        :param organization: OpenAI组织ID (可选)
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "OpenAI SDK未安装。请运行: pip install openai"
            )

        # 初始化OpenAI客户端
        client_kwargs = {}
        if api_key:
            client_kwargs['api_key'] = api_key
        if base_url:
            client_kwargs['base_url'] = base_url
        if organization:
            client_kwargs['organization'] = organization

        self.client = OpenAI(**client_kwargs)
        self.model = model
        self.max_tokens = 128000

        # 统计信息
        self.stats = {
            'total_calls': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_cost': 0.0
        }

        # 模型定价 (USD per 1K tokens)
        self.pricing = {
            'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
            'gpt-4': {'input': 0.03, 'output': 0.06},
            'gpt-3.5-turbo': {'input': 0.0005, 'output': 0.0015},
            'gpt-3.5-turbo-16k': {'input': 0.003, 'output': 0.004},
        }

        logger.info(f"LLM助手初始化完成: 模型={model}")

    def analyze_chapter_candidates(
        self,
        candidates: List[ChapterCandidate],
        full_content: str,
        existing_chapters: List[Dict],
        doc_context: Dict = None
    ) -> List[LLMDecision]:
        """
        分析候选章节,判断是否为真实章节

        :param candidates: 候选章节列表
        :param full_content: 完整文本内容
        :param existing_chapters: 已确认的章节信息
        :param doc_context: 文档上下文信息
        :return: 决策结果列表
        """
        if not candidates:
            return []

        logger.info(f"LLM分析 {len(candidates)} 个候选章节...")

        # 构建prompt
        prompt = self._build_chapter_analysis_prompt(
            candidates,
            full_content,
            existing_chapters,
            doc_context
        )

        # 调用LLM
        response = self._call_llm(prompt)

        # 解析响应
        decisions = self._parse_llm_response(response)

        # 更新统计
        confirmed = sum(1 for d in decisions if d.is_chapter)
        logger.info(f"LLM确认 {confirmed}/{len(candidates)} 个为真实章节")

        return decisions

    def infer_chapter_structure(
        self,
        content: str,
        max_length: int = 10000,
        language: str = 'chinese'
    ) -> List[Dict]:
        """
        对无明显章节标记的文本,推断章节结构

        :param content: 文本内容
        :param max_length: 最大分析长度
        :param language: 文档语言
        :return: 建议的章节结构
        """
        logger.info(f"LLM推断结构,文本长度: {len(content)} 字符...")

        # 截取分析样本
        sample = content[:max_length]

        prompt = f"""你是文档结构分析专家。以下文本没有明显章节标记,请分析并建议章节划分。

【文本样本】({len(sample)}字符)
{sample}

【语言】{language}

【任务】
1. 识别内容的主题变化点
2. 建议章节划分位置
3. 为每个章节生成标题

输出JSON格式:
{{
  "suggested_chapters": [
    {{
      "start_char": 0,
      "end_char": 500,
      "title": "建议标题",
      "reason": "划分依据",
      "confidence": 0.85
    }}
  ],
  "format_analysis": "格式特点分析",
  "confidence": 0.8
}}
"""

        response = self._call_llm(prompt, max_tokens=128000)
        result = self._parse_structure_response(response)

        logger.info(f"LLM建议 {len(result)} 个章节")
        return result

    def disambiguate_reference(
        self,
        text_snippet: str,
        candidate: str,
        context: Dict
    ) -> Dict:
        """
        消歧:判断是章节标题还是正文引用（支持中英文）

        :param text_snippet: 包含候选的文本片段
        :param candidate: 候选章节文本
        :param context: 上下文信息
        :return: 决策字典
        """
        logger.debug(f"LLM消歧: {candidate}")

        language = context.get('language', 'chinese')

        if language == 'english':
            prompt = f"""Determine whether "{candidate}" in the following text is a chapter title or a reference in the text?

【Text Snippet】
{text_snippet}

【Context】
- Previous Chapter: {context.get('prev_chapter', 'N/A')}
- Document Type: {context.get('doc_type', 'Unknown')}
- Language: English

Analysis Points:
1. Position: Standalone on a line or in the middle of a sentence?
2. Grammar: Is it part of sentence structure?
3. Format: Does it match chapter title format?

Response Format:
{{
  "type": "chapter" or "reference",
  "confidence": 0.0-1.0,
  "reason": "Reasoning for judgment"
}}
"""
        else:
            prompt = f"""判断以下文本中的"{candidate}"是章节标题还是正文中的引用?

【文本片段】
{text_snippet}

【上下文】
- 前一章节: {context.get('prev_chapter', 'N/A')}
- 文档类型: {context.get('doc_type', '未知')}
- 语言: 中文

分析要点:
1. 位置: 独占一行还是句子中间?
2. 语法: 是否在句子结构中?
3. 格式: 是否符合章节标题格式?

回答格式:
{{
  "type": "chapter" 或 "reference",
  "confidence": 0.0-1.0,
  "reason": "判断理由"
}}
"""

        response = self._call_llm(prompt, max_tokens=128000)

        # 处理空响应
        if not response or not response.strip():
            logger.warning("LLM返回空响应（消歧）")
            return {
                'type': 'reference',
                'confidence': 0.5,
                'reason': 'LLM未能提供明确判断'
            }

        try:
            result = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败（消歧）: {e}")
            return {
                'type': 'reference',
                'confidence': 0.5,
                'reason': '解析失败，保守判断为引用'
            }

        logger.debug(f"决策: {result['type']} (置信度: {result['confidence']})")
        return result

    def identify_table_of_contents(
        self,
        content_sample: str,
        language: str = 'chinese'
    ) -> Dict:
        """
        识别文本中是否包含目录页，并返回目录的位置范围

        :param content_sample: 文本样本（前1000行或更多）
        :param language: 语言类型
        :return: 目录识别结果
        """
        logger.info("LLM识别目录页...")

        if language == 'english':
            prompt = f"""You are a document structure analysis expert. Please identify whether the following text contains a Table of Contents (TOC) page.

【Text Sample】(first 3000 characters)
{content_sample[:3000]}

【Task】
Carefully analyze if there is a TOC section, even WITHOUT explicit "Contents" or "TOC" labels.

【Key TOC Characteristics】
1. **High density of chapter-like patterns**: Multiple lines with "Chapter X", "Part X", etc.
2. **Consecutive short lines**: Lines with chapter names but minimal content (usually < 80 chars)
3. **Page numbers**: Lines ending with numbers (e.g., "Chapter 1 ... 15")
4. **Lack of narrative content**: No story text, just titles and numbers
5. **Early position**: Usually at document beginning (first 100-500 lines)
6. **Consistent format**: All entries follow similar pattern

【Important】
- A TOC can exist WITHOUT the word "Contents" or "Table of Contents"
- Focus on structural patterns, not keywords
- Look for 5+ consecutive chapter-like entries

【Response Format】JSON:
{{
  "has_toc": true/false,
  "confidence": 0.0-1.0,
  "start_indicator": "description of where TOC starts (e.g., 'line 5' or 'after preface')",
  "end_indicator": "description of where TOC ends (e.g., 'line 45' or 'before first paragraph')",
  "reason": "detailed explanation (mention specific patterns observed)",
  "toc_entries_count": estimated number of entries,
  "key_evidence": ["evidence 1", "evidence 2", "evidence 3"]
}}
"""
        else:
            prompt = f"""你是文档结构分析专家。请识别以下文本中是否包含目录页。

【文本样本】(前3000字符)
{content_sample[:3000]}

【任务】
仔细分析是否存在目录页，即使**没有明确的"目录"或"CONTENTS"标识**。

【目录页的关键特征】
1. **章节模式密集**：多行包含"第X章"、"第X部"等模式
2. **连续短行**：行内容简短（通常 < 80字符），只有章节名
3. **页码标记**：行尾有数字（如："第一章 开始 ... 15"）
4. **缺乏叙事内容**：没有故事正文，只有标题和数字
5. **位置靠前**：通常在文档开头（前100-500行）
6. **格式一致**：所有条目遵循相似格式

【重要提示】
- 目录可以没有"目录"这个词
- 重点关注结构模式，而非关键词
- 寻找5个以上连续的章节样式条目

【输出格式】JSON:
{{
  "has_toc": true/false,
  "confidence": 0.0-1.0,
  "start_indicator": "目录开始位置描述（如：'第5行' 或 '序言之后'）",
  "end_indicator": "目录结束位置描述（如：'第45行' 或 '第一个长段落前'）",
  "reason": "详细说明判断理由（提及观察到的具体模式）",
  "toc_entries_count": 估计的目录条目数量,
  "key_evidence": ["证据1", "证据2", "证据3"]
}}
"""

        response = self._call_llm(prompt, max_tokens=128000, temperature=0.1)

        # 处理空响应
        if not response or not response.strip():
            logger.warning("LLM返回空响应（目录识别）")
            return {
                'has_toc': False,
                'confidence': 0.0,
                'reason': 'LLM未能提供判断'
            }

        try:
            result = json.loads(response)
            logger.info(f"目录识别结果: {'发现目录' if result.get('has_toc') else '无目录'} "
                       f"(置信度: {result.get('confidence', 0):.2f})")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败（目录识别）: {e}")
            return {
                'has_toc': False,
                'confidence': 0.0,
                'reason': '解析失败',
                'error': str(e)
            }

    def identify_special_format(
        self,
        content_sample: str,
        observed_patterns: List[str]
    ) -> Dict:
        """
        识别特殊格式书籍的章节模式

        :param content_sample: 文本样本
        :param observed_patterns: 观察到的模式
        :return: 格式识别结果
        """
        logger.info("LLM识别特殊格式...")

        patterns_text = "\n".join(f"- {p}" for p in observed_patterns)

        prompt = f"""这是一本特殊格式的书籍,请帮助识别其章节结构。

【文本样本】
{content_sample[:2000]}

【观察到的模式】
{patterns_text}

请分析:
1. 该书采用什么章节标记方式?
2. 如何识别章节边界?
3. 建议的正则表达式

输出JSON:
{{
  "format_type": "格式类型",
  "chapter_pattern": "模式描述",
  "identification_rules": ["规则1", "规则2"],
  "sample_chapters": [{{"title": "...", "position": 0}}],
  "confidence": 0.8,
  "suggested_regex": "正则表达式"
}}
"""

        response = self._call_llm(prompt, max_tokens=128000)

        # 调试：打印原始响应
        logger.debug(f"LLM原始响应: {response}")

        # 处理空响应
        if not response or not response.strip():
            logger.warning("LLM返回空响应")
            return {
                'format_type': 'unknown',
                'chapter_pattern': 'unknown',
                'confidence': 0.0,
                'suggested_regex': None
            }

        try:
            result = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}, 原始响应: {response[:200]}")
            # 返回默认结果
            return {
                'format_type': 'parse_error',
                'chapter_pattern': 'unknown',
                'confidence': 0.0,
                'suggested_regex': None,
                'error': str(e)
            }

        logger.info(f"识别格式: {result.get('format_type', 'unknown')}")
        return result

    def generate_chapter_title(
        self,
        chapter_number: str,
        chapter_content: str,
        language: str = 'chinese',
        max_content_length: int = 400
    ) -> Dict:
        """
        使用 LLM 根据章节内容生成合适的章节标题

        :param chapter_number: 章节号（如 "第007章", "Chapter 7"）
        :param chapter_content: 章节内容（开头部分）
        :param language: 语言类型
        :param max_content_length: 用于分析的最大内容长度（默认400字符，约200个汉字）
        :return: 包含生成标题的字典
        """
        logger.info(f"LLM生成章节标题: {chapter_number}")

        # 限制内容长度 - 减少到400字符以提高速度
        content_sample = chapter_content[:max_content_length].strip()

        if language == 'english':
            # 精简英文提示词
            prompt = f"""Generate a 3-8 word chapter title for: {chapter_number}

Content: {content_sample}

Requirements: Concise, meaningful, avoid dialogue quotes.

JSON response:
{{"title": "title text", "confidence": 0.0-1.0}}"""
        else:
            # 精简中文提示词
            prompt = f"""为章节生成3-12字的标题：{chapter_number}

内容：{content_sample}

要求：简洁有意义，避免对话引号。

JSON格式：
{{"title": "标题", "confidence": 0.0-1.0}}"""

        try:
            response = self._call_llm(prompt, temperature=0.3, max_tokens=100)
            result = json.loads(response)

            # 验证结果
            if 'title' not in result:
                logger.warning("LLM 响应缺少 'title' 字段")
                result['title'] = ""

            if 'confidence' not in result:
                result['confidence'] = 0.5

            logger.info(f"✓ 生成标题: {result.get('title', 'N/A')} (置信度: {result.get('confidence', 0):.2f})")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败（标题生成）: {e}, 原始响应: {response[:200] if 'response' in locals() else 'N/A'}")
            return {
                'title': "",
                'confidence': 0.0,
                'reason': f'解析失败: {str(e)}',
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"生成标题失败: {e}")
            return {
                'title': "",
                'confidence': 0.0,
                'reason': f'生成失败: {str(e)}',
                'error': str(e)
            }

    def generate_chapter_titles_batch(
        self,
        chapters_info: List[Dict[str, str]],
        language: str = 'chinese',
        max_content_length: int = 400
    ) -> List[Dict]:
        """
        批量生成章节标题（一次 LLM 调用处理多个章节）

        :param chapters_info: 章节信息列表，每项包含 {"number": "第X章", "content": "内容..."}
        :param language: 语言类型
        :param max_content_length: 每个章节用于分析的最大内容长度
        :return: 标题结果列表，每项包含 {"title": "标题", "confidence": 0.9}
        """
        if not chapters_info:
            return []

        logger.info(f"LLM批量生成 {len(chapters_info)} 个章节标题...")

        # 限制批量大小，避免超过 token 限制
        batch_size = 50  # 每次最多处理50个章节
        all_results = []

        for batch_start in range(0, len(chapters_info), batch_size):
            batch = chapters_info[batch_start:batch_start + batch_size]

            # 构建批量章节列表
            chapters_text = []
            for i, ch_info in enumerate(batch, start=batch_start + 1):
                content_sample = ch_info['content'][:max_content_length].strip()
                chapters_text.append(f"{i}. {ch_info['number']}\n内容: {content_sample[:200]}...")

            chapters_list = "\n\n".join(chapters_text)

            if language == 'english':
                prompt = f"""Generate concise titles (3-8 words) for the following chapters based on their content:

{chapters_list}

Requirements:
- Title should be meaningful and reflect the content
- Avoid dialogue quotes
- Keep titles concise

JSON response format:
{{
  "titles": [
    {{"index": 1, "title": "generated title", "confidence": 0.0-1.0}},
    {{"index": 2, "title": "generated title", "confidence": 0.0-1.0}}
  ]
}}"""
            else:
                prompt = f"""为以下章节生成简洁标题（3-12字），基于章节内容：

{chapters_list}

要求：
- 标题要有意义，反映内容
- 避免对话引号
- 保持简洁

JSON格式：
{{
  "titles": [
    {{"index": 1, "title": "生成的标题", "confidence": 0.0-1.0}},
    {{"index": 2, "title": "生成的标题", "confidence": 0.0-1.0}}
  ]
}}"""

            try:
                response = self._call_llm(prompt, temperature=0.3, max_tokens=2000)
                result = json.loads(response)

                # 解析结果
                titles = result.get('titles', [])

                # 创建索引到结果的映射
                title_map = {item['index']: item for item in titles}

                # 按原始顺序返回结果
                for i, ch_info in enumerate(batch, start=batch_start + 1):
                    if i in title_map:
                        all_results.append(title_map[i])
                    else:
                        # 如果 LLM 未返回该章节的标题，使用默认值
                        all_results.append({
                            'index': i,
                            'title': "",
                            'confidence': 0.0
                        })

                logger.info(f"✓ 批量生成完成: {len(titles)}/{len(batch)} 个标题")

            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败（批量标题生成）: {e}")
                # 返回空结果
                for i in range(len(batch)):
                    all_results.append({
                        'index': batch_start + i + 1,
                        'title': "",
                        'confidence': 0.0,
                        'error': str(e)
                    })
            except Exception as e:
                logger.error(f"批量生成标题失败: {e}")
                for i in range(len(batch)):
                    all_results.append({
                        'index': batch_start + i + 1,
                        'title': "",
                        'confidence': 0.0,
                        'error': str(e)
                    })

        logger.info(f"批量标题生成完成: 共 {len(all_results)} 个章节")
        return all_results


    def _build_chapter_analysis_prompt(
        self,
        candidates: List[ChapterCandidate],
        full_content: str,
        existing_chapters: List[Dict],
        doc_context: Dict = None
    ) -> str:
        """构建章节分析prompt（支持中英文）"""

        doc_context = doc_context or {}
        language = doc_context.get('language', 'chinese')

        # 计算平均章节长度
        if existing_chapters:
            avg_length = sum(ch.get('length', 0) for ch in existing_chapters) / len(existing_chapters)
        else:
            avg_length = 0

        # 根据语言选择prompt模板
        if language == 'english':
            return self._build_english_prompt(candidates, existing_chapters, avg_length, doc_context)
        else:
            return self._build_chinese_prompt(candidates, existing_chapters, avg_length, doc_context)

    def _build_chinese_prompt(
        self,
        candidates: List[ChapterCandidate],
        existing_chapters: List[Dict],
        avg_length: float,
        doc_context: Dict
    ) -> str:
        """构建中文章节分析prompt"""

        # 格式化候选项
        candidates_text = []
        for i, c in enumerate(candidates, 1):
            issues_text = f" [问题: {', '.join(c.issues)}]" if c.issues else ""
            candidates_text.append(
                f"{i}. \"{c.text}\" (第{c.line_number}行, "
                f"置信度:{c.confidence:.2f}, 类型:{c.pattern_type}){issues_text}"
            )

        # 提取每个候选的上下文
        contexts = []
        for i, c in enumerate(candidates, 1):
            context = f"""
【候选{i}上下文】
前文: ...{c.context_before}
>>> {c.text} <<<
后文: {c.context_after}..."""
            contexts.append(context)

        # 已确认章节示例
        chapter_examples = []
        for ch in existing_chapters[:5]:
            chapter_examples.append(f"- {ch.get('title', 'Unknown')}")

        prompt = f"""你是文档结构分析专家。请判断以下候选项是否为真正的章节标题。

【文档信息】
- 文档类型: {doc_context.get('doc_type', '未知')}
- 语言: 中文
- 已识别章节数: {len(existing_chapters)}
- 平均章节长度: {avg_length:.0f}字

【已确认章节示例】
{chr(10).join(chapter_examples) if chapter_examples else '暂无'}

【待判断候选项】
{chr(10).join(candidates_text)}

{chr(10).join(contexts)}

【判断标准】
1. ✓ 独占一行
2. ✓ 前后有适当分隔
3. ✓ 不在句子语法结构中
4. ✓ 格式与已识别章节一致
5. ✗ 位于句子中间
6. ✗ 前有"在/如/见"等引用词
7. ✗ 后有"中/里/结束时"等连接词

请为每个候选给出判断,JSON格式:
{{
  "decisions": [
    {{
      "index": 1,
      "is_chapter": true/false,
      "confidence": 0.0-1.0,
      "reason": "详细理由",
      "action": "accept/reject/modify",
      "suggested_title": "如需修改的标题"
    }}
  ],
  "overall_analysis": "整体分析"
}}
"""
        return prompt

    def _build_english_prompt(
        self,
        candidates: List[ChapterCandidate],
        existing_chapters: List[Dict],
        avg_length: float,
        doc_context: Dict
    ) -> str:
        """构建英文章节分析prompt"""

        # 格式化候选项
        candidates_text = []
        for i, c in enumerate(candidates, 1):
            issues_text = f" [Issues: {', '.join(c.issues)}]" if c.issues else ""
            candidates_text.append(
                f"{i}. \"{c.text}\" (Line {c.line_number}, "
                f"Confidence:{c.confidence:.2f}, Type:{c.pattern_type}){issues_text}"
            )

        # 提取每个候选的上下文
        contexts = []
        for i, c in enumerate(candidates, 1):
            context = f"""
【Candidate {i} Context】
Before: ...{c.context_before}
>>> {c.text} <<<
After: {c.context_after}..."""
            contexts.append(context)

        # 已确认章节示例
        chapter_examples = []
        for ch in existing_chapters[:5]:
            chapter_examples.append(f"- {ch.get('title', 'Unknown')}")

        prompt = f"""You are a professional document structure analyst. Please determine whether the following candidates are genuine chapter titles.

【Document Information】
- Document Type: {doc_context.get('doc_type', 'Unknown')}
- Language: English
- Identified Chapters: {len(existing_chapters)}
- Average Chapter Length: {avg_length:.0f} characters

【Confirmed Chapter Examples】
{chr(10).join(chapter_examples) if chapter_examples else 'None'}

【Candidates to Judge】
{chr(10).join(candidates_text)}

{chr(10).join(contexts)}

【Judgment Criteria】
1. ✓ Standalone on its own line
2. ✓ Properly separated before and after
3. ✓ Not embedded in sentence grammar
4. ✓ Format consistent with identified chapters
5. ✗ Located in middle of sentence
6. ✗ Preceded by reference words like "in/as/see"
7. ✗ Followed by connectors like "where/that/which"

Please provide judgment for each candidate in JSON format:
{{
  "decisions": [
    {{
      "index": 1,
      "is_chapter": true/false,
      "confidence": 0.0-1.0,
      "reason": "Detailed reasoning",
      "action": "accept/reject/modify",
      "suggested_title": "Suggested title if modification needed"
    }}
  ],
  "overall_analysis": "Overall analysis"
}}
"""
        return prompt

    def _call_llm(
        self,
        prompt: str,
        max_tokens: int = None,
        temperature: float = 0.1
    ) -> str:
        """
        调用LLM API

        :param prompt: 提示词
        :param max_tokens: 最大token数
        :param temperature: 温度参数 (0-2, 越低越确定)
        :return: LLM响应文本
        """
        try:
            self.stats['total_calls'] += 1

            # 构建消息
            messages = [
                {
                    "role": "system",
                    "content": "你是专业的文档结构分析助手,擅长识别章节和目录结构。请始终以JSON格式返回结果。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            # 确定实际使用的max_tokens
            actual_max_tokens = max_tokens or self.max_tokens

            # 如果max_tokens > 5000,必须使用stream=True
            use_streaming = actual_max_tokens > 5000

            if use_streaming:
                # 使用流式调用
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=actual_max_tokens,
                    temperature=temperature,
                    response_format={"type": "json_object"},
                    stream=True
                )

                # 收集流式响应
                content = ""
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content += chunk.choices[0].delta.content

                # 注意: 流式响应没有usage信息,使用估算值
                # 粗略估算: 1 token ≈ 4 characters for Chinese, 1.3 for English
                estimated_prompt_tokens = len(prompt) // 3
                estimated_completion_tokens = len(content) // 3

                self.stats['total_input_tokens'] += estimated_prompt_tokens
                self.stats['total_output_tokens'] += estimated_completion_tokens

                logger.debug(f"LLM流式调用成功: ~{estimated_prompt_tokens} in + ~{estimated_completion_tokens} out tokens (估算)")

            else:
                # 使用非流式调用
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=actual_max_tokens,
                    temperature=temperature,
                    response_format={"type": "json_object"}
                )

                # 提取响应文本
                content = response.choices[0].message.content

                # 更新统计
                usage = response.usage
                self.stats['total_input_tokens'] += usage.prompt_tokens
                self.stats['total_output_tokens'] += usage.completion_tokens

                # 计算成本
                model_key = self.model
                if model_key not in self.pricing:
                    # 尝试匹配前缀
                    for key in self.pricing:
                        if self.model.startswith(key):
                            model_key = key
                            break

                if model_key in self.pricing:
                    pricing = self.pricing[model_key]
                    input_cost = usage.prompt_tokens * pricing['input'] / 1000
                    output_cost = usage.completion_tokens * pricing['output'] / 1000
                    self.stats['total_cost'] += input_cost + output_cost

                logger.debug(f"LLM调用成功: {usage.prompt_tokens} in + {usage.completion_tokens} out tokens")

            return content

        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            raise

    def _parse_llm_response(self, response: str) -> List[LLMDecision]:
        """解析LLM JSON响应"""
        try:
            data = json.loads(response)
            decisions = []

            for item in data.get('decisions', []):
                decisions.append(LLMDecision(
                    is_chapter=item.get('is_chapter', False),
                    confidence=item.get('confidence', 0.5),
                    reason=item.get('reason', ''),
                    suggested_title=item.get('suggested_title'),
                    suggested_position=item.get('suggested_position')
                ))

            return decisions

        except json.JSONDecodeError as e:
            logger.error(f"解析LLM响应失败: {e}")
            logger.debug(f"响应内容: {response}")
            return []

    def _parse_structure_response(self, response: str) -> List[Dict]:
        """解析结构推断响应"""
        try:
            data = json.loads(response)
            return data.get('suggested_chapters', [])
        except json.JSONDecodeError as e:
            logger.error(f"解析结构响应失败: {e}")
            return []

    def get_stats(self) -> Dict:
        """获取使用统计"""
        return self.stats.copy()

    def reset_stats(self):
        """重置统计"""
        self.stats = {
            'total_calls': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_cost': 0.0
        }


# ==================== 使用示例 ====================

def example_usage():
    """使用示例"""

    # 示例1: 基础使用
    print("=== 示例1: 基础使用 ===")
    assistant = LLMParserAssistant(
        api_key="your-api-key",
        model="gpt-3.5-turbo"  # 使用经济模型
    )

    # 创建测试候选
    candidates = [
        ChapterCandidate(
            text="第一章 开始",
            position=0,
            line_number=1,
            confidence=0.95,
            context_before="",
            context_after="这是第一章的内容...",
            pattern_type="standard"
        ),
        ChapterCandidate(
            text="在第二章中",
            position=100,
            line_number=10,
            confidence=0.45,
            context_before="如前所述,",
            context_after="我们会详细讨论...",
            pattern_type="ambiguous",
            issues=["疑似引用"]
        )
    ]

    # 分析候选章节
    decisions = assistant.analyze_chapter_candidates(
        candidates=candidates,
        full_content="完整文本...",
        existing_chapters=[],
        doc_context={'language': 'chinese'}
    )

    for i, decision in enumerate(decisions):
        print(f"候选{i+1}: {decision.is_chapter}, 置信度: {decision.confidence}")
        print(f"  理由: {decision.reason}")

    # 查看统计
    stats = assistant.get_stats()
    print(f"\n统计: {stats['total_calls']} 次调用, ${stats['total_cost']:.4f} 成本")

    # 示例2: 混合解析器
    print("\n=== 示例2: 混合解析器 ===")
    parser = HybridParser(
        llm_api_key="your-api-key",
        llm_model="gpt-3.5-turbo"
    )

    content = """
第一章 开始
这是第一章的内容。

第二章 继续
这是第二章的内容。
"""

    volumes = parser.parse(content)
    print(f"解析结果: {len(volumes)} 卷")


class RuleBasedParserWithConfidence:
    """带置信度评分的规则解析器"""

    def __init__(self, config=None):
        """
        初始化规则解析器

        :param config: ParserConfig实例
        """
        from .parser_config import ParserConfig, DEFAULT_CONFIG
        self.config = config or DEFAULT_CONFIG

    def parse_with_confidence(self, content: str, skip_toc_removal: bool = False, context=None, resume_state=None) -> Dict:
        """
        解析内容并返回置信度

        :param content: 文本内容
        :param skip_toc_removal: If True, skip TOC removal (useful when content already processed)
        :param context: Context for progress reporting
        :param resume_state: Resume state for checkpoint resume
        :return: {
            'volumes': [...],
            'chapters': [...],
            'uncertain_regions': [...],
            'overall_confidence': 0.85
        }
        """
        from .parser import parse_hierarchical_content, detect_language

        # 使用现有解析器，传递 resume_state 参数
        volumes = parse_hierarchical_content(content, self.config, llm_assistant=None, skip_toc_removal=skip_toc_removal, context=context, resume_state=resume_state)

        # 检测语言
        language = detect_language(content)

        # 为每个章节计算置信度
        chapters_with_confidence = []
        uncertain_regions = []

        for volume in volumes:
            for chapter in volume.chapters:
                # 计算置信度
                confidence = self._estimate_confidence(chapter, content, language)

                chapter_info = {
                    'chapter': chapter,
                    'confidence': confidence,
                    'volume': volume,
                    'length': len(chapter.content) + sum(len(s.content) for s in chapter.sections),
                    'pattern_type': 'standard'
                }

                chapters_with_confidence.append(chapter_info)

                if confidence < 0.7:
                    uncertain_regions.append(chapter_info)

        if chapters_with_confidence:
            overall_confidence = sum(c['confidence'] for c in chapters_with_confidence) / len(chapters_with_confidence)
        else:
            overall_confidence = 0.0

        return {
            'volumes': volumes,
            'chapters': chapters_with_confidence,
            'uncertain_regions': uncertain_regions,
            'overall_confidence': overall_confidence
        }

    def _estimate_confidence(self, chapter, content: str, language: str) -> float:
        """估算章节置信度"""
        import re

        score = 0.6  # 基础分

        # 因素1: 标题长度
        title_len = len(chapter.title)
        if 5 <= title_len <= 30:
            score += 0.15
        elif title_len < 5 or title_len > 50:
            score -= 0.1

        # 因素2: 内容长度
        total_length = len(chapter.content) + sum(len(s.content) for s in chapter.sections)
        if 500 <= total_length <= 50000:
            score += 0.15
        elif total_length < 100:
            score -= 0.2

        # 因素3: 标题格式
        if language == 'chinese':
            if re.match(r'第[一二三四五六七八九十百千万\d]+章', chapter.title):
                score += 0.1  # 标准格式
        else:
            if re.match(r'Chapter\s+[\dIVXivx]+', chapter.title, re.IGNORECASE):
                score += 0.1

        # 因素4: 位置检查(简化)
        position = content.find(chapter.title)
        if position > 0:
            before = content[max(0, position-20):position]
            if re.search(r'[在如见]第', before):
                score -= 0.3  # 疑似引用

        return max(0.0, min(1.0, score))


class HybridParser:
    """混合解析器: 规则 + LLM"""

    def __init__(
        self,
        llm_api_key: str = None,
        llm_base_url: str = None,
        llm_model: str = "deepseek-v3.2",
        config = None
    ):
        """
        初始化混合解析器

        :param llm_api_key: LLM API密钥
        :param llm_base_url: LLM API基础URL
        :param llm_model: 使用的模型
        :param config: 解析器配置
        """
        from .parser_config import ParserConfig, DEFAULT_CONFIG

        self.config = config or DEFAULT_CONFIG
        self.rule_parser = RuleBasedParserWithConfidence(self.config)

        # 如果启用LLM辅助，初始化LLM助手
        self.llm_assistant = None
        if self.config.enable_llm_assistance or llm_api_key:
            self.llm_assistant = LLMParserAssistant(
                api_key=llm_api_key or self.config.llm_api_key,
                base_url=llm_base_url or self.config.llm_base_url,
                model=llm_model or self.config.llm_model
            )

    def parse(self, content: str, skip_toc_removal: bool = False, context=None, resume_state=None):
        """
        混合解析流程

        :param content: 文本内容
        :param skip_toc_removal: If True, skip TOC removal (useful when content already processed)
        :param context: Context object for progress reporting
        :param resume_state: Resume state for checkpoint resume
        :return: 卷列表
        """
        from .parser import detect_language

        # 阶段0: 使用LLM识别并移除目录页
        if self.llm_assistant:
            logger.info("阶段0: LLM识别目录页...")

        # 阶段1: 规则解析 + 置信度评分（使用LLM助手辅助目录识别）
        logger.info("阶段1: 规则解析...")

        # 【修复】只调用一次规则解析，直接使用 parse_with_confidence 的结果
        rule_result = self.rule_parser.parse_with_confidence(content, skip_toc_removal=skip_toc_removal, context=context)
        volumes = rule_result['volumes']
        confidence = rule_result['overall_confidence']
        threshold = self.config.llm_confidence_threshold
        logger.debug(f"规则解析置信度: {confidence:.2f}, 阈值: {threshold:.2f}")

        # 如果整体置信度高,直接返回
        if confidence >= threshold:
            logger.info(f"高置信度 ({confidence:.2f} >= {threshold:.2f}), 跳过章节级LLM辅助")
            logger.info(f"解析完成: {len(volumes)} 卷")
            return volumes

        logger.info(f"置信度 < 阈值, 需要LLM辅助章节识别")

        # 阶段2: 识别需要LLM的区域
        uncertain_regions = rule_result.get('uncertain_regions', [])
        chapters = rule_result.get('chapters', [])

        logger.debug(f"规则解析识别到 {len(chapters)} 个章节")

        if uncertain_regions and self.llm_assistant:
            logger.info(f"阶段2: LLM辅助处理 {len(uncertain_regions)} 个不确定区域...")

            # 转换为候选格式
            candidates = self._convert_to_candidates(uncertain_regions, content)

            # LLM分析
            llm_decisions = self.llm_assistant.analyze_chapter_candidates(
                candidates,
                content,
                rule_result['chapters'],
                {'language': detect_language(content), 'doc_type': '小说'}
            )

            logger.debug(f"LLM决策结果: 处理了 {len(llm_decisions)} 个候选")

            # 阶段3: 融合结果
            logger.info("阶段3: 融合结果...")
            final_volumes = self._merge_results(
                volumes,
                llm_decisions,
                candidates
            )

            # 输出统计
            stats = self.llm_assistant.get_stats()
            logger.info(f"LLM统计: {stats['total_calls']} 次调用, ${stats['total_cost']:.4f} 成本")

            return final_volumes

        # 无需LLM或未提供客户端
        return volumes

    def _convert_to_candidates(
        self,
        uncertain_regions: List[Dict],
        content: str
    ) -> List[ChapterCandidate]:
        """转换为候选格式"""
        candidates = []

        for region in uncertain_regions:
            chapter = region['chapter']
            confidence = region['confidence']

            # 查找在内容中的位置
            position = content.find(chapter.title)
            if position == -1:
                continue

            # 提取上下文
            context_size = 200
            context_before = content[max(0, position-context_size):position]
            context_after = content[position+len(chapter.title):position+len(chapter.title)+context_size]

            # 计算行号
            line_number = content[:position].count('\n') + 1

            # 确定问题
            issues = []
            if confidence < 0.5:
                issues.append("极低置信度")
            elif confidence < 0.7:
                issues.append("低置信度")

            if "第" in chapter.title and ("在" in context_before[-10:] or "如" in context_before[-10:]):
                issues.append("疑似引用")

            candidates.append(ChapterCandidate(
                text=chapter.title,
                position=position,
                line_number=line_number,
                confidence=confidence,
                context_before=context_before,
                context_after=context_after,
                pattern_type=region.get('pattern_type', 'standard'),
                issues=issues
            ))

        return candidates

    def _merge_results(
        self,
        rule_volumes,
        llm_decisions: List[LLMDecision],
        candidates: List[ChapterCandidate]
    ):
        """融合规则和LLM结果"""
        from .data_structures import Volume, Chapter

        # 创建决策映射
        decision_map = {
            candidates[i].text: llm_decisions[i]
            for i in range(min(len(candidates), len(llm_decisions)))
        }

        # 处理每个卷
        new_volumes = []
        for volume in rule_volumes:
            new_chapters = []

            for chapter in volume.chapters:
                decision = decision_map.get(chapter.title)

                if decision:
                    if decision.is_chapter:
                        # LLM确认为章节
                        if decision.suggested_title:
                            # 使用建议的标题
                            new_chapter = Chapter(
                                title=decision.suggested_title,
                                content=chapter.content,
                                sections=chapter.sections
                            )
                            new_chapters.append(new_chapter)
                        else:
                            new_chapters.append(chapter)
                    else:
                        # LLM拒绝,不添加
                        logger.info(f"LLM拒绝章节: {chapter.title}")
                else:
                    # 无LLM决策,保留原结果
                    new_chapters.append(chapter)

            if new_chapters:
                new_volumes.append(Volume(
                    title=volume.title,
                    chapters=new_chapters
                ))

        return new_volumes

    def get_stats(self) -> Dict:
        """获取LLM使用统计"""
        if self.llm_assistant:
            return self.llm_assistant.get_stats()
        return {
            'total_calls': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_cost': 0.0
        }


if __name__ == "__main__":
    # 运行示例(需要设置API密钥)
    # example_usage()
    pass
