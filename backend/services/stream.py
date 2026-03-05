"""
流式任务管理
用于管理客户端连接和任务取消
"""

import threading
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class StreamTask:
    """流式任务"""
    
    def __init__(self, task_id: str, session_id: str):
        self.task_id = task_id
        self.session_id = session_id
        self._cancel_event = threading.Event()
    
    @property
    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()
    
    def cancel(self):
        self._cancel_event.set()
    
    def __repr__(self):
        return f"StreamTask(task_id={self.task_id}, session_id={self.session_id})"


class StreamManager:
    """流式任务管理器"""
    
    def __init__(self):
        self._tasks: Dict[str, StreamTask] = {}
        self._lock = threading.Lock()
    
    def register_task(self, task_id: str, session_id: str) -> StreamTask:
        """注册新任务"""
        with self._lock:
            # 取消同一会话的旧任务
            for existing_task in self._tasks.values():
                if existing_task.session_id == session_id:
                    existing_task.cancel()
            
            task = StreamTask(task_id, session_id)
            self._tasks[task_id] = task
            logger.info(f"注册流式任务: {task}")
            return task
    
    def unregister_task(self, task_id: str):
        """注销任务"""
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                logger.info(f"注销流式任务: {task_id}")
    
    def cancel_task(self, task_id: str):
        """取消任务"""
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].cancel()
                logger.info(f"取消流式任务: {task_id}")
    
    def cancel_session_tasks(self, session_id: str):
        """取消会话的所有任务"""
        with self._lock:
            for task in self._tasks.values():
                if task.session_id == session_id:
                    task.cancel()


_stream_manager: Optional[StreamManager] = None
_manager_lock = threading.Lock()


def get_stream_manager() -> StreamManager:
    """获取流式管理器单例"""
    global _stream_manager
    if _stream_manager is None:
        with _manager_lock:
            if _stream_manager is None:
                _stream_manager = StreamManager()
    return _stream_manager
