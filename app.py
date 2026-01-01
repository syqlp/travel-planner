import streamlit as st
import json
import os
from datetime import datetime
from utils.api_handler import ZhipuAIClient

# 页面配置
st.set_page_config(
    page_title="个性化旅行规划助手",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #4B5563;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton button {
        background-color: #3B82F6;
        color: white;
        font-weight: bold;
        border-radius: 10px;
        padding: 0.5rem 2rem;
    }
    .stButton button:hover {
        background-color: #2563EB;
    }
    .plan-card {
        background-color: #F8FAFC;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #3B82F6;
        margin-bottom: 1rem;
    }
    .hotel-card {
        background-color: #EFF6FF;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 初始化API客户端
@st.cache_resource
def get_client():
    return ZhipuAIClient()

# 加载模拟酒店数据
def load_hotel_data():
    try:
        with open("data/hotels_mock.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

# 主界面
def main():
    # 标题
    st.markdown('<h1 class="main-header">✈️ 个性化旅行规划与叙事生成助手</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">基于大语言模型的智能旅行规划系统 • 毕业设计项目</p>', unsafe_allow_html=True)
    
    # 侧边栏 - 用户输入
    with st.sidebar:
        st.header("📋 填写旅行需求")
        
        # 目的地
        destination = st.text_input(
            "目的地",
            placeholder="例如：北京、青岛海边、云南大理",
            help="可以输入城市名或具体景区"
        )
        
        # 基础信息
        col1, col2 = st.columns(2)
        with col1:
            days = st.number_input("旅行天数", 1, 30, 3)
        with col2:
            people = st.number_input("出行人数", 1, 20, 2)
        
        # 预算选择
        budget = st.selectbox(
            "预算等级",
            ["经济型(人均300元/天以下)", "舒适型(人均300-600元/天)", "豪华型(人均600元/天以上)"],
            index=1
        )
        
        # 旅行风格
        travel_styles = {
            "🏖️ 休闲放松": "想要轻松度假，享受慢生活",
            "🎨 文化探索": "参观博物馆、历史遗迹，了解当地文化",
            "🍜 美食之旅": "品尝当地特色美食，探访餐馆小吃",
            "🏞️ 自然风光": "欣赏自然景观，户外活动",
            "🎢 冒险刺激": "寻求刺激体验，挑战性活动",
            "👨‍👩‍👧‍👦 家庭亲子": "适合家庭出行，儿童友好",
            "💖 情侣浪漫": "浪漫氛围，适合情侣"
        }
        
        style = st.multiselect(
            "旅行风格（可多选）",
            list(travel_styles.keys()),
            default=["🏖️ 休闲放松", "🏞️ 自然风光"]
        )
        
        # 额外需求
        with st.expander("⚙️ 高级选项"):
            hotel_preference = st.selectbox(
                "住宿偏好",
                ["无特殊要求", "靠近景点", "交通便利", "安静区域", "特色民宿"]
            )
            
            include_hotel_links = st.checkbox("包含酒店预订链接", value=True)
            generate_story = st.checkbox("生成旅行叙事", value=True)
        
        st.markdown("---")
        
        # 生成按钮
        generate_btn = st.button(
            "🚀 生成个性化旅行计划",
            type="primary",
            use_container_width=True,
            disabled=not destination
        )
        
        # 系统状态
        st.markdown("### 🔧 系统状态")
        client = get_client()
        if client.api_key:
            st.success("✅ 智谱AI连接正常")
        else:
            st.error("❌ 请配置API密钥")
    
    # 主内容区
    if not destination:
        show_welcome()
    elif generate_btn:
        generate_travel_plan(destination, days, people, budget, style, hotel_preference, 
                           include_hotel_links, generate_story)
    else:
        show_input_summary(destination, days, people, budget, style)

def show_welcome():
    """显示欢迎页面"""
    st.info("👈 请在左侧填写旅行需求，开始规划您的旅程")
    
    # 示例展示
    st.markdown("### 💡 功能演示")
    
    col1, col2, col3 = st.columns(3)
    
    examples = [
        {
            "title": "🏖️ 海边度假",
            "destination": "青岛",
            "days": 4,
            "budget": "舒适型",
            "description": "海滨风光、海鲜美食、悠闲假期"
        },
        {
            "title": "⛰️ 登山探险",
            "destination": "黄山",
            "days": 3,
            "budget": "经济型",
            "description": "日出云海、奇松怪石、登山体验"
        },
        {
            "title": "🏮 古城文化",
            "destination": "西安",
            "days": 5,
            "budget": "舒适型",
            "description": "历史遗迹、美食探索、文化体验"
        }
    ]
    
    for col, example in zip([col1, col2, col3], examples):
        with col:
            st.markdown(f'<div class="plan-card">', unsafe_allow_html=True)
            st.subheader(example["title"])
            st.write(f"**目的地**: {example['destination']}")
            st.write(f"**天数**: {example['days']}天")
            st.write(f"**预算**: {example['budget']}")
            st.write(f"**特色**: {example['description']}")
            st.markdown('</div>', unsafe_allow_html=True)
    
    # 功能特色
    st.markdown("### ✨ 系统特色")
    features = [
        ("🎯 个性化规划", "根据您的偏好生成独一无二的行程"),
        ("💰 智能预算", "合理分配住宿、餐饮、交通等费用"),
        ("🏨 酒店推荐", "提供多种住宿选择及预订信息"),
        ("📖 旅行叙事", "生成生动的旅行故事，增强体验感"),
        ("🗺️ 详细安排", "精确到每天的上午、下午、晚上活动")
    ]
    
    for icon, desc in features:
        st.write(f"{icon} {desc}")

def show_input_summary(destination, days, people, budget, style):
    """显示输入摘要"""
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

def generate_travel_plan(destination, days, people, budget, style, hotel_preference, 
                        include_hotel_links, generate_story):
    """生成旅行计划"""
    # 显示进度
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 模拟进度
    for percent in range(0, 101, 25):
        status_text.text(f"🔄 正在规划您的{destination}之旅... {percent}%")
        progress_bar.progress(percent / 100)
        import time
        time.sleep(0.5)
    
    # 准备用户输入
    user_input = {
        "destination": destination,
        "days": days,
        "people": people,
        "budget": budget,
        "style": ", ".join(style),
        "hotel_preference": hotel_preference
    }
    
    # 调用AI生成计划
    status_text.text("🤖 AI正在创作个性化行程...")
    client = get_client()
    result = client.generate_travel_plan(user_input)
    
    progress_bar.progress(1.0)
    status_text.text("✅ 行程生成完成！")
    time.sleep(0.5)
    
    # 显示结果
    st.markdown("## ✨ 您的个性化旅行计划")
    st.markdown(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.markdown("---")
    
    if result["raw_response"].startswith("❌") or result["raw_response"].startswith("⏰"):
        st.error(result["raw_response"])
    else:
        # 显示AI生成的内容
        st.markdown(result["formatted_plan"])
        
        # 添加酒店数据（模拟）
        if include_hotel_links:
            show_hotel_recommendations(destination)
        
        # 导出功能
        show_export_options(result["formatted_plan"], destination)

def show_hotel_recommendations(destination):
    """显示酒店推荐"""
    st.markdown("---")
    st.markdown("## 🏨 酒店推荐")
    
    hotels_data = load_hotel_data()
    city_hotels = hotels_data.get(destination, hotels_data.get("default", []))
    
    if city_hotels:
        for hotel in city_hotels[:3]:  # 显示前3个
            with st.container():
                st.markdown(f'<div class="hotel-card">', unsafe_allow_html=True)
                st.markdown(f"### {hotel['name']}")
                st.markdown(f"**价格范围**: {hotel['price_range']}")
                st.markdown(f"**特点**: {', '.join(hotel['features'])}")
                st.markdown(f"**[模拟预订链接]({hotel['link']})**")
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("暂无该目的地的酒店数据，将为您推荐通用酒店")

def show_export_options(content, destination):
    """显示导出选项"""
    st.markdown("---")
    st.markdown("## 📤 导出与分享")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 下载为文本
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{destination}_旅行计划_{timestamp}.txt"
        st.download_button(
            label="💾 下载文本文件",
            data=content,
            file_name=filename,
            mime="text/plain"
        )
    
    with col2:
        # 复制到剪贴板
        if st.button("📋 复制到剪贴板"):
            st.code(content[:500] + "..." if len(content) > 500 else content)
            st.success("已复制到剪贴板（请手动复制）")
    
    with col3:
        st.button("🖨️ 打印计划", disabled=True, help="功能开发中")

if __name__ == "__main__":
    main()