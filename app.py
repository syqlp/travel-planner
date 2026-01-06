# app.py 
import streamlit as st
import json
import os
import time
from datetime import datetime
from streamlit_folium import st_folium

# 导入工具模块
from utils.api_handler import ZhipuAIClient
from utils.data_fetcher import geocode, nearby_search

from utils.data_fetcher import search_real_hotels,parse_hotels
from utils.data_fetcher import classify_hotel,budget_match,estimate_price

from utils.gaode_client import GaodeMapClient
from utils.gaode_route_display import GaodeRouteDisplay
from utils.gaode_hotel_display import GaodeHotelDisplay

from utils.gaode_restaurant_display import GaodeRestaurantDisplay
from utils.gaode_route_planner import GaodeRoutePlanner
# 页面配置
st.set_page_config(
    page_title="个性化旅行规划助手",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)
# 2. 初始化高德客户端
@st.cache_resource
def get_gaode_client():
    return GaodeMapClient()

# ========== 主题样式 ==========
theme_css = """
<style>
    :root {
        --bg-color: #0f172a;
        --text-color: #e2e8f0;
        --card-bg: #1e293b;
        --card-border: #334155;
        --primary-color: #60a5fa;
        --header-color: #93c5fd;
        --sidebar-bg: #1e293b;
        --metric-bg: #1e293b;
        --success-bg: #065f46;
        --info-bg: #1e40af;
    }
    
    .stApp {
        background-color: var(--bg-color) !important;
        color: var(--text-color) !important;
    }
    
    .main-header {
        font-size: 2.5rem;
        text-align: center;
        margin-bottom: 1rem;
        color: var(--header-color) !important;
    }
    
    .sub-header {
        font-size: 1.2rem;
        text-align: center;
        margin-bottom: 2rem;
        color: var(--text-color) !important;
    }
    
    .plan-card, .hotel-card {
        background-color: var(--card-bg) !important;
        border-color: var(--card-border) !important;
        color: var(--text-color) !important;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .plan-card {
        border-left: 5px solid var(--primary-color) !important;
    }
    
    .hotel-card {
        border: 1px solid var(--card-border) !important;
        padding: 1rem;
    }
    
    section[data-testid="stSidebar"] {
        background-color: var(--sidebar-bg) !important;
    }
    
    .stButton button {
        background-color: var(--primary-color) !important;
        color: white !important;
        font-weight: bold;
        border-radius: 10px;
        padding: 0.5rem 2rem;
        border: none;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(96, 165, 250, 0.3);
    }
    
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        background-color: var(--card-bg) !important;
        color: var(--text-color) !important;
        border-color: var(--card-border) !important;
    }
    
    label, p, span, div {
        color: var(--text-color) !important;
    }
    
    .stProgress > div > div {
        background-color: var(--primary-color) !important;
    }
    
    [data-testid="metric-container"] {
        background-color: var(--metric-bg) !important;
        border: 1px solid var(--card-border) !important;
    }
    
    .stAlert {
        background-color: var(--info-bg) !important;
        border-color: var(--card-border) !important;
    }
    
    .stSuccess {
        background-color: var(--success-bg) !important;
    }
    
    .streamlit-expanderHeader {
        background-color: var(--card-bg) !important;
        color: var(--text-color) !important;
    }
    
    .stCodeBlock {
        background-color: var(--card-bg) !important;
    }
    
    .day-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
"""
st.markdown(theme_css, unsafe_allow_html=True)

# ========== 核心函数 ==========
#初始化智谱 AI,缓存,避免重复创建
@st.cache_resource 
def get_client():
    return ZhipuAIClient()
    
