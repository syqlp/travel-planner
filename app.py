import streamlit as st
import json
import os
import time
from datetime import datetime
from utils.api_handler import ZhipuAIClient
from utils.data_fetcher import geocode, nearby_search

# 页面配置
st.set_page_config(
    page_title="个性化旅行规划助手",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== 只保留夜间模式 ==========
# 夜间模式颜色
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

# 注入CSS
st.markdown(theme_css, unsafe_allow_html=True)

# 初始化API客户端
@st.cache_resource
def get_client():
    return ZhipuAIClient()

# 加载模拟酒店数据
def load_hotel_data():
    try:
        with open("data/hotels_mock.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"加载酒店数据失败: {e}")
        return {}

# 保存生成的行程
def save_plan_to_file(plan_data, destination):
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

# ------------------- 酒店推荐 -------------------
def show_hotel_recommendations(destination):
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

# ------------------- 导出选项 -------------------
def show_export_options(content, destination):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if isinstance(content, dict):
        text_content = json.dumps(content, ensure_ascii=False, indent=2)
    else:
        text_content = str(content)

    st.markdown("---")
    st.markdown("## 📤 导出与分享")
    col1, col2, col3 = st.columns(3)

    # 文本下载
    filename_txt = f"{destination}_旅行计划_{timestamp}.txt"
    st.download_button(
        label="💾 下载文本文件",
        data=text_content,
        file_name=filename_txt,
        mime="text/plain"
    )

    # JSON 下载
    filename_json = f"{destination}_旅行计划_{timestamp}.json"
    st.download_button(
        label="⬇️ 下载JSON",
        data=text_content,
        file_name=filename_json,
        mime="application/json"
    )

    # 复制到剪贴板
    if st.button("📋 复制到剪贴板"):
        st.code(text_content[:500] + "..." if len(text_content) > 500 else text_content)
        st.success("请手动选择并复制上述内容 (Ctrl+C)")

# ------------------- 主程序 -------------------
def main():
    st.markdown('<h1 class="main-header">✈️ 个性化旅行规划与叙事生成助手</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">基于大语言模型的智能旅行规划系统 • 毕业设计项目</p>', unsafe_allow_html=True)

    with st.sidebar:
        st.header("📋 填写旅行需求")
        
        destination = st.text_input("目的地", placeholder="例如：北京、青岛海边、云南大理", key="destination_input")
        col1, col2 = st.columns(2)
        with col1:
            days = st.number_input("旅行天数", 1, 30, 3, key="days_input")
        with col2:
            people = st.number_input("出行人数", 1, 20, 2, key="people_input")
        
        budget = st.selectbox(
            "预算等级",
            ["经济型(人均300元/天以下)", "舒适型(人均300-600元/天)", "豪华型(人均600元/天以上)"],
            index=1,
            key="budget_input"
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
                "住宿偏好", ["无特殊要求", "靠近景点", "交通便利", "安静区域", "特色民宿", "商务酒店"], key="hotel_input"
            )
            include_hotel_links = st.checkbox("包含酒店推荐", value=True, key="hotel_check")
            generate_story = st.checkbox("生成旅行叙事故事", value=True, key="story_check")
            save_plan = st.checkbox("保存本次行程", value=True, key="save_check")
        
        st.markdown("---")
        generate_btn = st.button("🚀 生成个性化旅行计划", type="primary", use_container_width=True, disabled=not destination, key="generate_btn")
        
        st.markdown("### 🔧 系统状态")
        client = get_client()
        if client.api_key:
            st.success("✅ 智谱AI连接正常")
        else:
            st.error("❌ 请配置API密钥")
    
    if not destination:
        show_welcome()
    elif generate_btn:
        generate_travel_plan(destination, days, people, budget, style, hotel_preference, include_hotel_links, generate_story, save_plan)
    else:
        show_input_summary(destination, days, people, budget, style)

# ------------------- 页面辅助 -------------------
def show_welcome():
    st.info("👈 请在左侧填写旅行需求，开始规划您的旅程")

def show_input_summary(destination, days, people, budget, style):
    st.success("✅ 旅行需求已保存")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("目的地", destination)
    with col2:
        st.metric("天数", f"{days}天")
    with col3:
        st.metric("人数", f"{people}人")
    with col4:
        st.metric("预算", budget)
    st.write(f"**旅行风格**: {', '.join(style)}")
    st.info("点击左侧的 🚀 按钮生成您的旅行计划")

# ------------------- 生成行程 -------------------
def generate_travel_plan(destination, days, people, budget, style, hotel_preference, include_hotel_links, generate_story, save_plan):
    progress_bar = st.progress(0)
    status_text = st.empty()

    # === 步骤 1: 获取目的地真实坐标 ===
    status_text.text("🗺️ 正在定位目的地...")
    progress_bar.progress(20)
    
    geo_result = geocode(destination)
    
    # 如果查询失败，尝试在地址后加上"市"再查询
    if geo_result.get("status") != "1" or not geo_result.get("geocodes"):
        geo_result = geocode(destination + "市")
    
    if geo_result.get("status") != "1" or not geo_result.get("geocodes"):
        st.error(f"❌ 无法找到目的地 '{destination}'。请尝试更具体的名称，如'XX市'。")
        return
    
    city_location = geo_result["geocodes"][0]["location"]
    city_name = geo_result["geocodes"][0].get("formatted_address", destination)
    progress_bar.progress(40)
    
    # === 步骤 2: 获取周边真实POI（景点、美食） ===
    status_text.text("🔍 正在探索当地景点与美食...")
    progress_bar.progress(60)
    
    # 搜索景点 (类型代码: 050000)
    attractions = nearby_search("", city_location, radius=15000, types="050000")
    # 搜索美食 (类型代码: 050300)
    restaurants = nearby_search("", city_location, radius=5000, types="050300")
    
    # 提取POI名称列表
    real_attractions = [a["name"] for a in attractions.get("pois", [])[:8]]
    real_restaurants = [r["name"] for r in restaurants.get("pois", [])[:8]]
    
    # === 步骤 3: 调用AI生成行程 ===
    status_text.text("🤖 AI正在整合信息，生成个性化行程...")
    progress_bar.progress(80)
    
    client = get_client()
    user_input = {
        "destination": destination,
        "city_location": city_location,
        "real_attractions": real_attractions,
        "real_restaurants": real_restaurants,
        "days": days,
        "people": people,
        "budget": budget,
        "style": ", ".join(style),
        "hotel_preference": hotel_preference,
        "generate_story": generate_story
    }
    
    result = client.generate_travel_plan(user_input)
    progress_bar.progress(90)
    
    if "❌" in result["raw_response"] or "⏰" in result["raw_response"]:
        st.error(result["raw_response"])
        progress_bar.progress(100)
        return
    
    # === 步骤 4: 解析并展示结果 ===
    status_text.text("🎨 正在为您渲染最终行程...")
    
    plan = result["formatted_plan"]
    
    # 展示行程概览
    st.markdown("## ✨ 您的个性化旅行计划")
    st.markdown(f"**目的地**: {city_name} | **天数**: {days}天 | **人数**: {people}人")
    st.markdown("---")
    
    if "overview" in plan:
        st.markdown("### 📖 行程概述")
        st.markdown(plan.get("overview", ""))
    
    # 展示每日行程
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
    
    # 展示预算建议
    if "budget_advice" in plan and plan["budget_advice"]:
        st.markdown("### 💰 预算建议")
        st.markdown(plan.get("budget_advice", ""))
    
    # 展示旅行叙事
    if generate_story and "travel_story" in plan and plan["travel_story"]:
        st.markdown("### 📖 旅行叙事")
        st.markdown(plan.get("travel_story", ""))
    
    # === 步骤 5: 展示参考的真实地点 ===
    if real_attractions or real_restaurants:
        st.markdown("---")
        st.markdown("## 🗺️ 本次行程参考的真实地点")
        
        col1, col2 = st.columns(2)
        with col1:
            if real_attractions:
                st.markdown("**🏞️ 当地热门景点**")
                for attr in real_attractions[:5]:
                    st.markdown(f"- {attr}")
        
        with col2:
            if real_restaurants:
                st.markdown("**🍽️ 当地热门美食**")
                for rest in real_restaurants[:5]:
                    st.markdown(f"- {rest}")
    
    # === 步骤 6: 酒店推荐 ===
    if include_hotel_links:
        show_hotel_recommendations(destination)
    
    # === 步骤 7: 保存行程 ===
    if save_plan:
        status_text.text("💾 保存行程文件...")
        plan_data = {
            "user_input": user_input,
            "real_attractions": real_attractions,
            "real_restaurants": real_restaurants,
            "ai_response": result["raw_response"],
            "formatted_plan": plan,
            "generated_at": datetime.now().isoformat()
        }
        saved_file = save_plan_to_file(plan_data, destination)
        if saved_file:
            st.success(f"✅ 行程已保存到: `{saved_file}`")
    
    # 完成
    progress_bar.progress(100)
    status_text.text("✅ 行程生成完成！")
    time.sleep(0.5)
    
    # 显示导出选项
    show_export_options(plan, destination)

# ------------------- 主程序入口 -------------------
if __name__ == "__main__":
    main()