# utils/weather_service.py
import requests
import json
import streamlit as st
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class WeatherService:
    """天气服务 - 使用和风天气API"""
    
    def __init__(self):
        # 从环境变量获取API Key，如果没有则使用测试key（需要你替换）
        import os
        self.api_key = os.getenv("QWEATHER_API_KEY", "你的和风天气API_Key")
        self.base_url = "https://devapi.qweather.com/v7"
        
    def get_city_code(self, city_name: str) -> Optional[str]:
        """获取城市代码"""
        url = f"{self.base_url}/geo/city/lookup"
        params = {
            "location": city_name,
            "key": self.api_key,
            "range": "cn",
            "number": 5
        }
        
        try:
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            if data.get("code") == "200" and data.get("location"):
                # 返回第一个匹配的城市
                return data["location"][0]["id"]
            else:
                print(f"获取城市代码失败: {data.get('message')}")
                return None
                
        except Exception as e:
            print(f"获取城市代码异常: {str(e)}")
            return None
    
    def get_weather_forecast(self, city_name: str, start_date: str, end_date: str) -> Dict:
        """
        获取天气预测
        Args:
            city_name: 城市名
            start_date: 开始日期 "YYYY-MM-DD"
            end_date: 结束日期 "YYYY-MM-DD"
        """
        # 获取城市代码
        city_code = self.get_city_code(city_name)
        if not city_code:
            return {"status": "error", "message": "无法获取城市代码"}
        
        # 计算天数
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days = (end - start).days + 1
        
        if days <= 0:
            return {"status": "error", "message": "结束日期必须晚于开始日期"}
        
        if days > 7:
            # 和风天气免费版最多7天预报
            days = 7
            st.warning(f"⚠️ 免费API最多支持7天预报，将显示前7天天气")
        
        # 获取7天天气预报
        url = f"{self.base_url}/weather/7d"
        params = {
            "location": city_code,
            "key": self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            if data.get("code") == "200":
                # 过滤出指定日期范围内的预报
                forecast_days = data.get("daily", [])
                
                # 过滤和格式化
                filtered_forecast = []
                for forecast in forecast_days:
                    fx_date = forecast.get("fxDate")
                    if start_date <= fx_date <= end_date and len(filtered_forecast) < days:
                        filtered_forecast.append(self._format_forecast_data(forecast))
                
                return {
                    "status": "success",
                    "city": city_name,
                    "city_code": city_code,
                    "start_date": start_date,
                    "end_date": end_date,
                    "total_days": days,
                    "forecast": filtered_forecast,
                    "update_time": data.get("updateTime", "")
                }
            else:
                return {"status": "error", "message": data.get("message", "获取天气数据失败")}
                
        except Exception as e:
            print(f"获取天气数据异常: {str(e)}")
            return {"status": "error", "message": f"网络请求失败: {str(e)}"}
    
    def _format_forecast_data(self, forecast: Dict) -> Dict:
        """格式化预报数据"""
        # 天气代码到描述的映射
        weather_codes = {
            "100": "晴", "101": "多云", "102": "少云", "103": "晴间多云",
            "104": "阴", "200": "有风", "201": "平静", "202": "微风",
            "203": "和风", "204": "清风", "205": "强风", "206": "疾风",
            "207": "大风", "208": "烈风", "209": "风暴", "210": "狂风暴",
            "211": "飓风", "212": "龙卷风", "213": "热带风暴", "300": "阵雨",
            "301": "强阵雨", "302": "雷阵雨", "303": "强雷阵雨", "304": "冰雹",
            "305": "小雨", "306": "中雨", "307": "大雨", "308": "极端降雨",
            "309": "毛毛雨", "310": "暴雨", "311": "大暴雨", "312": "特大暴雨",
            "313": "冻雨", "400": "小雪", "401": "中雪", "402": "大雪",
            "403": "暴雪", "404": "雨夹雪", "405": "雨雪天气", "406": "阵雨夹雪",
            "407": "阵雪", "500": "薄雾", "501": "雾", "502": "霾",
            "503": "扬沙", "504": "浮尘", "507": "沙尘暴", "508": "强沙尘暴",
            "900": "热", "901": "冷", "999": "未知"
        }
        
        # 空气质量指数描述
        aqi_levels = {
            "1": "优", "2": "良", "3": "轻度污染",
            "4": "中度污染", "5": "重度污染", "6": "严重污染"
        }
        
        # 日出日落时间计算建议
        sunrise = forecast.get("sunrise", "06:00")
        sunset = forecast.get("sunset", "18:00")
        
        # 天气图标映射
        icon_code = forecast.get("iconDay", "100")
        weather_icon = self._get_weather_icon(icon_code)
        
        # 出行建议
        suggestions = self._generate_travel_suggestions(
            forecast.get("textDay", ""),
            int(forecast.get("tempMax", 25)),
            int(forecast.get("tempMin", 15))
        )
        
        return {
            "date": forecast.get("fxDate", ""),
            "weekday": self._get_weekday(forecast.get("fxDate", "")),
            "weather_day": forecast.get("textDay", "晴"),
            "weather_night": forecast.get("textNight", "晴"),
            "weather_code": icon_code,
            "weather_icon": weather_icon,
            "temp_max": forecast.get("tempMax", "25"),
            "temp_min": forecast.get("tempMin", "15"),
            "wind_dir_day": forecast.get("windDirDay", "无持续风向"),
            "wind_scale_day": forecast.get("windScaleDay", "1-2"),
            "humidity": forecast.get("humidity", "50"),
            "precip": forecast.get("precip", "0"),  # 降水量
            "uv_index": forecast.get("uvIndex", "3"),  # 紫外线指数
            "sunrise": sunrise,
            "sunset": sunset,
            "daylight_hours": self._calculate_daylight_hours(sunrise, sunset),
            "suggestions": suggestions,
            "aqi": forecast.get("aqi", "50"),  # 空气质量指数
            "aqi_level": aqi_levels.get(forecast.get("category", "2"), "良")
        }
    
    def _get_weather_icon(self, weather_code: str) -> str:
        """获取天气图标"""
        icon_map = {
            "100": "☀️",  # 晴
            "101": "⛅",  # 多云
            "102": "🌤️",  # 少云
            "103": "🌥️",  # 晴间多云
            "104": "☁️",  # 阴
            "300": "🌦️",  # 阵雨
            "301": "🌧️",  # 强阵雨
            "302": "⛈️",  # 雷阵雨
            "305": "🌧️",  # 小雨
            "306": "🌧️",  # 中雨
            "307": "💦",  # 大雨
            "400": "🌨️",  # 小雪
            "401": "❄️",  # 中雪
            "402": "☃️",  # 大雪
            "500": "🌫️",  # 薄雾
            "501": "🌁",  # 雾
            "502": "😷",  # 霾
        }
        return icon_map.get(weather_code, "🌈")
    
    def _get_weekday(self, date_str: str) -> str:
        """获取星期几"""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            return weekdays[date_obj.weekday()]
        except:
            return ""
    
    def _calculate_daylight_hours(self, sunrise: str, sunset: str) -> str:
        """计算日照时长"""
        try:
            sunrise_time = datetime.strptime(sunrise, "%H:%M")
            sunset_time = datetime.strptime(sunset, "%H:%M")
            daylight = sunset_time - sunrise_time
            hours = daylight.seconds // 3600
            minutes = (daylight.seconds % 3600) // 60
            return f"{hours}小时{minutes}分钟"
        except:
            return "12小时"
    
    def _generate_travel_suggestions(self, weather: str, temp_max: int, temp_min: int) -> List[str]:
        """生成出行建议"""
        suggestions = []
        
        # 温度建议
        avg_temp = (temp_max + temp_min) / 2
        if avg_temp >= 30:
            suggestions.append("天气炎热，注意防暑降温")
        elif avg_temp >= 25:
            suggestions.append("天气温暖，适合户外活动")
        elif avg_temp >= 15:
            suggestions.append("天气凉爽，建议携带薄外套")
        elif avg_temp >= 5:
            suggestions.append("天气较冷，注意保暖")
        else:
            suggestions.append("天气寒冷，注意防寒")
        
        # 天气建议
        if "雨" in weather:
            suggestions.append("有降雨，建议携带雨具")
        if "雪" in weather:
            suggestions.append("有降雪，注意路面湿滑")
        if "雷" in weather:
            suggestions.append("有雷电，避免户外活动")
        if "雾" in weather or "霾" in weather:
            suggestions.append("能见度较低，出行注意安全")
        if "晴" in weather and temp_max >= 28:
            suggestions.append("紫外线较强，注意防晒")
        
        # 通用建议
        suggestions.append("建议穿着舒适的鞋子")
        
        return suggestions[:4]  # 最多4条建议
    
    def get_real_time_weather(self, city_name: str) -> Dict:
        """获取实时天气"""
        city_code = self.get_city_code(city_name)
        if not city_code:
            return {"status": "error", "message": "无法获取城市代码"}
        
        url = f"{self.base_url}/weather/now"
        params = {
            "location": city_code,
            "key": self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            if data.get("code") == "200":
                now = data.get("now", {})
                return {
                    "status": "success",
                    "temp": now.get("temp", "25"),
                    "feels_like": now.get("feelsLike", "25"),
                    "weather": now.get("text", "晴"),
                    "wind_dir": now.get("windDir", "无持续风向"),
                    "wind_scale": now.get("windScale", "1-2"),
                    "humidity": now.get("humidity", "50"),
                    "visibility": now.get("vis", "10"),  # 能见度
                    "update_time": data.get("updateTime", "")
                }
            else:
                return {"status": "error", "message": data.get("message", "获取实时天气失败")}
                
        except Exception as e:
            return {"status": "error", "message": f"网络请求失败: {str(e)}"}

# 备用方案：如果API不可用，使用模拟数据
class MockWeatherService:
    """模拟天气服务（备用方案）"""
    
    def get_weather_forecast(self, city_name: str, start_date: str, end_date: str) -> Dict:
        """模拟天气预测"""
        import random
        
        # 解析日期
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days = (end - start).days + 1
        
        weather_types = ["晴", "多云", "阴", "小雨", "中雨", "阵雨", "雷阵雨"]
        icons = ["☀️", "⛅", "☁️", "🌧️", "🌧️", "🌦️", "⛈️"]
        forecasts = []
        
        for i in range(min(days, 7)):
            current_date = start + timedelta(days=i)
            weather_idx = random.randint(0, len(weather_types)-1)
            
            forecasts.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "weekday": self._get_weekday(current_date),
                "weather_day": weather_types[weather_idx],
                "weather_night": "晴",
                "weather_icon": icons[weather_idx],
                "temp_max": str(random.randint(20, 35)),
                "temp_min": str(random.randint(10, 25)),
                "wind_dir_day": random.choice(["东北风", "东南风", "西南风", "西北风"]),
                "wind_scale_day": f"{random.randint(1, 4)}-{random.randint(2, 5)}",
                "humidity": str(random.randint(40, 90)),
                "precip": str(random.randint(0, 50)),
                "suggestions": ["建议携带雨具", "注意防晒", "穿着舒适"]
            })
        
        return {
            "status": "success",
            "city": city_name,
            "start_date": start_date,
            "end_date": end_date,
            "total_days": days,
            "forecast": forecasts,
            "is_mock": True,
            "message": "此为模拟数据，请配置和风天气API获取真实数据"
        }
    
    def _get_weekday(self, date_obj):
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        return weekdays[date_obj.weekday()]

# 工厂函数，根据配置返回合适的服务
def get_weather_service():
    """获取天气服务实例"""
    import os
    api_key = os.getenv("QWEATHER_API_KEY", "")
    
    if api_key and api_key != "你的和风天气API_Key":
        return WeatherService()
    else:
        return MockWeatherService()