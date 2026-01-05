# utils/gaode_hotel_display.py
import streamlit as st
import urllib.parse

class GaodeHotelDisplay:
    """高德真实酒店数据显示"""
    
    @staticmethod
    def display_real_hotels(gaode_client, city_name, city_location, user_budget, hotel_count=6):
        """显示真实酒店推荐"""
        st.markdown("---")
        st.markdown("## 🏨 真实酒店推荐（高德地图）")
        
        # 解析预算
        budget_ranges = {
            "经济型(人均300元/天以下)": (0, 300),
            "舒适型(人均300-600元/天)": (300, 600),
            "豪华型(人均600元/天以上)": (600, 5000)
        }
        
        budget_range = budget_ranges.get(user_budget, (0, 1000))
        
        with st.spinner(f"正在搜索{city_name}的真实酒店信息..."):
            hotels_result = gaode_client.search_hotels_real(
                city_name=city_name,
                city_location=city_location,
                budget_range=budget_range,
                count=hotel_count
            )
        
        if hotels_result.get("status") != "success":
            st.warning("暂时无法获取真实酒店数据")
            GaodeHotelDisplay._display_fallback_info(city_name, budget_range)
            return
        
        hotels = hotels_result.get("hotels", [])
        
        if not hotels:
            st.info("当前预算范围内没有找到酒店")
            GaodeHotelDisplay._display_fallback_info(city_name, budget_range)
            return
        
        st.success(f"✅ 找到 {len(hotels)} 个符合预算的真实酒店")
        
        # 显示筛选器
        col1, col2 = st.columns(2)
        with col1:
            sort_by = st.selectbox(
                "排序方式",
                ["评分从高到低", "价格从低到高", "价格从高到低"],
                key="hotel_sort"
            )
        with col2:
            show_type = st.multiselect(
                "酒店类型",
                ["豪华酒店", "商务酒店", "特色民宿", "经济型酒店"],
                default=["商务酒店", "经济型酒店"],
                key="hotel_type"
            )
        
        # 筛选和排序
        filtered_hotels = [h for h in hotels if h.get('type') in show_type or not show_type]
        
        if sort_by == "评分从高到低":
            filtered_hotels.sort(key=lambda x: x.get('rating', 0), reverse=True)
        elif sort_by == "价格从低到高":
            filtered_hotels.sort(key=lambda x: x.get('price', 9999))
        elif sort_by == "价格从高到低":
            filtered_hotels.sort(key=lambda x: x.get('price', 0), reverse=True)
        
        # 显示酒店卡片
        for i, hotel in enumerate(filtered_hotels):
            GaodeHotelDisplay._display_hotel_card(hotel, i + 1)
        
        # 显示预订平台
        GaodeHotelDisplay._display_booking_platforms(city_name)
    
    @staticmethod
    def _display_hotel_card(hotel, index):
        """显示酒店卡片"""
        name = hotel.get("name", f"酒店{index}")
        address = hotel.get("address", "")
        price_display = hotel.get("price_display", "价格待询")
        rating = hotel.get("rating", 0)
        hotel_type = hotel.get("type", "酒店")
        facilities = hotel.get("facilities", [])
        telephone = hotel.get("telephone", "")
        booking_url = hotel.get("booking_url", "#")
        detail_url = hotel.get("detail_url", "#")
        
        with st.container():
            # 标题行
            col_title, col_price = st.columns([3, 1])
            
            with col_title:
                st.markdown(f"### {index}. {name}")
                st.caption(f"🏷️ {hotel_type} | 📍 {address}")
            
            with col_price:
                st.markdown(f"### {price_display}")
                if rating > 0:
                    stars = "⭐" * int(rating)
                    st.markdown(f"**{stars}** ({rating:.1f})")
            
            # 详细信息
            col_info, col_actions = st.columns([2, 1])
            
            with col_info:
                # 设施
                if facilities:
                    st.markdown("**🏪 设施**")
                    st.caption(" · ".join(facilities))
                
                # 数据来源
                if hotel.get("is_real"):
                    st.caption("✅ 真实数据来自高德地图")
            
            with col_actions:
                # 电话
                if telephone:
                    st.markdown(f"**📞 电话**")
                    st.caption(telephone)
                
                # 操作按钮
                st.markdown("**🔗 快速操作**")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    st.markdown(f"[🗺️ 地图]({detail_url})", unsafe_allow_html=True)
                with col_btn2:
                    st.markdown(f"[🏨 预订]({booking_url})", unsafe_allow_html=True)
            
            st.markdown("---")
    
    @staticmethod
    def _display_fallback_info(city_name, budget_range):
        """显示备用信息"""
        min_price, max_price = budget_range
        
        st.info(f"""
        ### 💡 酒店搜索建议
        
        **预算范围**: {min_price}-{max_price}元/晚
        **目的地**: {city_name}
        
        **推荐搜索方式**:
        1. **携程旅行**: hotels.ctrip.com
        2. **美团酒店**: hotel.meituan.com  
        3. **飞猪旅行**: www.fliggy.com
        
        **搜索技巧**:
        - 使用"价格筛选"功能
        - 查看用户真实评价和图片
        - 注意酒店的取消政策
        - 提前预订可能有优惠
        """)
    
    @staticmethod
    def _display_booking_platforms(city_name):
        """显示预订平台"""
        st.markdown("### 💡 更多预订平台")
        
        encoded_city = urllib.parse.quote(city_name)
        
        platforms = [
            ("🏨 携程酒店", f"https://hotels.ctrip.com/hotels/list?city={encoded_city}"),
            ("📱 美团酒店", f"https://hotel.meituan.com/city/{encoded_city}"),
            ("✈️ 飞猪酒店", f"https://www.fliggy.com/hotel/search?cityName={encoded_city}"),
            ("🔍 高德地图", f"https://www.amap.com/search?query={encoded_city}酒店")
        ]
        
        cols = st.columns(2)
        for i, (name, url) in enumerate(platforms):
            with cols[i % 2]:
                st.markdown(f"[{name}]({url})", unsafe_allow_html=True)