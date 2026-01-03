# utils/route_display.py
import streamlit as st
from datetime import datetime, timedelta

class RouteDisplay:
    """路线详情显示"""
    
    @staticmethod
    def display_route_details(route_plan, pois_data, mode="transit"):
        """显示详细的路线规划"""
        if route_plan.get("status") != "success":
            st.warning("无法获取详细路线信息")
            return
        
        routes = route_plan.get("routes", [])
        total_distance = route_plan.get("total_distance", 0)
        total_duration = route_plan.get("total_duration", 0)
        
        # 显示路线概览
        st.markdown("### 🚏 详细路线规划")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总距离", f"{total_distance/1000:.1f} km")
        with col2:
            st.metric("预计时间", f"{total_duration//60} 分钟")
        with col3:
            st.metric("景点数量", route_plan.get("location_count", 0))
        with col4:
            mode_icon = "🚇" if mode == "transit" else "🚶" if mode == "walking" else "🚗"
            st.metric("交通方式", mode_icon)
        
        st.markdown("---")
        
        # 显示每段路线详情
        for i, route in enumerate(routes):
            if i >= len(pois_data) - 1:
                break
            
            start_poi = pois_data[i]
            end_poi = pois_data[i + 1]
            
            with st.expander(f"**第{i+1}段: {start_poi.get('name')} → {end_poi.get('name')}**", expanded=(i==0)):
                col_left, col_right = st.columns([1, 2])
                
                with col_left:
                    st.markdown("**📊 基本信息**")
                    st.write(f"距离: {route.get('distance', 0)/1000:.2f} km")
                    st.write(f"时间: {route.get('duration', 0)//60} 分钟")
                    
                    # 交通方式统计
                    steps = route.get("steps", [])
                    walk_steps = [s for s in steps if s.get("vehicle", {}).get("type") == "walking"]
                    transit_steps = [s for s in steps if s.get("vehicle", {}).get("type") in ["subway", "bus"]]
                    
                    st.markdown("**🚦 交通组成**")
                    if walk_steps:
                        walk_dist = sum(s.get("distance", 0) for s in walk_steps)
                        st.write(f"🚶 步行: {walk_dist}米 ({len(walk_steps)}段)")
                    
                    if transit_steps:
                        for step in transit_steps:
                            vehicle = step.get("vehicle", {})
                            if vehicle.get("type") == "subway":
                                st.write(f"🚇 地铁: {vehicle.get('name', '')}")
                            elif vehicle.get("type") == "bus":
                                st.write(f"🚌 公交: {vehicle.get('name', '')}")
                
                with col_right:
                    st.markdown("**🗺️ 详细步骤**")
                    
                    # 模拟时间线
                    current_time = datetime.now().replace(hour=9, minute=0, second=0)  # 假设9点开始
                    
                    for j, step in enumerate(steps[:5]):  # 最多显示5个步骤
                        vehicle = step.get("vehicle", {})
                        instruction = step.get("instruction", "")
                        distance = step.get("distance", 0)
                        duration = step.get("duration", 0)
                        
                        # 格式化显示
                        time_str = current_time.strftime("%H:%M")
                        current_time += timedelta(seconds=duration)
                        
                        with st.container():
                            col_icon, col_text = st.columns([1, 10])
                            with col_icon:
                                st.write(f"**{vehicle.get('icon', '📍')}**")
                            with col_text:
                                st.write(f"**{time_str}** {instruction}")
                                st.caption(f"距离: {distance}米 | 时间: {duration//60}分钟")
                        
                        if j < len(steps[:5]) - 1:
                            st.markdown("<div style='margin-left: 20px; border-left: 2px dashed #ccc; height: 10px;'></div>", 
                                      unsafe_allow_html=True)
        
        # 显示路线建议
        st.markdown("---")
        st.markdown("### 💡 路线建议")
        
        advice_cols = st.columns(3)
        with advice_cols[0]:
            st.info("**🎫 票务建议**\n\n- 提前下载当地交通APP\n- 准备零钱或交通卡\n- 关注地铁运营时间")
        
        with advice_cols[1]:
            st.info("**⏰ 时间安排**\n\n- 每个景点预留1-2小时\n- 避开早晚高峰\n- 留出用餐和休息时间")
        
        with advice_cols[2]:
            st.info("**💰 费用预估**\n\n- 公共交通费用较低\n- 景点间交通约10-30元\n- 建议预留应急资金")
    
    @staticmethod
    def create_transit_card(route_plan):
        """创建交通卡样式显示"""
        if not route_plan or route_plan.get("status") != "success":
            return
        
        routes = route_plan.get("routes", [])
        
        st.markdown("### 🎫 交通路线卡")
        
        # 创建时间线
        timeline_html = """
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 10px; color: white;">
            <h4 style="margin-top: 0; color: white;">🚇 公共交通路线</h4>
        """
        
        current_time = "09:00"
        for i, route in enumerate(routes[:4]):  # 最多显示4段
            steps = route.get("steps", [])
            
            # 提取公共交通步骤
            transit_steps = [s for s in steps if s.get("vehicle", {}).get("type") in ["subway", "bus"]]
            
            for step in transit_steps[:2]:  # 每段最多显示2个交通步骤
                vehicle = step.get("vehicle", {})
                
                timeline_html += f"""
                <div style="margin: 10px 0; padding: 10px; background: rgba(255,255,255,0.2); border-radius: 5px;">
                    <div style="display: flex; align-items: center;">
                        <div style="font-size: 24px; margin-right: 10px;">{vehicle.get('icon', '🚇')}</div>
                        <div>
                            <div style="font-weight: bold;">{vehicle.get('name', '交通')}</div>
                            <div style="font-size: 12px; opacity: 0.9;">{current_time} | {step.get('distance', 0)}米</div>
                        </div>
                    </div>
                </div>
                """
                # 模拟时间增加
                hours = int(current_time.split(":")[0])
                minutes = int(current_time.split(":")[1]) + (step.get("duration", 0) // 60)
                if minutes >= 60:
                    hours += 1
                    minutes -= 60
                current_time = f"{hours:02d}:{minutes:02d}"
        
        timeline_html += "</div>"
        st.markdown(timeline_html, unsafe_allow_html=True)