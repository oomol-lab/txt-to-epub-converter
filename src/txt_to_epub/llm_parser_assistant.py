"""
LLM-assisted parser for ambiguous chapter detection
LLM-Assisted Parser - Implemented using OpenAI SDK

Supported models:
- GPT-4 series (recommended): gpt-4-turbo, gpt-4
- GPT-3.5 series (economical): gpt-3.5-turbo
- Other models compatible with OpenAI API
"""
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChapterCandidate:
    """Candidate chapter data structure"""
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
    """LLM decision result data structure"""
    is_chapter: bool
    confidence: float
    reason: str
    suggested_title: Optional[str] = None
    suggested_position: Optional[int] = None


class LLMParserAssistant:
    """LLM-Assisted Parser - OpenAI Implementation"""

    def __init__(self, api_key: str = None, model: str = "gpt-4-turbo",
                 base_url: str = None, organization: str = None):
        """
        Initialize LLM assistant

        :param api_key: OpenAI API key (if None, will read from environment variables)
        :param model: Model to use
        :param base_url: API base URL (for compatibility with other services)
        :param organization: OpenAI organization ID (optional)
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "OpenAI SDK not installed. Please run: pip install openai"
            )

        # Initialize OpenAI client
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

        # Statistics information
        self.stats = {
            'total_calls': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_cost': 0.0
        }

        # Model pricing (USD per 1K tokens)
        self.pricing = {
            'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
            'gpt-4': {'input': 0.03, 'output': 0.06},
            'gpt-3.5-turbo': {'input': 0.0005, 'output': 0.0015},
            'gpt-3.5-turbo-16k': {'input': 0.003, 'output': 0.004},
        }

        logger.info(f"LLM assistant initialized: model={model}")

    def analyze_chapter_candidates(
        self,
        candidates: List[ChapterCandidate],
        full_content: str,
        existing_chapters: List[Dict],
        doc_context: Dict = None
    ) -> List[LLMDecision]:
        """
        Analyze chapter candidates to determine if they are real chapters

        :param candidates: List of chapter candidates
        :param full_content: Full text content
        :param existing_chapters: Confirmed chapter information
        :param doc_context: Document context information
        :return: List of decision results
        """
        if not candidates:
            return []

        logger.info(f"LLM analyzing {len(candidates)} chapter candidates...")

        # Build prompt
        prompt = self._build_chapter_analysis_prompt(
            candidates,
            full_content,
            existing_chapters,
            doc_context
        )

        # Call LLM
        response = self._call_llm(prompt)

        # Parse response
        decisions = self._parse_llm_response(response)

        # Update statistics
        confirmed = sum(1 for d in decisions if d.is_chapter)
        logger.info(f"LLM confirmed {confirmed}/{len(candidates)} as real chapters")

        return decisions

    def infer_chapter_structure(
        self,
        content: str,
        max_length: int = 10000,
        language: str = 'chinese'
    ) -> List[Dict]:
        """
        Infer chapter structure for text without obvious chapter markers

        :param content: Text content
        :param max_length: Maximum analysis length
        :param language: Document language
        :return: Suggested chapter structure
        """
        logger.info(f"LLM inferring structure, text length: {len(content)} characters...")

        # Extract analysis sample
        sample = content[:max_length]

        prompt = f"""You are a document structure analysis expert. The following text lacks clear chapter markers; please analyze and suggest chapter divisions.

【Text Sample】({len(sample)} characters)
{sample}

【Language】{language}

【Task】
1. Identify topic transition points in the content
2. Suggest chapter division positions
3. Generate a title for each chapter

