# app.py 
import streamlit as st
import json
import os
from datetime import datetime, timedelta
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

from utils.weather_display import WeatherDisplay
from utils.smart_weather_service import SmartWeatherService
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
        
        # 添加出行日期选择
        st.markdown("---")
        st.markdown("### 📅 出行日期")
        
        today = datetime.now().date()
        col_date1, col_date2 = st.columns(2)
        with col_date1:
            # 开始日期，默认今天
            start_date = st.date_input(
                "出发日期",
                value=today,
                min_value=today,
                max_value=today + timedelta(days=365),
                format="YYYY-MM-DD"
            )
        
        with col_date2:
            # 结束日期，根据天数自动计算
            end_date = st.date_input(
                "结束日期",
                value=today + timedelta(days=days-1),
                min_value=start_date,
                max_value=start_date + timedelta(days=30),
                format="YYYY-MM-DD"
            )
        
        # 如果结束日期早于开始日期，自动调整
        if end_date < start_date:
            end_date = start_date + timedelta(days=days-1)
            st.warning("结束日期已自动调整为开始日期之后")
        
        # 更新天数显示
        actual_days = (end_date - start_date).days + 1
        if actual_days != days:
            days = actual_days
            st.info(f"实际旅行天数: {days}天")
        
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
        
        # 这里定义 style 变量
        style = st.multiselect(
            "旅行风格（可多选）", 
            list(travel_styles.keys()), 
            default=["🏖️ 休闲放松", "🏞️ 自然风光"]
        )
        
        with st.expander("⚙️ 高级选项"):
            # 这里定义 hotel_preference 变量
            hotel_preference = st.selectbox(
                "住宿偏好", 
                ["无特殊要求", "靠近景点", "交通便利", "安静区域", "特色民宿", "商务酒店"]
            )
            
            # 这里定义 include_hotel_links 变量
            include_hotel_links = st.checkbox("包含酒店推荐", value=True)
            
            # 这里定义 generate_story 变量
            generate_story = st.checkbox("生成旅行叙事故事", value=True)
            
            # 这里定义 save_plan 变量
            save_plan = st.checkbox("保存本次行程", value=True)
        
        st.markdown("---")
        
        # 这里定义 generate_btn 变量
        generate_btn = st.button(
            "🚀 生成个性化旅行计划", 
            type="primary", 
            use_container_width=True, 
            disabled=not destination
        )
        
        st.markdown("### 🔧 系统状态")
        client = get_client()
        if client.api_key:
            st.success("✅ 智谱AI连接正常")
        else:
            st.error("❌ 请配置API密钥")
    
    # 确保返回所有定义的变量
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
        'generate_btn': generate_btn,  
        'start_date': start_date.strftime("%Y-%m-%d"),
        'end_date': end_date.strftime("%Y-%m-%d")
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
    restaurants_data = []
    real_restaurants = []
    
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
    progress_bar.progress(50)
    
    attractions_result = gaode_client.search_attractions(
        city_name=user_input['destination'],
        city_location=city_location,
        count=15
    )
    
    if attractions_result.get("status") == "success":
        attractions_data = attractions_result.get("results", [])
        real_attractions = [a["name"] for a in attractions_data[:10]]
        #st.success(f"✅ 找到 {len(attractions_data)} 个真实景点")
    else:
        st.warning(f"景点搜索失败: {attractions_result.get('message')}")
    
    # 步骤3：搜索餐厅（高德地图）
    status_text.text("🍽️ 正在搜索当地美食餐厅...")
    progress_bar.progress(60)
    
    restaurants_result = gaode_client.search_restaurants(
        city_name=user_input['destination'],
        city_location=city_location,
        count=15,
        sort_by='rating'
    )
    
    if restaurants_result.get("status") == "success":
        restaurants_data = restaurants_result.get("restaurants", [])
        real_restaurants = [r["name"] for r in restaurants_data[:10]]
        #st.success(f"✅ 找到 {len(restaurants_data)} 个优质餐厅")
    else:
        restaurants_data = []
        real_restaurants = []
        st.warning(f"餐厅搜索失败: {restaurants_result.get('message')}")
    
    # 步骤4：删除和风天气城市识别（不再需要）
    status_text.text("🌍 正在获取城市信息...")
    progress_bar.progress(70)
    
    # 初始化天气相关变量
    weather_data = None
    weather_city_name = city_name  # 使用高德地图的城市名
    
    # 步骤5：AI生成行程
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
    
    if "❌" in result.get("raw_response", "") or "⏰" in result.get("raw_response", ""):
        st.error(result["raw_response"])
        progress_bar.progress(100)
        return None
    
    # 步骤6：获取天气预测（使用智能天气服务）
    status_text.text("🌤️ 正在获取智能天气预测...")
    progress_bar.progress(90)
    
    try:
        # 导入智能天气服务
        from utils.smart_weather_service import SmartWeatherService
        smart_weather = SmartWeatherService(use_cache=True)
        
        # 智能识别城市（可处理任意输入）
        city_info = smart_weather.search_city_id(user_input['destination'])
        
        if city_info:
            weather_city_name = city_info.get("city_name", user_input['destination'])
            city_id = city_info.get("city_id", "")
            #st.success(f"✅ 已智能识别: {weather_city_name} (来源: {city_info.get('source')})")
            # 如果是智能生成的，给用户提示
            #if "智能" in city_info.get("source", ""):
                #st.info(f"💡 系统正在为您智能生成'{weather_city_name}'的天气预报")
            
            # 计算旅行天数
            from datetime import datetime
            start_date_obj = datetime.strptime(user_input['start_date'], "%Y-%m-%d")
            end_date_obj = datetime.strptime(user_input['end_date'], "%Y-%m-%d")
            travel_days = (end_date_obj - start_date_obj).days + 1
            
            # 获取智能天气数据
            forecast_days_needed = min(travel_days, 7)
            weather_result = smart_weather.get_weather_forecast(city_id, forecast_days_needed)
            
            if weather_result:
                # 格式化数据
                weather_data = smart_weather.format_for_display(
                    weather_result, 
                    weather_city_name, 
                    user_input['start_date'], 
                    user_input['end_date']
                )
                
                if weather_data and weather_data.get("status") == "success":
                    forecast_count = len(weather_data.get('forecast', []))
                    #st.success(f"✅ 已获取{forecast_count}天天气预测")
                else:
                    weather_data = {
                        "status": "error", 
                        "message": "天气数据格式化失败"
                    }
                    st.warning("⚠️ 天气数据获取不完整")
            else:
                weather_data = {
                    "status": "error", 
                    "message": "获取天气数据失败"
                }
                st.warning("⚠️ 天气数据获取失败")
        else:
            weather_data = {
                "status": "error", 
                "message": "无法识别城市"
            }
            st.warning("⚠️ 无法识别城市，跳过天气获取")
            
    except ImportError:
        st.warning("⚠️ 智能天气服务模块未找到，跳过天气获取")
        weather_data = {
            "status": "error", 
            "message": "天气服务模块未安装"
        }
    except Exception as e:
        st.error(f"天气服务错误: {str(e)}")
        weather_data = {
            "status": "error", 
            "message": f"天气服务暂时不可用: {str(e)}"
        }
    
    # 步骤7：智能预算分析
    status_text.text("💰 正在分析行程预算...")
    progress_bar.progress(95)

    try:
        from utils.smart_budget_analyzer import SmartBudgetAnalyzer
        
        # 使用智能分析器
        budget_analysis = SmartBudgetAnalyzer.analyze(
            user_input=user_input,
            city_name=city_name,
            attractions_count=len(attractions_data)
        )
        
        st.success("✅ 预算分析完成")
        
    except Exception as e:
        st.warning(f"⚠️ 预算分析失败: {str(e)}")
        budget_analysis = {
            "城市": city_name,
            "错误": f"预算分析异常: {str(e)}",
            "建议": "请检查输入格式"
        }
    # 步骤7：完成
    status_text.text("🎨 正在为您渲染最终行程...")
    progress_bar.progress(100)

    # 确保返回所有必要数据
    return {
        'plan': result["formatted_plan"],
        'city_name': city_name,  # 高德地图的城市名
        'weather_city_name': weather_city_name,  # 智能天气服务的城市名
        'city_location': city_location,
        'attractions_data': attractions_data,
        'restaurants_data': restaurants_data,
        'real_attractions': real_attractions,
        'real_restaurants': real_restaurants,
        'ai_input': ai_input,
        'result': result,
        'weather_data': weather_data,  # 包含天气数据
        'budget_analysis': budget_analysis,
    }
    
