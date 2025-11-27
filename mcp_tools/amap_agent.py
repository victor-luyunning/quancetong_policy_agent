import httpx
import json
from typing import Dict, Any, List

MCP_AMAP_URL = "https://mcp.api-inference.modelscope.net/0fcda8c99abf4a/mcp"


async def generate_industry_map(companies: List[Dict], province: str = "山东省") -> Dict[str, Any]:
    """
    生成产业分布地图（企业光点标注）
    
    Args:
        companies: [{"name": "海尔", "city": "青岛", "industry": "家电", "score": 85}]
        province: 省份名称
    
    Returns:
        地图配置和标注点位
    """
    try:
        # 山东省主要城市坐标（示例）
        city_coords = {
            "济南": [117.12, 36.65],
            "青岛": [120.38, 36.07],
            "淄博": [118.05, 36.81],
            "烟台": [121.45, 37.46],
            "潍坊": [119.16, 36.71],
            "济宁": [116.59, 35.42],
            "泰安": [117.09, 36.20],
            "威海": [122.12, 37.51],
            "日照": [119.53, 35.42],
            "临沂": [118.35, 35.10],
            "德州": [116.36, 37.43],
            "聊城": [115.98, 36.45],
            "滨州": [117.97, 37.38],
            "菏泽": [115.48, 35.23],
            "枣庄": [117.32, 34.81],
            "东营": [118.67, 37.43]
        }
        
        # 构建标注点位
        markers = []
        for company in companies:
            city = company.get("city", "").replace("市", "")
            if city in city_coords:
                markers.append({
                    "name": company["name"],
                    "position": city_coords[city],
                    "score": company.get("score", 0),
                    "industry": company.get("industry", "未知")
                })
        
        # 地图配置
        map_config = {
            "province": province,
            "center": [117.12, 36.65],  # 山东中心
            "zoom": 7,
            "markers": markers,
            "style": {
                "marker_color": "red",
                "marker_size": "medium"
            }
        }
        
        return {
            "success": True,
            "map_config": map_config,
            "total_markers": len(markers)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def get_city_boundary(city: str) -> Dict[str, Any]:
    """
    获取城市行政区划边界（用于地图渲染）
    
    Args:
        city: 城市名称
    
    Returns:
        城市边界数据
    """
    # 这里返回模拟数据，实际应调用高德API
    return {
        "success": True,
        "city": city,
        "boundary": "simulated_boundary_data"
    }
