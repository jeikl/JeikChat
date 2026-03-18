from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
import yaml
from pathlib import Path
from api.response import success, error
from agent.prompt import Prompts

router = APIRouter()

# 统一使用 config/prompts.yaml
PROMPTS_FILE = Path(__file__).parent.parent.parent / "config" / "prompts.yaml"

@router.get("/prompts/list")
async def list_prompts():
    """获取所有提示词配置"""
    if not PROMPTS_FILE.exists():
        # 尝试查找旧路径，如果存在则读取
        old_path = Path(__file__).parent.parent.parent / "agent" / "prompt" / "prompts.yaml"
        if old_path.exists():
            try:
                with open(old_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                return success(data)
            except Exception as e:
                return error(f"读取旧提示词配置失败: {str(e)}")
        return success({})
    
    try:
        with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return success(data)
    except Exception as e:
        return error(f"读取提示词配置失败: {str(e)}")

class PromptsSaveRequest(BaseModel):
    data: Dict[str, Any]

@router.post("/prompts/save")
async def save_prompts(request: PromptsSaveRequest):
    """保存提示词配置"""
    try:
        # 确保目录存在
        PROMPTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
            # allow_unicode=True 确保中文正常显示
            # default_flow_style=False 确保输出块状格式
            # sort_keys=False 保持原有顺序（如果Python版本支持有序字典，通常3.7+支持）
            yaml.safe_dump(request.data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        # 重新加载内存中的配置
        Prompts().reload()
        
        return success(msg="提示词配置已保存")
    except Exception as e:
        return error(f"保存提示词配置失败: {str(e)}")
