# utils/weather_display.py
import streamlit as st

class WeatherDisplay:
    """天气数据显示 - 兼容和风天气格式"""
    
    @staticmethod
    def display_detailed_weather(weather_data):
        """显示详细天气信息"""
        if not weather_data or weather_data.get("status") != "success":
            error_msg = weather_data.get('message', '未知错误') if weather_data else '天气数据为空'
            st.warning(f"天气数据显示失败: {error_msg}")
            return
        
        st.markdown("---")
        st.markdown(f"## 🌤️ {weather_data.get('city', '')} 天气预测")
        
        # 实时天气（如果有）
        current = weather_data.get("current_weather")
        if current:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("当前温度", f"{current.get('temp', 'N/A')}°C")
            with col2:
                st.metric("天气状况", current.get('text', 'N/A'))
            with col3:
                st.metric("体感温度", f"{current.get('feelsLike', 'N/A')}°C")
        
        # 天气预报
        forecast = weather_data.get("forecast", [])
        if not forecast:
            st.info("暂无天气预报数据")
            return
        
        # 显示行程期间的每一天
        st.markdown(f"### 📅 旅行期间天气 ({len(forecast)}天)")
        
        # 动态调整列数
        num_days = len(forecast)
        cols_per_row = min(4, num_days)
        
        for i in range(0, num_days, cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                idx = i + j
                if idx < num_days:
                    with cols[j]:
                        WeatherDisplay._display_weather_card(forecast[idx], idx + 1)
        
        # 显示数据来源
        if weather_data.get('update_time'):
            st.caption(f"🕒 更新时间: {weather_data.get('update_time')} | 数据来源: {weather_data.get('source', '和风天气')}")
    
    @staticmethod
    def _display_weather_card(day_data, day_num):
        """显示单日天气卡片"""
        # 解析日期
        date_str = day_data.get("fxDate", "")
        weekday = WeatherDisplay._get_weekday(date_str)
        
        with st.container():
            # 日期信息
            if date_str:
                display_date = f"{date_str}"
                if weekday:
                    display_date = f"{date_str} ({weekday})"
                st.markdown(f"**第{day_num}天**")
                st.caption(display_date)
            
            # 天气图标和描述
            icon_code = day_data.get("iconDay", "100")
            weather_icon = WeatherDisplay._get_qweather_icon(icon_code)
            
            col_icon, col_desc = st.columns([1, 2])
            with col_icon:
                st.markdown(f"<h2 style='text-align: center;'>{weather_icon}</h2>", unsafe_allow_html=True)
            with col_desc:
                weather_day = day_data.get("textDay", "晴")
                weather_night = day_data.get("textNight", "")
                st.markdown(f"**{weather_day}**")
                if weather_night and weather_night != weather_day:
                    st.caption(f"夜间: {weather_night}")
            
            # 温度
            temp_max = day_data.get("tempMax", "")
            temp_min = day_data.get("tempMin", "")
            if temp_max and temp_min:
                st.markdown(f"🌡️ **{temp_min}°C ~ {temp_max}°C**")
            
            # 其他信息
            details = []
            humidity = day_data.get("humidity")
            if humidity:
                details.append(f"💧 {humidity}%")
            
            wind_dir = day_data.get("windDirDay")
            wind_scale = day_data.get("windScaleDay")
            if wind_dir:
                wind_info = wind_dir
                if wind_scale:
                    wind_info += f" {wind_scale}级"
                details.append(f"💨 {wind_info}")
            
            precip = day_data.get("precip")
            if precip and precip != "0":
                details.append(f"🌧️ {precip}mm")
            
            if details:
                st.caption(" | ".join(details))
            
            # 简单建议
            uv_index = day_data.get("uvIndex", "0")
            if int(uv_index) >= 6:
                st.info("💡 注意防晒")
            elif "雨" in day_data.get("textDay", ""):
                st.info("💡 建议携带雨具")
    
    @staticmethod
    def _get_qweather_icon(code):
        """获取和风天气图标"""
        icon_map = {
            "100": "☀️", "101": "⛅", "102": "🌤️", "103": "🌥️",
            "104": "☁️", "150": "🌙", "151": "☁️",
            "300": "🌦️", "301": "🌧️", "302": "⛈️", "303": "🌧️",
            "304": "🌧️", "305": "🌧️", "306": "🌧️", "307": "🌧️",
            "308": "🌧️", "309": "🌧️", "310": "🌧️", "311": "🌧️",
            "312": "🌧️", "313": "🌧️", "314": "🌧️", "315": "🌧️",
            "316": "🌧️", "317": "🌧️", "318": "🌧️", "399": "🌧️",
            "400": "🌨️", "401": "❄️", "402": "☃️", "403": "❄️",
            "404": "🌨️", "405": "🌨️", "406": "🌨️", "407": "🌨️",
            "408": "🌨️", "409": "🌨️", "410": "🌨️", "499": "❄️",
            "500": "🌫️", "501": "🌁", "502": "😷", "503": "💨",
            "504": "💨", "507": "💨", "508": "💨", "509": "🌫️",
            "510": "🌫️", "511": "🌁", "512": "🌁", "513": "🌁",
            "900": "🔥", "901": "🥶", "999": "🌈"
        }
        return icon_map.get(code, "🌈")
    
    @staticmethod
    def _get_weekday(date_str):
        """获取星期几"""
        from datetime import datetime
        try:
            weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return weekdays[date_obj.weekday()]
        except:
            return ""

# 兼容性版本
def display_weather_simple(weather_data):
    """简单显示天气（兼容旧版本）"""
    if not weather_data or weather_data.get("status") != "success":
        return
    
    st.markdown("---")
    st.markdown("## 🌤️ 天气预测")
    
    forecasts = weather_data.get("forecast", [])
    if forecasts:
        for i, forecast in enumerate(forecasts):
            col1, col2, col3 = st.columns([1, 2, 2])
            with col1:
                icon = forecast.get('icon', forecast.get('weather_icon', '🌈'))
                st.markdown(f"**{icon}**")
            with col2:
                st.write(f"**{forecast.get('date', f'第{i+1}天')}**")
                weather = forecast.get('weather', forecast.get('weather_day', '晴'))
                st.caption(weather)
            with col3:
                temp = f"{forecast.get('temp_min', '')}~{forecast.get('temp_max', '')}°C"
                st.write(temp)
@staticmethod
def display_detailed_weather(weather_data):
    """显示详细天气信息（包括多天）"""
    if not weather_data or weather_data.get("status") != "success":
        st.error(f"无法显示天气: {weather_data.get('message', '未知错误')}")
        return
    
    st.markdown("---")
    
    # 城市和时间信息
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"### 🌍 {weather_data.get('city', '')}")
    with col2:
        st.caption(f"📅 行程: {weather_data.get('start_date')} 至 {weather_data.get('end_date')}")
    with col3:
        if weather_data.get('update_time'):
            st.caption(f"🕒 更新: {weather_data.get('update_time')}")
    
    # 实时天气（如果有）
    current = weather_data.get("current_weather")
    if current:
        st.info(f"""
        **当前天气**: {current.get('text', '')} {current.get('temp', '')}°C  
        **体感温度**: {current.get('feelsLike', '')}°C | **湿度**: {current.get('humidity', '')}%  
        **风力**: {current.get('windDir', '')} {current.get('windScale', '')}级
        """)
    
    # 天气预报网格
    st.markdown("### 📅 行程天气预报")
    
    forecasts = weather_data.get("forecast", [])
    if not forecasts:
        st.warning("暂无天气预报数据")
        return
    
    # ✅ 改进：根据天数动态调整列数
    num_days = len(forecasts)
    cols_per_row = min(4, num_days)
    
    for i in range(0, num_days, cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            idx = i + j
            if idx < num_days:
                with cols[j]:
                    WeatherDisplay._display_detailed_day_card(forecasts[idx], idx+1)
    
    # 生活指数（如果有）
    indices = weather_data.get("indices")
    if indices:
        st.markdown("### 📊 生活指数")
        indices_cols = st.columns(min(3, len(indices)))
        for idx, index_data in enumerate(indices[:3]):
            with indices_cols[idx]:
                st.metric(
                    label=index_data.get("name", "指数"),
                    value=index_data.get("category", ""),
                    help=index_data.get("text", "")
                )

@staticmethod
def _display_detailed_day_card(forecast, day_num):
    """显示单日详细天气卡片"""
    with st.container():
        # 卡片样式
        st.markdown(f"""
        <style>
        .weather-card {{
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #e0e0e0;
            margin-bottom: 10px;
            background-color: #f9f9f9;
        }}
        </style>
        """, unsafe_allow_html=True)
        
        # 日期和星期
        date_display = f"{forecast.get('date', '')}"
        if forecast.get('weekday'):
            date_display = f"{date_display} ({forecast.get('weekday')})"
        
        st.markdown(f"**第{day_num}天**")
        st.caption(date_display)
        
        # 天气图标和描述
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(f"<h1>{forecast.get('weather_icon', '🌈')}</h1>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"**{forecast.get('weather_day', '晴')}**")
            if forecast.get('weather_night'):
                st.caption(f"夜间: {forecast.get('weather_night')}")
        
        # 温度
        st.markdown(f"🌡️ **{forecast.get('temp_min', '')}°C ~ {forecast.get('temp_max', '')}°C**")
        
        # 详细信息
        details = []
        if forecast.get('humidity'):
            details.append(f"💧 {forecast.get('humidity')}%")
        if forecast.get('wind_dir_day'):
            wind_info = forecast.get('wind_dir_day', '')
            if forecast.get('wind_scale_day'):
                wind_info += f" {forecast.get('wind_scale_day')}级"
            details.append(f"💨 {wind_info}")
        if forecast.get('precip') and forecast.get('precip') != '0':
            details.append(f"🌧️ {forecast.get('precip')}mm")
        if forecast.get('sunrise'):
            details.append(f"🌅 {forecast.get('sunrise')}")
        
        if details:
            st.caption(" | ".join(details))
        
        # 建议
        suggestions = forecast.get('suggestions', [])
        if suggestions:
            with st.expander("💡 出行建议", expanded=False):
                for suggestion in suggestions:
                    st.write(f"• {suggestion}")