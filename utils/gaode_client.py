# utils/gaode_client.py
import requests
import json
import os
import streamlit as st
from dotenv import load_dotenv
import math

load_dotenv()

class GaodeMapClient:
    """高德地图API客户端"""
    
    def __init__(self):
        self.api_key = os.getenv("GAODE_MAP_API_KEY", "")
        self.base_urls = {
            "geocode": "https://restapi.amap.com/v3/geocode/geo",  # 地理编码
            "place": "https://restapi.amap.com/v3/place/text",  # 地点搜索
            "around": "https://restapi.amap.com/v3/place/around",  # 周边搜索
            "route": "https://restapi.amap.com/v3/direction/transit/integrated",  # 路线规划
            "static_map": "https://restapi.amap.com/v3/staticmap"  # 静态地图
        }
        
        if not self.api_key:
            st.warning("⚠️ 高德地图API密钥未配置")
    
    def geocode(self, address, city=None):
        """地址转坐标"""
        params = {
            'address': address,
            'key': self.api_key,
            'output': 'json'
        }
        
        if city:
            params['city'] = city
        
        try:
            response = requests.get(self.base_urls["geocode"], params=params, timeout=10)
            data = response.json()
            
            if data.get('status') == '1' and data.get('geocodes'):
                geocode = data['geocodes'][0]
                location = geocode.get('location')  # "lng,lat"
                
                return {
                    "status": "success",
                    "location": location,
                    "formatted_address": geocode.get('formatted_address', address),
                    "city": geocode.get('city', ''),
                    "district": geocode.get('district', '')
                }
            else:
                return {"status": "error", "message": data.get('info', '地理编码失败')}
                
        except Exception as e:
            return {"status": "error", "message": f"请求异常: {str(e)}"}
    
    def search_attractions(self, city_name, city_location, count=10):
        """搜索景点"""
        params = {
            'key': self.api_key,
            'keywords': '景点',
            'location': city_location,
            'types': '风景名胜|公园广场|博物馆|展览馆',
            'city': city_name,
            'citylimit': 'true',
            'offset': min(count, 25),
            'page': 1,
            'extensions': 'all',
            'output': 'json'
        }
        
        try:
            response = requests.get(self.base_urls["around"], params=params, timeout=10)
            data = response.json()
            
            if data.get('status') == '1':
                pois = data.get('pois', [])
                results = []
                
                for poi in pois:
                    results.append({
                        'name': poi.get('name', ''),
                        'location': poi.get('location', ''),
                        'address': poi.get('address', ''),
                        'type': poi.get('type', ''),
                        'rating': float(poi.get('biz_ext', {}).get('rating', 0) or 0),
                        'photos': poi.get('photos', []),
                        'telephone': poi.get('tel', ''),
                        'detail_url': f"https://www.amap.com/place/{poi.get('id', '')}"
                    })
                
                return {
                    "status": "success",
                    "results": results,
                    "total": len(results),
                    "message": f"找到{len(results)}个景点"
                }
            else:
                return {"status": "error", "message": data.get('info', '搜索失败')}
                
        except Exception as e:
            return {"status": "error", "message": f"请求异常: {str(e)}"}
    
    def plan_route(self, origin, destination, city=None):
        """
        规划公共交通路线
        Returns: 详细的路线步骤，包括步行、地铁、公交等
        """
        params = {
            'key': self.api_key,
            'origin': origin,  # "lng,lat"
            'destination': destination,  # "lng,lat"
            'city': city or '',
            'output': 'json',
            'extensions': 'all',
            'strategy': 0  # 最快捷模式
        }
        
        try:
            response = requests.get(self.base_urls["route"], params=params, timeout=10)
            data = response.json()
            
            if data.get('status') == '1' and data.get('route'):
                route = data['route']
                paths = route.get('paths', [])
                
                if paths:
                    best_path = paths[0]  # 取最优路线
                    return self._parse_route_details(best_path)
                
            return {"status": "error", "message": "未找到路线"}
                
        except Exception as e:
            return {"status": "error", "message": f"请求异常: {str(e)}"}
    
    def _parse_route_details(self, path):
        """解析路线详细信息"""
        distance = path.get('distance', 0)  # 总距离（米）
        duration = path.get('duration', 0)  # 总时间（秒）
        steps = []
        
        # 解析每个步骤
        for segment in path.get('steps', []):
            instruction = segment.get('instruction', '')
            step_distance = segment.get('distance', 0)
            step_duration = segment.get('duration', 0)
            action = segment.get('action', '')
            
            # 解析交通方式
            vehicle = self._parse_vehicle_type(segment)
            
            steps.append({
                'instruction': instruction,
                'distance': step_distance,
                'duration': step_duration,
                'vehicle': vehicle,
                'action': action,
                'road': segment.get('road', ''),
                'polyline': segment.get('polyline', '')
            })
        
        return {
            "status": "success",
            "total_distance": distance,
            "total_duration": duration,
            "steps": steps,
            "taxi_cost": path.get('taxi_cost', 0)
        }
    
    def _parse_vehicle_type(self, segment):
        """解析交通方式"""
        instruction = segment.get('instruction', '').lower()
        
        if '步行' in instruction or 'walk' in instruction:
            return {'type': 'walking', 'icon': '🚶', 'name': '步行'}
        elif '地铁' in instruction or 'subway' in instruction:
            # 提取地铁线路
            import re
            line_match = re.search(r'地铁(\w+)号线', instruction)
            line = line_match.group(1) if line_match else ''
            return {'type': 'subway', 'icon': '🚇', 'name': f'地铁{line}号线', 'line': line}
        elif '公交' in instruction or 'bus' in instruction:
            # 提取公交线路
            import re
            bus_match = re.search(r'(\w+路)公交', instruction)
            bus_line = bus_match.group(1) if bus_match else '公交'
            return {'type': 'bus', 'icon': '🚌', 'name': bus_line}
        elif '出租车' in instruction or 'taxi' in instruction:
            return {'type': 'taxi', 'icon': '🚕', 'name': '出租车'}
        else:
            return {'type': 'other', 'icon': '📍', 'name': '其他'}
    
    def get_static_map(self, location, zoom=13, size="800*600", markers=None):
        """获取静态地图图片"""
        params = {
            'key': self.api_key,
            'location': location,
            'zoom': zoom,
            'size': size,
            'scale': 2  # 高清
        }
        
        # 添加标记点
        if markers:
            markers_str = []
            for i, marker in enumerate(markers):
                label = chr(65 + i)  # A, B, C...
                marker_str = f"mid,0xFF0000,{label}:{marker['location']}"
                markers_str.append(marker_str)
            params['markers'] = "|".join(markers_str)
        
        try:
            response = requests.get(self.base_urls["static_map"], params=params, timeout=10)
            if response.status_code == 200:
                # 返回base64编码的图片
                import base64
                image_base64 = base64.b64encode(response.content).decode()
                return f"data:image/png;base64,{image_base64}"
        except:
            pass
        
        return None
    
    def search_hotels_real(self, city_name, city_location, budget_range, count=10):
        """
        搜索真实酒店
        budget_range: (min_price, max_price)
        """
        # 先搜索酒店
        params = {
            'key': self.api_key,
            'keywords': '酒店',
            'location': city_location,
            'types': '宾馆|旅馆|酒店|度假村',
            'city': city_name,
            'citylimit': 'true',
            'radius': 5000,  # 5公里范围内
            'offset': min(count * 2, 25),  # 多搜一些用于筛选
            'page': 1,
            'extensions': 'all',
            'output': 'json'
        }
        
        try:
            response = requests.get(self.base_urls["around"], params=params, timeout=10)
            data = response.json()
            
            if data.get('status') == '1':
                pois = data.get('pois', [])
                hotels = []
                
                for poi in pois:
                    hotel = self._format_hotel_data(poi, budget_range)
                    if hotel:
                        hotels.append(hotel)
                
                # 按评分排序
                hotels.sort(key=lambda x: x.get('rating', 0), reverse=True)
                
                return {
                    "status": "success",
                    "hotels": hotels[:count],
                    "total": len(hotels),
                    "message": f"找到{len(hotels)}个酒店"
                }
            else:
                return {"status": "error", "message": data.get('info', '搜索失败')}
                
        except Exception as e:
            return {"status": "error", "message": f"请求异常: {str(e)}"}
    
    def _format_hotel_data(self, poi_data, budget_range):
        """格式化酒店数据"""
        try:
            name = poi_data.get('name', '')
            address = poi_data.get('address', '')
            location = poi_data.get('location', '')
            telephone = poi_data.get('tel', '')
            
            # 获取详细信息
            biz_ext = poi_data.get('biz_ext', {})
            rating = float(biz_ext.get('rating', 0) or 0)
            
            # 解析价格
            cost = biz_ext.get('cost', '')
            price = self._extract_price(cost, name)
            
            # 检查是否符合预算
            min_price, max_price = budget_range
            if price and not (min_price <= price <= max_price):
                return None
            
            # 解析酒店类型
            hotel_type = self._parse_hotel_type(poi_data.get('type', ''), name)
            
            # 解析设施
            facilities = self._parse_facilities(poi_data.get('tag', ''))
            
            # 生成链接
            hotel_id = poi_data.get('id', '')
            detail_url = f"https://www.amap.com/place/{hotel_id}"
            
            # 生成预订链接 - 修复这里的错误
            import urllib.parse
            encoded_name = urllib.parse.quote(name)
            encoded_city = poi_data.get('cityname', '')  # 使用POI数据中的城市名
            booking_url = f"https://hotels.ctrip.com/hotels/list?keyword={encoded_name}&city={encoded_city}"
            
            return {
                'id': hotel_id,
                'name': name,
                'address': address,
                'location': location,
                'telephone': telephone,
                'rating': rating,
                'price': price,
                'price_display': f"{price}元/晚" if price else "价格待询",
                'type': hotel_type,
                'facilities': facilities,
                'rating_stars': "⭐" * int(rating) if rating > 0 else "暂无评分",
                'detail_url': detail_url,
                'booking_url': booking_url,
                'is_real': True,
                'source': '高德地图'
            }
            
        except Exception as e:
            print(f"格式化酒店数据失败: {e}")
            return None
    
    def _extract_price(self, cost_str, name):
        """提取价格"""
        import re
        
        # 先从cost字段提取
        if cost_str and cost_str.isdigit():
            return int(cost_str)
        
        # 从名称中提取
        patterns = [r'(\d+)-(\d+)元?', r'(\d+)元?', r'￥(\d+)']
        for pattern in patterns:
            match = re.search(pattern, name)
            if match:
                return int(match.group(1))
        
        return None
    
    def _parse_hotel_type(self, type_str, name):
        """解析酒店类型"""
        # 确保 type_str 是字符串
        if isinstance(type_str, list):
            type_str = ', '.join(type_str) if type_str else ""
        elif not isinstance(type_str, str):
            type_str = str(type_str) if type_str else ""
        
        text = (type_str + " " + name).lower()
        
        if any(word in text for word in ["星级", "豪华", "五星", "四星", "国际"]):
            return "豪华酒店"
        elif any(word in text for word in ["商务", "连锁", "快捷", "经济"]):
            return "商务酒店"
        elif any(word in text for word in ["民宿", "客栈", "青旅", "客栈"]):
            return "特色民宿"
        elif any(word in text for word in ["度假", "温泉", "海景", "别墅"]):
            return "度假酒店"
        else:
            return "经济型酒店"

    def _parse_facilities(self, tag_str):
        """解析设施"""
        facilities = []
        
        # 确保 tag_str 是字符串
        if isinstance(tag_str, list):
            tag_str = ', '.join(tag_str) if tag_str else ""
        elif not isinstance(tag_str, str):
            tag_str = str(tag_str) if tag_str else ""
        
        tag_lower = tag_str.lower()
        
        facility_map = {
            "wifi": "WiFi",
            "无线": "WiFi",
            "停车": "停车场",
            "车位": "停车场",
            "早餐": "早餐",
            "餐厅": "餐厅",
            "餐饮": "餐厅",
            "健身房": "健身房",
            "健身": "健身房",
            "游泳池": "游泳池",
            "泳池": "游泳池",
            "商务": "商务中心",
            "会议": "会议室"
        }
        
        for key, facility in facility_map.items():
            if key in tag_lower:
                facilities.append(facility)
        
        return facilities[:4]
    
    def search_restaurants(self, city_name, city_location, keywords=None, count=10, sort_by='rating'):
        """搜索餐厅"""
        params = {
            'key': self.api_key,
            'keywords': keywords or '美食',
            'location': city_location,
            'types': '餐饮服务|中餐厅|外国餐厅|快餐厅|咖啡厅|茶艺馆|冷饮店|糕饼店',
            'city': city_name,
            'citylimit': 'true',
            'radius': 5000,  # 5公里范围内
            'offset': min(count * 2, 25),  # 多搜一些用于筛选
            'page': 1,
            'extensions': 'all',
            'output': 'json'
        }
        
        try:
            response = requests.get(self.base_urls["around"], params=params, timeout=10)
            data = response.json()
            
            if data.get('status') == '1':
                pois = data.get('pois', [])
                restaurants = []
                
                for poi in pois:
                    restaurant = self._format_restaurant_data(poi, city_name)  # ✅ 添加city_name参数
                    if restaurant:
                        restaurants.append(restaurant)
                
                # 排序
                if sort_by == 'rating':
                    restaurants.sort(key=lambda x: x.get('rating', 0), reverse=True)
                elif sort_by == 'price_low':
                    restaurants.sort(key=lambda x: x.get('avg_price', float('inf')))
                elif sort_by == 'price_high':
                    restaurants.sort(key=lambda x: x.get('avg_price', 0), reverse=True)
                
                return {
                    "status": "success",
                    "restaurants": restaurants[:count],
                    "total": len(restaurants),
                    "message": f"找到{len(restaurants)}个餐厅"
                }
            else:
                return {"status": "error", "message": data.get('info', '搜索失败')}
                
        except Exception as e:
            return {"status": "error", "message": f"请求异常: {str(e)}"}

    def _format_restaurant_data(self, poi_data, city_name=""):
        """格式化餐厅数据"""
        try:
            print(f"[DEBUG] 处理餐厅POI: {poi_data.get('name')}")
            print(f"[DEBUG] POI类型字段: {type(poi_data.get('type'))}, 值: {poi_data.get('type')}")
            print(f"[DEBUG] POI标签字段: {type(poi_data.get('tag'))}, 值: {poi_data.get('tag')}")
            
            name = poi_data.get('name', '')
            address = poi_data.get('address', '')
            location = poi_data.get('location', '')
            telephone = poi_data.get('tel', '')
            
            # 获取详细信息
            biz_ext = poi_data.get('biz_ext', {})
            rating = float(biz_ext.get('rating', 0) or 0)
            
            # 解析价格
            cost = biz_ext.get('cost', '')
            avg_price = self._extract_restaurant_price(cost, name)
            
            # 解析餐厅类型和菜系
            type_str = poi_data.get('type', '')
            cuisine, restaurant_type = self._parse_restaurant_type(type_str, name)
            
            # 解析标签/特色
            tag = poi_data.get('tag', '')
            features = self._parse_restaurant_features(tag)
            
            # 检查是否有推荐菜
            recommendation = self._extract_recommendation(name, tag)
            
            # 生成链接
            restaurant_id = poi_data.get('id', '')
            detail_url = f"https://www.amap.com/place/{restaurant_id}"
            
            # 生成点评链接
            import urllib.parse
            encoded_name = urllib.parse.quote(name)
            encoded_city = city_name or poi_data.get('cityname', '')
            review_url = f"https://www.dianping.com/search/keyword/1/0_{encoded_name}"
            
            restaurant_info = {
                'id': restaurant_id,
                'name': name,
                'address': address,
                'location': location,
                'telephone': telephone,
                'rating': rating,
                'avg_price': avg_price,
                'price_display': f"人均¥{avg_price}" if avg_price else "价格待询",
                'cuisine': cuisine,
                'type': restaurant_type,
                'features': features,
                'recommendation': recommendation,
                'rating_stars': "⭐" * int(rating) if rating > 0 else "暂无评分",
                'detail_url': detail_url,
                'review_url': review_url,
                'is_real': True,
                'source': '高德地图'
            }
            
            print(f"[SUCCESS] 成功格式化餐厅: {name}")
            return restaurant_info
            
        except Exception as e:
            print(f"[ERROR] 格式化餐厅数据失败: {e}, POI数据: {json.dumps(poi_data, ensure_ascii=False)[:200]}")
            return None
        
    def _extract_restaurant_price(self, cost_str, name):
        """提取餐厅人均价格"""
        import re
        
        # 先从cost字段提取
        if cost_str and cost_str.isdigit():
            price = int(cost_str)
            return price if price > 10 else price * 100  # 假设是百位
        
        # 从名称中提取
        patterns = [r'人均(\d+)元?', r'人均(\d+)-(\d+)元?', r'¥?(\d+)元/人']
        for pattern in patterns:
            match = re.search(pattern, name)
            if match:
                return int(match.group(1))
        
        # 根据餐厅类型估算
        text = name.lower()
        if any(word in text for word in ["快餐", "小吃", "简餐"]):
            return 30
        elif any(word in text for word in ["咖啡", "奶茶", "甜品"]):
            return 40
        elif any(word in text for word in ["家常", "川菜", "湘菜", "粤菜"]):
            return 80
        elif any(word in text for word in ["日料", "西餐", "法式", "意大利"]):
            return 150
        elif any(word in text for word in ["高端", "豪华", "五星"]):
            return 300
        else:
            return 60  # 默认

    def _parse_restaurant_type(self, type_str, name):
        """解析餐厅类型和菜系"""
        # 确保 type_str 是字符串
        if isinstance(type_str, list):
            type_str = ', '.join(type_str) if type_str else ""
        elif not isinstance(type_str, str):
            type_str = str(type_str) if type_str else ""
        
        text = (type_str + " " + name).lower()
        
        # 菜系
        cuisine_map = {
            "川菜": ["川菜", "四川", "火锅", "麻辣", "串串", "重庆"],
            "湘菜": ["湘菜", "湖南", "辣椒", "剁椒"],
            "粤菜": ["粤菜", "广东", "港式", "茶餐厅", "早茶", "烧腊"],
            "江浙菜": ["江浙", "本帮菜", "苏菜", "杭帮菜", "上海菜"],
            "日料": ["日式", "日料", "寿司", "刺身", "拉面", "居酒屋"],
            "西餐": ["西餐", "牛排", "意面", "披萨", "汉堡", "西式"],
            "火锅": ["火锅", "涮肉", "串串", "麻辣烫"],
            "快餐": ["快餐", "汉堡", "炸鸡", "简餐", "便当"],
            "咖啡": ["咖啡", "咖啡馆", "星巴克", "瑞幸", "奶茶"],
            "甜品": ["甜品", "蛋糕", "奶茶", "冰激凌", "烘焙"]
        }
        
        cuisine = "其他"
        for cuisine_name, keywords in cuisine_map.items():
            if any(keyword in text for keyword in keywords):
                cuisine = cuisine_name
                break
        
        # 餐厅类型
        if any(word in text for word in ["连锁", "快餐", "简餐", "便当"]):
            restaurant_type = "快餐简餐"
        elif any(word in text for word in ["咖啡", "茶饮", "甜品", "奶茶", "面包"]):
            restaurant_type = "咖啡甜品"
        elif any(word in text for word in ["火锅", "烧烤", "串串", "烤肉"]):
            restaurant_type = "火锅烧烤"
        elif any(word in text for word in ["高端", "豪华", "五星", "米其林", "会所"]):
            restaurant_type = "高端餐厅"
        elif any(word in text for word in ["家常", "小炒", "排档", "土菜"]):
            restaurant_type = "家常菜馆"
        elif any(word in text for word in ["自助", "自助餐"]):
            restaurant_type = "自助餐厅"
        else:
            restaurant_type = "普通餐厅"
        
        return cuisine, restaurant_type

    def _parse_restaurant_features(self, tag_str):
        """解析餐厅特色"""
        features = []
        
        # 确保 tag_str 是字符串
        if isinstance(tag_str, list):
            tag_str = ', '.join(tag_str) if tag_str else ""
        elif not isinstance(tag_str, str):
            tag_str = str(tag_str) if tag_str else ""
        
        tag_lower = tag_str.lower()
        
        feature_map = {
            "wifi": "免费WiFi",
            "无线": "免费WiFi",
            "停车": "停车位",
            "车位": "停车位",
            "外卖": "支持外卖",
            "团购": "有团购",
            "优惠": "有优惠",
            "包间": "有包间",
            "包厢": "有包间",
            "24小时": "24小时营业",
            "全天": "24小时营业",
            "景观": "景观位",
            "观景": "景观位",
            "露天": "露天座位",
            "室外": "露天座位",
            "儿童": "儿童友好",
            "亲子": "儿童友好"
        }
        
        for key, feature in feature_map.items():
            if key in tag_lower:
                features.append(feature)
        
        return features[:4]  # 最多返回4个特色

    def _extract_recommendation(self, name, tag):
        """提取推荐菜"""
        import random
        
        # 确保 tag 是字符串
        if isinstance(tag, list):
            tag = ', '.join(tag) if tag else ""
        elif not isinstance(tag, str):
            tag = str(tag) if tag else ""
        
        text = (name + " " + tag).lower()
        
        recommendations = {
            "火锅": ["毛肚", "肥牛", "虾滑", "鸭血", "黄喉", "牛肉丸"],
            "川菜": ["水煮鱼", "回锅肉", "麻婆豆腐", "夫妻肺片", "宫保鸡丁", "鱼香肉丝"],
            "湘菜": ["剁椒鱼头", "小炒肉", "毛氏红烧肉", "湘西腊肉", "口味虾"],
            "粤菜": ["烧鹅", "叉烧", "虾饺", "肠粉", "白切鸡", "煲仔饭"],
            "日料": ["三文鱼刺身", "寿司拼盘", "天妇罗", "烤鳗鱼", "味增汤", "乌冬面"],
            "西餐": ["牛排", "意大利面", "披萨", "沙拉", "汉堡", "薯条"],
            "咖啡": ["拿铁", "美式咖啡", "卡布奇诺", "摩卡", "焦糖玛奇朵"],
            "甜品": ["提拉米苏", "芝士蛋糕", "芒果布丁", "杨枝甘露", "珍珠奶茶"]
        }
        
        # 根据餐厅类型推荐
        for cuisine, dishes in recommendations.items():
            if cuisine in text:
                return random.choice(dishes)
        
        # 默认推荐
        default_dishes = ["招牌菜", "特色菜", "人气菜品", "主厨推荐"]
        return random.choice(default_dishes)
