"""
输出辅助模块 - 统一管理用户友好的输出和日志
"""
import logging
from typing import Optional


logger = logging.getLogger(__name__)


class UserOutput:
    """用户友好的输出管理器"""

    def __init__(self, verbose: bool = True):
        """
        初始化输出管理器

        :param verbose: 是否启用详细输出
        """
        self.verbose = verbose

    def section_header(self, title: str):
        """
        打印节标题

        :param title: 标题文本
        """
        if self.verbose:
            print("\n" + "=" * 60)
            print(title)
            print("=" * 60)
        logger.info(title)

    def section_footer(self):
        """打印节尾部"""
        if self.verbose:
            print("=" * 60 + "\n")

    def info(self, message: str, prefix: str = ""):
        """
        打印信息消息

        :param message: 消息内容
        :param prefix: 消息前缀（如 "✓", "⚠"）
        """
        if self.verbose:
            if prefix:
                print(f"{prefix} {message}")
            else:
                print(message)
        logger.info(message)

    def success(self, message: str):
        """打印成功消息"""
        self.info(message, prefix="✓")

    def warning(self, message: str):
        """打印警告消息"""
        self.info(message, prefix="⚠")
        logger.warning(message)

    def detail(self, message: str, indent: int = 2):
        """
        打印详情消息（缩进）

        :param message: 消息内容
        :param indent: 缩进空格数
        """
        if self.verbose:
            print(" " * indent + message)
        logger.debug(message)

    def progress_message(self, current: int, total: int, item_name: str):
        """
        打印进度消息

        :param current: 当前进度
        :param total: 总数
        :param item_name: 项目名称
        """
        if self.verbose:
            percent = int(current / total * 100) if total > 0 else 0
            print(f"[{current}/{total}] ({percent}%) {item_name}")
        logger.debug(f"Progress: {current}/{total} - {item_name}")


# 全局实例（可选）
_default_output = None


def get_output(verbose: bool = True) -> UserOutput:
    """
    获取输出管理器实例

    :param verbose: 是否启用详细输出
    :return: UserOutput 实例
    """
    global _default_output
    if _default_output is None:
        _default_output = UserOutput(verbose)
    return _default_output
