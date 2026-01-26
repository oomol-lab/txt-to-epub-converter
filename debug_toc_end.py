#!/usr/bin/env python3
"""调试：为什么第一章被误删"""

import re
from src.txt_to_epub.parser.patterns import ChinesePatterns

# 读取文件
with open('qm.txt', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
patterns = ChinesePatterns()
chapter_patterns = [patterns.CHAPTER_PATTERN, patterns.VOLUME_PATTERN]

# 检查第287-295行
print("=== 检查第287-295行 ===\n")
for i in range(286, min(295, len(lines))):
    line = lines[i]
    stripped = line.strip()

    # 检查是否匹配章节模式
    is_chapter = any(p.search(stripped) for p in chapter_patterns)

    print(f"第{i+1}行 (长度:{len(stripped):3d}) 章节:{is_chapter}")
    print(f"  内容: {stripped[:80]}")
    print()

# 特别检查第289-292行的逻辑
print("\n=== 模拟TOC结束检测逻辑（从第289行开始）===\n")
i = 288  # 第289行（索引288）
stripped_line = lines[i].strip()
print(f"当前行{i+1}: {stripped_line}")
print(f"是否为空: {not stripped_line}")
print()

# 模拟检测下一行
if not stripped_line:
    next_content_idx = -1
    for j in range(i + 1, min(i + 5, len(lines))):
        if lines[j].strip():
            next_content_idx = j
            break

    if next_content_idx != -1:
        next_line = lines[next_content_idx].strip()
        print(f"下一行{next_content_idx+1}: {next_line[:60]}...")
        print(f"长度: {len(next_line)}")

        is_chapter = any(p.search(next_line) for p in chapter_patterns)
        is_preface = any(kw.lower() == next_line.lower() for kw in patterns.PREFACE_KEYWORDS)

        print(f"是章节标题: {is_chapter}")
        print(f"是序言: {is_preface}")
        print(f"\n应该停止TOC: {not is_chapter or is_preface}")

# 检查第290行
print("\n\n=== 检查第290行（空行）===\n")
i = 289  # 第290行
stripped_line = lines[i].strip()
print(f"第{i+1}行是否为空: {not stripped_line}")

if not stripped_line:
    # 查找下一个内容
    next_content_idx = -1
    for j in range(i + 1, min(i + 5, len(lines))):
        if lines[j].strip():
            next_content_idx = j
            break

    if next_content_idx != -1:
        next_line = lines[next_content_idx].strip()
        print(f"\n下一个非空行是第{next_content_idx+1}行:")
        print(f"内容: {next_line[:80]}...")
        print(f"长度: {len(next_line)}")

        is_chapter = any(p.search(next_line) for p in chapter_patterns)
        is_preface = any(kw.lower() == next_line.lower() for kw in patterns.PREFACE_KEYWORDS)

        print(f"是章节标题: {is_chapter}")
        print(f"是序言: {is_preface}")
        print(f"\n✅ 应该在第{i+1}行结束TOC: {len(next_line) > 50 and (not is_chapter or is_preface)}")
