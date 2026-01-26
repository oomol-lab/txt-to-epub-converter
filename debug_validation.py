#!/usr/bin/env python3
"""详细分析第二章为什么通过了验证"""

import re
from src.txt_to_epub.parser.validator import is_valid_chapter_title

# 读取文件
with open('qm.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找所有"第二章"的匹配
pattern = r'第二章[^\r\n]*'
matches = list(re.finditer(pattern, content))

print(f"找到 {len(matches)} 个'第二章'匹配\n")

for i, match in enumerate(matches[:5], 1):
    match_start = match.start()
    match_end = match.end()
    match_text = match.group(0)
    line_num = content[:match_start].count('\n') + 1

    print(f"=== 匹配 {i}: 位置 {match_start} (第{line_num}行) ===")
    print(f"标题: {match_text}")

    # 显示前后文
    context_start = max(0, match_start - 100)
    context_end = min(len(content), match_end + 200)
    context = content[context_start:context_end]

    print(f"\n前后文:\n{context}\n")

    # 测试验证
    is_valid = is_valid_chapter_title(match, content)
    print(f"验证结果: {'✅ 通过' if is_valid else '❌ 拒绝'}\n")
    print("-" * 80 + "\n")
