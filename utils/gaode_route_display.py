# utils/gaode_route_display.py
import streamlit as st
import folium
from streamlit_folium import st_folium

class GaodeRouteDisplay:
    """高德路线显示"""
    
    @staticmethod
    def display_route_planning(attractions, city, gaode_client):
        """显示路线规划"""
        if len(attractions) < 2:
            st.warning("至少需要2个景点才能规划路线")
            return
        
        # 选择起点和终点
        col1, col2 = st.columns(2)
        with col1:
            start_idx = st.selectbox(
                "选择起点",
                range(len(attractions)),
                format_func=lambda i: f"{chr(65+i)}. {attractions[i].get('name', f'景点{i+1}')}"
            )
        
        with col2:
            end_idx = st.selectbox(
                "选择终点",
                range(len(attractions)),
                index=min(1, len(attractions)-1),
                format_func=lambda i: f"{chr(65+i)}. {attractions[i].get('name', f'景点{i+1}')}"
            )
        
        if start_idx == end_idx:
            st.warning("起点和终点不能相同")
            return
        
        # 获取起点和终点的坐标
        origin = attractions[start_idx].get('location')
        destination = attractions[end_idx].get('location')
        
        if not origin or not destination:
            st.error("景点坐标信息不完整")
            return
        
        # 规划路线
        if st.button("🚀 开始规划路线"):
            with st.spinner("正在规划路线..."):
                route_result = gaode_client.plan_route(
                    origin=origin,
                    destination=destination,
                    city=city
                )
                
                if route_result.get("status") == "success":
                    GaodeRouteDisplay._display_route_details(route_result, attractions[start_idx], attractions[end_idx])
                else:
                    st.error(f"路线规划失败: {route_result.get('message')}")
    
    @staticmethod
    def _display_route_details(route_result, start_attraction, end_attraction):
        """显示路线详情"""
        st.success("✅ 路线规划成功！")
        
        # 显示概览
        total_distance = route_result.get("total_distance", 0)
        total_duration = route_result.get("total_duration", 0)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("起点", start_attraction.get('name', '起点'))
        with col2:
            st.metric("终点", end_attraction.get('name', '终点'))
        with col3:
            st.metric("总距离", f"{total_distance/1000:.1f}公里")
        
        # 显示详细步骤
        st.markdown("### 🗺️ 详细路线")
        
        steps = route_result.get("steps", [])
        for i, step in enumerate(steps):
            with st.expander(f"**第{i+1}步**: {step.get('instruction', '')[:80]}...", expanded=(i<2)):
                cols = st.columns(4)
                with cols[0]:
                    vehicle = step.get('vehicle', {})
                    st.write(f"**方式**: {vehicle.get('icon', '📍')} {vehicle.get('name', '其他')}")
                with cols[1]:
                    st.write(f"**距离**: {step.get('distance', 0)}米")
                with cols[2]:
                    st.write(f"**时间**: {step.get('duration', 0)/60:.0f}分钟")
                with cols[3]:
                    if step.get('road'):
                        st.write(f"**道路**: {step.get('road')}")
                
                # 如果是公共交通，显示线路详情
                if vehicle.get('type') in ['subway', 'bus']:
                    if vehicle.get('line'):
                        st.info(f"乘坐 **{vehicle.get('name')}** 线路")
    
    @staticmethod
    def display_multi_route(attractions, city, gaode_client):
        """显示多点路线规划"""
        st.info("🔍 正在为您规划游览顺序...")
        
        if len(attractions) < 2:
            st.warning("需要至少2个景点才能规划多点路线")
            return
        
        # 简单的游览顺序建议
        st.markdown("### 💡 推荐游览顺序")
        
        # 显示推荐的游览顺序
        ordered_attractions = attractions[:5]  # 取前5个
        
        st.write("建议按以下顺序游览：")
        for i, attraction in enumerate(ordered_attractions):
            st.write(f"{i+1}. **{attraction.get('name')}**")
            if i < len(ordered_attractions) - 1:
                st.write(f"   ↓ ({GaodeRouteDisplay._estimate_time(i)}分钟)")
        
        # 显示游览时间估算
        total_time = sum(GaodeRouteDisplay._estimate_time(i) for i in range(len(ordered_attractions)-1))
        st.metric("预计总游览时间", f"{total_time}分钟")
    
    @staticmethod
    def _estimate_time(index):
        """估算景点间的时间"""
        # 根据景点顺序简单估算
        base_times = [15, 20, 25, 30, 15]  # 示例时间
        return base_times[index % len(base_times)]