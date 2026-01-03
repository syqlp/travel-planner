# utils/baidu_fetcher.py - 改进版本
import requests
import json
import os
import math
from dotenv import load_dotenv
import streamlit as st

# 加载环境变量
load_dotenv()

class BaiduMapClient:
    """百度地图API客户端"""
    
    def __init__(self):
        self.api_key = os.getenv("BAIDU_MAP_API_KEY", "")
        self.geocode_url = "https://api.map.baidu.com/geocoding/v3/"
        self.place_url = "https://api.map.baidu.com/place/v2/search"
        self.route_url = "https://api.map.baidu.com/direction/v2/"  # 路线规划API
       
        if not self.api_key:
            st.warning("⚠️ 百度地图API密钥未配置")
    
    def geocode(self, address, city=None):
        """地理编码"""
        if not self.api_key:
            return {"status": "error", "message": "API密钥未配置"}
        
        params = {
            "address": address,
            "output": "json",
            "ak": self.api_key,
            "ret_coordtype": "bd09ll"
        }
        
        if city:
            params["city"] = city
        
        try:
            response = requests.get(self.geocode_url, params=params, timeout=10)
            data = response.json()
            
            if data.get("status") == 0:
                result = data.get("result", {})
                location = result.get("location", {})
                
                return {
                    "status": "success",
                    "location": f"{location.get('lng')},{location.get('lat')}",
                    "formatted_address": result.get("formatted_address", address),
                    "confidence": result.get("confidence", 0),
                    "level": result.get("level", ""),
                    "coordinate_type": "bd09ll"
                }
            else:
                return {"status": "error", "message": data.get("message", f"地理编码失败，状态码: {data.get('status')}")}
                
        except Exception as e:
            return {"status": "error", "message": f"请求异常: {str(e)}"}
    
    def place_search(self, query, location, radius=5000, tag=None, page_size=20):
        """地点搜索"""
        if not self.api_key:
            return {"status": "error", "message": "API密钥未配置"}
        
        params = {
            "query": query,
            "location": location,
            "radius": radius,
            "output": "json",
            "ak": self.api_key,
            "page_size": page_size,
            "coord_type": 3  # 百度经纬度坐标
        }
        
        if tag:
            params["tag"] = tag
        
        try:
            response = requests.get(self.place_url, params=params, timeout=10)
            data = response.json()
            
            if data.get("status") == 0:
                results = data.get("results", [])
                
                formatted_results = []
                for item in results:
                    formatted_results.append({
                        "name": item.get("name", ""),
                        "location": f"{item.get('location', {}).get('lng', 0)},{item.get('location', {}).get('lat', 0)}",
                        "address": item.get("address", ""),
                        "province": item.get("province", ""),
                        "city": item.get("city", ""),
                        "area": item.get("area", ""),
                        "telephone": item.get("telephone", ""),
                        "uid": item.get("uid", ""),
                        "detail_info": item.get("detail_info", {}),
                        "type": item.get("detail_info", {}).get("type", ""),
                        "tag": item.get("detail_info", {}).get("tag", ""),
                        "price": item.get("detail_info", {}).get("price", ""),
                        "rating": float(item.get("detail_info", {}).get("overall_rating", 0) or 0),
                        "coordinate_type": "bd09ll"
                    })
                
                return {
                    "status": "success",
                    "total": len(formatted_results),
                    "results": formatted_results,
                    "message": f"找到{len(formatted_results)}个结果"
                }
            else:
                return {"status": "error", "message": f"地点搜索失败: {data.get('message', '未知错误')}"}
                
        except Exception as e:
            return {"status": "error", "message": f"请求异常: {str(e)}"}
    
    def search_attractions(self, location, radius=10000):
        """搜索旅游景点"""
        # 百度地图景点查询，扩大搜索范围
        return self.place_search(
            query="景点",
            location=location,
            radius=radius,
            page_size=20
        )
    
    def search_restaurants(self, location, radius=5000):
        """搜索餐厅"""
        return self.place_search(
            query="餐厅",
            location=location,
            radius=radius,
            tag="餐饮",
            page_size=15
        )
    
    def get_route_plan(self, origin, destination, mode="transit"):
        """
        获取路线规划
        Args:
            origin: 起点坐标 "lng,lat"
            destination: 终点坐标 "lng,lat"
            mode: 交通方式 
                  "walking" - 步行
                  "transit" - 公共交通
                  "driving" - 驾车
        """
        if not self.api_key:
            return {"status": "error", "message": "API密钥未配置"}
        
        params = {
            "origin": origin,
            "destination": destination,
            "mode": mode,
            "output": "json",
            "ak": self.api_key,
            "coord_type": "bd09ll",  # 百度坐标
            "ret_coordtype": "bd09ll",
            "tactics": 12 if mode == "transit" else None  # 公交策略：较快捷
        }
        
        if mode == "transit":
            params["transit_mode"] = "subway|bus"  # 地铁+公交
        
        try:
            response = requests.get(self.route_url, params=params, timeout=10)
            data = response.json()
            
            if data.get("status") == 0:
                result = data.get("result", {})
                routes = result.get("routes", [])
                
                if routes:
                    route = routes[0]  # 取第一条路线
                    return {
                        "status": "success",
                        "distance": route.get("distance", 0),  # 总距离(米)
                        "duration": route.get("duration", 0),  # 总时间(秒)
                        "steps": self._parse_route_steps(route.get("steps", []), mode),
                        "taxi_fare": route.get("taxi", {}).get("fare", {}).get("total_fare", 0),
                        "origin": origin,
                        "destination": destination,
                        "mode": mode
                    }
                else:
                    return {"status": "error", "message": "未找到路线"}
            else:
                return {"status": "error", "message": data.get("message", "路线规划失败")}
                
        except Exception as e:
            return {"status": "error", "message": f"请求异常: {str(e)}"}
    
    def _parse_route_steps(self, steps, mode):
        """解析路线步骤"""
        parsed_steps = []
        
        for step in steps:
            step_info = {
                "instruction": step.get("instruction", ""),
                "distance": step.get("distance", 0),
                "duration": step.get("duration", 0),
                "path": step.get("path", ""),  # 路线坐标点
                "vehicle": self._parse_vehicle_info(step, mode),
                "start_location": step.get("start_location", {}),
                "end_location": step.get("end_location", {})
            }
            
            # 如果是公共交通，解析详细信息
            if mode == "transit" and step.get("vehicle", {}):
                vehicle = step["vehicle"]
                step_info["vehicle_details"] = {
                    "name": vehicle.get("name", ""),
                    "type": vehicle.get("type", ""),
                    "lines": self._parse_transit_lines(step.get("lines", []))
                }
            
            parsed_steps.append(step_info)
        
        return parsed_steps
    
    def _parse_vehicle_info(self, step, mode):
        """解析交通工具信息"""
        if mode == "walking":
            return {
                "type": "walking",
                "name": "步行",
                "icon": "🚶"
            }
        elif mode == "transit" and "vehicle" in step:
            vehicle = step["vehicle"]
            vehicle_type = vehicle.get("type", "")
            
            if vehicle_type == "subway":
                return {
                    "type": "subway",
                    "name": vehicle.get("name", "地铁"),
                    "icon": "🚇",
                    "line": vehicle.get("name", "").split("(")[0]
                }
            elif vehicle_type == "bus":
                return {
                    "type": "bus",
                    "name": vehicle.get("name", "公交"),
                    "icon": "🚌",
                    "line": vehicle.get("name", "")
                }
        
        return {"type": "unknown", "name": "未知", "icon": "❓"}
    
    def _parse_transit_lines(self, lines):
        """解析公交/地铁线路信息"""
        parsed_lines = []
        for line in lines:
            parsed_lines.append({
                "name": line.get("name", ""),
                "type": line.get("type", ""),
                "vehicle_type": line.get("vehicle_type", ""),
                "departure_stop": line.get("departure_stop", {}).get("name", ""),
                "arrival_stop": line.get("arrival_stop", {}).get("name", ""),
                "num_stops": line.get("via_num", 0)
            })
        return parsed_lines
    
    def get_multi_route_plan(self, locations, mode="transit"):
        """
        获取多点路线规划
        Args:
            locations: 坐标列表 ["lng,lat", "lng,lat", ...]
            mode: 交通方式
        """
        if len(locations) < 2:
            return {"status": "error", "message": "至少需要2个地点"}
        
        all_routes = []
        total_distance = 0
        total_duration = 0
        
        for i in range(len(locations) - 1):
            origin = locations[i]
            destination = locations[i + 1]
            
            route_result = self.get_route_plan(origin, destination, mode)
            
            if route_result["status"] == "success":
                all_routes.append(route_result)
                total_distance += route_result.get("distance", 0)
                total_duration += route_result.get("duration", 0)
            else:
                # 如果某段路线失败，尝试步行
                walking_result = self.get_route_plan(origin, destination, "walking")
                if walking_result["status"] == "success":
                    all_routes.append(walking_result)
                    total_distance += walking_result.get("distance", 0)
                    total_duration += walking_result.get("duration", 0)
                else:
                    st.warning(f"无法规划 {i+1} 到 {i+2} 的路线: {route_result.get('message')}")
        
        return {
            "status": "success" if all_routes else "error",
            "routes": all_routes,
            "total_distance": total_distance,
            "total_duration": total_duration,
            "location_count": len(locations)
        }
