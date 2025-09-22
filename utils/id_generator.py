"""
ID生成器工具
"""
import random
import os
from typing import Optional


class IDGenerator:
    """生成唯一ID的工具类"""

    @staticmethod
    def generate_unique_id(data_dir: str = "data", prefix: str = "", length: int = 7) -> str:
        """
        生成唯一的ID

        Args:
            data_dir: 数据存储目录
            prefix: ID前缀
            length: ID长度（不包括前缀）

        Returns:
            唯一的ID字符串
        """
        min_val = 10 ** (length - 1)
        max_val = (10 ** length) - 1

        # 确保目录存在
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        # 生成唯一ID
        while True:
            id_num = random.randint(min_val, max_val)
            unique_id = f"{prefix}{id_num}"

            # 检查文件是否存在
            if not os.path.exists(os.path.join(data_dir, f"{unique_id}.json")):
                return unique_id

    @staticmethod
    def validate_id(unique_id: str, data_dir: str = "data") -> bool:
        """
        验证ID是否存在

        Args:
            unique_id: 要验证的ID
            data_dir: 数据存储目录

        Returns:
            如果ID存在返回True，否则返回False
        """
        return os.path.exists(os.path.join(data_dir, f"{unique_id}.json"))