#!/usr/bin/env python3
"""检查解析后章节的顺序和位置"""

from src.txt_to_epub.parser.core import parse_chapters_from_content

# 读取文件
with open('qm.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# 解析章节
chapters = parse_chapters_from_content(content)

print(f"✅ 总章节数: {len(chapters)}\n")

# 检查前20章的标题和在原文件中的位置
print("前20章的标题和出现位置：\n")
for i, chapter in enumerate(chapters[:20], 1):
    # 找到章节标题在原文中第一次出现的位置
    title = chapter.title
    char_pos = content.find(title)
    # 计算行号（粗略估计）
    line_num = content[:char_pos].count('\n') + 1 if char_pos >= 0 else -1

    print(f"{i:3d}. 位置:{char_pos:7d} (约第{line_num}行) - {title}")

# 特别检查第一章、第二章、第三章的位置
print("\n=== 关键章节检查 ===")
chapter_map = {}
for idx, chapter in enumerate(chapters):
    title = chapter.title
    if '第一章' in title:
        char_pos = content.find(title)
        chapter_map['第一章'] = (idx + 1, char_pos)
    elif '第二章' in title:
        char_pos = content.find(title)
        chapter_map['第二章'] = (idx + 1, char_pos)
    elif '第三章' in title:
        char_pos = content.find(title)
        chapter_map['第三章'] = (idx + 1, char_pos)
    elif '第九十三章' in title:
        char_pos = content.find(title)
        chapter_map['第九十三章'] = (idx + 1, char_pos)

for ch_name in ['第一章', '第二章', '第三章', '第九十三章']:
    if ch_name in chapter_map:
        pos, char_pos = chapter_map[ch_name]
        line_num = content[:char_pos].count('\n') + 1 if char_pos >= 0 else -1
        print(f"{ch_name}: 在解析结果的第{pos}位，原文位置{char_pos}(约第{line_num}行)")
    else:
        print(f"{ch_name}: ❌ 未找到")