Output JSON format:
{{
  "suggested_chapters": [
    {{
      "start_char": 0,
      "end_char": 500,
      "title": "Suggested title",
      "reason": "Basis for division",
      "confidence": 0.85
    }}
  ],
  "format_analysis": "Analysis of format characteristics",
  "confidence": 0.8
}}
"""

        response = self._call_llm(prompt, max_tokens=128000)
        result = self._parse_structure_response(response)

        logger.info(f"LLM suggested {len(result)} chapters")
        return result

    def disambiguate_reference(
        self,
        text_snippet: str,
        candidate: str,
        context: Dict
    ) -> Dict:
        """
        Disambiguate: determine if chapter title or text reference (supports Chinese and English)

        :param text_snippet: Text snippet containing candidate
        :param candidate: Candidate chapter text
        :param context: Context information
        :return: Decision dictionary
        """
        logger.debug(f"LLM disambiguation: {candidate}")

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
            prompt = f"""Determine whether this is a chapter title or a reference in the following Chinese text?

【Text Snippet】
{text_snippet}

【Context】
- Previous Chapter: {context.get('prev_chapter', 'N/A')}
- Document Type: {context.get('doc_type', 'Unknown')}
- Language: Chinese

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

        response = self._call_llm(prompt, max_tokens=128000)

        # Handle empty response
        if not response or not response.strip():
            logger.warning("LLM returned empty response (disambiguation)")
            return {
                'type': 'reference',
                'confidence': 0.5,
                'reason': 'LLM could not provide clear judgment'
            }

        try:
            result = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed (disambiguation): {e}")
            return {
                'type': 'reference',
                'confidence': 0.5,
                'reason': 'Parsing failed, conservatively judging as reference'
            }

        logger.debug(f"Decision: {result['type']} (confidence: {result['confidence']})")
        return result

    def identify_table_of_contents(
        self,
        content_sample: str,
        language: str = 'chinese'
    ) -> Dict:
        """
        Identify if text contains table of contents page and return TOC location range

        :param content_sample: Text sample (first 1000 lines or more)
        :param language: Language type
        :return: TOC identification result
        """
        logger.info("LLM identifying table of contents page...")

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
            prompt = f"""You are a document structure analysis expert. Please identify whether the following text contains a table of contents page.

【Text Sample】(first 3000 characters)
{content_sample[:3000]}

【Task】
Carefully analyze if there is a table of contents page, even **without explicit "Contents" or "CONTENTS" labels**.

【Key Characteristics of Table of Contents】
1. **High density of chapter patterns**: Multiple lines containing "Chapter X", "Part X" patterns
2. **Consecutive short lines**: Line content is brief (usually < 80 characters), only chapter names
3. **Page number markers**: Numbers at end of lines (e.g., "Chapter 1 Beginning ... 15")
4. **Lack of narrative content**: No story text, just titles and numbers
5. **Early position**: Usually at document beginning (first 100-500 lines)
6. **Consistent format**: All entries follow similar format

【Important Notes】
- Table of contents may not have the word "contents"
- Focus on structural patterns, not keywords
- Look for 5 or more consecutive chapter-style entries

【Output Format】JSON:
{{
  "has_toc": true/false,
  "confidence": 0.0-1.0,
  "start_indicator": "Description of where TOC starts (e.g., 'line 5' or 'after preface')",
  "end_indicator": "Description of where TOC ends (e.g., 'line 45' or 'before first long paragraph')",
  "reason": "Detailed explanation of reasoning (mention specific patterns observed)",
  "toc_entries_count": Estimated number of TOC entries,
  "key_evidence": ["evidence 1", "evidence 2", "evidence 3"]
}}
"""

        response = self._call_llm(prompt, max_tokens=128000, temperature=0.1)

        # Handle empty response
        if not response or not response.strip():
            logger.warning("LLM returned empty response (TOC identification)")
            return {
                'has_toc': False,
                'confidence': 0.0,
                'reason': 'LLM could not provide judgment'
            }

        try:
            result = json.loads(response)
            logger.info(f"TOC identification result: {'Found TOC' if result.get('has_toc') else 'No TOC'} "
                       f"(confidence: {result.get('confidence', 0):.2f})")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed (TOC identification): {e}")
            return {
                'has_toc': False,
                'confidence': 0.0,
                'reason': 'Parsing failed',
                'error': str(e)
            }

    def identify_special_format(
        self,
        content_sample: str,
        observed_patterns: List[str]
    ) -> Dict:
        """
        Identify chapter patterns for books with special formats

        :param content_sample: Text sample
        :param observed_patterns: Observed patterns
        :return: Format identification result
        """
        logger.info("LLM identifying special format...")

        patterns_text = "\n".join(f"- {p}" for p in observed_patterns)

        prompt = f"""This is a book with a special format. Please help identify its chapter structure.

【Text Sample】
{content_sample[:2000]}

【Observed Patterns】
{patterns_text}

Please analyze:
1. What chapter marking method does this book use?
2. How to identify chapter boundaries?
3. Suggested regular expression

Output JSON:
{{
  "format_type": "Format type",
  "chapter_pattern": "Pattern description",
  "identification_rules": ["Rule 1", "Rule 2"],
  "sample_chapters": [{{"title": "...", "position": 0}}],
  "confidence": 0.8,
  "suggested_regex": "Regular expression"
}}
"""

        response = self._call_llm(prompt, max_tokens=128000)

        # Debug: print raw response
        logger.debug(f"LLM raw response: {response}")

        # Handle empty response
        if not response or not response.strip():
            logger.warning("LLM returned empty response")
            return {
                'format_type': 'unknown',
                'chapter_pattern': 'unknown',
                'confidence': 0.0,
                'suggested_regex': None
            }

        try:
            result = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}, raw response: {response[:200]}")
            # Return default result
            return {
                'format_type': 'parse_error',
                'chapter_pattern': 'unknown',
                'confidence': 0.0,
                'suggested_regex': None,
                'error': str(e)
            }

        logger.info(f"Identified format: {result.get('format_type', 'unknown')}")
        return result

    def generate_chapter_title(
        self,
        chapter_number: str,
        chapter_content: str,
        language: str = 'chinese',
        max_content_length: int = 400
    ) -> Dict:
        """
        Use LLM to generate appropriate chapter title based on chapter content

        :param chapter_number: Chapter number (e.g., "Chapter 007", "Chapter 7")
        :param chapter_content: Chapter content (beginning portion)
        :param language: Language type
        :param max_content_length: Maximum content length for analysis (default 400 characters, about 200 Chinese characters)
        :return: Dictionary containing generated title
        """
        logger.info(f"LLM generating chapter title: {chapter_number}")

        # Limit content length - reduced to 400 characters to improve speed
        content_sample = chapter_content[:max_content_length].strip()

        if language == 'english':
            # Simplified English prompt
            prompt = f"""Generate a 3-8 word chapter title for: {chapter_number}

Content: {content_sample}

Requirements: Concise, meaningful, avoid dialogue quotes.

JSON response:
{{"title": "title text", "confidence": 0.0-1.0}}"""
        else:
            # Simplified Chinese prompt
            prompt = f"""Generate a 3-12 character title for the chapter: {chapter_number}

Content: {content_sample}

Requirements: Concise and meaningful, avoid dialogue quotes.

JSON format:
{{"title": "title", "confidence": 0.0-1.0}}"""

        try:
            response = self._call_llm(prompt, temperature=0.3, max_tokens=100)
            result = json.loads(response)

            # Validate result
            if 'title' not in result:
                logger.warning("LLM response missing 'title' field")
                result['title'] = ""

            if 'confidence' not in result:
                result['confidence'] = 0.5

            logger.info(f"✓ Generated title: {result.get('title', 'N/A')} (confidence: {result.get('confidence', 0):.2f})")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed (title generation): {e}, raw response: {response[:200] if 'response' in locals() else 'N/A'}")
            return {
                'title': "",
                'confidence': 0.0,
                'reason': f'Parsing failed: {str(e)}',
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Title generation failed: {e}")
            return {
                'title': "",
                'confidence': 0.0,
                'reason': f'Generation failed: {str(e)}',
                'error': str(e)
            }

    def generate_chapter_titles_batch(
        self,
        chapters_info: List[Dict[str, str]],
        language: str = 'chinese',
        max_content_length: int = 400
    ) -> List[Dict]:
        """
        Batch generate chapter titles (process multiple chapters in one LLM call)

        :param chapters_info: List of chapter information, each item contains {"number": "Chapter X", "content": "content..."}
        :param language: Language type
        :param max_content_length: Maximum content length for analysis per chapter
        :return: List of title results, each item contains {"title": "title", "confidence": 0.9}
        """
        if not chapters_info:
            return []

        logger.info(f"LLM batch generating {len(chapters_info)} chapter titles...")

        # Limit batch size to avoid exceeding token limit
        batch_size = 50  # Process up to 50 chapters at a time
        all_results = []

        for batch_start in range(0, len(chapters_info), batch_size):
            batch = chapters_info[batch_start:batch_start + batch_size]

            # Build batch chapter list
            chapters_text = []
            for i, ch_info in enumerate(batch, start=batch_start + 1):
                content_sample = ch_info['content'][:max_content_length].strip()
                chapters_text.append(f"{i}. {ch_info['number']}\nContent: {content_sample[:200]}...")

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
                prompt = f"""Generate concise titles (3-12 characters) for the following chapters based on their content:

{chapters_list}

Requirements:
- Title should be meaningful and reflect the content
- Avoid dialogue quotes
- Keep titles concise

JSON format:
{{
  "titles": [
    {{"index": 1, "title": "generated title", "confidence": 0.0-1.0}},
    {{"index": 2, "title": "generated title", "confidence": 0.0-1.0}}
  ]
}}"""

            try:
                response = self._call_llm(prompt, temperature=0.3, max_tokens=2000)
                result = json.loads(response)

                # Parse results
                titles = result.get('titles', [])

                # Create index-to-result mapping
                title_map = {item['index']: item for item in titles}

                # Return results in original order
                for i, ch_info in enumerate(batch, start=batch_start + 1):
                    if i in title_map:
                        all_results.append(title_map[i])
                    else:
                        # If LLM didn't return title for this chapter, use default value
                        all_results.append({
                            'index': i,
                            'title': "",
                            'confidence': 0.0
                        })

                logger.info(f"✓ Batch generation complete: {len(titles)}/{len(batch)} titles")

            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed (batch title generation): {e}")
                # Return empty results
                for i in range(len(batch)):
                    all_results.append({
                        'index': batch_start + i + 1,
                        'title': "",
                        'confidence': 0.0,
                        'error': str(e)
                    })
            except Exception as e:
                logger.error(f"Batch title generation failed: {e}")
                for i in range(len(batch)):
                    all_results.append({
                        'index': batch_start + i + 1,
                        'title': "",
                        'confidence': 0.0,
                        'error': str(e)
                    })

        logger.info(f"Batch title generation complete: total {len(all_results)} chapters")
        return all_results


    def _build_chapter_analysis_prompt(
        self,
        candidates: List[ChapterCandidate],
        full_content: str,
        existing_chapters: List[Dict],
        doc_context: Dict = None
    ) -> str:
        """Build chapter analysis prompt (supports Chinese and English)"""

        doc_context = doc_context or {}
        language = doc_context.get('language', 'chinese')

        # Calculate average chapter length
        if existing_chapters:
            avg_length = sum(ch.get('length', 0) for ch in existing_chapters) / len(existing_chapters)
        else:
            avg_length = 0

        # Select prompt template based on language
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
        """Build Chinese chapter analysis prompt"""

        # Format candidates
        candidates_text = []
        for i, c in enumerate(candidates, 1):
            issues_text = f" [Issues: {', '.join(c.issues)}]" if c.issues else ""
            candidates_text.append(
                f"{i}. \"{c.text}\" (Line {c.line_number}, "
                f"Confidence:{c.confidence:.2f}, Type:{c.pattern_type}){issues_text}"
            )

        # Extract context for each candidate
        contexts = []
        for i, c in enumerate(candidates, 1):
            context = f"""
【Candidate {i} Context】
Before: ...{c.context_before}
>>> {c.text} <<<
After: {c.context_after}..."""
            contexts.append(context)

        # Confirmed chapter examples
        chapter_examples = []
        for ch in existing_chapters[:5]:
            chapter_examples.append(f"- {ch.get('title', 'Unknown')}")

        prompt = f"""You are a document structure analysis expert. Please determine whether the following candidates are genuine chapter titles.

【Document Information】
- Document Type: {doc_context.get('doc_type', 'Unknown')}
- Language: Chinese
- Identified Chapters: {len(existing_chapters)}
- Average Chapter Length: {avg_length:.0f} characters

【Confirmed Chapter Examples】
{chr(10).join(chapter_examples) if chapter_examples else 'None yet'}

【Candidates to Judge】
{chr(10).join(candidates_text)}

{chr(10).join(contexts)}

【Judgment Criteria】
1. ✓ Standalone on its own line
2. ✓ Properly separated before and after
3. ✓ Not embedded in sentence grammar structure
4. ✓ Format consistent with identified chapters
5. ✗ Located in middle of sentence
6. ✗ Preceded by reference words like "in/as/see"
7. ✗ Followed by connectors like "in/inside/at the end of"

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

    def _build_english_prompt(
        self,
        candidates: List[ChapterCandidate],
        existing_chapters: List[Dict],
        avg_length: float,
        doc_context: Dict
    ) -> str:
        """Build English chapter analysis prompt"""

        # Format candidates
        candidates_text = []
        for i, c in enumerate(candidates, 1):
            issues_text = f" [Issues: {', '.join(c.issues)}]" if c.issues else ""
            candidates_text.append(
                f"{i}. \"{c.text}\" (Line {c.line_number}, "
                f"Confidence:{c.confidence:.2f}, Type:{c.pattern_type}){issues_text}"
            )

        # Extract context for each candidate
        contexts = []
        for i, c in enumerate(candidates, 1):
            context = f"""
【Candidate {i} Context】
Before: ...{c.context_before}
>>> {c.text} <<<
After: {c.context_after}..."""
            contexts.append(context)

        # Confirmed chapter examples
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
        Call LLM API

        :param prompt: Prompt text
        :param max_tokens: Maximum token count
        :param temperature: Temperature parameter (0-2, lower means more deterministic)
        :return: LLM response text
        """
        try:
            self.stats['total_calls'] += 1

            # Build messages
            messages = [
                {
                    "role": "system",
                    "content": "You are a professional document structure analysis assistant, skilled at identifying chapters and table of contents structure. Please always return results in JSON format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            # Determine actual max_tokens to use
            actual_max_tokens = max_tokens or self.max_tokens

            # If max_tokens > 5000, must use stream=True
            use_streaming = actual_max_tokens > 5000

            if use_streaming:
                # Use streaming call
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=actual_max_tokens,
                    temperature=temperature,
                    response_format={"type": "json_object"},
                    stream=True
                )

                # Collect streaming response
                content = ""
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content += chunk.choices[0].delta.content

                # Note: streaming response has no usage info, use estimated values
                # Rough estimate: 1 token ≈ 4 characters for Chinese, 1.3 for English
                estimated_prompt_tokens = len(prompt) // 3
                estimated_completion_tokens = len(content) // 3

                self.stats['total_input_tokens'] += estimated_prompt_tokens
                self.stats['total_output_tokens'] += estimated_completion_tokens

                logger.debug(f"LLM streaming call successful: ~{estimated_prompt_tokens} in + ~{estimated_completion_tokens} out tokens (estimated)")

            else:
                # Use non-streaming call
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=actual_max_tokens,
                    temperature=temperature,
                    response_format={"type": "json_object"}
                )

                # Extract response text
                content = response.choices[0].message.content

                # Update statistics
                usage = response.usage
                self.stats['total_input_tokens'] += usage.prompt_tokens
                self.stats['total_output_tokens'] += usage.completion_tokens

                # Calculate cost
                model_key = self.model
                if model_key not in self.pricing:
                    # Try matching prefix
                    for key in self.pricing:
                        if self.model.startswith(key):
                            model_key = key
                            break

                if model_key in self.pricing:
                    pricing = self.pricing[model_key]
                    input_cost = usage.prompt_tokens * pricing['input'] / 1000
                    output_cost = usage.completion_tokens * pricing['output'] / 1000
                    self.stats['total_cost'] += input_cost + output_cost

                logger.debug(f"LLM call successful: {usage.prompt_tokens} in + {usage.completion_tokens} out tokens")

            return content

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    def _parse_llm_response(self, response: str) -> List[LLMDecision]:
        """Parse LLM JSON response"""
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
            logger.error(f"Failed to parse LLM response: {e}")
            logger.debug(f"Response content: {response}")
            return []

    def _parse_structure_response(self, response: str) -> List[Dict]:
        """Parse structure inference response"""
        try:
            data = json.loads(response)
            return data.get('suggested_chapters', [])
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse structure response: {e}")
            return []

    def get_stats(self) -> Dict:
        """Get usage statistics"""
        return self.stats.copy()

    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            'total_calls': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_cost': 0.0
        }


