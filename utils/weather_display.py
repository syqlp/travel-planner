# utils/weather_display.py
import streamlit as st

class WeatherDisplay:
    """天气数据显示 - 兼容多种数据源格式"""
    
    @staticmethod
    def display_detailed_weather(weather_data):
        """显示详细天气信息 - 静态方法"""
        if not weather_data or weather_data.get("status") != "success":
            if weather_data and weather_data.get("message"):
                st.warning(f"天气数据显示失败: {weather_data.get('message')}")
            else:
                st.warning("天气数据不可用")
            return
        
        st.markdown("---")
        st.markdown(f"## 🌤️ {weather_data.get('city', '未知城市')} 天气预测")
        
        # 当前天气（如果有）
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
            st.caption(f"🕒 更新时间: {weather_data.get('update_time')} | 数据来源: {weather_data.get('source', '智能天气系统')}")
    
    @staticmethod
    def _display_weather_card(day_data, day_num):
        """显示单日天气卡片 - 兼容多种数据源"""
        # 解析日期
        date_str = day_data.get("fxDate") or day_data.get("date") or f"第{day_num}天"
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
            icon_code = day_data.get("iconDay") or day_data.get("weather_icon") or "🌈"
            weather_day = day_data.get("textDay") or day_data.get("weather_day") or "晴"
            weather_night = day_data.get("textNight") or day_data.get("weather_night") or ""
            
            col_icon, col_desc = st.columns([1, 2])
            with col_icon:
                st.markdown(f"<h2 style='text-align: center;'>{icon_code}</h2>", unsafe_allow_html=True)
            with col_desc:
                st.markdown(f"**{weather_day}**")
                if weather_night and weather_night != weather_day:
                    st.caption(f"夜间: {weather_night}")
            
            # 温度
            temp_max = day_data.get("tempMax") or day_data.get("temp_max") or "25"
            temp_min = day_data.get("tempMin") or day_data.get("temp_min") or "15"
            st.markdown(f"🌡️ **{temp_min}°C ~ {temp_max}°C**")
            
            # 其他信息
            details = []
            humidity = day_data.get("humidity")
            if humidity:
                details.append(f"💧 {humidity}%")
            
            wind_dir = day_data.get("windDirDay") or day_data.get("wind_dir_day") or day_data.get("wind", "")
            wind_scale = day_data.get("windScaleDay") or day_data.get("wind_scale_day") or ""
            if wind_dir:
                wind_info = wind_dir
                if wind_scale:
                    wind_info += f" {wind_scale}级"
                details.append(f"💨 {wind_info}")
            
            precip = day_data.get("precip") or day_data.get("precipitation") or "0"
            if precip and precip != "0":
                details.append(f"🌧️ {precip}mm")
            
            if details:
                st.caption(" | ".join(details))
            
            # 使用建议字段
            suggestions = day_data.get("suggestions", [])
            if suggestions:
                with st.expander("💡 出行建议", expanded=False):
                    for suggestion in suggestions:
                        st.write(f"• {suggestion}")
            else:
                # 简单建议
                uv_index = day_data.get("uvIndex", "0")
                if int(uv_index) >= 6:
                    st.info("💡 注意防晒")
                elif "雨" in weather_day:
                    st.info("💡 建议携带雨具")
    
    @staticmethod
    def _get_weekday(date_str):
        """获取星期几"""
        from datetime import datetime
        try:
            weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            # 尝试解析日期
            if "-" in date_str:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            else:
                # 如果不是标准格式，返回空
                return ""
            return weekdays[date_obj.weekday()]
        except:
            return ""