# utils/gaode_route_planner.py
import streamlit as st

class GaodeRoutePlanner:
    """高德路线规划器 - 根据AI游览顺序自动规划"""
    
    @staticmethod
    def display_ai_route_plan(generation_result, city_name, gaode_client):
        """根据AI推荐的游览顺序显示路线规划"""
        
        attractions = generation_result.get('attractions_data', [])
        if len(attractions) < 2:
            st.warning("至少需要2个景点才能规划路线")
            return
        
        st.markdown("---")
        st.markdown("## 🗺️ AI智能路线规划")
        
        # 显示AI推荐的游览顺序
        st.markdown("### 📋 AI推荐游览顺序")
        
        # 创建游览顺序（按景点评分排序或按距离排序）
        ordered_attractions = GaodeRoutePlanner._order_attractions(attractions)
        
        # 显示顺序
        cols = st.columns(3)
        for i, attraction in enumerate(ordered_attractions[:6]):
            with cols[i % 3]:
                st.markdown(f"**{i+1}.** {attraction.get('name', f'景点{i+1}')}")
        
        # 规划每段路线
        st.markdown("### 🚶 详细路线规划")
        
        total_walking_time = 0
        total_distance = 0
        
        for i in range(len(ordered_attractions) - 1):
            current = ordered_attractions[i]
            next_att = ordered_attractions[i + 1]
            
            with st.expander(f"**第{i+1}段**: {current.get('name')} → {next_att.get('name')}", expanded=(i<2)):
                GaodeRoutePlanner._display_segment_route(
                    current, next_att, city_name, gaode_client, i+1
                )
        
        # 显示统计信息
        st.markdown("### 📊 行程统计")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总景点数", len(ordered_attractions))
        with col2:
            st.metric("路线段数", len(ordered_attractions) - 1)
        with col3:
            st.metric("建议游览时间", f"{len(ordered_attractions) * 1.5:.1f}小时")
    
    @staticmethod
    def _order_attractions(attractions):
        """对景点进行排序（简单按评分排序）"""
        return sorted(attractions, key=lambda x: x.get('rating', 0), reverse=True)
    
    @staticmethod
    def _display_segment_route(current, next_att, city_name, gaode_client, segment_num):
        """显示单段路线"""
        
        origin = current.get('location')
        destination = next_att.get('location')
        
        if not origin or not destination:
            st.warning("景点坐标信息不完整")
            return
        
        # 获取路线规划
        with st.spinner(f"规划第{segment_num}段路线..."):
            route_result = gaode_client.plan_route_enhanced(
                origin=origin,
                destination=destination,
                city=city_name
            )
        
        if route_result.get("status") == "success":
            # 显示概览
            total_distance = route_result.get("total_distance", 0)
            total_duration = route_result.get("total_duration", 0)
            walking_time = route_result.get("walking_time_minutes", 0)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("总距离", f"{total_distance/1000:.1f}公里")
            with col2:
                st.metric("预计时间", f"{total_duration/60:.0f}分钟")
            with col3:
                if walking_time > 0:
                    st.metric("步行时间", f"{walking_time:.0f}分钟")
            
            # 显示交通方式统计
            transit_types = []
            if route_result.get("has_subway"):
                transit_types.append("🚇 地铁")
            if route_result.get("has_bus"):
                transit_types.append("🚌 公交")
            
            if transit_types:
                st.info(f"**推荐交通**: {' + '.join(transit_types)}")
            
            # 显示详细步骤
            st.markdown("**详细路线:**")
            steps = route_result.get("steps", [])
            
            for i, step in enumerate(steps[:8]):  # 最多显示8步
                instruction = step.get("instruction", "")
                if len(instruction) > 60:
                    instruction = instruction[:60] + "..."
                
                with st.container():
                    col_step1, col_step2, col_step3 = st.columns([1, 2, 1])
                    
                    with col_step1:
                        vehicle = step.get("vehicle", {})
                        icon = vehicle.get("icon", "📍")
                        st.write(f"**{icon}**")
                    
                    with col_step2:
                        st.write(instruction)
                    
                    with col_step3:
                        distance = step.get("distance", 0)
                        if distance > 0:
                            st.caption(f"{distance}米")
                    
                    st.markdown("---")
            
            # 显示小贴士
            if route_result.get("is_estimated"):
                st.warning("⚠️ 此为估算路线，建议使用导航APP获取实时路线")
            else:
                if route_result.get("taxi_cost", 0) > 0:
                    st.info(f"💡 打车费用约 {route_result['taxi_cost']}元")
        
        else:
            st.error(f"路线规划失败: {route_result.get('message')}")
            
            # 提供备用方案
            st.info(f"""
            💡 **备用方案**:
            
            1. **直接打车**: 在两个景点间打车
            2. **使用导航APP**: 打开高德/百度地图搜索路线
            3. **询问当地人**: 获取最佳交通方式
            """)
    
    @staticmethod
    def display_simple_walking_route(attractions, city_name, gaode_client):
        """显示简单的步行路线规划"""
        if len(attractions) < 2:
            return
        
        st.markdown("### 🚶 步行方案")
        
        ordered_attractions = attractions[:4]  # 最多4个景点
        
        total_walk_distance = 0
        total_walk_time = 0
        
        for i in range(len(ordered_attractions) - 1):
            current = ordered_attractions[i]
            next_att = ordered_attractions[i + 1]
            
            origin = current.get('location')
            destination = next_att.get('location')
            
            if origin and destination:
                # 计算步行距离和时间
                route_result = gaode_client._get_walking_route(origin, destination)
                
                if route_result.get("status") == "success":
                    distance = route_result.get("total_distance", 0)
                    duration = route_result.get("total_duration", 0)
                    
                    total_walk_distance += distance
                    total_walk_time += duration
                    
                    st.write(f"**{current.get('name')} → {next_att.get('name')}**")
                    st.caption(f"步行约{distance/1000:.1f}公里，{duration/60:.0f}分钟")
        
        if total_walk_distance > 0:
            st.info(f"**总计步行**: {total_walk_distance/1000:.1f}公里，约{total_walk_time/60:.0f}分钟")