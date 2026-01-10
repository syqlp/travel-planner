# utils/weather_service_pro.py
import requests
import json
import streamlit as st
from datetime import datetime, timedelta
import os

class QWeatherService:
    """和风天气专业服务"""
    
    def __init__(self):
        # 从环境变量获取
        self.api_key = os.getenv("QWEATHER_API_KEY", "")
        
        # 如果环境变量没有，直接在这里写死（开发时方便）
        if not self.api_key:
            self.api_key = "f02a3e6aff14430781b28d46f85664f8"  
        
        self.base_urls = {
            # 注意：和风天气v7 API的格式
            "geo": "https://geoapi.qweather.com/v2/city",  # 这个可能是对的
            "weather": "https://api.qweather.com/v7/weather",  # 改为 api.qweather.com
            "indices": "https://api.qweather.com/v7/indices/1d",
            
            # 备用：devapi版本
            "geo_dev": "https://devapi.qweather.com/v2/city",
            "weather_dev": "https://devapi.qweather.com/v7/weather",
        }
    
    def search_city(self, city_name, adm=None, country="CN"):
        """搜索城市 - 修复版"""
        if not self.api_key:
            return None
        
        # 尝试不同的API端点组合
        endpoints = [
            # 格式：base_url, endpoint_path, description
            ("https://geoapi.qweather.com", "/v2/city/lookup", "geoapi v2"),
            ("https://api.qweather.com", "/v7/geo/city/lookup", "api v7 geo"),
            ("https://devapi.qweather.com", "/v2/city/lookup", "devapi v2"),
            ("https://devapi.qweather.com", "/v7/geo/city/lookup", "devapi v7 geo"),
        ]
        
        params = {
            "location": city_name,
            "key": self.api_key,
            "range": "cn",
            "number": 20,
            "lang": "zh"
        }
        
        if adm:
            params["adm"] = adm
        
        print(f"[QWeather] 搜索城市: {city_name}")
        print(f"[QWeather] API密钥: {self.api_key[:8]}...")
        
        for base_url, endpoint_path, desc in endpoints:
            url = f"{base_url}{endpoint_path}"
            print(f"[QWeather] 尝试端点 [{desc}]: {url}")
            
            try:
                response = requests.get(url, params=params, timeout=10)
                print(f"[QWeather]   状态码: {response.status_code}")
                print(f"[QWeather]   内容类型: {response.headers.get('content-type', '未知')}")
                
                # 打印前100个字符看看响应内容
                if response.text:
                    print(f"[QWeather]   响应预览: {response.text[:100]}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"[QWeather]   JSON解析成功, 代码: {data.get('code')}")
                        
                        if data.get("code") == "200":
                            locations = data.get("location", [])
                            print(f"[QWeather] ✅ 成功找到 {len(locations)} 个城市")
                            return locations
                        else:
                            print(f"[QWeather]   API错误: {data.get('message')}")
                    except Exception as e:
                        print(f"[QWeather]   JSON解析失败: {str(e)}")
                        print(f"[QWeather]   原始响应: {response.text[:200]}")
                
                elif response.status_code in [404, 202]:
                    print(f"[QWeather]   ⚠️  状态码 {response.status_code}, 尝试下一个端点")
                    continue
                    
            except Exception as e:
                print(f"[QWeather]   ⚠️  请求失败: {str(e)}")
                continue
        
        print(f"[QWeather] ❌ 所有端点都失败")
        return None

    def _normalize_city_name(self, city_name):
        """
        标准化城市名称，提高搜索成功率
        """
        # 移除多余的空格
        name = city_name.strip()
        
        # 常见别名映射（只包含最常用的几个）
        alias_map = {
            "阿勒泰": "阿勒泰地区",
            "喀什": "喀什地区",
            "伊犁": "伊犁哈萨克自治州",
            "巴州": "巴音郭楞蒙古自治州",
        }
        
        # 检查是否在别名映射中
        for alias, official_name in alias_map.items():
            if alias in name and official_name not in name:
                name = name.replace(alias, official_name)
                print(f"[QWeather] 名称映射: {alias} -> {official_name}")
                break
        
        # 确保有完整的行政区划后缀
        if not any(name.endswith(suffix) for suffix in ["市", "县", "区", "地区", "自治州", "自治县"]):
            # 对于常见的城市，尝试添加后缀
            if name in ["北京", "上海", "天津", "重庆"]:
                name = f"{name}市"
            elif "新疆" in name and "地区" not in name and "自治州" not in name:
                # 新疆的特殊情况：很多地方是"地区"
                name = f"{name}地区"
        
        return name
    
    def get_city_weather(self, city_id, forecast_days=7):
        """
        获取城市天气
        Args:
            city_id: 城市ID（从search_city获取）
            forecast_days: 预报天数（3/7/10/15/30）
        """
        if not self.api_key:
            return None
        
        # 获取实时天气
        current_url = f"{self.base_urls['weather']}/now"
        current_params = {"location": city_id, "key": self.api_key, "lang": "zh"}
        
        # 获取天气预报
        forecast_url = f"{self.base_urls['weather']}/{forecast_days}d"
        forecast_params = {"location": city_id, "key": self.api_key, "lang": "zh"}
        
        try:
            # 获取实时天气
            current_response = requests.get(current_url, params=current_params, timeout=5)
            current_data = current_response.json()
            
            # 获取天气预报
            forecast_response = requests.get(forecast_url, params=forecast_params, timeout=5)
            forecast_data = forecast_response.json()
            
            if current_data.get("code") == "200" and forecast_data.get("code") == "200":
                return {
                    "current": current_data.get("now", {}),
                    "forecast": forecast_data.get("daily", []),
                    "updateTime": forecast_data.get("updateTime", "")
                }
            else:
                print(f"[QWeather] 天气获取失败: {current_data.get('message')}")
                return None
                
        except Exception as e:
            print(f"[QWeather] 天气获取异常: {str(e)}")
            return None
    
    def get_city_indices(self, city_id, indices_type="1,3,9,13"):
        """
        获取生活指数
        Args:
            city_id: 城市ID
            indices_type: 指数类型
                1: 运动指数, 3: 洗车指数, 5: 紫外线指数
                9: 旅游指数, 13: 舒适度指数, 14: 化妆指数
        """
        if not self.api_key:
            return None
        
        url = f"{self.base_urls['indices']}"
        params = {
            "location": city_id,
            "key": self.api_key,
            "type": indices_type,
            "lang": "zh"
        }
        
        try:
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            if data.get("code") == "200":
                return data.get("daily", [])
            return None
            
        except Exception as e:
            print(f"[QWeather] 指数获取异常: {str(e)}")
            return None
    
    def find_best_city_match(self, city_name, adm=None):
        """
        智能匹配最佳城市 - 增强版
        """
        if not city_name or not isinstance(city_name, str):
            return None
        
        print(f"[QWeather] 智能匹配: '{city_name}'")
        
        # 尝试多种搜索策略
        search_strategies = []
        
        # 策略1：原始名称
        search_strategies.append(("原始名称", city_name, adm))
        
        # 策略2：如果不包含省份信息，尝试添加常见省份前缀
        if not any(province in city_name for province in ["省", "新疆", "内蒙古", "广西", "西藏", "宁夏"]):
            # 只对可能的地级市添加省份前缀
            if any(keyword in city_name for keyword in ["阿勒泰", "喀什", "伊犁"]):
                search_strategies.append(("添加新疆前缀", f"新疆{city_name}", "新疆"))
        
        # 策略3：移除可能的错误后缀
        if "省" in city_name:
            name_without_province = city_name.replace("省", "")
            search_strategies.append(("移除省字", name_without_province, adm))
        
        # 尝试所有搜索策略
        all_locations = []
        for strategy_name, search_name, search_adm in search_strategies:
            print(f"[QWeather] 尝试策略: {strategy_name} -> '{search_name}'")
            locations = self.search_city(search_name, search_adm)
            
            if locations:
                for loc in locations:
                    # 避免重复
                    if loc["id"] not in [l["id"] for l in all_locations]:
                        all_locations.append(loc)
        
        if not all_locations:
            print(f"[QWeather] 所有搜索策略都失败")
            return None
        
        # 根据匹配程度排序
        ranked_locations = []
        for loc in all_locations:
            score = 0
            name = loc.get("name", "")
            adm1 = loc.get("adm1", "")
            
            # 名称相似度（使用简单的字符串匹配）
            if city_name == name:
                score += 100
            elif city_name in name:
                score += 50
            elif name in city_name:
                score += 40
            
            # 热门城市加分
            rank = loc.get("rank", "99")
            if rank == "10":  # 一线城市
                score += 30
            elif rank == "20":  # 二线城市
                score += 20
            elif rank == "30":  # 三线城市
                score += 10
            
            # 行政级别加分（地级市优先）
            if loc.get("adm2", "").endswith("市"):
                score += 15
            
            ranked_locations.append((score, loc))
        
        # 按分数排序
        ranked_locations.sort(key=lambda x: x[0], reverse=True)
        
        if ranked_locations:
            best_match = ranked_locations[0][1]
            best_score = ranked_locations[0][0]
            print(f"[QWeather] 最佳匹配: {best_match.get('name')} (分数: {best_score})")
            return best_match
        
        return None