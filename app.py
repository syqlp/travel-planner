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

from utils.baidu_fetcher import BaiduMapClient, convert_bd09_to_wgs84_str #百度地图
from utils.map_generator import create_travel_map, create_simple_map, save_map_to_html

from utils.enhanced_map_generator import EnhancedTravelMap
from utils.route_display import RouteDisplay
# 页面配置
st.set_page_config(
    page_title="个性化旅行规划助手",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)
# 初始化百度地图客户端
#为避免重复初始化地图客户端、降低 API 调用开销，对地图客户端进行缓存
@st.cache_resource
def get_baidu_client():
    return BaiduMapClient()
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
#酒店数据（目前模拟数据）
def load_hotel_data():
    """加载酒店数据"""
    try:
        with open("data/hotels_mock.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"加载酒店数据失败: {e}")
        return {}
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
    # 初始化所有变量
    attractions_data = []
    real_attractions = []
    restaurants_data = []
    real_restaurants = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 步骤1：获取坐标（百度地图）
    status_text.text("🗺️ 正在定位目的地...")
    progress_bar.progress(20)
    
    baidu_client = get_baidu_client()
    #从地址到经纬度
    geo_result = baidu_client.geocode(user_input['destination'])
    
    if geo_result.get("status") != "success":
        # 尝试添加"市"后缀
        geo_result = baidu_client.geocode(user_input['destination'] + "市")
    
    if geo_result.get("status") != "success":
        st.error(f"❌ 无法找到目的地 '{user_input['destination']}': {geo_result.get('message', '未知错误')}")
        return None
    
    city_location = geo_result["location"]  # 格式: "lng,lat"
    city_name = geo_result.get("formatted_address", user_input['destination'])
    progress_bar.progress(40)
    
    # 步骤2：搜索景点和美食（百度地图）
    status_text.text("🔍 正在探索当地景点与美食...")
    progress_bar.progress(60)
    
    # 搜索景点
    attractions_result = baidu_client.search_attractions(city_location, radius=15000)
    
    # 搜索美食
    restaurants_result = baidu_client.search_restaurants(city_location, radius=5000)
    
    # 提取数据
    if attractions_result.get("status") == "success":
        attractions_data = attractions_result.get("results", [])
        real_attractions = [a["name"] for a in attractions_data[:8]]
    else:
        st.warning(f"景点搜索失败: {attractions_result.get('message')}")
    
    if restaurants_result.get("status") == "success":
        restaurants_data = restaurants_result.get("results", [])
        real_restaurants = [r["name"] for r in restaurants_data[:8]]
    else:
        st.warning(f"美食搜索失败: {restaurants_result.get('message')}")
    
    # 步骤3：AI生成行程
    status_text.text("🤖 AI正在整合信息，生成个性化行程...")
    progress_bar.progress(80)
    
    client = get_client()
    ai_input = {
        "destination": user_input['destination'],
        "city_location": city_location,
        "real_attractions": real_attractions,
        "real_restaurants": real_restaurants,
        "days": user_input['days'],
        "people": user_input['people'],
        "budget": user_input['budget'],
        "style": ", ".join(user_input['style']),
        "hotel_preference": user_input['hotel_preference'],
        "generate_story": user_input['generate_story']
    }
    
    result = client.generate_travel_plan(ai_input)
    progress_bar.progress(90)
    
    if "❌" in result["raw_response"] or "⏰" in result["raw_response"]:
        st.error(result["raw_response"])
        progress_bar.progress(100)
        return None
    
    # 步骤4：准备结果
    status_text.text("🎨 正在为您渲染最终行程...")
    plan = result["formatted_plan"]
    
    return {
        'plan': plan,
        'city_name': city_name,
        'city_location': city_location,
        'attractions_data': attractions_data,
        'restaurants_data': restaurants_data,
        'real_attractions': real_attractions,
        'real_restaurants': real_restaurants,
        'ai_input': ai_input,
        'result': result,
        'progress_bar': progress_bar,
        'status_text': status_text,
        'is_baidu': True
    }
# ========== 结果显示 ==========
def display_results(generation_result, user_input):
    """显示生成结果"""
    plan = generation_result['plan']
    
    # 显示行程概览
    st.markdown("## ✨ 您的个性化旅行计划")
    st.markdown(f"**目的地**: {generation_result['city_name']} | **天数**: {user_input['days']}天 | **人数**: {user_input['people']}人")
    st.markdown("---")
    
    # 显示详细行程
    display_detailed_plan(plan)
    
    # 显示地图
    display_travel_map(generation_result, user_input)
    
    # 显示真实地点
    display_real_locations(generation_result)
    
    # 酒店推荐
    if user_input['include_hotel_links']:
        display_hotel_recommendations(user_input['destination'])
    
    # 保存行程
    if user_input['save_plan']:
        save_plan(generation_result, user_input['destination'])
    
    # 导出选项
    show_export_options(plan, user_input['destination'])

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

# 显示地图
def display_travel_map(generation_result, user_input):
    """显示增强版旅行地图"""
    st.markdown("---")
    st.markdown("## 🗺️ 智能路线规划")
    
    # 交通方式选择
    travel_mode = st.radio(
        "选择交通方式:",
        ["🚶 纯步行", "🚇 公共交通(地铁+公交)", "🚗 驾车"],
        index=1,
        horizontal=True
    )
    
    mode_map = {
        "🚶 纯步行": "walking",
        "🚇 公共交通(地铁+公交)": "transit",
        "🚗 驾车": "driving"
    }
    
    mode_key = mode_map[travel_mode]
    
    # 检查景点数据
    if 'attractions_data' in generation_result and generation_result['attractions_data']:
        pois_data = generation_result['attractions_data']
        
        if len(pois_data) >= 2:
            # 创建增强地图
            baidu_client = get_baidu_client()
            map_generator = EnhancedTravelMap(baidu_client)
            
            # 获取路线规划
            bd_locations = [poi.get("location") for poi in pois_data[:6] if poi.get("location")]
            route_plan = baidu_client.get_multi_route_plan(bd_locations, mode_key)
            
            # 显示路线详情
            RouteDisplay.display_route_details(route_plan, pois_data[:6], mode_key)
            
            # 显示地图
            travel_map = map_generator.create_intelligent_route_map(
                destination=generation_result['city_name'],
                pois_data=pois_data[:6],  # 最多6个景点
                city_location=generation_result['city_location'],
                mode=mode_key
            )
            
            if travel_map:
                st.markdown("### 📍 交互式地图")
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    map_component = st_folium(
                        travel_map,
                        width=800,
                        height=600,
                        returned_objects=[]
                    )
                
                with col2:
                    st.markdown("### 🎯 使用说明")
                    st.markdown("""
                    1. **点击数字标记**查看景点详情
                    2. **蓝色路线**为推荐游览顺序
                    3. **地图上的标签**显示每段路线信息
                    4. **右上角**可全屏查看
                    5. **右下角**有小地图导航
                    """)
                    
                    # 路线统计
                    if route_plan.get("status") == "success":
                        total_km = route_plan.get("total_distance", 0) / 1000
                        total_min = route_plan.get("total_duration", 0) // 60
                        
                        st.info(f"""
                        **📊 路线统计**
                        - 总距离: {total_km:.1f}公里
                        - 预计时间: {total_min}分钟
                        - 景点数量: {len(pois_data[:6])}个
                        - 建议游览: 1天
                        """)
        else:
            st.warning("至少需要2个景点才能生成路线规划")
            # 显示简单地图
            simple_map = create_simple_map(generation_result['city_location'])
            if simple_map:
                st_folium(simple_map, width=800, height=400)
    else:
        st.warning("未找到景点数据")

def display_real_locations(generation_result):
    """显示真实地点"""
    if generation_result['real_attractions'] or generation_result['real_restaurants']:
        st.markdown("---")
        st.markdown("## 🗺️ 本次行程参考的真实地点")
        
        col1, col2 = st.columns(2)
        with col1:
            if generation_result['real_attractions']:
                st.markdown("**🏞️ 当地热门景点**")
                for attr in generation_result['real_attractions'][:5]:
                    st.markdown(f"- {attr}")
        
        with col2:
            if generation_result['real_restaurants']:
                st.markdown("**🍽️ 当地热门美食**")
                for rest in generation_result['real_restaurants'][:5]:
                    st.markdown(f"- {rest}")

def display_hotel_recommendations(destination):
    """显示酒店推荐"""
    st.markdown("---")
    st.markdown("## 🏨 酒店推荐")
    
    hotels_data = load_hotel_data()
    city_hotels = None
    
    for city in hotels_data.keys():
        if city in destination or destination in city:
            city_hotels = hotels_data[city]
            break
    
    if not city_hotels:
        city_hotels = hotels_data.get("default", [])
    
    if city_hotels:
        st.info(f"为您推荐{destination}的酒店（模拟数据）")
        for hotel in city_hotels[:3]:
            with st.container():
                st.markdown('<div class="hotel-card">', unsafe_allow_html=True)
                col1, col2 = st.columns([3,1])
                with col1:
                    st.markdown(f"### {hotel['name']}")
                    st.markdown(f"**特点**: {', '.join(hotel['features'])}")
                    st.markdown(f"**设施**: {hotel.get('amenities','WiFi、早餐、停车场')}")
                with col2:
                    st.markdown(f"**价格**")
                    st.markdown(f"### {hotel['price_range']}")
                    st.markdown(f"**[查看详情]({hotel['link']})**")
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("暂时没有该目的地的酒店数据")

def save_plan(generation_result, destination):
    """保存行程"""
    plan_data = {
        "user_input": generation_result['ai_input'],
        "real_attractions": generation_result['real_attractions'],
        "real_restaurants": generation_result['real_restaurants'],
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