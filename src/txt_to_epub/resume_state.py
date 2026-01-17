"""
Resume state management module
"""
import json
import os
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime


class ResumeState:
    """Resume checkpoint state manager"""

    def __init__(self, state_file: str, save_interval: int = 10):
        """
        Initialize state manager

        :param state_file: State file path
        :param save_interval: Save interval (save every N chapters processed, default 10)
        """
        self.state_file = state_file
        self.save_interval = save_interval
        self._dirty = False  # Flag for unsaved changes
        self._unsaved_count = 0  # Counter for unsaved chapters
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """Load state file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    # Convert list back to set
                    if 'processed_chapter_indices' in state:
                        state['processed_chapter_indices'] = set(state['processed_chapter_indices'])
                    # Compatibility with old version: if using old processed_chapters list
                    elif 'processed_chapters' in state:
                        # Migrate to new format, but cannot recover indices, have to clear
                        state['processed_chapter_indices'] = set()
                        del state['processed_chapters']
                    return state
            except Exception as e:
                print(f"Warning: Failed to load state file: {e}")
                return self._create_empty_state()
        return self._create_empty_state()

    def _create_empty_state(self) -> Dict[str, Any]:
        """Create empty state"""
        return {
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'source_file_hash': None,
            'processed_chapter_indices': set(),  # Use index set instead of title list
            'current_chapter_index': 0,
            'total_chapters': 0,
            'completed': False,
            'metadata': {}
        }

    def save_state(self, force: bool = False):
        """
        Save state to file

        :param force: Force save, ignoring save interval
        """
        self.state['updated_at'] = datetime.now().isoformat()

        # Convert set to list for JSON serialization
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
        """Set source file hash"""
        self.state['source_file_hash'] = self._calculate_file_hash(file_path)

    def verify_source_file(self, file_path: str) -> bool:
        """Verify if source file is consistent with previous"""
        if not self.state.get('source_file_hash'):
            return False
        current_hash = self._calculate_file_hash(file_path)
        return current_hash == self.state['source_file_hash']

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate file hash"""
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
        """Set total chapter count"""
        self.state['total_chapters'] = total

    def mark_chapter_processed(self, chapter_index: int):
        """
        Mark chapter as processed (using index instead of title to avoid duplicate title issues)

        :param chapter_index: Chapter index (starting from 0)
        """
        if chapter_index not in self.state['processed_chapter_indices']:
            self.state['processed_chapter_indices'].add(chapter_index)
            self.state['current_chapter_index'] = len(self.state['processed_chapter_indices'])
            self._dirty = True
            self._unsaved_count += 1

            # Save every save_interval chapters or upon completion
            if self._unsaved_count >= self.save_interval:
                self.save_state()

    def is_chapter_processed(self, chapter_index: int) -> bool:
        """
        Check if chapter has been processed

        :param chapter_index: Chapter index (starting from 0)
        :return: Whether processed
        """
        return chapter_index in self.state['processed_chapter_indices']

    def get_processed_count(self) -> int:
        """Get processed chapter count"""
        return len(self.state['processed_chapter_indices'])

    def get_current_index(self) -> int:
        """Get current processing index"""
        return self.state.get('current_chapter_index', 0)

    def mark_completed(self):
        """Mark conversion as completed"""
        self.state['completed'] = True
        self.save_state(force=True)  # Force save upon completion

    def is_completed(self) -> bool:
        """Check if completed"""
        return self.state.get('completed', False)

    def set_metadata(self, key: str, value: Any):
        """Set metadata"""
        self.state['metadata'][key] = value
        self.save_state()

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata"""
        return self.state['metadata'].get(key, default)

    def reset(self):
        """Reset state"""
        self.state = self._create_empty_state()
        self.save_state(force=True)

    def flush(self):
        """Flush: save all unsaved changes"""
        if self._dirty:
            self.save_state(force=True)

    def cleanup(self):
        """Cleanup state file"""
        if os.path.exists(self.state_file):
            try:
                os.remove(self.state_file)
            except Exception as e:
                print(f"Warning: Failed to cleanup state file: {e}")


def get_state_file_path(txt_file: str, epub_dir: str) -> str:
    """
    Generate state file path

    :param txt_file: Source text file path
    :param epub_dir: EPUB output directory
    :return: State file path
    """
    # Generate state file name using source file name
    basename = os.path.basename(txt_file)
    name_without_ext = os.path.splitext(basename)[0]
    state_filename = f".{name_without_ext}_resume.json"
    return os.path.join(epub_dir, state_filename)
