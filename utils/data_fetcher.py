import requests
import os
from dotenv import load_dotenv
load_dotenv()

AMAP_KEY = os.getenv("AMAP_API_KEY", "fd3bde69015215f85200247b34e4da5b")

AMAP_KEY = "fd3bde69015215f85200247b34e4da5b"

def geocode(address: str):
    """地址 → 坐标"""
    url = "https://restapi.amap.com/v3/geocode/geo"
    params = {
        "key": AMAP_KEY,
        "address": address,
        "city": ""  # 可选：指定城市
    }
    response = requests.get(url, params=params, timeout=10)
    return response.json()

def reverse_geocode(location: str):
    """坐标 → 地址"""
    url = "https://restapi.amap.com/v3/geocode/regeo"
    params = {
        "key": AMAP_KEY,
        "location": location,  # 格式 "经度,纬度"
        "extensions": "all"
    }
    response = requests.get(url, params=params, timeout=10)
    return response.json()

def nearby_search(keywords: str, location: str, radius: int = 3000, types: str = "050000"):
    """周边搜索（景点/酒店）"""
    url = "https://restapi.amap.com/v3/place/around"
    params = {
        "key": AMAP_KEY,
        "keywords": keywords,
        "location": location,
        "radius": radius,  # 搜索半径（米）
        "types": types,    # 类别码，050000表示旅游景点
        "offset": 20,
        "page": 1,
        "extensions": "all"
    }
    response = requests.get(url, params=params, timeout=10)
    return response.json()

def walking_route_planning(origin: str, destination: str):
    """
    步行路线规划
    """
    url = "https://restapi.amap.com/v3/direction/walking"
    params = {
        "key": AMAP_KEY,
        "origin": origin,
        "destination": destination,
        "extensions": "all"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("status") == "1":
            path = data.get("route", {}).get("paths", [])
            if path:
                steps = path[0].get("steps", [])
                all_coords = []
                
                for step in steps:
                    polyline = step.get("polyline", "")
                    if polyline:
                        coords = polyline.split(";")
                        for coord in coords:
                            if coord:
                                lng, lat = map(float, coord.split(","))
                                all_coords.append([lat, lng])  # Folium格式
                
                return {
                    "status": "success",
                    "distance": path[0].get("distance", 0),
                    "duration": path[0].get("duration", 0),
                    "coordinates": all_coords
                }
        
        return {"status": "error", "message": "路线规划失败"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

def driving_route_planning(origin: str, destination: str):
    """
    驾车路线规划
    """
    url = "https://restapi.amap.com/v3/direction/driving"
    params = {
        "key": AMAP_KEY,
        "origin": origin,
        "destination": destination,
        "extensions": "all",
        "strategy": 0
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("status") == "1":
            path = data.get("route", {}).get("paths", [])
            if path:
                steps = path[0].get("steps", [])
                all_coords = []
                
                for step in steps:
                    polyline = step.get("polyline", "")
                    if polyline:
                        coords = polyline.split(";")
                        for coord in coords:
                            if coord:
                                lng, lat = map(float, coord.split(","))
                                all_coords.append([lat, lng])
                
                return {
                    "status": "success",
                    "distance": path[0].get("distance", 0),
                    "duration": path[0].get("duration", 0),
                    "coordinates": all_coords
                }
        
        return {"status": "error", "message": "驾车路线规划失败"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
def search_real_hotels(location, radius=5000):
    """
    在高德地图中搜索真实酒店
    location: "lng,lat"
    """
    url = "https://restapi.amap.com/v3/place/around"
    params = {
        "key": AMAP_KEY,
        "location": location,
        "keywords": "酒店",
        "types": "110100",  # 宾馆酒店
        "radius": radius,
        "offset": 10,
        "page": 1
    }
    return requests.get(url, params=params, timeout=10).json()    
def parse_hotels(poi_data, city_center):
    hotels = []

    for h in poi_data.get("pois", []):
        hotels.append({
            "name": h.get("name"),
            "address": h.get("address", "暂无地址"),
            "location": h.get("location"),   # lng,lat
            "type": h.get("type", ""),
            "tel": h.get("tel", ""),
            "distance": int(h.get("distance", 9999))
        })
    return hotels
def classify_hotel(hotel):
    t = hotel["type"]
    if "经济" in t:
        return "经济型"
    if "高档" in t or "星级" in t:
        return "豪华型"
    return "舒适型"
def budget_match(hotel_level, user_budget):
    if user_budget == "经济型":
        return hotel_level != "豪华型"
    if user_budget == "豪华型":
        return hotel_level != "经济型"
    return True
def estimate_price(level):
    if level == "经济型":
        return "¥200–350 / 晚"
    if level == "豪华型":
        return "¥600–900 / 晚"
    return "¥350–600 / 晚"


