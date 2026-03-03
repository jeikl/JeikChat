"""
流式请求管理器
管理所有活跃的流式请求，支持客户端断开时真正停止后端通信
"""

import asyncio
import threading
import logging
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class StreamTask:
    """流式任务信息"""
    task_id: str
    session_id: str
    cancel_event: threading.Event
    created_at: datetime = field(default_factory=datetime.now)
    client_disconnected: bool = False
    
    def is_cancelled(self) -> bool:
        return self.cancel_event.is_set()


class StreamManager:
    """
    流式请求管理器（单例）
    管理所有活跃的流式请求，支持：
    1. 客户端断开时真正停止后端与大模型的通信
    2. 任务超时自动清理
    3. 统计和监控
    """
    _instance: Optional['StreamManager'] = None
    _lock: threading.Lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._tasks: Dict[str, StreamTask] = {}
        self._tasks_lock = threading.RLock()
        self._initialized = True
        self._cleanup_interval = 60  # 清理间隔（秒）
        self._task_timeout = 300  # 任务超时时间（秒）
        
        # 启动清理任务
        self._start_cleanup_task()
        
        logger.info("StreamManager 初始化完成")
    
    def register_task(self, task_id: str, session_id: str) -> StreamTask:
        """
        注册新的流式任务
        
        Args:
            task_id: 任务唯一标识
            session_id: 会话ID
            
        Returns:
            StreamTask: 任务对象，包含取消事件
        """
        cancel_event = threading.Event()
        task = StreamTask(
            task_id=task_id,
            session_id=session_id,
            cancel_event=cancel_event
        )
        
        with self._tasks_lock:
            # 如果同一会话已有任务，先取消它
            existing_tasks = [
                t for t in self._tasks.values() 
                if t.session_id == session_id and not t.is_cancelled()
            ]
            for existing in existing_tasks:
                logger.info(f"取消同一会话的现有任务: {existing.task_id}")
                existing.cancel_event.set()
            
            self._tasks[task_id] = task
            
        logger.info(f"注册流式任务: {task_id}, 会话: {session_id}")
        return task
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消指定任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功取消
        """
        with self._tasks_lock:
            task = self._tasks.get(task_id)
            if task:
                task.cancel_event.set()
                task.client_disconnected = True
                logger.info(f"任务已取消: {task_id}")
                return True
        return False
    
    def cancel_session_tasks(self, session_id: str) -> int:
        """
        取消指定会话的所有任务
        
        Args:
            session_id: 会话ID
            
        Returns:
            int: 取消的任务数量
        """
        cancelled_count = 0
        with self._tasks_lock:
            for task in self._tasks.values():
                if task.session_id == session_id and not task.is_cancelled():
                    task.cancel_event.set()
                    task.client_disconnected = True
                    cancelled_count += 1
                    
        if cancelled_count > 0:
            logger.info(f"会话 {session_id} 的 {cancelled_count} 个任务已取消")
        return cancelled_count
    
    def get_task(self, task_id: str) -> Optional[StreamTask]:
        """获取任务信息"""
        with self._tasks_lock:
            return self._tasks.get(task_id)
    
    def remove_task(self, task_id: str):
        """移除任务（任务完成时调用）"""
        with self._tasks_lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                logger.debug(f"任务已移除: {task_id}")
    
    def is_task_active(self, task_id: str) -> bool:
        """检查任务是否仍在活跃"""
        task = self.get_task(task_id)
        return task is not None and not task.is_cancelled()
    
    def should_stop(self, task_id: str) -> bool:
        """
        检查任务是否应该停止
        在流式生成器的每次迭代中调用
        """
        task = self.get_task(task_id)
        if task is None:
            return True  # 任务不存在，应该停止
        return task.is_cancelled()
    
    def get_active_tasks_count(self) -> int:
        """获取活跃任务数量"""
        with self._tasks_lock:
            return sum(1 for task in self._tasks.values() if not task.is_cancelled())
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._tasks_lock:
            total = len(self._tasks)
            active = sum(1 for t in self._tasks.values() if not t.is_cancelled())
            cancelled = total - active
            
        return {
            "total_tasks": total,
            "active_tasks": active,
            "cancelled_tasks": cancelled,
        }
    
    def _start_cleanup_task(self):
        """启动后台清理任务"""
        def cleanup_worker():
            while True:
                threading.Event().wait(self._cleanup_interval)
                self._cleanup_expired_tasks()
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        logger.info("流式任务清理线程已启动")
    
    def _cleanup_expired_tasks(self):
        """清理过期任务"""
        now = datetime.now()
        expired_tasks = []
        
        with self._tasks_lock:
            for task_id, task in list(self._tasks.items()):
                # 检查是否超时或已取消很久
                age = (now - task.created_at).total_seconds()
                if age > self._task_timeout or (task.is_cancelled() and age > 30):
                    expired_tasks.append(task_id)
            
            for task_id in expired_tasks:
                del self._tasks[task_id]
        
        if expired_tasks:
            logger.info(f"清理了 {len(expired_tasks)} 个过期任务")


# 全局单例实例
stream_manager = StreamManager()


def get_stream_manager() -> StreamManager:
    """获取 StreamManager 单例"""
    return stream_manager
