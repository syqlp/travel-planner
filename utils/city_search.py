# utils/city_search.py
import streamlit as st
from utils.weather_service_pro import QWeatherService

class CitySearch:
    """城市搜索组件"""
    
    @staticmethod
    def show_city_search():
        """显示城市搜索界面"""
        st.markdown("### 🔍 城市搜索")
        
        # 创建服务实例
        service = QWeatherService()
        
        # 输入城市名
        city_name = st.text_input("输入城市名称", placeholder="例如：北京、上海、广州")
        
        # 可选：输入省份
        with st.expander("高级选项", expanded=False):
            adm = st.text_input("省份/直辖市（可选）", placeholder="例如：广东、江苏")
            search_type = st.selectbox("搜索类型", ["精确匹配", "模糊匹配"])
        
        if city_name and st.button("搜索城市", type="primary"):
            with st.spinner("正在搜索..."):
                # 搜索城市
                cities = service.search_city(city_name, adm if adm else None)
                
                if not cities:
                    st.error("未找到相关城市，请尝试其他名称")
                    return
                
                # 显示搜索结果
                st.success(f"找到 {len(cities)} 个相关城市")
                
                # 让用户选择
                city_options = []
                for city in cities:
                    name = city.get("name", "未知")
                    adm1 = city.get("adm1", "")
                    adm2 = city.get("adm2", "")
                    
                    if adm1 and adm2:
                        display_name = f"{name} ({adm1}-{adm2})"
                    elif adm1:
                        display_name = f"{name} ({adm1})"
                    else:
                        display_name = name
                    
                    city_options.append((display_name, city))
                
                # 显示选择框
                selected_display = st.selectbox(
                    "选择城市",
                    options=[opt[0] for opt in city_options],
                    index=0
                )
                
                # 获取选择的城市
                selected_city = None
                for display, city in city_options:
                    if display == selected_display:
                        selected_city = city
                        break
                
                if selected_city:
                    # 显示城市信息
                    st.markdown("---")
                    st.markdown("### 📍 城市信息")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("城市", selected_city.get("name"))
                    with col2:
                        st.metric("省份", selected_city.get("adm1", ""))
                    with col3:
                        st.metric("地区", selected_city.get("adm2", ""))
                    
                    # 获取天气
                    weather_data = service.get_city_weather(selected_city["id"])
                    if weather_data:
                        CitySearch._show_weather_preview(weather_data, selected_city["name"])
                    
                    # 获取生活指数
                    indices = service.get_city_indices(selected_city["id"])
                    if indices:
                        CitySearch._show_living_indices(indices)
                    
                    # 返回城市信息
                    return {
                        "id": selected_city["id"],
                        "name": selected_city["name"],
                        "adm1": selected_city.get("adm1", ""),
                        "adm2": selected_city.get("adm2", ""),
                        "lat": selected_city.get("lat", ""),
                        "lon": selected_city.get("lon", "")
                    }
    
    @staticmethod
    def _show_weather_preview(weather_data, city_name):
        """显示天气预览"""
        current = weather_data.get("current", {})
        forecast = weather_data.get("forecast", [])
        
        st.markdown("### 🌤️ 天气预览")
        
        # 当前天气
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("当前温度", f"{current.get('temp', 'N/A')}°C")
        with col2:
            st.metric("天气状况", current.get('text', 'N/A'))
        with col3:
            st.metric("体感温度", f"{current.get('feelsLike', 'N/A')}°C")
        
        # 未来3天预报
        if forecast:
            st.markdown("**未来3天预报:**")
            cols = st.columns(3)
            for i in range(min(3, len(forecast))):
                day = forecast[i]
                with cols[i]:
                    st.write(f"{day.get('fxDate', '')}")
                    st.write(f"🌡 {day.get('tempMin')}~{day.get('tempMax')}°C")
                    st.write(f"{day.get('textDay')}")
    
    @staticmethod
    def _show_living_indices(indices):
        """显示生活指数"""
        st.markdown("### 📊 生活指数")
        
        # 指数映射
        index_names = {
            "1": "运动指数", "2": "洗车指数", "3": "穿衣指数",
            "4": "钓鱼指数", "5": "紫外线指数", "6": "旅游指数",
            "7": "过敏指数", "8": "舒适度指数", "9": "感冒指数"
        }
        
        cols = st.columns(3)
        for i, index in enumerate(indices[:6]):  # 最多显示6个
            with cols[i % 3]:
                type_name = index_names.get(index.get("type", ""), "其他指数")
                st.info(f"**{type_name}**\n{index.get('category', '')}\n{index.get('text', '')}")

# 使用示例
if __name__ == "__main__":
    CitySearch.show_city_search()