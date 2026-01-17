#!/usr/bin/env python3
"""
Script to translate Chinese comments to English in Python source files.
This is a helper script for code maintenance.
"""

import re
import os
from pathlib import Path

# Mapping of Chinese comments to English translations
TRANSLATIONS = {
    # parser.py
    "# 移除常见的开头词汇": "# Remove common opening phrases",
    '# 移除"话说"、"且说"、"却说"等开头': "# Remove opening phrases like \"话说\", \"且说\", \"却说\"",
    "# 寻找第一个完整的句子": "# Find first complete sentence",
    "# 检查是否包含有意义的内容": "# Check if contains meaningful content",
    "# 截取前max_length个字符": "# Extract first max_length characters",
    "# 确保不以不完整词语结束": "# Ensure not ending with incomplete word",
    "# 尝试在标点或自然断点处结束": "# Try to end at punctuation or natural break point",
    "# 如果没有找到合适的句子，取前几个字符": "# If no suitable sentence found, take first few characters",
    "# 避免切断词语": "# Avoid cutting words",
    "# 寻找最后一个空格或标点": "# Find last space or punctuation",
    "# 英文处理": "# English processing",
    "# 包含有意义的词": "# Contains meaningful words",
    "# 在合适的位置截断": "# Truncate at appropriate position",
    "# 如果标题已经有实质内容，直接返回": "# If title already has substantial content, return directly",
    "# 提取章节号": "# Extract chapter number",
    "# 优先使用 LLM 生成标题": "# Prioritize using LLM to generate title",
    "# 如果 LLM 生成成功且置信度足够高": "# If LLM generation successful and confidence high enough",
    "# 组合章节号和生成的标题": "# Combine chapter number and generated title",
    "# 回退方案：从内容中提取有意义的标题": "# Fallback: extract meaningful title from content",
    "# 保留原始章节号，添加实质内容": "# Keep original chapter number, add substantial content",
    "# 如果无法提取有意义的内容，返回原始标题": "# If unable to extract meaningful content, return original title",
    '# 匹配只有"第X章"或"第X章 "的标题': "# Match titles with only \"第X章\" or \"第X章 \"",
    '# 如果标题长度小于等于5个字符,且包含"第"和"章",认为是简单标题': "# If title length is <= 5 characters and contains \"第\" and \"章\", consider it simple",
    "# 英文简单标题模式": "# English simple title patterns",
    "# 设置断点续传的总章节数": "# Set total chapter count for resume feature",
    "# 记录开始处理章节": "# Log start of chapter processing",
    "# 【优化】批量收集需要 LLM 增强的章节": "# [Optimization] Batch collect chapters needing LLM enhancement",
    "# 断点续传：跳过已处理的章节（使用索引）": "# Resume: skip processed chapters (using index)",
    "# 存储章节数据": "# Store chapter data",
    "# 收集需要增强的章节": "# Collect chapters needing enhancement",
    "# 提取章节号": "# Extract chapter number",
    "# 【优化】批量调用 LLM 生成标题": "# [Optimization] Batch call LLM to generate titles",
    "# 构建索引到标题的映射": "# Build index to title mapping",
    "# 处理所有章节，应用增强的标题": "# Process all chapters, apply enhanced titles",
    "# 计算并上报进度：5% 到 95% 之间（生成目录阶段占 90%）": "# Calculate and report progress: between 5% and 95% (TOC generation phase takes 90%)",
    "# 将章节处理进度映射到 5% - 95% 区间": "# Map chapter processing progress to 5% - 95% range",
    "# 打印进度": "# Print progress",
    "# 应用增强的标题（如果有）": "# Apply enhanced title (if available)",
    "# 如果没有 LLM，回退到规则提取": "# If no LLM, fall back to rule extraction",
    "# 断点续传：标记章节已处理（使用索引）": "# Resume: mark chapter as processed (using index)",
    "# 完成日志": "# Completion log",
}

def translate_file(file_path: Path):
    """Translate Chinese comments in a single file."""
    print(f"Processing {file_path}...")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Apply translations
    for chinese, english in TRANSLATIONS.items():
        content = content.replace(chinese, english)

    # Write back if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ Translated {file_path.name}")
    else:
        print(f"  - No changes needed for {file_path.name}")

def main():
    """Main function to translate all Python files."""
    src_dir = Path(__file__).parent / "src" / "txt_to_epub"

    python_files = list(src_dir.glob("*.py"))

    for file_path in python_files:
        translate_file(file_path)

    print(f"\n✓ Processed {len(python_files)} files")

if __name__ == "__main__":
    main()
