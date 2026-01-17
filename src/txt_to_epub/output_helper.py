"""
Output helper module - Unified management of user-friendly output and logging
"""
import logging
from typing import Optional


logger = logging.getLogger(__name__)


class UserOutput:
    """User-friendly output manager"""

    def __init__(self, verbose: bool = True):
        """
        Initialize output manager

        :param verbose: Whether to enable verbose output
        """
        self.verbose = verbose

    def section_header(self, title: str):
        """
        Print section header

        :param title: Header text
        """
        if self.verbose:
            print("\n" + "=" * 60)
            print(title)
            print("=" * 60)
        logger.info(title)

    def section_footer(self):
        """Print section footer"""
        if self.verbose:
            print("=" * 60 + "\n")

    def info(self, message: str, prefix: str = ""):
        """
        Print info message

        :param message: Message content
        :param prefix: Message prefix (e.g., "✓", "⚠")
        """
        if self.verbose:
            if prefix:
                print(f"{prefix} {message}")
            else:
                print(message)
        logger.info(message)

    def success(self, message: str):
        """Print success message"""
        self.info(message, prefix="✓")

    def warning(self, message: str):
        """Print warning message"""
        self.info(message, prefix="⚠")
        logger.warning(message)

    def detail(self, message: str, indent: int = 2):
        """
        Print detail message (indented)

        :param message: Message content
        :param indent: Number of indent spaces
        """
        if self.verbose:
            print(" " * indent + message)
        logger.debug(message)

    def progress_message(self, current: int, total: int, item_name: str):
        """
        Print progress message

        :param current: Current progress
        :param total: Total count
        :param item_name: Item name
        """
        if self.verbose:
            percent = int(current / total * 100) if total > 0 else 0
            print(f"[{current}/{total}] ({percent}%) {item_name}")
        logger.debug(f"Progress: {current}/{total} - {item_name}")


# Global instance (optional)
_default_output = None


def get_output(verbose: bool = True) -> UserOutput:
    """
    Get output manager instance

    :param verbose: Whether to enable verbose output
    :return: UserOutput instance
    """
    global _default_output
    if _default_output is None:
        _default_output = UserOutput(verbose)
    return _default_output