# ==================== Usage Examples ====================

def example_usage():
    """Usage examples"""

    # Example 1: Basic usage
    print("=== Example 1: Basic Usage ===")
    assistant = LLMParserAssistant(
        api_key="your-api-key",
        model="gpt-3.5-turbo"  # Use economical model
    )

    # Create test candidates
    candidates = [
        ChapterCandidate(
            text="Chapter 1 Beginning",
            position=0,
            line_number=1,
            confidence=0.95,
            context_before="",
            context_after="This is the content of chapter 1...",
            pattern_type="standard"
        ),
        ChapterCandidate(
            text="In chapter 2",
            position=100,
            line_number=10,
            confidence=0.45,
            context_before="As mentioned earlier,",
            context_after="we will discuss in detail...",
            pattern_type="ambiguous",
            issues=["Suspected reference"]
        )
    ]

    # Analyze chapter candidates
    decisions = assistant.analyze_chapter_candidates(
        candidates=candidates,
        full_content="Complete text...",
        existing_chapters=[],
        doc_context={'language': 'chinese'}
    )

    for i, decision in enumerate(decisions):
        print(f"Candidate {i+1}: {decision.is_chapter}, confidence: {decision.confidence}")
        print(f"  Reason: {decision.reason}")

    # View statistics
    stats = assistant.get_stats()
    print(f"\nStatistics: {stats['total_calls']} calls, ${stats['total_cost']:.4f} cost")

    # Example 2: Hybrid parser
    print("\n=== Example 2: Hybrid Parser ===")
    parser = HybridParser(
        llm_api_key="your-api-key",
        llm_model="gpt-3.5-turbo"
    )

    content = """
Chapter 1 Beginning
This is the content of chapter 1.

Chapter 2 Continuing
This is the content of chapter 2.
"""

    volumes = parser.parse(content)
    print(f"Parse result: {len(volumes)} volumes")