# ========== 结果显示 ==========
#"""显示真实地点"""
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
#"""显示详细行程"""
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
#"""显示真实酒店推荐"""
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
#"""保存行程"""
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
#"""显示导出选项"""
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
#"""显示AI智能路线规划"""
def display_ai_route_planning(generation_result, user_input):
    """显示AI智能路线规划"""
    
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
#"""格式化和风天气的预报数据"""
def _format_qweather_forecast(self, forecast_days, start_date, end_date):
    """格式化和风天气的预报数据"""
    from datetime import datetime
    
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    formatted = []
    for day in forecast_days:
        fx_date = day.get("fxDate", "")
        if start_date <= fx_date <= end_date:
            formatted.append({
                "date": fx_date,
                "weekday": self._get_weekday(datetime.strptime(fx_date, "%Y-%m-%d")),
                "weather_day": day.get("textDay", "晴"),
                "weather_night": day.get("textNight", "晴"),
                "weather_icon": self._get_weather_icon(day.get("iconDay", "100")),
                "temp_max": day.get("tempMax", "25"),
                "temp_min": day.get("tempMin", "15"),
                "humidity": day.get("humidity", "50"),
                "wind_dir_day": day.get("windDirDay", "无持续风向"),
                "wind_scale_day": day.get("windScaleDay", "1-2"),
                "precip": day.get("precip", "0"),
                "uv_index": day.get("uvIndex", "3"),
                "sunrise": day.get("sunrise", "06:00"),
                "sunset": day.get("sunset", "18:00"),
                "suggestions": self._generate_weather_suggestions(day)
            })
    
    return formatted
