import requests

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

def route_planning(origin: str, destination: str):
    """路线规划（驾车）"""
    url = "https://restapi.amap.com/v3/direction/driving"
    params = {
        "key": AMAP_KEY,
        "origin": origin,        # "经度,纬度"
        "destination": destination,
        "extensions": "base"
    }
    response = requests.get(url, params=params, timeout=10)
    return response.json()

# 示例
if __name__ == "__main__":
    # 1. 获取城市坐标
    geo_res = geocode("邵阳")
    location = geo_res["geocodes"][0]["location"]
    print("城市坐标:", location)
    
    # 2. 周边景点搜索
    spots = nearby_search("景点", location)
    for poi in spots["pois"][:5]:
        print(poi["name"], poi["address"], poi["location"])
    
    # 3. 酒店搜索
    hotels = nearby_search("酒店", location, types="110000")
    for hotel in hotels["pois"][:5]:
        print(hotel["name"], hotel["address"], hotel["location"])
    
    # 4. 路线规划示例
    if len(spots["pois"]) > 1:
        origin = spots["pois"][0]["location"]
        destination = spots["pois"][1]["location"]
        route = route_planning(origin, destination)
        print("路线距离:", route["route"]["paths"][0]["distance"], "米")
