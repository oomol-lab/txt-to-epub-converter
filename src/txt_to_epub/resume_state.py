"""
断点续传状态管理模块
"""
import json
import os
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime


class ResumeState:
    """断点续传状态管理器"""

    def __init__(self, state_file: str):
        """
        初始化状态管理器

        :param state_file: 状态文件路径
        """
        self.state_file = state_file
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """加载状态文件"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load state file: {e}")
                return self._create_empty_state()
        return self._create_empty_state()

    def _create_empty_state(self) -> Dict[str, Any]:
        """创建空状态"""
        return {
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'source_file_hash': None,
            'processed_chapters': [],
            'current_chapter_index': 0,
            'total_chapters': 0,
            'completed': False,
            'metadata': {}
        }

    def save_state(self):
        """保存状态到文件"""
        self.state['updated_at'] = datetime.now().isoformat()
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save state file: {e}")

    def set_source_hash(self, file_path: str):
        """设置源文件哈希值"""
        self.state['source_file_hash'] = self._calculate_file_hash(file_path)

    def verify_source_file(self, file_path: str) -> bool:
        """验证源文件是否与之前一致"""
        if not self.state.get('source_file_hash'):
            return False
        current_hash = self._calculate_file_hash(file_path)
        return current_hash == self.state['source_file_hash']

    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希值"""
        hasher = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            print(f"Warning: Failed to calculate file hash: {e}")
            return ""

    def set_total_chapters(self, total: int):
        """设置总章节数"""
        self.state['total_chapters'] = total

    def mark_chapter_processed(self, chapter_title: str):
        """标记章节已处理"""
        if chapter_title not in self.state['processed_chapters']:
            self.state['processed_chapters'].append(chapter_title)
            self.state['current_chapter_index'] = len(self.state['processed_chapters'])
            self.save_state()

    def is_chapter_processed(self, chapter_title: str) -> bool:
        """检查章节是否已处理"""
        return chapter_title in self.state['processed_chapters']

    def get_processed_count(self) -> int:
        """获取已处理章节数"""
        return len(self.state['processed_chapters'])

    def get_current_index(self) -> int:
        """获取当前处理索引"""
        return self.state.get('current_chapter_index', 0)

    def mark_completed(self):
        """标记转换完成"""
        self.state['completed'] = True
        self.save_state()

    def is_completed(self) -> bool:
        """检查是否已完成"""
        return self.state.get('completed', False)

    def set_metadata(self, key: str, value: Any):
        """设置元数据"""
        self.state['metadata'][key] = value
        self.save_state()

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        return self.state['metadata'].get(key, default)

    def reset(self):
        """重置状态"""
        self.state = self._create_empty_state()
        self.save_state()

    def cleanup(self):
        """清理状态文件"""
        if os.path.exists(self.state_file):
            try:
                os.remove(self.state_file)
            except Exception as e:
                print(f"Warning: Failed to cleanup state file: {e}")


def get_state_file_path(txt_file: str, epub_dir: str) -> str:
    """
    生成状态文件路径

    :param txt_file: 源文本文件路径
    :param epub_dir: EPUB输出目录
    :return: 状态文件路径
    """
    # 使用源文件名生成状态文件名
    basename = os.path.basename(txt_file)
    name_without_ext = os.path.splitext(basename)[0]
    state_filename = f".{name_without_ext}_resume.json"
    return os.path.join(epub_dir, state_filename)
