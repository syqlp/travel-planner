# utils/map_generator.py - 完整版本
import folium
from folium import plugins
import streamlit as st
from utils.baidu_fetcher import convert_bd09_to_wgs84_str, get_wgs84_coordinates
import os

def create_simple_map(location_str, zoom=12, title="目的地地图"):
    """创建简单的地图（备用方案）"""
    try:
        # 转换坐标
        center_coords = convert_bd09_to_wgs84_str(location_str)
        center_lng, center_lat = map(float, center_coords.split(','))
        
        # 创建基础地图
        m = folium.Map(
            location=[center_lat, center_lng], 
            zoom_start=zoom,
            control_scale=True,
            tiles='OpenStreetMap'
        )
        
        # 添加中心标记
        folium.Marker(
            [center_lat, center_lng],
            popup=title,
            tooltip="中心位置",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
        
        # 添加全屏控件
        plugins.Fullscreen(position='topright').add_to(m)
        
        return m
    except Exception as e:
        st.error(f"创建简单地图失败: {e}")
        return None

def create_travel_map(destination, pois_data, city_location, travel_mode="walking", is_baidu=True):
    """
    创建旅行地图
    Args:
        destination: 目的地名称
        pois_data: 景点数据列表
        city_location: 城市中心坐标
        travel_mode: 交通方式 (walking/driving)
        is_baidu: 是否是百度地图数据
    """
    
    if not pois_data:
        st.warning("没有景点数据，使用简单地图")
        return create_simple_map(city_location, zoom=12, title=f"{destination}位置图")
    
    try:
        # 1. 获取中心点坐标（转换为WGS84）
        if is_baidu:
            center_coords = convert_bd09_to_wgs84_str(city_location)
        else:
            center_coords = city_location
        
        center_lng, center_lat = map(float, center_coords.split(','))
        
        # 2. 创建基础地图
        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=13,
            control_scale=True,
            tiles='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
            attr='© OpenStreetMap contributors, © CARTO'
        )
        
        # 3. 添加城市中心标记
        folium.Marker(
            [center_lat, center_lng],
            popup=f"<b>{destination}</b><br>行程中心点",
            tooltip="行程中心",
            icon=folium.Icon(color='blue', icon='info-sign', prefix='fa')
        ).add_to(m)
        
        # 4. 处理景点数据并添加到地图
        valid_pois = []
        for i, poi in enumerate(pois_data[:10]):  # 最多显示10个景点
            try:
                # 获取景点坐标
                if is_baidu:
                    poi_coords = get_wgs84_coordinates(poi)
                else:
                    poi_coords = poi.get("location", "")
                
                if not poi_coords:
                    continue
                    
                poi_lng, poi_lat = map(float, poi_coords.split(','))
                poi_name = poi.get("name", f"景点{i+1}")
                poi_address = poi.get("address", "地址未知")
                poi_rating = poi.get("rating", 0)
                
                # 添加景点标记
                color = 'green' if poi_rating >= 4.0 else 'orange' if poi_rating >= 3.0 else 'red'
                
                popup_content = f"""
                <div style="width: 250px;">
                    <h4>{poi_name}</h4>
                    <p><b>地址:</b> {poi_address}</p>
                    <p><b>类型:</b> {poi.get('type', '未知')}</p>
                    <p><b>标签:</b> {poi.get('tag', '无')}</p>
                    <p><b>评分:</b> ⭐ {poi_rating}/5.0</p>
                    <p><b>电话:</b> {poi.get('telephone', '无')}</p>
                </div>
                """
                
                folium.Marker(
                    [poi_lat, poi_lng],
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=f"{i+1}. {poi_name}",
                    icon=folium.Icon(color=color, icon='star', prefix='fa')
                ).add_to(m)
                
                valid_pois.append([poi_lat, poi_lng])
                
            except Exception as e:
                st.warning(f"添加景点 {poi.get('name', '未知')} 时出错: {e}")
                continue
        
        # 5. 如果有足够的有效景点，添加游览路线
        if len(valid_pois) >= 2:
            try:
                # 添加多边形连线（游览路线）
                folium.PolyLine(
                    valid_pois,
                    color='blue',
                    weight=3,
                    opacity=0.7,
                    popup=f"<b>{destination}游览路线</b><br>{travel_mode}路线",
                    tooltip=f"{len(valid_pois)}个景点游览路线"
                ).add_to(m)
                
                # 添加起点和终点特殊标记
                if valid_pois:
                    # 起点
                    folium.Marker(
                        valid_pois[0],
                        popup="<b>游览起点</b>",
                        tooltip="起点",
                        icon=folium.Icon(color='green', icon='play', prefix='fa')
                    ).add_to(m)
                    
                    # 终点
                    folium.Marker(
                        valid_pois[-1],
                        popup="<b>游览终点</b>",
                        tooltip="终点",
                        icon=folium.Icon(color='red', icon='flag-checkered', prefix='fa')
                    ).add_to(m)
                    
                # 添加距离测量
                if len(valid_pois) > 1:
                    plugins.MeasureControl(position='bottomleft').add_to(m)
                    
            except Exception as e:
                st.warning(f"添加游览路线时出错: {e}")
        
        # 6. 添加图层控制和全屏按钮
        folium.LayerControl().add_to(m)
        plugins.Fullscreen(position='topright').add_to(m)
        
        # 7. 添加缩放控件
        plugins.MiniMap(tile_layer='OpenStreetMap', position='bottomright').add_to(m)
        
        # 8. 添加鼠标位置显示
        plugins.MousePosition(position='bottomleft').add_to(m)
        
        # 9. 添加景点数量信息
        legend_html = f'''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 180px; height: auto;
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px; border-radius: 5px; opacity: 0.9;">
            <b>🗺️ {destination} 游览地图</b><br>
            景点数量: {len(valid_pois)}个<br>
            交通方式: {'步行' if travel_mode == 'walking' else '驾车'}<br>
            ⭐ 绿色: 评分≥4.0<br>
            ⭐ 橙色: 评分3.0-4.0<br>
            ⭐ 红色: 评分<3.0
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        return m
        
    except Exception as e:
        st.error(f"创建地图时发生错误: {e}")
        # 返回简单地图作为备选
        return create_simple_map(city_location, zoom=12, title=f"{destination}位置图")

def save_map_to_html(map_object, destination):
    """保存地图为HTML文件"""
    try:
        os.makedirs("data/maps", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/maps/{destination}_地图_{timestamp}.html"
        map_object.save(filename)
        return filename
    except Exception as e:
        st.error(f"保存地图失败: {e}")
        return None