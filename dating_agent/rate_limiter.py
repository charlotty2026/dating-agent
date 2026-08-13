"""
速率限制器 - 防止短时间内大量发送消息
"""

import time
from typing import Optional


class RateLimiter:
    """速率限制器"""

    def __init__(self, min_interval: float = 2.0):
        """
        Args:
            min_interval: 最小发送间隔（秒）
        """
        self.min_interval = min_interval
        self.last_send_time: Optional[float] = None

    def wait_if_needed(self) -> None:
        """等待必要的时间"""
        if self.last_send_time is not None:
            elapsed = time.time() - self.last_send_time
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
        self.last_send_time = time.time()

    def can_send(self) -> bool:
        """检查是否可以发送"""
        if self.last_send_time is None:
            return True
        return time.time() - self.last_send_time >= self.min_interval
