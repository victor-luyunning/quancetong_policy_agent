import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib

# 轻量级本地对话存储路径
CONTEXT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "context_history.jsonl")


class ContextManager:
    """上下文对话管理器（轻量级本地存储）"""
    
    def __init__(self):
        self.ensure_context_file()
    
    def ensure_context_file(self):
        """确保上下文文件存在"""
        os.makedirs(os.path.dirname(CONTEXT_FILE), exist_ok=True)
        if not os.path.exists(CONTEXT_FILE):
            with open(CONTEXT_FILE, "w", encoding="utf-8") as f:
                pass
    
    def save_conversation(self, query: str, intent: str, result: Dict[str, Any]) -> str:
        """
        保存对话记录
        
        Args:
            query: 用户查询
            intent: 识别的意图
            result: 工作流结果
        
        Returns:
            conversation_id
        """
        conversation_id = hashlib.md5(
            f"{query}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        record = {
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "intent": intent,
            "result": result
        }
        
        with open(CONTEXT_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        
        return conversation_id
    
    def get_recent_conversations(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取最近的对话记录
        
        Args:
            limit: 返回数量
        
        Returns:
            对话记录列表
        """
        if not os.path.exists(CONTEXT_FILE):
            return []
        
        conversations = []
        with open(CONTEXT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        conversations.append(json.loads(line))
                    except:
                        continue
        
        # 返回最近的N条
        return conversations[-limit:] if conversations else []
    
    def find_related_context(self, current_query: str, threshold: float = 0.5) -> Optional[Dict[str, Any]]:
        """
        查找相关的上下文（简单关键词匹配）
        
        Args:
            current_query: 当前查询
            threshold: 相似度阈值
        
        Returns:
            相关的历史对话
        """
        recent = self.get_recent_conversations(limit=5)
        if not recent:
            return None
        
        # 简单关键词匹配（可以后续升级为向量相似度）
        current_keywords = set(current_query.split())
        
        best_match = None
        best_score = 0
        
        for conv in reversed(recent):  # 从最近的开始
            history_keywords = set(conv["query"].split())
            # 计算Jaccard相似度
            intersection = len(current_keywords & history_keywords)
            union = len(current_keywords | history_keywords)
            score = intersection / union if union > 0 else 0
            
            if score > best_score and score >= threshold:
                best_score = score
                best_match = conv
        
        return best_match
    
    def clear_old_conversations(self, keep_days: int = 7):
        """清理旧对话记录"""
        # TODO: 实现基于时间的清理逻辑
        pass


async def check_context_relevance(current_query: str, context_manager: ContextManager) -> Dict[str, Any]:
    """
    检查当前查询是否需要调用上下文（由大模型判断）
    
    Args:
        current_query: 当前查询
        context_manager: 上下文管理器
    
    Returns:
        {
            "need_context": bool,
            "related_conversation": dict or None,
            "reasoning": str
        }
    """
    # 简单规则判断（后续可接入大模型）
    context_keywords = ["刚才", "上面", "那个", "这个政策", "刚说的", "继续"]
    
    need_context = any(kw in current_query for kw in context_keywords)
    
    if need_context:
        related = context_manager.find_related_context(current_query)
        return {
            "need_context": True,
            "related_conversation": related,
            "reasoning": "检测到上下文关键词"
        }
    else:
        return {
            "need_context": False,
            "related_conversation": None,
            "reasoning": "独立查询"
        }
