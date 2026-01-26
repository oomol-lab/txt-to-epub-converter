#!/usr/bin/env python3
"""测试TOC移除功能"""

from src.txt_to_epub.parser.toc_remover import remove_table_of_contents

# 读取文件
with open('qm.txt', 'r', encoding='utf-8') as f:
    content = f.read()

print(f"原文件总字符数: {len(content)}")
print(f"原文件行数: {content.count(chr(10)) + 1}\n")

# 显示原文前60行
lines = content.split('\n')
print("=== 原文前60行 ===")
for i in range(min(60, len(lines))):
    print(f"{i+1:3d}: {lines[i][:80]}")

print("\n" + "="*80 + "\n")

# 执行TOC移除
cleaned_content = remove_table_of_contents(content, language='chinese')

print(f"\n处理后字符数: {len(cleaned_content)}")
print(f"处理后行数: {cleaned_content.count(chr(10)) + 1}")
print(f"移除了: {len(content) - len(cleaned_content)} 个字符\n")

# 显示处理后前30行
cleaned_lines = cleaned_content.split('\n')
print("=== 处理后前30行 ===")
for i in range(min(30, len(cleaned_lines))):
    print(f"{i+1:3d}: {cleaned_lines[i][:80]}")

# 检查"第二章"是否还在前面部分
second_chapter_pos = cleaned_content.find('第二章')
if second_chapter_pos >= 0:
    line_num = cleaned_content[:second_chapter_pos].count('\n') + 1
    print(f"\n'第二章'在处理后的第{line_num}行，字符位置{second_chapter_pos}")
else:
    print("\n'第二章'未找到")
