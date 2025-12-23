import httpx
import json
import os
from typing import Dict, Any, List
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

MCP_AMAP_URL = "https://mcp.api-inference.modelscope.net/0fcda8c99abf4a/mcp"
AMAP_API_KEY = os.getenv("AMAP_API_KEY", "")


async def generate_industry_map(companies: List[Dict], province: str = "山东省", use_amap: bool = True) -> Dict[str, Any]:
    """
    生成产业分布地图（混合方案）
    
    策略：
    1. 优先使用高德静态地图API（如果配置了AMAP_API_KEY）
    2. 降级到QuickChart散点图（坐标图）
    
    Args:
        companies: [{"name": "海尔", "city": "青岛", "industry": "家电", "score": 85}]
        province: 省份名称
        use_amap: 是否优先使用高德静态地图（默认True）
    
    Returns:
        地图配置和静态图片URL
    """
    try:
        import urllib.parse
        
        # 山东省主要城市坐标
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
        for idx, company in enumerate(companies, 1):
            city = company.get("city", "").replace("市", "").replace("省", "").strip()
            # 模糊匹配城市名
            matched_city = None
            for city_name in city_coords.keys():
                if city_name in city or city in city_name:
                    matched_city = city_name
                    break
            
            if matched_city:
                coord = city_coords[matched_city]
                markers.append({
                    "name": company["name"],
                    "position": coord,
                    "score": company.get("score", 0),
                    "industry": company.get("industry", "未知"),
                    "city": matched_city,
                    "label": str(idx)
                })
        
        map_image_url = None
        map_source = "none"
        
        # 方案1：尝试使用高德静态地图API（优先）
        if use_amap and AMAP_API_KEY and AMAP_API_KEY != "YOUR_AMAP_API_KEY_HERE" and markers:
            try:
                amap_url = await _generate_amap_static_map(markers, province)
                if amap_url:
                    map_image_url = amap_url
                    map_source = "amap"
            except Exception as e:
                print(f"高德静态地图生成失败，降级到QuickChart: {e}")
        
        # 方案2：降级到QuickChart散点图
        if not map_image_url and markers:
            # 提取经纬度
            lons = [m["position"][0] for m in markers]
            lats = [m["position"][1] for m in markers]
            
            # 构建散点图（模拟地图）
            map_chart = {
                "type": "scatter",
                "data": {
                    "datasets": [{
                        "label": "企业分布",
                        "data": [{"x": lon, "y": lat} for lon, lat in zip(lons, lats)],
                        "backgroundColor": "rgba(231, 76, 60, 0.8)",
                        "borderColor": "rgba(192, 57, 43, 1)",
                        "borderWidth": 2,
                        "pointRadius": 8,
                        "pointHoverRadius": 12
                    }]
                },
                "options": {
                    "responsive": True,
                    "plugins": {
                        "title": {
                            "display": True,
                            "text": f"🗺️ {province}产业分布地图（共{len(markers)}家企业）",
                            "font": {"size": 16, "weight": "bold"},
                            "color": "#2c3e50"
                        },
                        "legend": {"display": False},
                        "tooltip": {
                            "callbacks": {
                                "label": "function(context) { return context.dataset.label; }"
                            }
                        }
                    },
                    "scales": {
                        "x": {
                            "type": "linear",
                            "position": "bottom",
                            "title": {"display": True, "text": "经度"},
                            "min": 115,
                            "max": 123
                        },
                        "y": {
                            "title": {"display": True, "text": "纬度"},
                            "min": 34,
                            "max": 38
                        }
                    }
                }
            }
            
            chart_json = json.dumps(map_chart, ensure_ascii=False)
            map_image_url = f"https://quickchart.io/chart?w=700&h=500&c={urllib.parse.quote(chart_json)}"
            map_source = "quickchart"
        
        return {
            "success": True,
            "map_image_url": map_image_url,
            "map_source": map_source,  # amap / quickchart / none
            "map_config": {
                "province": province,
                "markers": markers
            },
            "total_markers": len(markers),
            "cities_covered": list(set([m["city"] for m in markers]))
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def _generate_amap_static_map(markers: List[Dict], province: str = "山东省") -> str:
    """
    生成高德静态地图URL
    
    文档: https://lbs.amap.com/api/webservice/guide/api/staticmaps
    
    Args:
        markers: 标注点位列表
        province: 省份名称
    
    Returns:
        高德静态地图图片URL
    """
    import urllib.parse
    
    if not markers:
        return None
    
    # 计算地图中心点（所有标注的平均坐标）
    avg_lon = sum([m["position"][0] for m in markers]) / len(markers)
    avg_lat = sum([m["position"][1] for m in markers]) / len(markers)
    center = f"{avg_lon},{avg_lat}"
    
    # 构建markers参数
    # 格式：size,color,label:lng,lat|size,color,label:lng,lat
    # 示例：mid,0xFF0000,A:116.37359,39.92437|mid,0x0000FF,B:116.38359,39.93437
    marker_strings = []
    for m in markers:
        lon, lat = m["position"]
        label = m.get("label", "")
        # 使用红色标注
        marker_str = f"mid,0xFF0000,{label}:{lon},{lat}"
        marker_strings.append(marker_str)
    
    markers_param = "|".join(marker_strings[:10])  # 最多10个标注
    
    # 构建URL参数
    params = {
        "location": center,         # 地图中心点
        "zoom": "8",                # 缩放级别（1-17）
        "size": "700*500",          # 图片尺寸
        "markers": markers_param,   # 标注点
        "key": AMAP_API_KEY         # API Key
    }
    
    # 生成URL
    base_url = "https://restapi.amap.com/v3/staticmap"
    query_string = urllib.parse.urlencode(params)
    static_map_url = f"{base_url}?{query_string}"
    
    return static_map_url


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
