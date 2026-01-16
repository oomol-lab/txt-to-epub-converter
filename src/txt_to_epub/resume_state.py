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

    def __init__(self, state_file: str, save_interval: int = 10):
        """
        初始化状态管理器

        :param state_file: 状态文件路径
        :param save_interval: 保存间隔（每处理N章保存一次，默认10）
        """
        self.state_file = state_file
        self.save_interval = save_interval
        self._dirty = False  # 标记是否有未保存的更改
        self._unsaved_count = 0  # 未保存的章节计数
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """加载状态文件"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    # 将列表转换回集合
                    if 'processed_chapter_indices' in state:
                        state['processed_chapter_indices'] = set(state['processed_chapter_indices'])
                    # 兼容旧版本：如果使用的是旧的 processed_chapters 列表
                    elif 'processed_chapters' in state:
                        # 迁移到新格式，但无法恢复索引，只能清空
                        state['processed_chapter_indices'] = set()
                        del state['processed_chapters']
                    return state
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
            'processed_chapter_indices': set(),  # 使用索引集合而非标题列表
            'current_chapter_index': 0,
            'total_chapters': 0,
            'completed': False,
            'metadata': {}
        }

    def save_state(self, force: bool = False):
        """
        保存状态到文件

        :param force: 强制保存，忽略保存间隔
        """
        self.state['updated_at'] = datetime.now().isoformat()

        # 将 set 转换为 list 用于 JSON 序列化
        state_to_save = self.state.copy()
        if isinstance(state_to_save.get('processed_chapter_indices'), set):
            state_to_save['processed_chapter_indices'] = list(state_to_save['processed_chapter_indices'])

        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state_to_save, f, ensure_ascii=False, indent=2)
            self._dirty = False
            self._unsaved_count = 0
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

    def mark_chapter_processed(self, chapter_index: int):
        """
        标记章节已处理（使用索引而非标题，避免重复标题问题）

        :param chapter_index: 章节索引（从0开始）
        """
        if chapter_index not in self.state['processed_chapter_indices']:
            self.state['processed_chapter_indices'].add(chapter_index)
            self.state['current_chapter_index'] = len(self.state['processed_chapter_indices'])
            self._dirty = True
            self._unsaved_count += 1

            # 每隔 save_interval 章或完成时保存
            if self._unsaved_count >= self.save_interval:
                self.save_state()

    def is_chapter_processed(self, chapter_index: int) -> bool:
        """
        检查章节是否已处理

        :param chapter_index: 章节索引（从0开始）
        :return: 是否已处理
        """
        return chapter_index in self.state['processed_chapter_indices']

    def get_processed_count(self) -> int:
        """获取已处理章节数"""
        return len(self.state['processed_chapter_indices'])

    def get_current_index(self) -> int:
        """获取当前处理索引"""
        return self.state.get('current_chapter_index', 0)

    def mark_completed(self):
        """标记转换完成"""
        self.state['completed'] = True
        self.save_state(force=True)  # 完成时强制保存

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
        self.save_state(force=True)

    def flush(self):
        """刷新：保存所有未保存的更改"""
        if self._dirty:
            self.save_state(force=True)

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
