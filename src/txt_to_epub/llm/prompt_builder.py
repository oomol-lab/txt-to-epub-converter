"""
Prompt builder for LLM analysis
"""
from typing import List, Dict
from .data_structures import ChapterCandidate


class PromptBuilder:
    """Build prompts for LLM analysis"""

    @staticmethod
    def build_chapter_analysis_prompt(
        candidates: List[ChapterCandidate],
        existing_chapters: List[Dict],
        avg_length: float,
        doc_context: Dict
    ) -> str:
        """Build chapter analysis prompt"""

        language = doc_context.get('language', 'chinese')

        # Select prompt template based on language
        if language == 'english':
            return PromptBuilder._build_english_chapter_prompt(
                candidates, existing_chapters, avg_length, doc_context
            )
        else:
            return PromptBuilder._build_chinese_chapter_prompt(
                candidates, existing_chapters, avg_length, doc_context
            )

    @staticmethod
    def _build_chinese_chapter_prompt(
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

    @staticmethod
    def _build_english_chapter_prompt(
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
