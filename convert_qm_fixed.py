#!/usr/bin/env python3
"""重新转换qm.txt为EPUB（使用修复后的TOC移除功能）"""

import sys
sys.path.insert(0, 'src')

from txt_to_epub import txt_to_epub

def main():
    print("开始转换 qm.txt...")

    result = txt_to_epub(
        txt_file="qm.txt",
        epub_file="qm_fixed.epub",
        title="琼明神女录精修版",
        author="倒悬山剑气长存（改编：半步作者境）"
    )

    print(f"\n✅ 转换完成!")
    print(f"输出文件: {result['output_file']}")
    print(f"总字符数: {result['total_chars']}")
    print(f"检测到章节数: {result['chapter_count']}")
    print(f"\n验证报告:")
    print(result['validation_report'])

if __name__ == "__main__":
    main()
