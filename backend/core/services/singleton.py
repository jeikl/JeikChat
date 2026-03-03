"""
单例模式工具模块
提供线程安全的单例装饰器和元类
"""

import threading
from typing import Dict, Any, Optional
from functools import wraps


class SingletonMeta(type):
    """
    单例元类
    使用方式: class MyClass(metaclass=SingletonMeta)
    """
    _instances: Dict[type, Any] = {}
    _lock: threading.Lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

    @classmethod
    def reset_instance(cls, target_class: type):
        """重置指定类的单例实例（用于测试）"""
        with cls._lock:
            if target_class in cls._instances:
                del cls._instances[target_class]

    @classmethod
    def get_instance(cls, target_class: type) -> Optional[Any]:
        """获取指定类的单例实例"""
        return cls._instances.get(target_class)


def singleton(cls):
    """
    单例装饰器
    使用方式: @singleton
    """
    instances: Dict[type, Any] = {}
    lock = threading.Lock()

    @wraps(cls)
    def wrapper(*args, **kwargs):
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    wrapper._instances = instances
    wrapper._lock = lock
    return wrapper


class ThreadSafeLazyInitializer:
    """
    线程安全的延迟初始化器
    用于延迟创建重量级对象
    """
    def __init__(self, factory_func):
        self._factory = factory_func
        self._instance = None
        self._lock = threading.Lock()
        self._initialized = False

    def get(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._instance = self._factory()
                    self._initialized = True
        return self._instance

    def reset(self):
        """重置实例，下次调用时重新创建"""
        with self._lock:
            self._instance = None
            self._initialized = False