#保存行程（json格式保存）
def save_plan_to_file(plan_data, destination):
    """保存行程到文件"""
    try:
        os.makedirs("data/saved_plans", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/saved_plans/{destination}_{timestamp}.json"
        plan_data['saved_at'] = timestamp
        plan_data['destination'] = destination
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(plan_data, f, ensure_ascii=False, indent=2)
        return filename
    except Exception as e:
        st.error(f"保存文件失败: {e}")
        return None

# ========== 侧边栏 ==========
def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.header("📋 填写旅行需求")
        
        destination = st.text_input("目的地", placeholder="例如：北京、青岛海边、云南大理")
        
        col1, col2 = st.columns(2)
        with col1:
            days = st.number_input("旅行天数", 1, 30, 3)
        with col2:
            people = st.number_input("出行人数", 1, 20, 2)
        
        budget = st.selectbox(
            "预算等级",
            ["经济型(人均300元/天以下)", "舒适型(人均300-600元/天)", "豪华型(人均600元/天以上)"],
            index=1
        )
        
        travel_styles = {
            "🏖️ 休闲放松": "轻松度假",
            "🎨 文化探索": "文化景点",
            "🍜 美食之旅": "品尝美食",
            "🏞️ 自然风光": "自然景观",
            "🎢 冒险刺激": "刺激体验",
            "👨‍👩‍👧‍👦 家庭亲子": "儿童友好",
            "💖 情侣浪漫": "浪漫",
            "📸 摄影打卡": "拍照打卡"
        }
        
        style = st.multiselect("旅行风格（可多选）", list(travel_styles.keys()), default=["🏖️ 休闲放松", "🏞️ 自然风光"])
        
        with st.expander("⚙️ 高级选项"):
            hotel_preference = st.selectbox(
                "住宿偏好", ["无特殊要求", "靠近景点", "交通便利", "安静区域", "特色民宿", "商务酒店"]
            )
            include_hotel_links = st.checkbox("包含酒店推荐", value=True)
            generate_story = st.checkbox("生成旅行叙事故事", value=True)
            save_plan = st.checkbox("保存本次行程", value=True)
        
        st.markdown("---")
        generate_btn = st.button("🚀 生成个性化旅行计划", type="primary", use_container_width=True, disabled=not destination)
        
        st.markdown("### 🔧 系统状态")
        client = get_client()
        if client.api_key:
            st.success("✅ 智谱AI连接正常")
        else:
            st.error("❌ 请配置API密钥")
    
    return {
        'destination': destination,
        'days': days,
        'people': people,
        'budget': budget,
        'style': style,
        'hotel_preference': hotel_preference,
        'include_hotel_links': include_hotel_links,
        'generate_story': generate_story,
        'save_plan': save_plan,
        'generate_btn': generate_btn
    }

# ========== 主页面 ==========
def render_main_page():
    """渲染主页面"""
    st.markdown('<h1 class="main-header">✈️ 个性化旅行规划与叙事生成助手</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">基于大语言模型的智能旅行规划系统 • 毕业设计项目</p>', unsafe_allow_html=True)

# ========== 行程生成 ==========
def generate_travel_plan(user_input):
    """生成旅行计划"""
    # 初始化变量
    attractions_data = []
    real_attractions = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 步骤1：获取坐标（高德地图）
    status_text.text("🗺️ 正在使用高德地图定位目的地...")
    progress_bar.progress(20)
    
    gaode_client = get_gaode_client()
    geo_result = gaode_client.geocode(user_input['destination'])
    
    if geo_result.get("status") != "success":
        st.error(f"❌ 无法找到目的地: {geo_result.get('message')}")
        return None
    
    city_location = geo_result["location"]
    city_name = geo_result.get("formatted_address", user_input['destination'])
    progress_bar.progress(40)
    
     # 步骤2：搜索景点（高德地图）
    status_text.text("🔍 正在使用高德地图探索当地景点...")
    progress_bar.progress(60)
    
    attractions_result = gaode_client.search_attractions(
        city_name=user_input['destination'],
        city_location=city_location,
        count=15
    )
    
    if attractions_result.get("status") == "success":
        attractions_data = attractions_result.get("results", [])
        real_attractions = [a["name"] for a in attractions_data[:10]]
        st.success(f"✅ 找到 {len(attractions_data)} 个真实景点")
    else:
        st.warning(f"景点搜索失败: {attractions_result.get('message')}")
    # 步骤3：搜索餐厅（高德地图）
    status_text.text("🍽️ 正在搜索当地美食餐厅...")
    progress_bar.progress(70)
    
    restaurants_result = gaode_client.search_restaurants(
        city_name=user_input['destination'],
        city_location=city_location,
        count=15,
        sort_by='rating'
    )
    
    if restaurants_result.get("status") == "success":
        restaurants_data = restaurants_result.get("restaurants", [])
        real_restaurants = [r["name"] for r in restaurants_data[:10]]
        st.success(f"✅ 找到 {len(restaurants_data)} 个优质餐厅")
    else:
        restaurants_data = []
        real_restaurants = []
        st.warning(f"餐厅搜索失败: {restaurants_result.get('message')}")
    
    # 步骤4：AI生成行程
    status_text.text("🤖 AI正在整合信息，生成个性化行程...")
    progress_bar.progress(80)
    
    client = get_client()
    ai_input = {
        "destination": user_input['destination'],
        "city_location": city_location,
        "real_attractions": real_attractions,
        "real_restaurants": real_restaurants,  # 添加餐厅信息
        "days": user_input['days'],
        "people": user_input['people'],
        "budget": user_input['budget'],
        "style": ", ".join(user_input['style']),
        "hotel_preference": user_input['hotel_preference'],
        "generate_story": user_input['generate_story']
    }
    
    result = client.generate_travel_plan(ai_input)
    progress_bar.progress(90)
    
    if "❌" in result.get("raw_response", "") or "⏰" in result.get("raw_response", ""):
        st.error(result["raw_response"])
        progress_bar.progress(100)
        return None
    
    # 步骤5：准备结果
    status_text.text("🎨 正在为您渲染最终行程...")
    plan = result["formatted_plan"]
    
    return {
        'plan': plan,
        'city_name': city_name,
        'city_location': city_location,
        'attractions_data': attractions_data,
        'restaurants_data': restaurants_data,  # ✅ 现在已定义
        'real_attractions': real_attractions,
        'real_restaurants': real_restaurants,  # ✅ 现在已定义
        'ai_input': ai_input,
        'result': result,
        'progress_bar': progress_bar,
        'status_text': status_text,
        'is_baidu': False  # 修改为False，因为用的是高德
    }
    
# ========== 结果显示 ==========

def display_real_locations(generation_result):
    """显示真实地点"""
    if generation_result.get('real_attractions') or generation_result.get('real_restaurants'):
        st.markdown("---")
        st.markdown("## 🗺️ 本次行程参考的真实地点")
        
        col1, col2 = st.columns(2)
        with col1:
            if generation_result.get('real_attractions'):
                st.markdown("**🏞️ 当地热门景点**")
                for attr in generation_result.get('real_attractions', [])[:5]:
                    st.markdown(f"- {attr}")
        
        with col2:
            if generation_result.get('real_restaurants'):  # ✅ 使用 .get()
                st.markdown("**🍽️ 当地热门美食**")
                for rest in generation_result.get('real_restaurants', [])[:5]:
                    st.markdown(f"- {rest}")

def display_detailed_plan(plan):
    """显示详细行程"""
    if "overview" in plan:
        st.markdown("### 📖 行程概述")
        st.markdown(plan.get("overview", ""))
    
    if "daily_plan" in plan and plan["daily_plan"]:
        st.markdown("### 📅 每日详细安排")
        for day in plan["daily_plan"]:
            with st.expander(f"**第{day.get('day', '?')}天**", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("**上午**")
                    st.markdown(day.get('morning', '暂无安排'))
                with col2:
                    st.markdown("**下午**")
                    st.markdown(day.get('afternoon', '暂无安排'))
                with col3:
                    st.markdown("**晚上**")
                    st.markdown(day.get('evening', '暂无安排'))
                if day.get('tips'):
                    st.info(f"💡 **小贴士**: {day['tips']}")
    
    if "budget_advice" in plan and plan["budget_advice"]:
        st.markdown("### 💰 预算建议")
        st.markdown(plan.get("budget_advice", ""))
    
    if "travel_story" in plan and plan["travel_story"]:
        st.markdown("### 📖 旅行叙事")
        st.markdown(plan.get("travel_story", ""))


def display_hotel_recommendations(city_name, city_location, user_budget):
    """显示真实酒店推荐"""
    try:
        # 导入高德酒店显示模块
        from utils.gaode_hotel_display import GaodeHotelDisplay
        gaode_client = get_gaode_client()
        
        GaodeHotelDisplay.display_real_hotels(
            gaode_client=gaode_client,
            city_name=city_name,
            city_location=city_location,
            user_budget=user_budget,
            hotel_count=8
        )
    except Exception as e:
        st.error(f"获取酒店数据失败: {str(e)}")
        st.info(f"""
        ### 💡 备用方案
        
        您可以直接在以下平台搜索"{city_name}"酒店：
        
        **📱 推荐平台：**
        - 携程旅行: https://hotels.ctrip.com
        - 美团酒店: https://hotel.meituan.com  
        - 飞猪旅行: https://www.fliggy.com
        
        **🔍 搜索建议：**
        1. 设置预算范围: {user_budget}
        2. 查看用户真实评价
        3. 注意酒店的取消政策
        4. 提前预订可能有优惠
        """)

def save_plan(generation_result, destination):
    """保存行程"""
    plan_data = {
        "user_input": generation_result['ai_input'],
        "real_attractions": generation_result['real_attractions'],
        # "real_restaurants": generation_result['real_restaurants'],  # 删除这行
        "ai_response": generation_result['result']["raw_response"],
        "formatted_plan": generation_result['plan'],
        "generated_at": datetime.now().isoformat()
    }
    
    saved_file = save_plan_to_file(plan_data, destination)
    if saved_file:
        st.success(f"✅ 行程已保存到: `{saved_file}`")
def show_export_options(plan_content, destination):
    """显示导出选项"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if isinstance(plan_content, dict):
        text_content = json.dumps(plan_content, ensure_ascii=False, indent=2)
    else:
        text_content = str(plan_content)
    
    st.markdown("---")
    st.markdown("## 📤 导出与分享")
    
    col1, col2, col3 = st.columns(3)
    
    # 文本下载
    filename_txt = f"{destination}_旅行计划_{timestamp}.txt"
    with col1:
        st.download_button(
            label="💾 下载文本文件",
            data=text_content,
            file_name=filename_txt,
            mime="text/plain"
        )
    
    # JSON 下载
    filename_json = f"{destination}_旅行计划_{timestamp}.json"
    with col2:
        st.download_button(
            label="⬇️ 下载JSON",
            data=text_content,
            file_name=filename_json,
            mime="application/json"
        )
    
    # 复制到剪贴板
    with col3:
        if st.button("📋 复制到剪贴板"):
            st.code(text_content[:500] + "..." if len(text_content) > 500 else text_content)
            st.success("请手动选择并复制上述内容 (Ctrl+C)")
def display_ai_route_planning(generation_result, user_input):
    """显示AI智能路线规划"""
    st.markdown("---")
    st.markdown("## 🗺️ AI智能路线规划")
    
    # 检查是否有景点数据
    attractions = generation_result.get('attractions_data', [])
    if len(attractions) < 2:
        st.warning("至少需要2个景点才能进行路线规划")
        
        # 显示简单地图
        gaode_client = get_gaode_client()
        map_image = gaode_client.get_static_map(
            location=generation_result['city_location'],
            zoom=12,
            size="800*400"
        )
        if map_image:
            st.markdown(f'<img src="{map_image}" style="width: 100%; border-radius: 10px;">', 
                      unsafe_allow_html=True)
        return
    
    # 获取高德客户端
    gaode_client = get_gaode_client()
    
    # 显示AI推荐的游览顺序和路线
    GaodeRoutePlanner.display_ai_route_plan(
        generation_result=generation_result,
        city_name=user_input['destination'],
        gaode_client=gaode_client
    )
    
    # 显示地图
    st.markdown("### 🗺️ 景点地图")
    
    # 准备标记点
    markers = []
    ordered_attractions = sorted(attractions, key=lambda x: x.get('rating', 0), reverse=True)
    
    for i, attraction in enumerate(ordered_attractions[:6]):
        location = attraction.get('location')
        if location:
            markers.append({
                "location": location,
                "label": str(i+1)  # 1, 2, 3...
            })
    
    if markers:
        map_image = gaode_client.get_static_map(
            location=generation_result['city_location'],
            zoom=13,
            size="800*500",
            markers=markers
        )
        
        if map_image:
            st.markdown(f'<img src="{map_image}" style="width: 100%; border-radius: 10px;">', 
                      unsafe_allow_html=True)
            
            # 显示图例
            st.markdown("**📍 地图标记（按推荐顺序）:**")
            cols = st.columns(3)
            for i, attraction in enumerate(ordered_attractions[:6]):
                with cols[i % 3]:
                    st.write(f"**{i+1}.** {attraction.get('name', f'景点{i+1}')[:12]}")
    
    # 显示步行方案
    GaodeRoutePlanner.display_simple_walking_route(
        attractions=attractions,
        city_name=user_input['destination'],
        gaode_client=gaode_client
    )
# ========== 主函数 ==========
# ========== 主函数 ==========
def main():
    """主函数"""
    # 初始化会话状态
    if 'should_generate' not in st.session_state:
        st.session_state.should_generate = False
    if 'generation_result' not in st.session_state:
        st.session_state.generation_result = None
    if 'current_user_input' not in st.session_state:
        st.session_state.current_user_input = None
    
    render_main_page()
    
    # 渲染侧边栏并获取用户输入
    user_input = render_sidebar()
    
    # 保存用户输入到会话状态
    st.session_state.current_user_input = user_input
    
    # 关键修改：如果按钮被点击，设置标志
    if user_input['generate_btn']:
        st.session_state.should_generate = True
        # 强制重绘
        st.rerun()
    
    # 关键修改：检查是否需要生成
    if st.session_state.should_generate and st.session_state.current_user_input:
        # 重置标志，避免重复生成
        st.session_state.should_generate = False
        
        # 显示加载状态
        with st.spinner('正在生成您的旅行计划，请稍候...'):
            # 生成行程
            generation_result = generate_travel_plan(st.session_state.current_user_input)
            
            if generation_result:
                # 保存结果
                st.session_state.generation_result = generation_result
            else:
                st.error("生成失败，请检查输入或稍后重试")
    
    # 显示结果（如果存在）
    if st.session_state.generation_result:
        display_results(st.session_state.generation_result, st.session_state.current_user_input)
    else:
        # 显示输入摘要
        display_input_summary(st.session_state.current_user_input)
def display_results(generation_result, user_input):
    """显示生成结果"""
    plan = generation_result['plan']
    
    # 显示行程概览
    st.markdown("## ✨ 您的个性化旅行计划")
    st.markdown(f"**目的地**: {generation_result['city_name']} | **天数**: {user_input['days']}天 | **人数**: {user_input['people']}人")
    st.markdown("---")
    
    # 显示详细行程
    display_detailed_plan(plan)
    
    # 显示地图和路线规划
    display_ai_route_planning(generation_result, user_input)
    
    # 显示真实地点
    display_real_locations(generation_result)
     # 也可以添加专门的路线规划调用
    if len(generation_result.get('attractions_data', [])) >= 2:
        from utils.gaode_route_display import GaodeRouteDisplay
        gaode_client = get_gaode_client()
        
        st.markdown("---")
        st.markdown("## 🗺️ 详细路线规划")
        
        GaodeRouteDisplay.display_route_planning(
            attractions=generation_result['attractions_data'][:5],
            city=user_input['destination'],
            gaode_client=gaode_client
        )
    
    # 酒店推荐（真实数据）
    if user_input['include_hotel_links']:
        display_hotel_recommendations(
            city_name=user_input['destination'],
            city_location=generation_result['city_location'],
            user_budget=user_input['budget']
        )
    # 餐厅推荐
    if user_input.get('budget'):  # 如果有预算信息
        try:
            gaode_client = get_gaode_client()
            GaodeRestaurantDisplay.display_restaurant_recommendations(
                gaode_client=gaode_client,
                city_name=user_input['destination'],
                city_location=generation_result['city_location'],
                user_budget=user_input['budget'],
                restaurant_count=6
            )
        except Exception as e:
            st.warning(f"餐厅推荐功能暂时不可用: {str(e)}")
    # 保存行程
    if user_input['save_plan']:
        save_plan(generation_result, user_input['destination'])
    
    # 导出选项
    show_export_options(plan, user_input['destination'])
def display_input_summary(user_input):
    """显示输入摘要"""
    if not user_input or not user_input['destination']:
        st.info("👈 请在左侧填写旅行需求，开始规划您的旅程")
    else:
        st.success("✅ 旅行需求已保存")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("目的地", user_input['destination'])
        with col2:
            st.metric("天数", f"{user_input['days']}天")
        with col3:
            st.metric("人数", f"{user_input['people']}人")
        with col4:
            st.metric("预算", user_input['budget'])
        st.write(f"**旅行风格**: {', '.join(user_input['style'])}")
        
        # 更明显的提示
        st.markdown("---")
        st.markdown("### 🎯 准备生成")
        st.info("请点击左侧边栏的 **🚀 生成个性化旅行计划** 按钮开始生成")
# ========== 入口点 ==========
if __name__ == "__main__":
    main()