# utils/gaode_restaurant_display.py
import streamlit as st

class GaodeRestaurantDisplay:
    """高德餐厅数据显示"""
    
    @staticmethod
    def display_restaurant_recommendations(gaode_client, city_name, city_location, user_budget, restaurant_count=8):
        """显示餐厅推荐"""
        st.markdown("---")
        st.markdown("## 🍽️ 美食推荐")
        
        # 根据预算筛选
        budget_ranges = {
            "经济型(人均300元/天以下)": (0, 50),
            "舒适型(人均300-600元/天)": (30, 120),
            "豪华型(人均600元/天以上)": (80, 500)
        }
        
        price_range = budget_ranges.get(user_budget, (30, 100))
        
        # 搜索餐厅
        result = gaode_client.search_restaurants(
            city_name=city_name,
            city_location=city_location,
            count=restaurant_count,
            sort_by='rating'
        )
        
        if result.get("status") == "success":
            restaurants = result.get("restaurants", [])
            
            # 按预算筛选
            filtered_restaurants = []
            for restaurant in restaurants:
                price = restaurant.get('avg_price', 0)
                if price_range[0] <= price <= price_range[1]:
                    filtered_restaurants.append(restaurant)
            
            if not filtered_restaurants:
                # 如果没有符合预算的，显示前几个
                filtered_restaurants = restaurants[:min(4, len(restaurants))]
                st.warning(f"在您的预算范围内未找到餐厅，为您推荐其他优质餐厅")
            
            # 显示餐厅
            cols = st.columns(2)
            for i, restaurant in enumerate(filtered_restaurants):
                with cols[i % 2]:
                    with st.container():
                        st.markdown(f"### 🍜 {restaurant.get('name', '')}")
                        
                        # 评分
                        rating = restaurant.get('rating', 0)
                        if rating > 0:
                            stars = "⭐" * int(rating)
                            st.caption(f"{stars} ({rating:.1f}分)")
                        
                        # 价格和类型
                        col_info1, col_info2 = st.columns(2)
                        with col_info1:
                            st.write(f"**{restaurant.get('price_display', '价格待询')}**")
                        with col_info2:
                            st.write(f"**{restaurant.get('cuisine', '')}**")
                        
                        # 地址和电话
                        if restaurant.get('address'):
                            st.caption(f"📍 {restaurant.get('address')}")
                        if restaurant.get('telephone'):
                            st.caption(f"📞 {restaurant.get('telephone')}")
                        
                        # 推荐菜
                        if restaurant.get('recommendation'):
                            st.info(f"👨‍🍳 推荐菜: **{restaurant.get('recommendation')}**")
                        
                        # 特色标签
                        features = restaurant.get('features', [])
                        if features:
                            feature_text = " | ".join(features)
                            st.caption(f"🏷️ {feature_text}")
                        
                        # 操作按钮
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button("查看详情", key=f"rest_detail_{i}"):
                                st.session_state.selected_restaurant = restaurant
                        with col_btn2:
                            url = restaurant.get('detail_url', '')
                            if url:
                                st.markdown(f"[🍽️ 前往高德]({url})", unsafe_allow_html=True)
                        
                        st.markdown("---")
        else:
            st.error(f"获取餐厅数据失败: {result.get('message')}")