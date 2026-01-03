# utils/enhanced_map_generator.py
import folium
from folium import plugins
import streamlit as st
from utils.baidu_fetcher import convert_bd09_to_wgs84_str, get_wgs84_coordinates

class EnhancedTravelMap:
    """增强版旅行地图生成器"""
    
    def __init__(self, baidu_client):
        self.baidu_client = baidu_client
    
    def create_intelligent_route_map(self, destination, pois_data, city_location, mode="transit"):
        """
        创建智能路线地图
        Args:
            destination: 目的地名称
            pois_data: 景点数据列表
            city_location: 城市中心坐标
            mode: 交通方式 (walking/transit/driving)
        """
        if not pois_data or len(pois_data) < 2:
            return self.create_simple_map(destination, pois_data, city_location)
        
        try:
            # 获取景点坐标
            poi_locations = []
            valid_pois = []
            
            for poi in pois_data[:10]:  # 最多10个景点
                poi_coords = get_wgs84_coordinates(poi)
                if poi_coords:
                    poi_lng, poi_lat = map(float, poi_coords.split(','))
                    poi_locations.append(poi_coords)
                    valid_pois.append({
                        "data": poi,
                        "coords": poi_coords,
                        "lat": poi_lat,
                        "lng": poi_lng
                    })
            
            if len(valid_pois) < 2:
                return self.create_simple_map(destination, pois_data, city_location)
            
            # 获取路线规划
            bd_locations = [poi["data"].get("location") for poi in valid_pois]
            route_plan = self.baidu_client.get_multi_route_plan(bd_locations, mode)
            
            # 创建地图
            center_coords = convert_bd09_to_wgs84_str(city_location)
            center_lng, center_lat = map(float, center_coords.split(','))
            
            m = folium.Map(
                location=[center_lat, center_lng],
                zoom_start=13,
                control_scale=True
            )
            
            # 添加景点标记
            self._add_poi_markers(m, valid_pois)
            
            # 添加路线
            if route_plan.get("status") == "success":
                self._add_route_lines(m, route_plan["routes"], valid_pois)
            
            # 添加控件
            plugins.Fullscreen(position='topright').add_to(m)
            plugins.MiniMap(position='bottomright').add_to(m)
            plugins.MousePosition(position='bottomleft').add_to(m)
            
            # 添加图例
            self._add_legend(m, destination, len(valid_pois), route_plan, mode)
            
            return m
            
        except Exception as e:
            st.error(f"创建智能地图失败: {e}")
            return self.create_simple_map(destination, pois_data, city_location)
    
    def _add_poi_markers(self, map_obj, pois):
        """添加景点标记"""
        colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 
                  'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue',
                  'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen',
                  'gray', 'black', 'lightgray']
        
        for i, poi in enumerate(pois):
            color = colors[i % len(colors)]
            poi_data = poi["data"]
            
            popup_content = f"""
            <div style="width: 250px;">
                <h4>{poi_data.get('name', f'景点{i+1}')}</h4>
                <p><b>地址:</b> {poi_data.get('address', '地址未知')}</p>
                <p><b>评分:</b> ⭐ {poi_data.get('rating', 0)}/5.0</p>
                <p><b>类型:</b> {poi_data.get('type', '未知')}</p>
                <hr>
                <p><b>路线顺序:</b> 第 {i+1} 站</p>
            </div>
            """
            
            folium.Marker(
                [poi["lat"], poi["lng"]],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=f"{i+1}. {poi_data.get('name', f'景点{i+1}')}",
                icon=folium.Icon(color=color, icon='star', prefix='fa')
            ).add_to(map_obj)
            
            # 添加数字标签
            folium.CircleMarker(
                [poi["lat"], poi["lng"]],
                radius=15,
                color='white',
                weight=2,
                fill=True,
                fill_color=color,
                fill_opacity=1,
                popup=f"第{i+1}站"
            ).add_to(map_obj)
            
            folium.map.Marker(
                [poi["lat"], poi["lng"]],
                icon=folium.DivIcon(
                    icon_size=(150,36),
                    icon_anchor=(0,0),
                    html=f'<div style="font-size: 12pt; color: white; font-weight: bold;">{i+1}</div>'
                )
            ).add_to(map_obj)
    
    def _add_route_lines(self, map_obj, routes, pois):
        """添加路线线条"""
        for i, route in enumerate(routes):
            if i >= len(pois) - 1:
                break
            
            # 获取起点和终点
            start_poi = pois[i]
            end_poi = pois[i + 1]
            
            # 绘制直线连接
            folium.PolyLine(
                [[start_poi["lat"], start_poi["lng"]], [end_poi["lat"], end_poi["lng"]]],
                color='blue',
                weight=3,
                opacity=0.7,
                popup=f"<b>第{i+1}段路线</b><br>从: {start_poi['data'].get('name')}<br>到: {end_poi['data'].get('name')}",
                tooltip=f"第{i+1}段路线"
            ).add_to(map_obj)
            
            # 添加路线信息标记
            mid_lat = (start_poi["lat"] + end_poi["lat"]) / 2
            mid_lng = (start_poi["lng"] + end_poi["lng"]) / 2
            
            # 显示路线详情
            if route.get("steps"):
                steps_text = self._format_route_steps(route["steps"])
                folium.Marker(
                    [mid_lat, mid_lng],
                    icon=folium.DivIcon(
                        icon_size=(250, 100),
                        icon_anchor=(125, 0),
                        html=f'''
                        <div style="background: white; border: 2px solid blue; border-radius: 5px; padding: 5px;">
                            <div style="font-size: 10px; color: blue; font-weight: bold;">
                                第{i+1}段路线<br>
                                距离: {route.get('distance', 0)/1000:.1f}km<br>
                                时间: {route.get('duration', 0)//60}分钟
                            </div>
                        </div>
                        '''
                    )
                ).add_to(map_obj)
    
    def _format_route_steps(self, steps):
        """格式化路线步骤为HTML"""
        html = "<div style='font-size: 12px;'>"
        for step in steps[:3]:  # 只显示前3个步骤
            vehicle = step.get("vehicle", {})
            html += f"""
            <div style='margin: 2px 0; padding: 2px; background: #f0f0f0; border-radius: 3px;'>
                {vehicle.get('icon', '📍')} {step.get('instruction', '')[:30]}...
                ({step.get('distance', 0)}米)
            </div>
            """
        html += "</div>"
        return html
    
    def _add_legend(self, map_obj, destination, poi_count, route_plan, mode):
        """添加图例"""
        total_distance = route_plan.get("total_distance", 0) / 1000  # 转为km
        total_duration = route_plan.get("total_duration", 0) // 60  # 转为分钟
        
        legend_html = f'''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 300px; height: auto;
                    background-color: white; border: 2px solid grey; z-index: 9999; 
                    font-size: 14px; padding: 10px; border-radius: 5px; opacity: 0.95;">
            <b>🗺️ {destination} 智能游览路线</b><br>
            <hr style="margin: 5px 0;">
            <b>📊 路线概览:</b><br>
            • 景点数量: {poi_count}个<br>
            • 交通方式: {"公共交通" if mode == "transit" else "步行" if mode == "walking" else "驾车"}<br>
            • 总距离: {total_distance:.1f}公里<br>
            • 预计时间: {total_duration}分钟<br>
            <hr style="margin: 5px 0;">
            <b>🎯 图例说明:</b><br>
            • 🔴 数字标记: 游览顺序<br>
            • 🔵 蓝色线条: 推荐路线<br>
            • ⭐ 星星标记: 景点位置<br>
            <button onclick="toggleLegend()" style="margin-top: 5px; padding: 3px 10px; 
                     background: #4CAF50; color: white; border: none; border-radius: 3px; cursor: pointer;">
                隐藏/显示
            </button>
        </div>
        
        <script>
        function toggleLegend() {{
            var legend = document.querySelector('[style*="position: fixed; bottom: 50px; left: 50px"]');
            if (legend.style.display === 'none') {{
                legend.style.display = 'block';
            }} else {{
                legend.style.display = 'none';
            }}
        }}
        </script>
        '''
        
        map_obj.get_root().html.add_child(folium.Element(legend_html))
    
    def create_simple_map(self, destination, pois_data, city_location):
        """创建简单地图（备用）"""
        try:
            center_coords = convert_bd09_to_wgs84_str(city_location)
            center_lng, center_lat = map(float, center_coords.split(','))
            
            m = folium.Map(location=[center_lat, center_lng], zoom_start=13)
            
            # 添加景点
            for i, poi in enumerate(pois_data[:8]):
                poi_coords = get_wgs84_coordinates(poi)
                if poi_coords:
                    poi_lng, poi_lat = map(float, poi_coords.split(','))
                    folium.Marker(
                        [poi_lat, poi_lng],
                        popup=poi.get("name", f"景点{i+1}"),
                        icon=folium.Icon(color='red', icon='star')
                    ).add_to(m)
            
            return m
        except:
            return None