#"""获取星期几"""
def _get_weekday(self, date_obj):
    """获取星期几"""
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return weekdays[date_obj.weekday()]
#"""获取天气图标"""
def _get_weather_icon(self, code):
    """获取天气图标"""
    icon_map = {
        "100": "☀️", "101": "⛅", "102": "🌤️", "103": "🌥️",
        "104": "☁️", "150": "🌙", "151": "☁️",
        "300": "🌦️", "301": "🌧️", "302": "⛈️", "303": "🌧️",
        "305": "🌧️", "306": "💦", "307": "🌧️", "308": "🌧️",
        "309": "🌧️", "310": "🌧️", "311": "🌧️", "312": "🌧️",
        "313": "🌧️", "314": "🌧️", "315": "🌧️", "316": "🌧️",
        "317": "🌧️", "318": "🌧️", "399": "🌧️",
        "400": "🌨️", "401": "❄️", "402": "☃️", "403": "❄️",
        "404": "🌨️", "405": "🌨️", "406": "🌨️", "407": "🌨️",
        "408": "🌨️", "409": "🌨️", "410": "🌨️", "499": "❄️",
        "500": "🌫️", "501": "🌁", "502": "😷", "503": "💨",
        "504": "💨", "507": "💨", "508": "💨", "509": "🌫️",
        "510": "🌫️", "511": "🌁", "512": "🌁", "513": "🌁",
        "900": "🔥", "901": "🥶", "999": "🌈"
    }
    return icon_map.get(code, "🌈")