class RuleBasedParserWithConfidence:
    """Rule-based parser with confidence scoring"""

    def __init__(self, config=None):
        """
        Initialize rule parser

        :param config: ParserConfig instance
        """
        from .parser_config import ParserConfig, DEFAULT_CONFIG
        self.config = config or DEFAULT_CONFIG

    def parse_with_confidence(self, content: str, skip_toc_removal: bool = False, context=None, resume_state=None) -> Dict:
        """
        Parse content and return confidence

        :param content: Text content
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

        # Use existing parser, pass resume_state parameter
        volumes = parse_hierarchical_content(content, self.config, llm_assistant=None, skip_toc_removal=skip_toc_removal, context=context, resume_state=resume_state)

        # Detect language
        language = detect_language(content)

        # Calculate confidence for each chapter
        chapters_with_confidence = []
        uncertain_regions = []

        for volume in volumes:
            for chapter in volume.chapters:
                # Calculate confidence
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
        """Estimate chapter confidence"""
        import re

        score = 0.6  # Base score

        # Factor 1: Title length
        title_len = len(chapter.title)
        if 5 <= title_len <= 30:
            score += 0.15
        elif title_len < 5 or title_len > 50:
            score -= 0.1

        # Factor 2: Content length
        total_length = len(chapter.content) + sum(len(s.content) for s in chapter.sections)
        if 500 <= total_length <= 50000:
            score += 0.15
        elif total_length < 100:
            score -= 0.2

        # Factor 3: Title format
        if language == 'chinese':
            if re.match(r'第[一二三四五六七八九十百千万\d]+章', chapter.title):
                score += 0.1  # Standard format
        else:
            if re.match(r'Chapter\s+[\dIVXivx]+', chapter.title, re.IGNORECASE):
                score += 0.1

        # Factor 4: Position check (simplified)
        position = content.find(chapter.title)
        if position > 0:
            before = content[max(0, position-20):position]
            if re.search(r'[在如见]第', before):
                score -= 0.3  # Suspected reference

        return max(0.0, min(1.0, score))


class HybridParser:
    """Hybrid parser: Rule-based + LLM"""

    def __init__(
        self,
        llm_api_key: str = None,
        llm_base_url: str = None,
        llm_model: str = "deepseek-v3.2",
        config = None
    ):
        """
        Initialize hybrid parser

        :param llm_api_key: LLM API key
        :param llm_base_url: LLM API base URL
        :param llm_model: Model to use
        :param config: Parser configuration
        """
        from .parser_config import ParserConfig, DEFAULT_CONFIG

        self.config = config or DEFAULT_CONFIG
        self.rule_parser = RuleBasedParserWithConfidence(self.config)

        # If LLM assistance is enabled, initialize LLM assistant
        self.llm_assistant = None
        if self.config.enable_llm_assistance or llm_api_key:
            self.llm_assistant = LLMParserAssistant(
                api_key=llm_api_key or self.config.llm_api_key,
                base_url=llm_base_url or self.config.llm_base_url,
                model=llm_model or self.config.llm_model
            )

    def parse(self, content: str, skip_toc_removal: bool = False, context=None, resume_state=None):
        """
        Hybrid parsing workflow

        :param content: Text content
        :param skip_toc_removal: If True, skip TOC removal (useful when content already processed)
        :param context: Context object for progress reporting
        :param resume_state: Resume state for checkpoint resume
        :return: List of volumes
        """
        from .parser import detect_language

        # Stage 0: Use LLM to identify and remove table of contents page
        if self.llm_assistant:
            logger.info("Stage 0: LLM identifying table of contents page...")

        # Stage 1: Rule-based parsing + confidence scoring (with LLM assistant for TOC identification)
        logger.info("Stage 1: Rule-based parsing...")

        # 【Fix】Only call rule parsing once, directly use parse_with_confidence result
        rule_result = self.rule_parser.parse_with_confidence(content, skip_toc_removal=skip_toc_removal, context=context)
        volumes = rule_result['volumes']
        confidence = rule_result['overall_confidence']
        threshold = self.config.llm_confidence_threshold
        logger.debug(f"Rule parsing confidence: {confidence:.2f}, threshold: {threshold:.2f}")

        # If overall confidence is high, return directly
        if confidence >= threshold:
            logger.info(f"High confidence ({confidence:.2f} >= {threshold:.2f}), skipping chapter-level LLM assistance")
            logger.info(f"Parsing complete: {len(volumes)} volumes")
            return volumes

        logger.info(f"Confidence < threshold, LLM assistance needed for chapter identification")

        # Stage 2: Identify regions requiring LLM
        uncertain_regions = rule_result.get('uncertain_regions', [])
        chapters = rule_result.get('chapters', [])

        logger.debug(f"Rule parsing identified {len(chapters)} chapters")

        if uncertain_regions and self.llm_assistant:
            logger.info(f"Stage 2: LLM assisting with {len(uncertain_regions)} uncertain regions...")

            # Convert to candidate format
            candidates = self._convert_to_candidates(uncertain_regions, content)

            # LLM analysis
            llm_decisions = self.llm_assistant.analyze_chapter_candidates(
                candidates,
                content,
                rule_result['chapters'],
                {'language': detect_language(content), 'doc_type': 'Novel'}
            )

            logger.debug(f"LLM decision results: processed {len(llm_decisions)} candidates")

            # Stage 3: Merge results
            logger.info("Stage 3: Merging results...")
            final_volumes = self._merge_results(
                volumes,
                llm_decisions,
                candidates
            )

            # Output statistics
            stats = self.llm_assistant.get_stats()
            logger.info(f"LLM statistics: {stats['total_calls']} calls, ${stats['total_cost']:.4f} cost")

            return final_volumes

        # No LLM needed or client not provided
        return volumes

    def _convert_to_candidates(
        self,
        uncertain_regions: List[Dict],
        content: str
    ) -> List[ChapterCandidate]:
        """Convert to candidate format"""
        candidates = []

        for region in uncertain_regions:
            chapter = region['chapter']
            confidence = region['confidence']

            # Find position in content
            position = content.find(chapter.title)
            if position == -1:
                continue

            # Extract context
            context_size = 200
            context_before = content[max(0, position-context_size):position]
            context_after = content[position+len(chapter.title):position+len(chapter.title)+context_size]

            # Calculate line number
            line_number = content[:position].count('\n') + 1

            # Determine issues
            issues = []
            if confidence < 0.5:
                issues.append("Extremely low confidence")
            elif confidence < 0.7:
                issues.append("Low confidence")

            if "第" in chapter.title and ("在" in context_before[-10:] or "如" in context_before[-10:]):
                issues.append("Suspected reference")

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
        """Merge rule-based and LLM results"""
        from .data_structures import Volume, Chapter

        # Create decision mapping
        decision_map = {
            candidates[i].text: llm_decisions[i]
            for i in range(min(len(candidates), len(llm_decisions)))
        }

        # Process each volume
        new_volumes = []
        for volume in rule_volumes:
            new_chapters = []

            for chapter in volume.chapters:
                decision = decision_map.get(chapter.title)

                if decision:
                    if decision.is_chapter:
                        # LLM confirmed as chapter
                        if decision.suggested_title:
                            # Use suggested title
                            new_chapter = Chapter(
                                title=decision.suggested_title,
                                content=chapter.content,
                                sections=chapter.sections
                            )
                            new_chapters.append(new_chapter)
                        else:
                            new_chapters.append(chapter)
                    else:
                        # LLM rejected, do not add
                        logger.info(f"LLM rejected chapter: {chapter.title}")
                else:
                    # No LLM decision, keep original result
                    new_chapters.append(chapter)

            if new_chapters:
                new_volumes.append(Volume(
                    title=volume.title,
                    chapters=new_chapters
                ))

        return new_volumes

    def get_stats(self) -> Dict:
        """Get LLM usage statistics"""
        if self.llm_assistant:
            return self.llm_assistant.get_stats()
        return {
            'total_calls': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_cost': 0.0
        }


if __name__ == "__main__":
    # Run examples (requires API key setup)
    # example_usage()
    pass
