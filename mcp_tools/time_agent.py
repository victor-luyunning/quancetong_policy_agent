# mcp_tools/time_agent.py - 时间感知MCP封装
import os
import json
import httpx
from typing import Dict, Any, List

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MCP_CONFIG_FILE = os.path.join(BASE_DIR, 'mcp_servers.json')
DEFAULT_TIME_URL = 'https://mcp.api-inference.modelscope.net/487f79a94fb641/mcp'


def _load_time_endpoint() -> str:
    """从 mcp_servers.json 读取 time MCP 的 URL，若不存在则使用默认值。"""
    try:
        with open(MCP_CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            servers = (data or {}).get('mcpServers', {})
            time_conf = servers.get('time', {})
            url = time_conf.get('url')
            return url or DEFAULT_TIME_URL
    except Exception:
        return DEFAULT_TIME_URL


async def get_current_time() -> Dict[str, Any]:
    """调用时间MCP获取当前时间（ISO8601），返回 {success, now, raw}."""
    url = _load_time_endpoint()
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            raw = {}
            if resp.headers.get('content-type', '').startswith('application/json'):
                raw = resp.json()
            # 兼容多种字段名
            now_iso = raw.get('now') or raw.get('current_time') or raw.get('iso') or raw.get('time')
            return {
                'success': True,
                'now': now_iso,
                'raw': raw,
            }
    except Exception as e:
        return {'success': False, 'error': str(e)}


async def validate_policy_periods(all_hits: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    校验命中政策是否处于有效期：返回 {success, now, active_hits, inactive_hits}
    - 命中项中需包含 effective_start/effective_end（ISO8601或YYYY-MM-DD）
    """
    time_res = await get_current_time()
    if not time_res.get('success'):
        return {'success': False, 'error': time_res.get('error', 'time mcp failed')}

    from datetime import datetime
    # 解析当前时间
    now = datetime.utcnow()
    now_iso = time_res.get('now')
    if now_iso:
        try:
            now = datetime.fromisoformat(str(now_iso).replace('Z', '+00:00'))
        except Exception:
            pass

    active_ids, inactive_ids = [], []
    def _hid(h: Dict[str, Any]) -> str:
        return h.get('doc_id') or h.get('title') or ''

    for hit in all_hits or []:
        start = hit.get('effective_start')
        end = hit.get('effective_end')
        is_active = True
        try:
            if start:
                start_dt = datetime.fromisoformat(str(start).replace('Z', '+00:00'))
                is_active = is_active and (now >= start_dt)
            if end:
                end_dt = datetime.fromisoformat(str(end).replace('Z', '+00:00'))
                is_active = is_active and (now <= end_dt)
        except Exception:
            # 不可解析时，默认为有效，避免误杀
            is_active = True
        (active_ids if is_active else inactive_ids).append(_hid(hit))

    return {
        'success': True,
        'now': now.isoformat(),
        'active_hits': active_ids,
        'inactive_hits': inactive_ids,
    }
