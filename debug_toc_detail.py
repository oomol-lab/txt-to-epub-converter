#!/usr/bin/env python3
"""检查TOC移除了哪些内容"""

from src.txt_to_epub.parser.toc_remover import remove_table_of_contents
import logging

# 启用详细日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

# 读取文件
with open('qm.txt', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')

print("=== 原文第40-70行 ===")
for i in range(39, min(70, len(lines))):
    print(f"{i+1:3d}: {lines[i]}")

print("\n" + "="*80 + "\n")

# 执行TOC移除（带日志）
cleaned_content = remove_table_of_contents(content, language='chinese')

cleaned_lines = cleaned_content.split('\n')

print("\n=== 处理后第40-70行 ===")
for i in range(39, min(70, len(cleaned_lines))):
    print(f"{i+1:3d}: {cleaned_lines[i]}")