# ========== 坐标转换函数（关键！） ==========
def bd09_to_wgs84(lng, lat):
    """
    百度坐标系 (BD-09) 转 WGS84坐标系
    使用百度官方提供的近似转换算法
    """
    try:
        x_pi = 3.14159265358979324 * 3000.0 / 180.0
        x = float(lng) - 0.0065
        y = float(lat) - 0.006
        z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * x_pi)
        theta = math.atan2(y, x) - 0.000003 * math.cos(x * x_pi)
        wgs_lng = z * math.cos(theta)
        wgs_lat = z * math.sin(theta)
        return wgs_lng, wgs_lat
    except:
        return float(lng), float(lat)

def convert_bd09_to_wgs84_str(location_str):
    """
    将百度坐标字符串转换为WGS84坐标字符串
    """
    try:
        lng, lat = map(float, location_str.split(','))
        wgs_lng, wgs_lat = bd09_to_wgs84(lng, lat)
        return f"{wgs_lng:.6f},{wgs_lat:.6f}"
    except Exception as e:
        st.warning(f"坐标转换失败: {e}, 使用原始坐标")
        return location_str

def get_wgs84_coordinates(poi_data):
    """从POI数据中获取WGS84坐标"""
    try:
        if isinstance(poi_data, str):
            # 如果是坐标字符串
            return convert_bd09_to_wgs84_str(poi_data)
        elif isinstance(poi_data, dict):
            # 如果是字典，尝试获取location
            location = poi_data.get("location", "")
            if location:
                return convert_bd09_to_wgs84_str(location)
            else:
                # 尝试从detail_info中获取
                detail = poi_data.get("detail_info", {})
                if "location" in detail:
                    return convert_bd09_to_wgs84_str(detail["location"])
        return None
    except:
        return None