#"""生成天气建议"""
def _generate_weather_suggestions(self, day):
    """生成天气建议"""
    suggestions = []
    
    weather_day = day.get("textDay", "")
    temp_max = int(day.get("tempMax", 25))
    temp_min = int(day.get("tempMin", 15))
    uv_index = day.get("uvIndex", "3")
    
    # 温度建议
    if temp_max >= 30:
        suggestions.append("天气炎热，注意防暑")
    elif temp_max >= 25:
        suggestions.append("天气温暖，适合户外")
    elif temp_min <= 10:
        suggestions.append("天气较冷，注意保暖")
    
    # 天气建议
    if "雨" in weather_day:
        suggestions.append("有降雨，建议携带雨具")
    if "雪" in weather_day:
        suggestions.append("有降雪，注意路面湿滑")
    if "雷" in weather_day:
        suggestions.append("有雷电，避免户外活动")
    if int(uv_index) >= 6:
        suggestions.append("紫外线较强，注意防晒")
    
    return suggestions if suggestions else ["天气适宜出行"]
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
#预算显示
def _display_simple_budget(budget_analysis):
    """简易预算显示（备用方案）"""
    if not budget_analysis or isinstance(budget_analysis, str):
        st.warning("预算分析数据无效")
        return
    
    st.markdown("---")
    st.markdown("## 💰 预算分析概览")
    
    # 检查是否有错误信息
    if '错误' in budget_analysis:
        st.warning(f"⚠️ {budget_analysis['错误']}")
        return
    
    # 创建概览卡片
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_cost = budget_analysis.get('总费用', 0)
        st.metric("总预算", f"¥{total_cost:,.0f}")
    
    with col2:
        per_person = budget_analysis.get('人均费用', 0)
        st.metric("人均费用", f"¥{per_person:,.0f}")
    
    with col3:
        per_day = budget_analysis.get('日均费用', 0)
        st.metric("日均费用", f"¥{per_day:,.0f}")
    
    # 显示城市和天数信息
    st.caption(f"📍 **城市**: {budget_analysis.get('城市', '未知')} | 📅 **天数**: {budget_analysis.get('天数', 0)}天 | 👥 **人数**: {budget_analysis.get('人数', 0)}人")
    
    # 显示费用明细
    st.markdown("### 📋 费用明细")
    cost_breakdown = budget_analysis.get('费用明细', {})
    
    if cost_breakdown:
        for category, amount in cost_breakdown.items():
            if total_cost > 0:
                percentage = (amount / total_cost) * 100
            else:
                percentage = 0
            
            # 创建进度条表示占比
            col_prog, col_text = st.columns([1, 3])
            with col_prog:
                st.progress(min(percentage / 100, 1.0))
            with col_text:
                st.markdown(f"**{category}**: ¥{amount:,.0f} ({percentage:.1f}%)")
    else:
        st.info("暂无详细的费用明细数据")
    
    # 显示预算评估
    budget_assessment = budget_analysis.get('预算评估', {})
    if budget_assessment:
        st.markdown("### 📊 预算评估")
        
        status = budget_assessment.get('状态', '未知')
        status_colors = {
            "预算合理": "green",
            "预算合理偏低": "lightgreen", 
            "预算偏低": "orange",
            "预算略高": "orange",
            "预算偏高": "red"
        }
        
        status_color = status_colors.get(status, "blue")
        
        st.markdown(f"""
        <div style="
            background-color: {status_color}20;
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid {status_color};
            margin: 10px 0;
        ">
            <h4 style="margin: 0; color: {status_color};">{status}</h4>
            <p style="margin: 5px 0 0 0;">{budget_assessment.get('评估', '')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if budget_assessment.get('合理预算范围'):
            st.caption(f"💰 **合理预算范围**: {budget_assessment['合理预算范围']}")
    
    # 显示优化建议
    suggestions = budget_analysis.get('优化建议', [])
    if suggestions:
        st.markdown("### 💡 优化建议")
        
        for i, suggestion in enumerate(suggestions[:3]):  # 只显示前3条
            with st.expander(f"建议 {i+1}: {suggestion.get('类别', '通用')}", expanded=(i==0)):
                st.markdown(f"**建议**: {suggestion.get('建议', '')}")
                if suggestion.get('预计节省'):
                    st.markdown(f"**预计节省**: {suggestion['预计节省']}")
    
    # 显示每日明细（如果有）
    daily_breakdown = budget_analysis.get('每日明细', [])
    if daily_breakdown and len(daily_breakdown) > 0:
        st.markdown("### 📅 每日费用概览")
        
        # 创建简单的每日表格
        import pandas as pd
        df = pd.DataFrame(daily_breakdown)
        
        # 格式化数字显示
        for col in ['住宿', '餐饮', '交通', '门票', '购物', '其他', '小计']:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: f"¥{x:,.0f}" if pd.notnull(x) else "¥0")
        
        st.dataframe(df, use_container_width=True, hide_index=True)
def display_results(generation_result, user_input):
    """显示生成结果"""
    if not generation_result:
        st.error("❌ 生成结果为空")
        return
    
    plan = generation_result.get('plan', {})
    
    # 显示行程概览
    st.markdown("## ✨ 您的个性化旅行计划")
    st.markdown(f"**目的地**: {generation_result.get('city_name', '未知')} | **天数**: {user_input.get('days', 1)}天 | **人数**: {user_input.get('people', 1)}人")
    st.markdown("---")
    if generation_result.get('budget_analysis'):
        try:
            from utils.smart_budget_analyzer import SmartBudgetAnalyzer
            SmartBudgetAnalyzer.display(generation_result['budget_analysis'])
        except Exception as e:
            st.warning(f"预算显示失败: {str(e)}")
    
    st.markdown("---")
    # 显示详细行程
    display_detailed_plan(plan)
    
    # 天气显示部分 - 修复版
    if generation_result and generation_result.get('weather_data'):
        weather_data = generation_result['weather_data']
        
        try:
            # 尝试导入天气显示模块
            from utils.weather_display import WeatherDisplay
            
            if hasattr(WeatherDisplay, 'display_detailed_weather'):
                # 方法存在，正常调用
                WeatherDisplay.display_detailed_weather(weather_data)
            else:
                # 方法不存在，使用备选方案
                st.markdown("---")
                st.markdown(f"## 🌤️ {weather_data.get('city', '目的地')} 旅行天气")
                _display_weather_fallback(weather_data)
                
        except ImportError:
            # 模块导入失败，使用简易天气显示
            st.markdown("---")
            st.markdown(f"## 🌤️ {weather_data.get('city', '目的地')} 旅行天气")
            _display_weather_fallback(weather_data)
            
        except AttributeError:
            # 属性错误，使用备选方案
            st.markdown("---")
            st.markdown(f"## 🌤️ {weather_data.get('city', '目的地')} 旅行天气")
            _display_weather_fallback(weather_data)
        
        except Exception as e:
            st.error(f"天气显示错误: {str(e)}")
    
    # 显示地图和路线规划
    display_ai_route_planning(generation_result, user_input)
    
    # 显示真实地点
    display_real_locations(generation_result)
    
    # 也可以添加专门的路线规划调用
    if len(generation_result.get('attractions_data', [])) >= 2:
        try:
            from utils.gaode_route_display import GaodeRouteDisplay
            gaode_client = get_gaode_client()
            
            st.markdown("---")
            st.markdown("## 🗺️ 详细路线规划")
            
            GaodeRouteDisplay.display_route_planning(
                attractions=generation_result['attractions_data'][:5],
                city=user_input['destination'],
                gaode_client=gaode_client
            )
        except ImportError:
            st.warning("⚠️ 路线规划模块不可用")
        except Exception as e:
            st.warning(f"路线规划功能暂时不可用: {str(e)}")
    
    # 酒店推荐（真实数据）
    if user_input.get('include_hotel_links', False):
        try:
            display_hotel_recommendations(
                city_name=user_input['destination'],
                city_location=generation_result.get('city_location', ''),
                user_budget=user_input.get('budget', '中等')
            )
        except Exception as e:
            st.warning(f"酒店推荐功能暂时不可用: {str(e)}")
    
    # 餐厅推荐
    if user_input.get('budget'):  # 如果有预算信息
        try:
            from utils.gaode_route_display import GaodeRestaurantDisplay
            gaode_client = get_gaode_client()
            GaodeRestaurantDisplay.display_restaurant_recommendations(
                gaode_client=gaode_client,
                city_name=user_input['destination'],
                city_location=generation_result.get('city_location', ''),
                user_budget=user_input.get('budget', '中等'),
                restaurant_count=6
            )
        except ImportError:
            st.warning("⚠️ 餐厅推荐模块不可用")
        except Exception as e:
            st.warning(f"餐厅推荐功能暂时不可用: {str(e)}")
    
    # 保存行程
    if user_input.get('save_plan', False):
        try:
            save_plan(generation_result, user_input['destination'])
        except Exception as e:
            st.warning(f"保存行程失败: {str(e)}")
    
    # 导出选项
    try:
        show_export_options(plan, user_input['destination'])
    except Exception as e:
        st.warning(f"导出功能暂时不可用: {str(e)}")


def _display_weather_fallback(weather_data):
    """天气显示备选方案"""
    if not weather_data or weather_data.get("status") != "success":
        if weather_data and weather_data.get("message"):
            st.warning(f"⚠️ 天气数据: {weather_data.get('message')}")
        else:
            st.warning("⚠️ 天气数据不可用")
        return
    
    city_name = weather_data.get('city', '目的地')
    forecast = weather_data.get('forecast', [])
    
    if not forecast:
        st.info("暂无天气预报数据")
        return
    
    st.markdown(f"### 📅 {city_name} 旅行天气 ({len(forecast)}天)")
    
    # 按行显示天气卡片
    for i in range(0, len(forecast), 3):  # 每行最多3个
        cols = st.columns(min(3, len(forecast) - i))
        
        for col_idx in range(len(cols)):
            idx = i + col_idx
            if idx < len(forecast):
                day = forecast[idx]
                
                with cols[col_idx]:
                    # 创建天气卡片
                    with st.container():
                        # 日期
                        date_str = day.get('fxDate') or day.get('date') or f"第{idx+1}天"
                        weekday = _get_weekday_fallback(date_str)
                        
                        st.markdown(f"**{date_str}**")
                        if weekday:
                            st.caption(weekday)
                        
                        # 天气图标和描述
                        col_icon, col_desc = st.columns([1, 2])
                        with col_icon:
                            icon = day.get('iconDay') or day.get('weather_icon') or '🌈'
                            st.markdown(f"<h3 style='text-align: center; margin: 0;'>{icon}</h3>", unsafe_allow_html=True)
                        with col_desc:
                            weather = day.get('textDay') or day.get('weather_day') or '晴'
                            st.markdown(f"**{weather}**")
                        
                        # 温度
                        temp_max = day.get('tempMax') or day.get('temp_max') or '25'
                        temp_min = day.get('tempMin') or day.get('temp_min') or '15'
                        st.markdown(f"🌡️ **{temp_min}°C ~ {temp_max}°C**")
                        
                        # 其他信息
                        details = []
                        if day.get('humidity'):
                            details.append(f"💧 {day['humidity']}%")
                        if day.get('windDirDay') or day.get('wind_dir_day'):
                            wind = day.get('windDirDay') or day.get('wind_dir_day') or ''
                            details.append(f"💨 {wind}")
                        if day.get('precip') and day.get('precip') != '0':
                            details.append(f"🌧️ {day['precip']}mm")
                        
                        if details:
                            st.caption(" | ".join(details))
                        
                        # 建议
                        suggestions = day.get('suggestions', [])
                        if suggestions:
                            with st.expander("💡 建议", expanded=False):
                                for suggestion in suggestions:
                                    st.write(f"• {suggestion}")
    
    # 数据来源
    if weather_data.get('update_time'):
        source = weather_data.get('source', '智能天气系统')
        st.caption(f"🕒 更新时间: {weather_data['update_time']} | 数据来源: {source}")


def _get_weekday_fallback(date_str):
    """获取星期几（备选方案）"""
    from datetime import datetime
    try:
        if '-' in date_str:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        elif '月' in date_str and '日' in date_str:
            # 处理中文日期格式，如 "5月15日"
            import re
            match = re.search(r'(\d+)月(\d+)日', date_str)
            if match:
                month = int(match.group(1))
                day = int(match.group(2))
                year = datetime.now().year
                date_obj = datetime(year, month, day)
            else:
                return ""
        else:
            return ""
        
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        return weekdays[date_obj.weekday()]
    except:
        return ""
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