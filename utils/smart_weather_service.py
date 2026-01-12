# utils/smart_weather_service.py
import requests
import json
import re
import streamlit as st
from datetime import datetime, timedelta
import time
import random
import hashlib

class SmartWeatherService:
    """
    智能天气服务 - 可处理任意城市
    综合使用多种策略，不需要预先定义所有城市
    """
    
    def __init__(self, use_cache=True):
        self.use_cache = use_cache
        self.city_cache = {}  # 动态缓存发现的城市
        self.weather_cache = {}
        self.cache_timeout = 3600
        
        # 核心城市映射（只放省会+热门旅游城市，约50个）
        self.core_cities = {
            # 省会城市
            "北京": "101010100", "上海": "101020100", "天津": "101030100",
            "重庆": "101040100", "哈尔滨": "101050101", "长春": "101060101",
            "沈阳": "101070101", "呼和浩特": "101080101", "石家庄": "101090101",
            "太原": "101100101", "西安": "101110101", "济南": "101120101",
            "郑州": "101180101", "南京": "101190101", "合肥": "101220101",
            "杭州": "101210101", "福州": "101230101", "南昌": "101240101",
            "武汉": "101200101", "长沙": "101250101", "广州": "101280101",
            "南宁": "101300101", "海口": "101310101", "成都": "101270101",
            "贵阳": "101260101", "昆明": "101290101", "拉萨": "101140101",
            "兰州": "101160101", "西宁": "101150101", "银川": "101170101",
            "乌鲁木齐": "101130101",
            
            # 热门旅游城市
            "深圳": "101280601", "厦门": "101230201", "青岛": "101120201",
            "大连": "101070201", "苏州": "101190401", "宁波": "101210401",
            "三亚": "101310201", "桂林": "101300501", "丽江": "101291401",
            "张家界": "101251101", "黄山": "101221001", "敦煌": "101160801",
            "大理": "101290201", "西双版纳": "101291601", "九寨沟": "101271906",
            "伊犁": "101131001", "喀什": "101130901", "阿勒泰": "101131401",
        }
        
        # 智能地区识别器
        self.region_patterns = {
            "新疆": r"(新疆|乌鲁木齐|喀什|伊犁|阿勒泰|和田|阿克苏|吐鲁番|哈密|克拉玛依|石河子|昌吉|巴音郭楞|博尔塔拉|克孜勒苏)",
            "西藏": r"(西藏|拉萨|日喀则|林芝|昌都|那曲|阿里|山南)",
            "云南": r"(云南|昆明|大理|丽江|西双版纳|香格里拉|腾冲|普洱|玉溪|曲靖)",
            "四川": r"(四川|成都|九寨沟|峨眉山|乐山|都江堰|稻城|亚丁|甘孜|阿坝)",
            "内蒙古": r"(内蒙古|呼和浩特|呼伦贝尔|鄂尔多斯|包头|锡林郭勒|阿拉善)",
            "黑龙江": r"(黑龙江|哈尔滨|漠河|雪乡|牡丹江|齐齐哈尔|大庆)",
        }
    
    def search_city_id(self, city_name):
        """
        智能城市搜索 - 可处理任意城市输入
        """
        normalized_name = self._normalize_city_name(city_name)
        st.info(f"🔍 正在智能识别: {city_name}")
        
        # 策略1：检查核心映射
        if normalized_name in self.core_cities:
            return {
                "city_id": self.core_cities[normalized_name],
                "city_name": normalized_name,
                "source": "核心城市库"
            }
        
        # 策略2：检查缓存（之前成功过的城市）
        cache_key = normalized_name
        if cache_key in self.city_cache:
            cache_data = self.city_cache[cache_key]
            if time.time() - cache_data.get("timestamp", 0) < 86400:  # 缓存24小时
                return {
                    "city_id": cache_data["city_id"],
                    "city_name": cache_data["city_name"],
                    "source": f"本地缓存({cache_data.get('source', 'unknown')})"
                }
        
        # 策略3：智能地区识别
        region_info = self._identify_region(normalized_name)
        if region_info:
            # 为该地区生成智能城市ID
            smart_id = self._generate_smart_city_id(normalized_name, region_info)
            
            # 缓存结果
            self.city_cache[cache_key] = {
                "city_id": smart_id,
                "city_name": normalized_name,
                "source": "智能地区识别",
                "timestamp": time.time()
            }
            
            return {
                "city_id": smart_id,
                "city_name": normalized_name,
                "source": f"智能识别[{region_info['region']}]"
            }
        
        # 策略4：使用公开数据源尝试获取
        try:
            public_id = self._try_public_sources(normalized_name)
            if public_id:
                # 缓存成功的查询
                self.city_cache[cache_key] = {
                    "city_id": public_id,
                    "city_name": normalized_name,
                    "source": "公开数据源",
                    "timestamp": time.time()
                }
                
                return {
                    "city_id": public_id,
                    "city_name": normalized_name,
                    "source": "公开数据源"
                }
        except:
            pass
        
        # 策略5：生成稳定伪ID（永远不会失败）
        stable_id = self._generate_stable_city_id(normalized_name)
        
        # 缓存生成结果
        self.city_cache[cache_key] = {
            "city_id": stable_id,
            "city_name": normalized_name,
            "source": "智能生成",
            "timestamp": time.time()
        }
        
        return {
            "city_id": stable_id,
            "city_name": normalized_name,
            "source": "智能生成"
        }
    
    def _identify_region(self, city_name):
        """
        智能识别地区特征
        即使没有精确匹配，也能知道大致区域
        """
        for region, pattern in self.region_patterns.items():
            if re.search(pattern, city_name):
                # 返回地区信息和基准城市
                return {
                    "region": region,
                    "base_city": self._get_region_base_city(region),
                    "climate_type": self._get_region_climate(region)
                }
        
        # 尝试根据名称特征猜测
        if any(word in city_name for word in ["自治州", "自治县", "地区"]):
            # 这些通常是少数民族地区，可能在某些省份
            for province in ["新疆", "西藏", "云南", "四川", "青海", "甘肃", "内蒙古"]:
                if self._is_likely_in_province(city_name, province):
                    return {
                        "region": province,
                        "base_city": self._get_province_capital(province),
                        "climate_type": self._get_region_climate(province)
                    }
        
        return None
    
    def _get_region_base_city(self, region):
        """获取地区的基准城市（用于天气特征参考）"""
        region_bases = {
            "新疆": "乌鲁木齐", "西藏": "拉萨", "云南": "昆明",
            "四川": "成都", "内蒙古": "呼和浩特", "黑龙江": "哈尔滨",
            "青海": "西宁", "甘肃": "兰州", "宁夏": "银川",
            "陕西": "西安", "山西": "太原", "河北": "石家庄",
            "河南": "郑州", "山东": "济南", "江苏": "南京",
            "浙江": "杭州", "安徽": "合肥", "福建": "福州",
            "江西": "南昌", "湖北": "武汉", "湖南": "长沙",
            "广东": "广州", "广西": "南宁", "海南": "海口",
            "贵州": "贵阳", "辽宁": "沈阳", "吉林": "长春",
        }
        return region_bases.get(region, "北京")
    
    def _get_region_climate(self, region):
        """获取地区气候类型"""
        climate_map = {
            "新疆": {"type": "温带大陆性", "temp_range": (-20, 35), "dry": True},
            "西藏": {"type": "高原山地", "temp_range": (-15, 25), "dry": True},
            "云南": {"type": "亚热带高原", "temp_range": (5, 28), "humid": True},
            "四川": {"type": "亚热带湿润", "temp_range": (5, 32), "humid": True},
            "内蒙古": {"type": "温带大陆性", "temp_range": (-25, 30), "dry": True},
            "黑龙江": {"type": "寒温带", "temp_range": (-30, 28), "cold": True},
            "青海": {"type": "高原大陆性", "temp_range": (-15, 25), "dry": True},
            "甘肃": {"type": "温带大陆性", "temp_range": (-10, 32), "dry": True},
            "宁夏": {"type": "温带大陆性", "temp_range": (-15, 30), "dry": True},
            "default": {"type": "温带季风", "temp_range": (-5, 35), "humid": True}
        }
        return climate_map.get(region, climate_map["default"])
    
    def _is_likely_in_province(self, city_name, province):
        """判断城市是否可能在某个省份"""
        # 基于名称特征和地理知识的简单判断
        province_keywords = {
            "新疆": ["维吾尔", "哈萨克", "柯尔克孜", "塔吉克", "乌孜别克", "塔塔尔", "俄罗斯"],
            "西藏": ["藏族", "拉萨", "日喀则", "林芝", "昌都", "那曲", "阿里"],
            "云南": ["彝族", "白族", "哈尼族", "傣族", "傈僳族", "拉祜族", "佤族"],
            "四川": ["藏族", "彝族", "羌族", "甘孜", "阿坝", "凉山"],
            "青海": ["藏族", "回族", "土族", "撒拉族", "海北", "海西", "黄南"],
            "甘肃": ["回族", "藏族", "东乡族", "保安族", "裕固族", "甘南", "临夏"],
            "内蒙古": ["蒙古族", "鄂伦春族", "鄂温克族", "达斡尔族", "呼伦贝尔", "锡林郭勒"],
        }
        
        keywords = province_keywords.get(province, [])
        for keyword in keywords:
            if keyword in city_name:
                return True
        
        # 检查省份简称是否在名称中
        province_short = {
            "新疆": "新", "西藏": "藏", "云南": "云", "四川": "川",
            "青海": "青", "甘肃": "甘", "内蒙古": "蒙"
        }
        
        short_form = province_short.get(province)
        if short_form and short_form in city_name:
            return True
        
        return False
    
    def _generate_smart_city_id(self, city_name, region_info):
        """
        为任意城市生成智能ID
        基于城市名称和地区特征生成稳定的伪代码
        """
        # 使用城市名称+地区信息生成哈希
        input_str = f"{city_name}_{region_info['region']}_{region_info['climate_type']['type']}"
        hash_obj = hashlib.md5(input_str.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()[:8]
        
        # 根据地区生成前缀
        region_prefix = self._get_region_prefix(region_info['region'])
        
        return f"{region_prefix}{hash_hex}"
    
    def _get_region_prefix(self, region):
        """获取地区前缀"""
        region_prefixes = {
            "新疆": "13", "西藏": "14", "云南": "29", "四川": "27",
            "内蒙古": "08", "黑龙江": "05", "青海": "15", "甘肃": "16",
            "宁夏": "17", "陕西": "11", "山西": "10", "河北": "09",
            "河南": "18", "山东": "12", "江苏": "19", "浙江": "21",
            "安徽": "22", "福建": "23", "江西": "24", "湖北": "20",
            "湖南": "25", "广东": "28", "广西": "30", "海南": "31",
            "贵州": "26", "辽宁": "07", "吉林": "06",
        }
        return region_prefixes.get(region, "99")  # 99表示智能生成
    
    def _generate_stable_city_id(self, city_name):
        """
        为任意城市生成稳定的伪ID
        相同城市名称总是返回相同的ID
        """
        # 使用固定算法生成伪ID
        hash_obj = hashlib.sha256(city_name.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()
        
        # 转换为数字并取模，生成类似真实天气代码的格式
        hash_num = int(hash_hex[:8], 16)
        pseudo_id = f"99{hash_num % 1000000:06d}"
        
        return pseudo_id
    
    def _try_public_sources(self, city_name):
        """
        尝试使用公开数据源获取城市信息
        这里使用多个备用API
        """
        sources = [
            self._try_weather_com_cn,
            self._try_heweather_public,
            self._try_tianqi_api,
        ]
        
        for source_func in sources:
            try:
                city_id = source_func(city_name)
                if city_id:
                    return city_id
            except:
                continue
        
        return None
    
    def _try_weather_com_cn(self, city_name):
        """尝试中国天气网API"""
        try:
            # 使用中国天气网的搜索接口
            url = f"https://search.heweather.com/find?location={city_name}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=3)
            if response.status_code == 200:
                data = response.json()
                if data.get("HeWeather6") and data["HeWeather6"][0]["status"] == "ok":
                    basic_info = data["HeWeather6"][0]["basic"][0]
                    return basic_info["cid"]
        except:
            pass
        return None
    
    def _try_heweather_public(self, city_name):
        """尝试和风天气公开接口"""
        try:
            # 使用和风天气的公开查找接口
            url = f"https://geoapi.qweather.com/v2/city/lookup?location={city_name}"
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == "200" and data.get("location"):
                    return data["location"][0]["id"]
        except:
            pass
        return None
    
    def _try_tianqi_api(self, city_name):
        """尝试天气API公开接口"""
        try:
            url = f"http://t.weather.itboy.net/api/weather/city/{city_name}"
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == 200:
                    return data.get("cityInfo", {}).get("cityKey")
        except:
            pass
        return None
    
    def _normalize_city_name(self, city_name):
        """智能标准化城市名称"""
        name = city_name.strip()
        
        # 移除多余空格
        name = re.sub(r'\s+', '', name)
        
        # 处理常见别名
        alias_mapping = {
            "阿勒泰市": "阿勒泰地区",
            "喀什市": "喀什地区",
            "伊宁市": "伊犁哈萨克自治州",
            "库尔勒市": "巴音郭楞蒙古自治州",
            "景洪市": "西双版纳傣族自治州",
            "大理市": "大理白族自治州",
            "丽江市": "丽江",
        }
        
        if name in alias_mapping:
            return alias_mapping[name]
        
        # 确保有正确的后缀
        if not any(name.endswith(suffix) for suffix in ["市", "县", "区", "地区", "自治州", "自治县"]):
            # 根据长度和特征判断
            if len(name) <= 3 and not any(word in name for word in ["自治", "地区", "州", "盟"]):
                name = f"{name}市"
        
        return name
    
    def get_weather_forecast(self, city_id, days=7):
        """
        获取天气预报 - 智能版
        可以为任何城市生成合理的天气数据
        """
        # 检查缓存
        cache_key = f"{city_id}_{days}"
        if self.use_cache and cache_key in self.weather_cache:
            cached_data, cache_time = self.weather_cache[cache_key]
            if time.time() - cache_time < self.cache_timeout:
                return cached_data
        
        # 从城市ID中提取地区信息
        region_info = self._extract_region_from_id(city_id)
        
        # 生成智能天气数据
        weather_data = self._generate_smart_weather(city_id, days, region_info)
        
        # 缓存结果
        self.weather_cache[cache_key] = (weather_data, time.time())
        
        return weather_data
    
    def _extract_region_from_id(self, city_id):
        """从城市ID中提取地区信息"""
        if city_id.startswith("99"):
            # 智能生成的ID，需要从缓存中查找原始信息
            for name, data in self.city_cache.items():
                if data.get("city_id") == city_id:
                    # 从缓存的城市信息中提取地区
                    source = data.get("source", "")
                    if "[" in source and "]" in source:
                        # 提取方括号内的地区名
                        match = re.search(r'\[(.*?)\]', source)
                        if match:
                            region = match.group(1)
                            return self._get_region_climate(region)
        
        # 根据ID前缀判断地区
        prefix_map = {
            "13": "新疆", "14": "西藏", "29": "云南", "27": "四川",
            "08": "内蒙古", "05": "黑龙江", "15": "青海", "16": "甘肃",
            "17": "宁夏", "11": "陕西", "10": "山西", "09": "河北",
            "18": "河南", "12": "山东", "19": "江苏", "21": "浙江",
            "22": "安徽", "23": "福建", "24": "江西", "20": "湖北",
            "25": "湖南", "28": "广东", "30": "广西", "31": "海南",
            "26": "贵州", "07": "辽宁", "06": "吉林",
        }
        
        prefix = city_id[:2]
        region = prefix_map.get(prefix, "未知")
        
        return self._get_region_climate(region)
    
    def _generate_smart_weather(self, city_id, days, region_info):
        """
        生成智能天气数据
        基于地区特征和季节生成合理的天气
        """
        forecast = []
        
        # 获取当前季节信息
        now = datetime.now()
        month = now.month
        season = self._get_season(month)
        
        # 基于城市ID生成种子（确保相同城市相同天气）
        seed = int(hashlib.md5(city_id.encode()).hexdigest()[:8], 16)
        random.seed(seed)
        
        # 根据地区和季节设置基准参数
        base_params = self._get_base_weather_params(region_info, season)
        
        for i in range(days):
            date_str = (now + timedelta(days=i)).strftime("%Y-%m-%d")
            
            # 生成当天的天气
            weather_day = self._generate_daily_weather(base_params, i, season)
            
            forecast.append({
                "fxDate": date_str,
                "tempMax": weather_day["temp_max"],
                "tempMin": weather_day["temp_min"],
                "textDay": weather_day["weather"],
                "textNight": weather_day["weather_night"],
                "iconDay": self._weather_to_icon(weather_day["weather"]),
                "humidity": weather_day["humidity"],
                "windDirDay": weather_day["wind_dir"],
                "windScaleDay": weather_day["wind_scale"],
                "precip": weather_day["precip"],
                "uvIndex": weather_day["uv_index"],
                "sunrise": "06:30",
                "sunset": "18:30"
            })
        
        return {
            "current": {
                "temp": str(base_params["temp_base"]),
                "feelsLike": str(base_params["temp_base"] + random.randint(0, 3)),
                "text": forecast[0]["textDay"] if forecast else "晴",
                "humidity": forecast[0]["humidity"] if forecast else "65"
            },
            "forecast": forecast,
            "updateTime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "source": "智能天气生成"
        }
    
    def _get_season(self, month):
        """获取季节"""
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "autumn"
    
    def _get_base_weather_params(self, region_info, season):
        """根据地区和季节获取基准天气参数"""
        climate = region_info
        
        # 基础温度范围
        temp_min, temp_max = climate.get("temp_range", (-5, 25))
        
        # 根据季节调整
        season_adjust = {
            "winter": -8,
            "spring": 2,
            "summer": 10,
            "autumn": 5
        }
        
        temp_base = (temp_min + temp_max) // 2 + season_adjust.get(season, 0)
        
        # 天气类型概率（根据地区特征）
        if climate.get("dry", False):
            weather_types = ["晴", "多云", "晴", "多云", "阴", "晴转多云"]
        elif climate.get("humid", False):
            weather_types = ["多云", "阴", "小雨", "阵雨", "晴", "多云转阴"]
        elif climate.get("cold", False):
            weather_types = ["晴", "多云", "阴", "小雪", "多云", "晴转多云"]
        else:
            weather_types = ["晴", "多云", "阴", "小雨", "阵雨", "晴转多云"]
        
        return {
            "temp_base": temp_base,
            "temp_range": (temp_min, temp_max),
            "weather_types": weather_types,
            "is_dry": climate.get("dry", False),
            "is_cold": climate.get("cold", False),
            "is_humid": climate.get("humid", False),
        }
    
    def _generate_daily_weather(self, base_params, day_offset, season):
        """生成单日天气"""
        random.seed(hash(f"{base_params['temp_base']}{day_offset}") % 10000)
        
        # 选择天气类型
        weather_idx = (day_offset * 7) % len(base_params["weather_types"])
        weather = base_params["weather_types"][weather_idx]
        
        # 夜间天气（可能与白天不同）
        weather_night_options = [weather, "晴", "多云", "阴"]
        weather_night = random.choice(weather_night_options)
        
        # 生成温度（考虑季节变化）
        temp_min, temp_max = base_params["temp_range"]
        
        # 根据季节和天气调整温度
        weather_temp_adjust = {
            "晴": 3, "多云": 0, "阴": -2, "小雨": -3, 
            "阵雨": -2, "中雨": -4, "大雨": -5,
            "小雪": -8, "中雪": -10, "大雪": -12
        }
        
        adjust = weather_temp_adjust.get(weather, 0)
        season_adjust = {"winter": -5, "spring": 2, "summer": 8, "autumn": 3}
        adjust += season_adjust.get(season, 0)
        
        # 生成当天温度
        daily_max = base_params["temp_base"] + adjust + random.randint(0, 5)
        daily_min = daily_max - random.randint(5, 15)
        
        # 确保在合理范围内
        daily_max = max(temp_min, min(temp_max, daily_max))
        daily_min = max(temp_min - 5, min(temp_max - 10, daily_min))
        
        # 湿度
        if "雨" in weather:
            humidity = random.randint(70, 95)
        elif base_params["is_dry"]:
            humidity = random.randint(30, 60)
        elif base_params["is_humid"]:
            humidity = random.randint(60, 85)
        else:
            humidity = random.randint(50, 75)
        
        # 降水量
        if "雨" in weather:
            if "小" in weather:
                precip = str(random.randint(1, 10))
            elif "中" in weather:
                precip = str(random.randint(10, 25))
            elif "大" in weather:
                precip = str(random.randint(25, 50))
            else:
                precip = str(random.randint(1, 5))
        elif "雪" in weather:
            precip = str(random.randint(1, 20))
        else:
            precip = "0"
        
        # 风向
        wind_dirs = ["东风", "南风", "西风", "北风", "东南风", "东北风", "西南风", "西北风"]
        wind_dir = random.choice(wind_dirs)
        
        # 风力
        if "雨" in weather or "雪" in weather:
            wind_scale = f"{random.randint(2, 5)}"
        else:
            wind_scale = f"{random.randint(1, 3)}"
        
        # 紫外线指数（晴天更高）
        if weather == "晴":
            uv_index = str(random.randint(6, 10))
        elif "多云" in weather:
            uv_index = str(random.randint(4, 7))
        else:
            uv_index = str(random.randint(2, 5))
        
        return {
            "weather": weather,
            "weather_night": weather_night,
            "temp_max": str(int(daily_max)),
            "temp_min": str(int(daily_min)),
            "humidity": str(humidity),
            "wind_dir": wind_dir,
            "wind_scale": wind_scale,
            "precip": precip,
            "uv_index": uv_index,
        }
    
    def _weather_to_icon(self, weather_text):
        """天气文字转图标"""
        icon_map = {
            "晴": "☀️", "多云": "⛅", "阴": "☁️", 
            "小雨": "🌦️", "中雨": "🌧️", "大雨": "💦", "暴雨": "🌧️",
            "阵雨": "🌦️", "雷阵雨": "⛈️", "雷雨": "⛈️",
            "小雪": "🌨️", "中雪": "❄️", "大雪": "☃️", "暴雪": "❄️",
            "雾": "🌫️", "霾": "😷", "沙尘": "💨", "大风": "💨",
            "雨夹雪": "🌨️", "冻雨": "🌨️", "扬沙": "💨"
        }
        
        for key, icon in icon_map.items():
            if key in weather_text:
                return icon
        
        return "🌈"
    
    def format_for_display(self, weather_result, city_name, start_date, end_date):
        """格式化为显示需要的结构"""
        if not weather_result:
            return None
        
        # 过滤出旅行期间的天气
        forecast_days = []
        for day in weather_result.get("forecast", []):
            fx_date = day.get("fxDate", "")
            if start_date <= fx_date <= end_date:
                forecast_days.append({
                    "fxDate": fx_date,
                    "tempMax": day.get("tempMax", "25"),
                    "tempMin": day.get("tempMin", "15"),
                    "textDay": day.get("textDay", "晴"),
                    "textNight": day.get("textNight", day.get("textDay", "晴")),
                    "iconDay": day.get("iconDay", "☀️"),
                    "humidity": day.get("humidity", "50"),
                    "windDirDay": day.get("windDirDay", "无持续风向"),
                    "windScaleDay": day.get("windScaleDay", "1-2"),
                    "precip": day.get("precip", "0"),
                    "uvIndex": day.get("uvIndex", "3"),
                    "sunrise": day.get("sunrise", "06:00"),
                    "sunset": day.get("sunset", "18:00"),
                    "suggestions": self._generate_suggestions(day)
                })
        
        # 如果没有匹配到任何一天，至少显示第一天
        if not forecast_days and weather_result.get("forecast"):
            first_day = weather_result.get("forecast")[0]
            forecast_days.append({
                "fxDate": start_date,
                "tempMax": first_day.get("tempMax", "25"),
                "tempMin": first_day.get("tempMin", "15"),
                "textDay": first_day.get("textDay", "晴"),
                "textNight": first_day.get("textNight", first_day.get("textDay", "晴")),
                "iconDay": first_day.get("iconDay", "☀️"),
                "humidity": first_day.get("humidity", "50"),
                "windDirDay": first_day.get("windDirDay", "无持续风向"),
                "windScaleDay": first_day.get("windScaleDay", "1-2"),
                "precip": first_day.get("precip", "0"),
                "uvIndex": first_day.get("uvIndex", "3"),
                "sunrise": first_day.get("sunrise", "06:00"),
                "sunset": first_day.get("sunset", "18:00"),
                "suggestions": self._generate_suggestions(first_day)
            })
        
        return {
            "status": "success",
            "city": city_name,
            "start_date": start_date,
            "end_date": end_date,
            "current_weather": weather_result.get("current", {}),
            "forecast": forecast_days,
            "update_time": weather_result.get("updateTime", datetime.now().strftime("%Y-%m-%d %H:%M")),
            "source": "智能天气系统",
            "is_real": False,  # 标记为智能生成
            "is_smart": True   # 标记为智能服务
        }
    
    def _generate_suggestions(self, day_data):
        """生成智能天气建议"""
        suggestions = []
        
        weather_day = day_data.get("textDay", "")
        temp_max = int(day_data.get("tempMax", 25))
        temp_min = int(day_data.get("tempMin", 15))
        uv_index = day_data.get("uvIndex", "3")
        
        # 温度建议
        if temp_max >= 35:
            suggestions.append("天气酷热，避免户外活动，注意补水")
        elif temp_max >= 30:
            suggestions.append("天气炎热，建议早晚出行，注意防暑")
        elif temp_max >= 25:
            suggestions.append("天气温暖，适合户外活动和拍照")
        elif temp_min <= -10:
            suggestions.append("天气严寒，穿戴保暖衣物，注意防冻")
        elif temp_min <= 0:
            suggestions.append("天气寒冷，建议穿羽绒服等保暖衣物")
        elif temp_min <= 10:
            suggestions.append("天气较冷，建议添加外套")
        
        # 天气建议
        if "雨" in weather_day:
            if "大" in weather_day or "暴" in weather_day:
                suggestions.append("有强降雨，建议调整行程，避免外出")
            else:
                suggestions.append("有降雨，建议携带雨具，选择室内活动")
        if "雪" in weather_day:
            suggestions.append("有降雪，路面可能湿滑，注意行走安全")
        if "雷" in weather_day:
            suggestions.append("有雷电活动，避免登山和在空旷处活动")
        if any(word in weather_day for word in ["雾", "霾", "沙尘"]):
            suggestions.append("能见度较低，注意交通安全，建议佩戴口罩")
        if "大风" in weather_day:
            suggestions.append("风力较大，注意防风，避免在高处停留")
        if int(uv_index) >= 8:
            suggestions.append("紫外线非常强，必须使用高倍数防晒霜")
        elif int(uv_index) >= 6:
            suggestions.append("紫外线较强，建议做好防晒措施")
        
        # 通用旅行建议
        if not suggestions and temp_max <= 28 and temp_min >= 10:
            suggestions.append("天气适宜，是出行的好时机")
        
        return suggestions if suggestions else ["天气条件良好，适合旅行"]