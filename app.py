# app.py 
import streamlit as st
import json
import os
import time 
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
import tempfile
import base64
from utils.voice_processor import VoiceProcessor
from utils.voice_synthesizer import VoiceSynthesizer
from utils.voice_recognizer import VoiceRecognizer  
# 页面配置
@st.cache_resource
def get_voice_recognizer():
    return VoiceRecognizer()
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
# 初始化语音组件
@st.cache_resource
def get_voice_processor():
    return VoiceProcessor()

@st.cache_resource  
def get_voice_synthesizer():
    return VoiceSynthesizer()
# ========== 主题样式 ==========
theme_css = """
<style>
.main-header {
        font-size: 2.8rem;
        font-weight: 800;
        text-align: center;
        margin: 1.5rem 0;
        background: linear-gradient(45deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .sub-header {
        font-size: 1.3rem;
        text-align: center;
        margin-bottom: 2.5rem;
        color: #94a3b8;
        font-weight: 300;
    }
    /* 主色调定义 */
    :root {
        --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        --bg-color: #0f172a;
        --text-color: #e2e8f0;
        --card-bg: #1e293b;
        --card-hover: #2d3748;
        --card-border: #4a5568;
        --primary-color: #60a5fa;
        --accent-color: #a78bfa;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --header-color: #93c5fd;
        --sidebar-bg: #1e293b;
        --metric-bg: #2d3748;
        --input-bg: #2d3748;
    }
    
    /* 整体样式 */
    .stApp {
        background-color: var(--bg-color) !important;
        color: var(--text-color) !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* 标题样式 */
    .main-header {
        font-size: 2.8rem;
        font-weight: 800;
        text-align: center;
        margin: 1.5rem 0;
        background: var(--primary-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
    }
    
    .sub-header {
        font-size: 1.3rem;
        text-align: center;
        margin-bottom: 2.5rem;
        color: #94a3b8;
        font-weight: 300;
    }
    
    /* 卡片设计 */
    .plan-card {
        background: var(--card-bg);
        border: none;
        border-radius: 16px;
        padding: 1.8rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        border-left: 6px solid var(--primary-color);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .plan-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: var(--primary-gradient);
    }
    
    .plan-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
    }
    
    /* 侧边栏美化 */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--sidebar-bg) 0%, #0f172a 100%);
        border-right: 1px solid #334155;
    }
    
    .stSidebarHeader {
        background: var(--primary-gradient) !important;
        padding: 1.5rem !important;
        margin-bottom: 1.5rem !important;
    }
    
    /* 按钮美化 */
    .stButton > button {
        background: var(--primary-gradient) !important;
        color: white !important;
        font-weight: 600;
        font-size: 1rem;
        border-radius: 12px;
        padding: 0.8rem 2rem;
        border: none;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        width: 100%;
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: 0.5s;
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
    }
    
    /* 输入框美化 */
    .stTextInput input, .stNumberInput input, .stSelectbox select, .stDateInput input {
        background-color: var(--input-bg) !important;
        color: var(--text-color) !important;
        border: 2px solid var(--card-border) !important;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus, .stSelectbox select:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.1) !important;
    }
    
    /* 标签样式 */
    label, p, span, div {
        color: var(--text-color) !important;
    }
    
    /* 进度条 */
    .stProgress > div > div {
        background: var(--primary-gradient) !important;
        border-radius: 10px;
    }
    
    /* 指标卡片 */
    [data-testid="metric-container"] {
        background: var(--metric-bg) !important;
        border: none !important;
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        border-left: 4px solid var(--accent-color);
    }
    
    [data-testid="metric-container"] > div > div {
        font-size: 1.1rem !important;
        color: var(--text-color) !important;
    }
    
    /* 警告/成功消息 */
    .stAlert {
        border-radius: 12px !important;
        border: none !important;
        padding: 1.2rem !important;
        margin: 1rem 0 !important;
    }
    
    .stSuccess {
        background: rgba(16, 185, 129, 0.15) !important;
        border-left: 4px solid var(--success-color) !important;
    }
    
    .stWarning {
        background: rgba(245, 158, 11, 0.15) !important;
        border-left: 4px solid var(--warning-color) !important;
    }
    
    .stError {
        background: rgba(239, 68, 68, 0.15) !important;
        border-left: 4px solid #ef4444 !important;
    }
    
    .stInfo {
        background: rgba(96, 165, 250, 0.15) !important;
        border-left: 4px solid var(--primary-color) !important;
    }
    
    /* 扩展器 */
    .streamlit-expanderHeader {
        background-color: var(--card-bg) !important;
        color: var(--text-color) !important;
        border-radius: 10px;
        padding: 1rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: var(--card-hover) !important;
    }
    
    /* 选项卡 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: var(--card-bg);
        padding: 8px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 20px;
        background-color: transparent;
        color: var(--text-color);
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--primary-gradient) !important;
        color: white !important;
        font-weight: 600;
    }
    
    /* 日间行程卡片 */
    .day-section {
        background: linear-gradient(135deg, rgba(96, 165, 250, 0.15) 0%, rgba(167, 139, 250, 0.15) 100%);
        border: 1px solid rgba(96, 165, 250, 0.2);
        color: white;
        padding: 1.2rem;
        border-radius: 12px;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
    }
    
    /* 美化滚动条 */
    ::-webkit-scrollbar {
        width: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--card-bg);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--primary-color);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-color);
    }
    
    /* 响应式调整 */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem;
        }
        
        .plan-card {
            padding: 1.2rem;
        }
    }
        /* 隐藏空容器 */
    .stMarkdownContainer:empty,
    .stMarkdown:empty {
        display: none !important;
    }

    /* 移除伪元素 */
    *::before, *::after {
        display: none !important;
        content: none !important;
    }
</style>
"""
st.markdown(theme_css, unsafe_allow_html=True)
#"""显示美化加载动画"""
def show_enhanced_loading():
    """显示美化加载动画"""
    import time
    
    # 创建加载容器
    with st.spinner(''):
        # 进度条
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 模拟步骤
        steps = [
            ("🗺️ 正在定位目的地...", 15),
            ("🔍 搜索景点和美食...", 30),
            ("🤖 AI智能规划行程...", 50),
            ("🌤️ 获取天气预测...", 70),
            ("💰 分析预算分配...", 85),
            ("✨ 生成最终方案...", 95),
            ("✅ 完成！", 100)
        ]
        
        for step_text, progress_value in steps:
            status_text.markdown(f"""
            <div style="
                background: linear-gradient(135deg, rgba(96, 165, 250, 0.1) 0%, rgba(167, 139, 250, 0.1) 100%);
                border: 1px solid rgba(96, 165, 250, 0.2);
                border-radius: 10px;
                padding: 1rem;
                margin: 0.5rem 0;
                color: #94a3b8;
            ">
                <span style="color: #60a5fa; font-weight: bold;">▶</span> {step_text}
            </div>
            """, unsafe_allow_html=True)
            
            progress_bar.progress(progress_value)
            time.sleep(0.3 if progress_value < 100 else 0.1)
        
        # 完成后的小动画
        time.sleep(0.5)
        status_text.success("🎉 行程生成完成！")
        progress_bar.empty()
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
def render_main_page():
    """渲染主页面"""
    st.markdown('<h1 class="main-header">🎤✈️ 智能语音旅行规划助手</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">基于CrewAI多代理协作 • 语音交互 • 智能规划</p>', unsafe_allow_html=True)
    
    # 添加特色功能展示
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 1rem; background: rgba(102, 126, 234, 0.1); border-radius: 10px;">
            <div style="font-size: 2rem;">🤖</div>
            <div style="font-weight: 600;">AI智能规划</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 1rem; background: rgba(245, 101, 101, 0.1); border-radius: 10px;">
            <div style="font-size: 2rem;">🎤</div>
            <div style="font-weight: 600;">语音交互</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 1rem; background: rgba(56, 161, 105, 0.1); border-radius: 10px;">
            <div style="font-size: 2rem;">🗺️</div>
            <div style="font-weight: 600;">实时地图</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style="text-align: center; padding: 1rem; background: rgba(139, 92, 246, 0.1); border-radius: 10px;">
            <div style="font-size: 2rem;">💰</div>
            <div style="font-weight: 600;">智能预算</div>
        </div>
        """, unsafe_allow_html=True)
def start_recording_process(voice_recognizer):
    """
    开始录音和识别过程 
    """
    import time
    import os
    from datetime import datetime
    
    try:
        # 1. 检查依赖
        success, message = voice_recognizer.check_dependencies()
        if not success:
            st.error(f"⚠️ {message}")
            return False
        
        # 2. 显示开始录音界面
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(245, 101, 101, 0.1) 0%, rgba(237, 100, 166, 0.1) 100%);
            border: 1px solid rgba(245, 101, 101, 0.3);
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
            text-align: center;
        ">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🎤</div>
            <div style="font-weight: 700; color: #f56565; font-size: 1.2rem; margin-bottom: 0.5rem;">
                正在准备录音...
            </div>
            <div style="color: #94a3b8;">
                请准备在提示后开始说话，说出您的旅行需求
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 3. 倒计时提示
        countdown_placeholder = st.empty()
        for i in range(3, 0, -1):
            countdown_placeholder.info(f"⏱️ 准备开始... {i}")
            time.sleep(1)
        countdown_placeholder.empty()
        
        # 4. 开始录音
        st.info("🎤 **正在录音... 请清晰说出您的旅行需求**")
        
        with st.spinner("🔴 录音中（8秒）..."):
            success, message = voice_recognizer.record_audio(duration=8)
        
        if not success:
            # 显示具体错误
            st.error(f"❌ **录音失败**")
            st.info(f"原因: {message}")
            
            # 提供解决方案
            st.markdown("""
            **💡 解决方案：**
            1. 检查麦克风是否已连接
            2. 确保麦克风权限已开启
            3. 点击右上角菜单 → 设置 → 重新运行
            4. 尝试重新录音
            """)
            return False
        
        # 5. 显示录音成功
        st.success("✅ **录音成功！**")
        
        # 6. 转录语音
        st.info("🔄 **正在识别语音内容...**")
        
        with st.spinner("识别中，请稍候..."):
            time.sleep(1)  # 让用户看到状态
            transcribe_success, result = voice_recognizer.transcribe_audio()
        
        if not transcribe_success:
            # 识别失败的处理
            st.warning(f"⚠️ **识别失败**")
            st.info(f"原因: {result}")
            
            # 但仍然显示录音数据（如果有）
            if hasattr(voice_recognizer, 'recording_data') and voice_recognizer.recording_data:
                st.session_state.recording_data = voice_recognizer.recording_data
                st.info("🎵 录音已保存，您可以重试识别或手动输入")
            
            return False
        
        # 7. 识别成功
        st.success("✨ **识别成功！**")
        
        # 8. 保存结果
        st.session_state.voice_text = result
        st.session_state.parsed_demand = voice_recognizer.parse_travel_demand(result)
        st.session_state.recording_data = voice_recognizer.recording_data
        
        # 9. 显示漂亮的结果卡片
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(52, 211, 153, 0.1) 100%);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
        ">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1rem;">
                <div style="
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    background: linear-gradient(45deg, #10b981, #34d399);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-shrink: 0;
                ">
                    <span style="color: white; font-size: 1.5rem;">✓</span>
                </div>
                <div>
                    <div style="font-weight: 800; color: #10b981; font-size: 1.3rem;">语音识别完成</div>
                    <div style="color: #94a3b8; font-size: 0.95rem;">系统已成功解析您的旅行需求</div>
                </div>
            </div>
            
            <div style="
                background: rgba(0, 0, 0, 0.15);
                border-radius: 10px;
                padding: 1.2rem;
                border-left: 5px solid #60a5fa;
                margin-top: 0.5rem;
            ">
                <div style="font-weight: 700; color: #60a5fa; margin-bottom: 0.8rem; font-size: 1.1rem;">
                    📝 识别结果
                </div>
                <div style="color: #e2e8f0; line-height: 1.7; font-size: 1.05rem; padding: 0.5rem;">
                    "{result}"
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 10. 显示解析结果
        if st.session_state.parsed_demand:
            demand = st.session_state.parsed_demand
            
            # 庆祝动画
            st.balloons()
            
            # 解析结果卡片
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(167, 139, 250, 0.1) 100%);
                border: 1px solid rgba(139, 92, 246, 0.3);
                border-radius: 12px;
                padding: 1.2rem;
                margin: 1rem 0;
            ">
                <div style="font-weight: 700; color: #8b5cf6; margin-bottom: 1rem; font-size: 1.1rem;">
                    🎯 已解析信息
                </div>
            """, unsafe_allow_html=True)
            
            # 创建信息网格
            cols = st.columns(4)
            info_items = [
                ("📍 目的地", demand['destination'] or "待确认", "#60a5fa"),
                ("📅 天数", f"{demand['days']}天", "#10b981"),
                ("👥 人数", f"{demand['people']}人", "#8b5cf6"),
                ("💰 预算", demand['budget'].split('(')[0], "#f59e0b")
            ]
            
            for idx, (label, value, color) in enumerate(info_items):
                with cols[idx]:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 0.8rem; background: rgba(255,255,255,0.05); border-radius: 8px;">
                        <div style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 0.3rem;">{label}</div>
                        <div style="color: {color}; font-weight: 700; font-size: 1.1rem;">{value}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # 提示用户应用设置
            st.info("💡 识别结果已保存，您可以：\n1. 点击下方'应用这些设置到表单'按钮\n2. 或直接在下方的表单中查看和调整")
        
        return True
        
    except Exception as e:
        st.error(f"❌ **录音过程中出现错误**")
        st.code(str(e))
        return False
def check_voice_dependencies():
    """检查语音识别依赖"""
    try:
        import speech_recognition as sr
        import pyaudio
        
        # 测试是否能创建Recognizer
        r = sr.Recognizer()
        
        # 测试是否能访问麦克风
        try:
            mics = sr.Microphone.list_microphone_names()
            if len(mics) == 0:
                return False, "未找到可用的麦克风设备"
            
            # 测试默认麦克风
            with sr.Microphone() as source:
                pass
                
            return True, "语音依赖检查通过"
            
        except Exception as e:
            return False, f"麦克风访问失败: {str(e)}"
            
    except ImportError as e:
        return False, f"缺少必要的库: {e}\n请安装: pip install SpeechRecognition pyaudio"
    except Exception as e:
        return False, f"依赖检查失败: {str(e)}"
# ========== 侧边栏 ==========
def render_sidebar():
    """渲染侧边栏 - 真实语音功能版"""
    with st.sidebar:
        # ========== 初始化所有session_state属性 ==========
        # 语音相关
        if 'voice_text' not in st.session_state:
            st.session_state.voice_text = ""
        if 'parsed_demand' not in st.session_state:
            st.session_state.parsed_demand = None
        if 'is_recording' not in st.session_state:
            st.session_state.is_recording = False
        if 'recording_start_time' not in st.session_state:
            st.session_state.recording_start_time = None
        if 'recording_duration' not in st.session_state:
            st.session_state.recording_duration = 0
        if 'recording_data' not in st.session_state:
            st.session_state.recording_data = None
        if 'audio_file_path' not in st.session_state:
            st.session_state.audio_file_path = None
        if 'recording_in_progress' not in st.session_state:
            st.session_state.recording_in_progress = False
        if 'apply_voice_settings' not in st.session_state:
            st.session_state.apply_voice_settings = False
        # ========== 美观的头部 ==========
        st.markdown("""
        <div style="
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            padding: 0.8rem 0;
            margin-bottom: 1.2rem;
            color: white;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        ">
            <div style="font-size: 2rem; line-height: 1;">🎤✈️</div>
            <div style="font-size: 1.3rem; font-weight: 700; line-height: 1.2; margin: 0.3rem 0 0.2rem 0;">智能语音旅行规划</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">毕业设计项目</div>
        </div>
        """, unsafe_allow_html=True)
        
        # ========== 语音输入区域 ==========
        st.markdown("#### 🎤 语音输入旅行需求")
        
        # 初始化语音识别器
        voice_recognizer = get_voice_recognizer()
        
        # 创建语音输入卡片
        with st.container():
            st.markdown("""<div style="background: rgba(30, 41, 59, 0.7); border-radius: 10px; padding: 1.2rem; border: 1px solid #334155; margin-bottom: 1rem;">""", unsafe_allow_html=True)
            
            # ========== 语音录音按钮 ==========
            st.markdown("##### 🎙️ 录音功能")
            
            # 检查依赖状态
            success, dep_message = voice_recognizer.check_dependencies()
             # 显示依赖状态
            if not success:
                st.markdown(f"""
                <div style="
                    background: rgba(245, 158, 11, 0.1);
                    border-radius: 8px;
                    padding: 0.8rem;
                    margin-bottom: 1rem;
                    border-left: 4px solid #f59e0b;
                ">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="color: #f59e0b;">⚠️</span>
                        <span style="color: #e2e8f0; font-weight: 600;">语音功能需要安装依赖</span>
                    </div>
                    <div style="color: #94a3b8; font-size: 0.9rem; margin-top: 0.5rem; padding-left: 24px;">
                        {dep_message}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # 创建录音控制行
            record_col1, record_col2, record_col3 = st.columns([2, 1, 1])
            
            with record_col1:
                # 开始录音按钮
                record_disabled = not success
                if st.button(
                    "● 开始录音",
                    key="start_record",
                    use_container_width=True,
                    type="primary",
                    disabled=record_disabled,
                    help="点击开始录音，请说出您的旅行需求"
                ):
                    if not success:
                        st.error(dep_message)
                    else:
                        st.session_state.is_recording = True
                        st.session_state.recording_start_time = time.time()
                        st.session_state.recording_duration = 0
                        
                        # 设置录音标志
                    st.session_state.recording_in_progress = True
                    st.session_state.voice_text = ""  # 清空旧结果
                    st.session_state.parsed_demand = None
                    st.rerun()
            
            with record_col2:
                # 停止录音按钮
                stop_disabled = not st.session_state.recording_in_progress
                if st.button(
                    "⏹️ 停止",
                    key="stop_record",
                    use_container_width=True,
                    disabled=stop_disabled,
                    help="停止当前录音"
                ):
                    st.session_state.recording_in_progress = False
                    st.info("录音已停止")
                    st.rerun()
            
            with record_col3:
                # 清除录音按钮
                if st.button(
                    "🗑️ 清除",
                    key="clear_record",
                    use_container_width=True,
                    help="清除当前录音内容"
                ):
                    st.session_state.recording_data = None
                    st.session_state.voice_text = ""
                    st.session_state.parsed_demand = None
                    st.session_state.recording_in_progress = False
                    st.session_state.recording_duration = 0
                    st.session_state.audio_file_path = None
                    st.success("录音内容已清除")
                    st.rerun()

            # ========== 执行录音过程 ==========
            if st.session_state.get('recording_in_progress', False):
                # 停止录音标志
                st.session_state.recording_in_progress = False
                
                # 执行录音过程
                recording_result = start_recording_process(voice_recognizer)
                
                # 如果录音成功，自动填充表单
                if recording_result and st.session_state.parsed_demand:
                    # 设置一个标志，让页面知道需要应用设置
                    st.session_state.apply_voice_settings = True
                    
            # ========== 显示录音结果 ==========
            if st.session_state.voice_text:
                st.markdown("##### 🔊 录音识别结果")
                
                # 显示识别结果
                st.markdown(f"""
                <div style="
                    background: rgba(96, 165, 250, 0.1);
                    border-radius: 8px;
                    padding: 1rem;
                    margin-top: 0.8rem;
                    margin-bottom: 1rem;
                    border-left: 4px solid #60a5fa;
                ">
                    <div style="font-weight: 600; color: #60a5fa; margin-bottom: 0.5rem;">📝 识别结果：</div>
                    <div style="color: #e2e8f0; line-height: 1.5; padding: 0.5rem; background: rgba(0,0,0,0.1); border-radius: 6px;">
                        {st.session_state.voice_text}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 显示录音时长
                if st.session_state.recording_duration > 0:
                    st.caption(f"⏱️ 录音时长: {st.session_state.recording_duration:.1f}秒")
                
                # 播放录音按钮
                if st.session_state.audio_file_path and os.path.exists(st.session_state.audio_file_path):
                    try:
                        with open(st.session_state.audio_file_path, "rb") as f:
                            audio_bytes = f.read()
                            audio_b64 = base64.b64encode(audio_bytes).decode()
                        
                        audio_html = f"""
                        <div style="margin: 1rem 0;">
                            <div style="font-weight: 600; color: #94a3b8; margin-bottom: 0.5rem; font-size: 0.9rem;">🔊 录音回放</div>
                            <audio controls style="width: 100%;">
                                <source src="data:audio/wav;base64,{audio_b64}" type="audio/wav">
                                您的浏览器不支持音频播放
                            </audio>
                        </div>
                        """
                        st.markdown(audio_html, unsafe_allow_html=True)
                    except:
                        st.info("🔊 录音文件存在，但播放需要刷新页面")
            
            # ========== 文本输入作为备选方案 ==========
            st.markdown("##### 📝 或手动输入")
            
            voice_input = st.text_area(
                "手动输入您的旅行需求",
                value=st.session_state.voice_text,
                placeholder="如果您不方便录音，也可以直接在这里输入文字\n示例：我想去北京玩三天，两个人，预算中等，喜欢文化古迹",
                height=80,
                key="voice_text_input",
                label_visibility="collapsed"
            )
            
            if voice_input != st.session_state.voice_text:
                st.session_state.voice_text = voice_input
                if voice_input.strip():
                    st.session_state.parsed_demand = parse_voice_demand(voice_input)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # ========== 快捷输入按钮 ==========
        st.markdown("##### 💡 快捷输入示例")
        
        quick_cols = st.columns(3)
        examples = [
            ("北京文化游", "北京三天文化游，两人，中等预算"),
            ("上海美食行", "上海周末美食之旅，两天时间"),
            ("青岛亲子游", "青岛七天亲子度假，预算宽松")
        ]
        
        for idx, (title, example) in enumerate(examples):
            with quick_cols[idx]:
                if st.button(
                    title,
                    key=f"quick_example_{idx}_{title}",
                    use_container_width=True,
                    help=f"点击使用：{example}"
                ):
                    st.session_state.voice_text = example
                    st.session_state.parsed_demand = parse_voice_demand(example)
                    st.rerun()
        
        # ========== 应用语音设置到表单 ==========
        if st.session_state.get('apply_voice_settings', False) and st.session_state.parsed_demand:
            st.session_state.apply_voice_settings = False
            
            with st.expander("📋 已识别需求（点击应用到表单）", expanded=True):
                demand = st.session_state.parsed_demand
                
                st.markdown("**🎯 系统已识别以下信息：**")
                
                info_cols = st.columns(4)
                
                with info_cols[0]:
                    st.markdown(f"""
                    <div style="...">
                        <div>目的地</div>
                        <div>{demand['destination'] or '待确认'}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with info_cols[1]:
                    st.markdown(f"""
                    <div style="...">
                        <div>旅行天数</div>
                        <div>{demand['days']}天</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with info_cols[2]:
                    st.markdown(f"""
                    <div style="...">
                        <div>出行人数</div>
                        <div>{demand['people']}人</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with info_cols[3]:
                    st.markdown(f"""
                    <div style="...">
                        <div>预算等级</div>
                        <div>{demand['budget'].split('(')[0]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # 自动应用按钮
                if st.button("✅ 自动填充到下方表单", use_container_width=True, type="primary"):
                    st.success("设置已应用到详细表单")
                    # 这里可以设置表单字段的默认值
                    st.rerun()
            # 文本输入作为备选方案
            st.markdown("##### 📝 或手动输入")
            
            voice_input = st.text_area(
                "手动输入您的旅行需求",
                value=st.session_state.voice_text,
                placeholder="如果您不方便录音，也可以直接在这里输入文字\n示例：我想去北京玩三天，两个人，预算中等，喜欢文化古迹",
                height=80,
                key="voice_text_input",
                label_visibility="collapsed"
            )
            
            if voice_input != st.session_state.voice_text:
                st.session_state.voice_text = voice_input
                if voice_input.strip():
                    st.session_state.parsed_demand = parse_voice_demand(voice_input)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # ========== 快捷输入按钮 ==========
        st.markdown("##### 💡 快捷输入示例")
        
        quick_cols = st.columns(3)
        examples = [
            ("北京文化游", "北京三天文化游，两人，中等预算"),
            ("上海美食行", "上海周末美食之旅，两天时间"),
            ("青岛亲子游", "青岛七天亲子度假，预算宽松")
        ]
        
        for idx, (title, example) in enumerate(examples):
            with quick_cols[idx]:
                if st.button(
                    title,
                    key=f"quick_example_{idx}",
                    use_container_width=True,
                    help=f"点击使用：{example}"
                ):
                    st.session_state.voice_text = example
                    st.session_state.parsed_demand = parse_voice_demand(example)
                    st.rerun()
        
        # ========== 解析结果展示 ==========
        if st.session_state.voice_text:
            with st.expander("📋 需求解析结果", expanded=True):
                # 显示解析结果
                if st.session_state.parsed_demand:
                    demand = st.session_state.parsed_demand
                    
                    # 创建信息卡片
                    st.markdown("**🎯 系统已识别以下信息：**")
                    
                    info_cols = st.columns(4)
                    
                    with info_cols[0]:
                        st.markdown(f"""
                        <div style="
                            background: rgba(96, 165, 250, 0.1);
                            border-radius: 8px;
                            padding: 0.8rem;
                            text-align: center;
                            border: 1px solid rgba(96, 165, 250, 0.3);
                        ">
                            <div style="font-size: 0.9rem; color: #94a3b8;">目的地</div>
                            <div style="font-size: 1.1rem; font-weight: 600; color: #60a5fa;">
                                {demand['destination'] or '待确认'}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with info_cols[1]:
                        st.markdown(f"""
                        <div style="
                            background: rgba(16, 185, 129, 0.1);
                            border-radius: 8px;
                            padding: 0.8rem;
                            text-align: center;
                            border: 1px solid rgba(16, 185, 129, 0.3);
                        ">
                            <div style="font-size: 0.9rem; color: #94a3b8;">旅行天数</div>
                            <div style="font-size: 1.1rem; font-weight: 600; color: #10b981;">
                                {demand['days']}天
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with info_cols[2]:
                        st.markdown(f"""
                        <div style="
                            background: rgba(139, 92, 246, 0.1);
                            border-radius: 8px;
                            padding: 0.8rem;
                            text-align: center;
                            border: 1px solid rgba(139, 92, 246, 0.3);
                        ">
                            <div style="font-size: 0.9rem; color: #94a3b8;">出行人数</div>
                            <div style="font-size: 1.1rem; font-weight: 600; color: #8b5cf6;">
                                {demand['people']}人
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with info_cols[3]:
                        st.markdown(f"""
                        <div style="
                            background: rgba(245, 158, 11, 0.1);
                            border-radius: 8px;
                            padding: 0.8rem;
                            text-align: center;
                            border: 1px solid rgba(245, 158, 11, 0.3);
                        ">
                            <div style="font-size: 0.9rem; color: #94a3b8;">预算等级</div>
                            <div style="font-size: 1.1rem; font-weight: 600; color: #f59e0b;">
                                {demand['budget'].split('(')[0]}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # 旅行风格展示
                    if demand['styles']:
                        st.markdown("**🎭 旅行风格偏好：**")
                        style_tags = " ".join([f"<span style='background: rgba(102, 126, 234, 0.2); padding: 4px 12px; border-radius: 20px; border: 1px solid rgba(102, 126, 234, 0.4); margin-right: 8px; display: inline-block; margin-bottom: 8px;'>{style}</span>" for style in demand['styles']])
                        st.markdown(f"<div>{style_tags}</div>", unsafe_allow_html=True)
                
                # 应用按钮
                if st.button("✅ 应用这些设置到下方表单", use_container_width=True, key="apply_settings"):
                    st.success("设置已应用到详细表单")
        
        st.markdown("---")
        st.markdown("#### ✍️ 详细设置（可调整）")
        
        # ========== 表单部分（预填语音识别结果）==========
        # 获取语音解析结果作为默认值
        default_dest = ""
        default_days = 3
        default_people = 2
        default_budget = "舒适型(人均300-600元/天)"
        default_styles = ["🏖️ 休闲放松", "🏞️ 自然风光"]
        
        if st.session_state.parsed_demand:
            demand = st.session_state.parsed_demand
            default_dest = demand['destination'] or ""
            default_days = demand['days']
            default_people = demand['people']
            default_budget = demand['budget']
            default_styles = demand['styles']
        
        # 使用卡片容器美化表单
        with st.container():
            st.markdown("""
            <div style="
                background: rgba(30, 41, 59, 0.7);
                border-radius: 10px;
                padding: 1.2rem;
                border: 1px solid #334155;
            ">
            """, unsafe_allow_html=True)
            
            # 目的地输入
            destination = st.text_input(
                "旅行目的地",
                value=default_dest,
                placeholder="请输入城市或景点名称",
                help="请填写具体的旅行目的地",
                key="destination_input"
            )
            
            # 基本参数
            col1, col2 = st.columns(2)
            with col1:
                days = st.number_input(
                    "旅行天数", 
                    1, 30, default_days, 
                    help="计划旅行的总天数",
                    key="days_input"
                )
            
            with col2:
                people = st.number_input(
                    "出行人数", 
                    1, 20, default_people, 
                    help="一起旅行的人数",
                    key="people_input"
                )
            
            # ========== 出行日期部分 ==========
            st.markdown("**📅 出行日期**")
            today = datetime.now().date()
            
            col_date1, col_date2 = st.columns(2)
            with col_date1:
                start_date = st.date_input(
                    "出发日期",
                    value=today,
                    min_value=today,
                    max_value=today + timedelta(days=365),
                    format="YYYY/MM/DD",
                    help="选择出发日期",
                    key="start_date_input",
                    label_visibility="collapsed"
                )
            
            with col_date2:
                end_date = st.date_input(
                    "结束日期",
                    value=today + timedelta(days=days-1),
                    min_value=start_date,
                    max_value=start_date + timedelta(days=30),
                    format="YYYY/MM/DD",
                    help="选择结束日期",
                    key="end_date_input",
                    label_visibility="collapsed"
                )
            
            # 日期验证提示
            if end_date < start_date:
                end_date = start_date + timedelta(days=days-1)
                st.warning("⚠️ 结束日期已自动调整为出发日期之后")
            
            actual_days = (end_date - start_date).days + 1
            if actual_days != days:
                days = actual_days
                st.info(f"📊 实际旅行天数: {days}天")
            
            # 预算选择
            budget = st.selectbox(
                "预算等级",
                ["经济型(人均300元/天以下)", "舒适型(人均300-600元/天)", "豪华型(人均600元/天以上)"],
                index=["经济型(人均300元/天以下)", "舒适型(人均300-600元/天)", "豪华型(人均600元/天以上)"].index(default_budget) 
                if default_budget in ["经济型(人均300元/天以下)", "舒适型(人均300-600元/天)", "豪华型(人均600元/天以上)"] else 1,
                help="根据您的消费能力选择合适的预算等级",
                key="budget_input"
            )
            
            # 旅行风格选择
            travel_styles = [
                "🏖️ 休闲放松", "🎨 文化探索", "🍜 美食之旅", 
                "🏞️ 自然风光", "🎢 冒险刺激", "👨‍👩‍👦 家庭亲子",
                "💖 情侣浪漫", "📸 摄影打卡"
            ]
            
            style = st.multiselect(
                "旅行风格偏好（可多选）",
                travel_styles,
                default=default_styles,
                help="选择您感兴趣的旅行体验类型",
                key="style_input"
            )
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # ========== 高级选项 ==========
        with st.expander("⚙️ 高级选项", expanded=False):
            cols = st.columns(2)
            
            with cols[0]:
                hotel_preference = st.selectbox(
                    "住宿偏好", 
                    ["无特殊要求", "靠近景点", "交通便利", "安静区域", "特色民宿", "商务酒店"],
                    help="选择您对住宿的特别要求",
                    key="hotel_preference_final"
                )
                
                include_hotel_links = st.checkbox(
                    "包含酒店推荐", 
                    value=True, 
                    help="在行程中包含推荐酒店信息",
                    key="hotel_checkbox_final"
                )
                
                generate_story = st.checkbox(
                    "生成旅行叙事故事", 
                    value=True, 
                    help="生成生动的旅行故事描述",
                    key="story_checkbox_final"
                )
            
            with cols[1]:
                save_plan = st.checkbox(
                    "保存本次行程", 
                    value=True, 
                    help="将生成的行程保存到本地文件",
                    key="save_checkbox_final"
                )
                
                # 语音播报设置
                st.markdown("**🔊 语音播报设置**")
                enable_voice_output = st.toggle(
                    "启用语音播报", 
                    value=True, 
                    help="生成行程后用语音播报关键信息",
                    key="enable_voice_output"
                )
                
                voice_style = st.selectbox(
                    "播报音色选择",
                    ["年轻女声", "专业男声", "温暖女声", "沉稳男声"],
                    index=0,
                    help="选择您喜欢的语音播报风格",
                    key="voice_style"
                )
        
        # ========== 生成按钮 ==========
        st.markdown("---")
        
        generate_btn = st.button(
            "🚀 开始生成个性化旅行计划", 
            type="primary", 
            use_container_width=True,
            disabled=not destination,
            help="点击开始生成您的专属旅行计划",
            key="generate_button_final"
        )
        
        # 提示信息
        if not destination:
            st.markdown("""
            <div style="
                text-align: center;
                padding: 1rem;
                background: linear-gradient(135deg, rgba(96, 165, 250, 0.1) 0%, rgba(167, 139, 250, 0.1) 100%);
                border-radius: 10px;
                border: 1px dashed #60a5fa;
                margin-top: 1rem;
            ">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">🎯</div>
                <div style="font-weight: 600; color: #e2e8f0; margin-bottom: 0.3rem;">请先填写旅行目的地</div>
                <div style="color: #94a3b8; font-size: 0.9rem;">
                    您可以使用上方语音输入或直接手动填写
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # 返回所有参数
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
        'enable_voice_output': enable_voice_output,
        'voice_style': voice_style,
        'start_date': start_date.strftime("%Y-%m-%d"),
        'end_date': end_date.strftime("%Y-%m-%d")
    }


def create_voice_output_panel(generation_result, user_input):
    """创建语音输出面板"""
    if not generation_result or not user_input.get('enable_voice_output', True):
        return
    
    st.markdown("---")
    st.markdown("### 🔊 语音播报行程")
    
    # 获取语音合成器
    voice_synth = get_voice_synthesizer()
    
    # 设置音色
    voice_map = {
        "年轻女声": "zh-CN-XiaoxiaoNeural",
        "专业男声": "zh-CN-YunxiNeural",
        "温暖女声": "zh-CN-XiaoyiNeural", 
        "沉稳男声": "zh-CN-YunjianNeural"
    }
    voice_synth.voice = voice_map.get(user_input.get('voice_style', '年轻女声'), "zh-CN-XiaoxiaoNeural")
    
    # 行程信息
    plan = generation_result.get('plan', {})
    city_name = generation_result.get('city_name', '目的地')
    days = user_input.get('days', 3)
    
    # 创建播报按钮
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📢 播报概览", use_container_width=True, key="voice_overview"):
            overview = plan.get('overview', f"为您规划了{days}天{city_name}的精彩旅行。")
            with st.spinner("生成语音中..."):
                audio_base64 = voice_synth.synthesize(overview[:300])
                if audio_base64:
                    audio_html = voice_synth.create_audio_player(audio_base64, autoplay=True)
                    st.markdown(audio_html, unsafe_allow_html=True)
                else:
                    st.warning("语音生成失败，请检查网络连接")
    
    with col2:
        if st.button("📍 播报安排", use_container_width=True, key="voice_daily"):
            daily_text = f"{city_name}{days}日游安排如下："
            daily_plan = plan.get('daily_plan', [])
            if daily_plan:
                for i, day in enumerate(daily_plan[:2]):  # 只播报前两天
                    day_num = day.get('day', i+1)
                    morning = day.get('morning', '自由活动')[:15]
                    afternoon = day.get('afternoon', '自由活动')[:15]
                    daily_text += f"第{day_num}天，上午{morning}，下午{afternoon}。"
            else:
                daily_text = f"{city_name}{days}天行程已规划完成。"
            
            with st.spinner("生成语音中..."):
                audio_base64 = voice_synth.synthesize(daily_text[:400])
                if audio_base64:
                    audio_html = voice_synth.create_audio_player(audio_base64, autoplay=True)
                    st.markdown(audio_html, unsafe_allow_html=True)
                else:
                    st.warning("语音生成失败")
    
    with col3:
        if st.button("💰 播报预算", use_container_width=True, key="voice_budget"):
            budget_text = plan.get('budget_advice', f"本次{city_name}{days}天旅行的详细预算建议已生成。")
            with st.spinner("生成语音中..."):
                audio_base64 = voice_synth.synthesize(budget_text[:200])
                if audio_base64:
                    audio_html = voice_synth.create_audio_player(audio_base64, autoplay=True)
                    st.markdown(audio_html, unsafe_allow_html=True)
                else:
                    st.warning("语音生成失败")
    
    # 自动播放欢迎语
    if user_input.get('auto_play', True) and 'voice_welcome_played' not in st.session_state:
        st.session_state.voice_welcome_played = True
        welcome_text = f"欢迎使用语音旅行助手，已为您生成{city_name}{days}天的个性化旅行计划。"
        audio_base64 = voice_synth.synthesize(welcome_text)
        if audio_base64:
            audio_html = voice_synth.create_audio_player(audio_base64, autoplay=True)
            st.markdown(audio_html, unsafe_allow_html=True)

# ========== 添加语音解析函数 ==========
def parse_voice_demand(text):
    """
    解析语音文本，提取旅行需求
    返回: 结构化需求字典
    """
    demand = {
        'destination': None,
        'days': 3,
        'people': 2,
        'budget': '舒适型(人均300-600元/天)',
        'styles': []
    }
    
    # 目的地提取
    destinations = ['北京', '上海', '广州', '深圳', '杭州', '成都', 
                   '西安', '南京', '武汉', '长沙', '青岛', '大理', 
                   '丽江', '三亚', '厦门', '重庆', '苏州', '云南',
                   '西藏', '新疆', '内蒙古', '哈尔滨', '桂林', '张家界']
    
    for dest in destinations:
        if dest in text:
            demand['destination'] = dest
            break
    
    # 天数提取
    import re
    day_patterns = [r'(\d+)\s*天', r'玩\s*(\d+)\s*天', r'旅行\s*(\d+)\s*天', r'(\d+)\s*日']
    for pattern in day_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                days = int(match.group(1))
                if 1 <= days <= 30:
                    demand['days'] = days
            except:
                pass
    
    # 人数提取
    people_patterns = [r'(\d+)\s*个人', r'(\d+)\s*人', r'(\d+)\s*位', r'(\d+)\s*个']
    for pattern in people_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                people = int(match.group(1))
                if 1 <= people <= 20:
                    demand['people'] = people
            except:
                pass
    
    # 预算提取
    if '经济' in text or '便宜' in text or '省钱' in text or '低预算' in text:
        demand['budget'] = '经济型(人均300元/天以下)'
    elif '豪华' in text or '奢侈' in text or '高端' in text or '高预算' in text:
        demand['budget'] = '豪华型(人均600元/天以上)'
    
    # 风格提取
    style_keywords = {
        '休闲': '🏖️ 休闲放松',
        '放松': '🏖️ 休闲放松',
        '文化': '🎨 文化探索', 
        '历史': '🎨 文化探索',
        '美食': '🍜 美食之旅',
        '吃': '🍜 美食之旅',
        '自然': '🏞️ 自然风光',
        '风景': '🏞️ 自然风光',
        '冒险': '🎢 冒险刺激',
        '刺激': '🎢 冒险刺激',
        '亲子': '👨‍👩‍👧‍👦 家庭亲子',
        '孩子': '👨‍👩‍👧‍👦 家庭亲子',
        '家庭': '👨‍👩‍👧‍👦 家庭亲子',
        '浪漫': '💖 情侣浪漫',
        '情侣': '💖 情侣浪漫',
        '摄影': '📸 摄影打卡',
        '拍照': '📸 摄影打卡'
    }
    
    for keyword, style in style_keywords.items():
        if keyword in text and style not in demand['styles']:
            demand['styles'].append(style)
    
    # 如果没有检测到风格，使用默认
    if not demand['styles']:
        demand['styles'] = ['🏖️ 休闲放松', '🏞️ 自然风光']
    
    return demand
# ========== 行程生成 ==========
def generate_travel_plan(user_input):
    """生成旅行计划 - 紧凑提示版"""
    # 初始化变量
    attractions_data = []
    real_attractions = []
    restaurants_data = []
    real_restaurants = []
    
    # 创建紧凑的消息容器
    message_container = st.empty()
    
    # 步骤1：获取坐标（高德地图）
    message_container.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(96, 165, 250, 0.1) 0%, rgba(167, 139, 250, 0.1) 100%);
        border: 1px solid rgba(96, 165, 250, 0.2);
        border-radius: 8px;
        padding: 0.8rem;
        margin: 0.5rem 0;
    ">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="
                width: 24px;
                height: 24px;
                border-radius: 50%;
                background: linear-gradient(45deg, #667eea, #764ba2);
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            ">
                <span style="color: white; font-size: 0.9rem;">1</span>
            </div>
            <div>
                <strong style="color: #e2e8f0;">🗺️ 正在定位目的地...</strong>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    gaode_client = get_gaode_client()
    geo_result = gaode_client.geocode(user_input['destination'])
    
    if geo_result.get("status") != "success":
        message_container.error(f"❌ 无法找到目的地: {geo_result.get('message')}")
        return None
    
    city_location = geo_result["location"]
    city_name = geo_result.get("formatted_address", user_input['destination'])
    
    # 步骤2：搜索景点（高德地图）
    message_container.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(96, 165, 250, 0.1) 0%, rgba(167, 139, 250, 0.1) 100%);
        border: 1px solid rgba(96, 165, 250, 0.2);
        border-radius: 8px;
        padding: 0.8rem;
        margin: 0.5rem 0;
    ">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="
                width: 24px;
                height: 24px;
                border-radius: 50%;
                background: linear-gradient(45deg, #667eea, #764ba2);
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            ">
                <span style="color: white; font-size: 0.9rem;">2</span>
            </div>
            <div>
                <strong style="color: #e2e8f0;">🔍 正在搜索当地景点和美食...</strong>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    attractions_result = gaode_client.search_attractions(
        city_name=user_input['destination'],
        city_location=city_location,
        count=15
    )
    
    if attractions_result.get("status") == "success":
        attractions_data = attractions_result.get("results", [])
        real_attractions = [a["name"] for a in attractions_data[:10]]
    else:
        # 使用紧凑的警告
        message_container.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(251, 191, 36, 0.1) 100%);
            border: 1px solid rgba(245, 158, 11, 0.3);
            border-radius: 8px;
            padding: 0.6rem;
            margin: 0.3rem 0;
        ">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="color: #f59e0b;">⚠️</span>
                <span style="color: #e2e8f0; font-size: 0.9rem;">景点搜索失败: {attractions_result.get('message', '未知错误')[:30]}...</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 步骤3：搜索餐厅
    restaurants_result = gaode_client.search_restaurants(
        city_name=user_input['destination'],
        city_location=city_location,
        count=15,
        sort_by='rating'
    )
    
    if restaurants_result.get("status") == "success":
        restaurants_data = restaurants_result.get("restaurants", [])
        real_restaurants = [r["name"] for r in restaurants_data[:10]]
    else:
        restaurants_data = []
        real_restaurants = []
    
    # 步骤4：AI生成行程
    message_container.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(96, 165, 250, 0.1) 0%, rgba(167, 139, 250, 0.1) 100%);
        border: 1px solid rgba(96, 165, 250, 0.2);
        border-radius: 8px;
        padding: 0.8rem;
        margin: 0.5rem 0;
    ">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="
                width: 24px;
                height: 24px;
                border-radius: 50%;
                background: linear-gradient(45deg, #667eea, #764ba2);
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            ">
                <span style="color: white; font-size: 0.9rem;">3</span>
            </div>
            <div>
                <strong style="color: #e2e8f0;">🤖 AI正在智能规划行程...</strong>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
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
        message_container.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(248, 113, 113, 0.1) 100%);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 8px;
            padding: 0.6rem;
            margin: 0.3rem 0;
        ">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="color: #ef4444;">❌</span>
                <span style="color: #e2e8f0; font-size: 0.9rem;">生成失败: {result.get('raw_response', '未知错误')[:40]}...</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return None
    
    # 步骤5：获取天气预测
    message_container.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(96, 165, 250, 0.1) 0%, rgba(167, 139, 250, 0.1) 100%);
        border: 1px solid rgba(96, 165, 250, 0.2);
        border-radius: 8px;
        padding: 0.8rem;
        margin: 0.5rem 0;
    ">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="
                width: 24px;
                height: 24px;
                border-radius: 50%;
                background: linear-gradient(45deg, #667eea, #764ba2);
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            ">
                <span style="color: white; font-size: 0.9rem;">4</span>
            </div>
            <div>
                <strong style="color: #e2e8f0;">🌤️ 正在获取天气预测...</strong>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    weather_data = {"status": "error", "message": "天气服务暂不可用"}
    weather_city_name = city_name
    
    try:
        from utils.smart_weather_service import SmartWeatherService
        smart_weather = SmartWeatherService(use_cache=True)
        city_info = smart_weather.search_city_id(user_input['destination'])
        
        if city_info:
            weather_city_name = city_info.get("city_name", user_input['destination'])
            city_id = city_info.get("city_id", "")
            
            # 计算旅行天数
            from datetime import datetime
            start_date_obj = datetime.strptime(user_input['start_date'], "%Y-%m-%d")
            end_date_obj = datetime.strptime(user_input['end_date'], "%Y-%m-%d")
            travel_days = (end_date_obj - start_date_obj).days + 1
            
            # 获取智能天气数据
            forecast_days_needed = min(travel_days, 7)
            weather_result = smart_weather.get_weather_forecast(city_id, forecast_days_needed)
            
            if weather_result:
                weather_data = smart_weather.format_for_display(
                    weather_result, 
                    weather_city_name, 
                    user_input['start_date'], 
                    user_input['end_date']
                )
    except:
        pass
    
    # 步骤6：智能预算分析
    message_container.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(96, 165, 250, 0.1) 0%, rgba(167, 139, 250, 0.1) 100%);
        border: 1px solid rgba(96, 165, 250, 0.2);
        border-radius: 8px;
        padding: 0.8rem;
        margin: 0.5rem 0;
    ">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="
                width: 24px;
                height: 24px;
                border-radius: 50%;
                background: linear-gradient(45deg, #667eea, #764ba2);
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            ">
                <span style="color: white; font-size: 0.9rem;">5</span>
            </div>
            <div>
                <strong style="color: #e2e8f0;">💰 正在进行预算分析...</strong>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    budget_analysis = {"城市": city_name, "错误": "预算分析暂不可用"}
    
    try:
        from utils.smart_budget_analyzer import SmartBudgetAnalyzer
        budget_analysis = SmartBudgetAnalyzer.analyze(
            user_input=user_input,
            city_name=city_name,
            attractions_count=len(attractions_data)
        )
    except:
        pass
    
    # 步骤7：完成提示 - 紧凑显示三个成功消息
    message_container.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(52, 211, 153, 0.1) 100%);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 8px;
        padding: 0.6rem;
        margin: 0.3rem 0;
    ">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: #10b981;">✅</span>
            <span style="color: #e2e8f0; font-size: 0.9rem; font-weight: 500;">行程生成完成！</span>
        </div>
    </div>
    
    <div style="
        background: linear-gradient(135deg, rgba(96, 165, 250, 0.1) 0%, rgba(167, 139, 250, 0.1) 100%);
        border: 1px solid rgba(96, 165, 250, 0.2);
        border-radius: 8px;
        padding: 0.6rem;
        margin: 0.3rem 0;
    ">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: #60a5fa;">🤖</span>
            <span style="color: #e2e8f0; font-size: 0.9rem;">正在智能识别: <strong>{city_name}</strong></span>
        </div>
    </div>
    
    <div style="
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(167, 139, 250, 0.1) 100%);
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 8px;
        padding: 0.6rem;
        margin: 0.3rem 0;
    ">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: #8b5cf6;">💰</span>
            <span style="color: #e2e8f0; font-size: 0.9rem; font-weight: 500;">预算分析完成</span>
        </div>
    </div>
    """.format(city_name=city_name), unsafe_allow_html=True)
    
    # 清空消息容器
    time.sleep(1)
    message_container.empty()
    
    # 确保返回所有必要数据
    return {
        'plan': result["formatted_plan"],
        'city_name': city_name,
        'weather_city_name': weather_city_name,
        'city_location': city_location,
        'attractions_data': attractions_data,
        'restaurants_data': restaurants_data,
        'real_attractions': real_attractions,
        'real_restaurants': real_restaurants,
        'ai_input': ai_input,
        'result': result,
        'weather_data': weather_data,
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
    """显示美化后的详细行程"""
    if "overview" in plan:
        with st.container():
            st.markdown('<div class="plan-card">', unsafe_allow_html=True)
            st.markdown("### 📖 行程概述")
            st.markdown(plan.get("overview", ""))
            st.markdown('</div>', unsafe_allow_html=True)
    
    if "daily_plan" in plan and plan["daily_plan"]:
        st.markdown("### 📅 每日详细安排")
        
        for day in plan["daily_plan"]:
            with st.expander(f"**第{day.get('day', '?')}天**", expanded=False):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown('<div class="day-section">', unsafe_allow_html=True)
                    st.markdown("#### 🌅 上午")
                    st.markdown(day.get('morning', '暂无安排'))
                    st.markdown('</div>', unsafe_allow_html=True)
                with col2:
                    st.markdown('<div class="day-section">', unsafe_allow_html=True)
                    st.markdown("#### ☀️ 下午")
                    st.markdown(day.get('afternoon', '暂无安排'))
                    st.markdown('</div>', unsafe_allow_html=True)
                with col3:
                    st.markdown('<div class="day-section">', unsafe_allow_html=True)
                    st.markdown("#### 🌃 晚上")
                    st.markdown(day.get('evening', '暂无安排'))
                    st.markdown('</div>', unsafe_allow_html=True)
                
                if day.get('tips'):
                    st.info(f"💡 **小贴士**: {day['tips']}")
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
    # 初始化语音相关的session_state
    if 'recording' not in st.session_state:
        st.session_state.recording = False
    if 'voice_text' not in st.session_state:
        st.session_state.voice_text = ""
    if 'parsed_demand' not in st.session_state:
        st.session_state.parsed_demand = None
    if 'voice_welcome_played' not in st.session_state:
        st.session_state.voice_welcome_played = False
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
    """显示美化后的生成结果"""
    if not generation_result:
        st.error("❌ 生成结果为空")
        return
    
    plan = generation_result.get('plan', {})
    
    # 显示行程概览
    st.markdown("## ✨ 您的个性化旅行计划")
    st.markdown(f"**目的地**: {generation_result.get('city_name', '未知')} | **天数**: {user_input.get('days', 1)}天 | **人数**: {user_input.get('people', 1)}人")
    st.markdown("---")
    
    # ========== 创建包含餐厅和酒店的导航栏 ==========
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📅 行程安排", 
        "🌤️ 天气预报", 
        "🗺️ 路线规划", 
        "💰 预算分析",
        "🏨 酒店推荐",  # 新增酒店选项卡
        "🍽️ 餐厅推荐",  # 新增餐厅选项卡
        "📋 详情导出"
    ])
    
    with tab1:
        # 显示详细行程
        display_detailed_plan(plan)
        
        # 显示真实地点
        display_real_locations(generation_result)
    
    with tab2:
        # 天气显示部分
        if generation_result.get('weather_data'):
            _display_weather_fallback(generation_result['weather_data'])
        else:
            st.info("天气数据正在加载中...")
    
    with tab3:
        # 显示地图和路线规划
        display_ai_route_planning(generation_result, user_input)
    
    with tab4:
        # 预算显示
        if generation_result.get('budget_analysis'):
            try:
                from utils.smart_budget_analyzer import SmartBudgetAnalyzer
                SmartBudgetAnalyzer.display(generation_result['budget_analysis'])
            except Exception as e:
                _display_simple_budget(generation_result['budget_analysis'])
    
    with tab5:  # 酒店推荐选项卡
        try:
            # 使用原有的酒店推荐函数
            display_hotel_recommendations(
                city_name=user_input['destination'],
                city_location=generation_result.get('city_location', ''),
                user_budget=user_input.get('budget', '中等')
            )
        except Exception as e:
            st.error(f"酒店推荐功能暂时不可用: {str(e)}")
            # 显示备用方案
            st.info(f"""
            ### 💡 酒店搜索备用方案
            
            您可以直接在以下平台搜索"{user_input['destination']}"酒店：
            
            **📱 推荐平台：**
            - 携程旅行: https://hotels.ctrip.com
            - 美团酒店: https://hotel.meituan.com  
            - 飞猪旅行: https://www.fliggy.com
            
            **💰 预算建议：**
            - {user_input.get('budget', '中等')}
            - 建议提前预订享受优惠
            """)
    
    with tab6:  # 餐厅推荐选项卡
        try:
            # 导入并使用餐厅显示模块
            from utils.gaode_restaurant_display import GaodeRestaurantDisplay
            
            gaode_client = get_gaode_client()
            GaodeRestaurantDisplay.display_restaurant_recommendations(
                gaode_client=gaode_client,
                city_name=user_input['destination'],
                city_location=generation_result.get('city_location', ''),
                user_budget=user_input.get('budget', '中等'),
                restaurant_count=8
            )
        except ImportError:
            st.error("餐厅推荐模块导入失败")
            # 尝试使用备用方案
            try:
                # 直接调用高德客户端搜索餐厅
                gaode_client = get_gaode_client()
                restaurants_result = gaode_client.search_restaurants(
                    city_name=user_input['destination'],
                    city_location=generation_result.get('city_location', ''),
                    count=10,
                    sort_by='rating'
                )
                
                if restaurants_result.get("status") == "success":
                    st.markdown("## 🍽️ 餐厅推荐")
                    restaurants = restaurants_result.get("restaurants", [])
                    
                    if restaurants:
                        # 显示餐厅列表
                        for i, restaurant in enumerate(restaurants[:8], 1):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"**{i}. {restaurant.get('name', '餐厅')}**")
                                if restaurant.get('address'):
                                    st.caption(f"📍 {restaurant['address'][:30]}")
                                rating = restaurant.get('rating', '0')
                                st.caption(f"⭐ {rating}分")
                            with col2:
                                if restaurant.get('price'):
                                    st.caption(f"💰 {restaurant['price']}")
                            st.markdown("---")
                    else:
                        st.info("暂无餐厅数据")
                else:
                    st.warning("餐厅数据获取失败")
            except Exception as e:
                st.error(f"餐厅推荐功能错误: {str(e)}")
        except Exception as e:
            st.error(f"餐厅推荐功能暂时不可用: {str(e)}")
    
    with tab7:
        # 保存和导出选项
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
        
        # 显示技术信息
        with st.expander("📊 技术详情", expanded=False):
            st.json({
                "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "城市坐标": generation_result.get('city_location', ''),
                "景点数量": len(generation_result.get('attractions_data', [])),
                "餐厅数量": len(generation_result.get('restaurants_data', [])),
                "AI模型": "智谱AI",
                "地图服务": "高德地图"
            })
            # ========== 新增：语音播报面板 ==========
    if generation_result and user_input.get('enable_voice_output', True):
        st.markdown("---")
        st.markdown("### 🔊 语音播报行程")
        
        # 初始化语音合成器
        voice_synth = get_voice_synthesizer()
        
        # 设置音色
        voice_map = {
            "年轻女声": "zh-CN-XiaoxiaoNeural",
            "专业男声": "zh-CN-YunxiNeural",
            "温暖女声": "zh-CN-XiaoyiNeural", 
            "沉稳男声": "zh-CN-YunjianNeural"
        }
        voice_synth.voice = voice_map.get(user_input.get('voice_style', '年轻女声'), "zh-CN-XiaoxiaoNeural")
        
        # 提取行程信息用于播报
        plan = generation_result.get('plan', {})
        city_name = generation_result.get('city_name', '目的地')
        days = user_input.get('days', 3)
        
        # 创建播报选项
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📢 播报行程概览", use_container_width=True, key="voice_overview"):
                overview_text = plan.get('overview', f"为您规划了{days}天{city_name}的精彩旅行。")
                with st.spinner("生成语音中..."):
                    audio_base64 = voice_synth.synthesize(overview_text[:300])  # 限制长度
                    if audio_base64:
                        audio_html = voice_synth.create_audio_player(audio_base64, autoplay=True)
                        st.markdown(audio_html, unsafe_allow_html=True)
        
        with col2:
            if st.button("📍 播报每日安排", use_container_width=True, key="voice_daily"):
                daily_text = f"{city_name}{days}日游安排如下："
                daily_plan = plan.get('daily_plan', [])
                for i, day in enumerate(daily_plan[:2]):  # 只播报前两天
                    day_num = day.get('day', i+1)
                    morning = day.get('morning', '自由活动')[:15]
                    afternoon = day.get('afternoon', '自由活动')[:15]
                    daily_text += f"第{day_num}天，上午{morning}，下午{afternoon}。"
                
                with st.spinner("生成语音中..."):
                    audio_base64 = voice_synth.synthesize(daily_text[:400])
                    if audio_base64:
                        audio_html = voice_synth.create_audio_player(audio_base64, autoplay=True)
                        st.markdown(audio_html, unsafe_allow_html=True)
        
        with col3:
            if st.button("💰 播报预算建议", use_container_width=True, key="voice_budget"):
                budget_text = plan.get('budget_advice', f"本次{city_name}{days}天旅行的详细预算建议已生成。")
                with st.spinner("生成语音中..."):
                    audio_base64 = voice_synth.synthesize(budget_text[:200])
                    if audio_base64:
                        audio_html = voice_synth.create_audio_player(audio_base64, autoplay=True)
                        st.markdown(audio_html, unsafe_allow_html=True)
        
        # 自动播放欢迎语
        if user_input.get('auto_play', True) and 'voice_welcome_played' not in st.session_state:
            st.session_state.voice_welcome_played = True
            welcome_text = f"欢迎使用语音旅行助手，已为您生成{city_name}{days}天的个性化旅行计划。"
            audio_base64 = voice_synth.synthesize(welcome_text)
            if audio_base64:
                audio_html = voice_synth.create_audio_player(audio_base64, autoplay=True)
                st.markdown(audio_html, unsafe_allow_html=True)
    create_voice_output_panel(generation_result, user_input)


def _display_weather_fallback(weather_data):
    """美化天气显示备选方案"""
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
    
    st.markdown(f"### 🌤️ {city_name} 旅行天气 ({len(forecast)}天)")
    
    # 创建天气卡片行
    for i in range(0, len(forecast), 4):  # 每行最多4个
        cols = st.columns(min(4, len(forecast) - i))
        
        for col_idx in range(len(cols)):
            idx = i + col_idx
            if idx < len(forecast):
                day = forecast[idx]
                
                with cols[col_idx]:
                    # 美化天气卡片
                    with st.container():
                        st.markdown("""
                        <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.9) 100%); 
                                    border: 1px solid #334155; 
                                    border-radius: 12px; 
                                    padding: 1rem; 
                                    text-align: center;
                                    transition: all 0.3s ease;">
                        """, unsafe_allow_html=True)
                        
                        # 日期
                        date_str = day.get('fxDate') or day.get('date') or f"第{idx+1}天"
                        weekday = _get_weekday_fallback(date_str)
                        
                        st.markdown(f"**{date_str}**")
                        if weekday:
                            st.caption(f"📅 {weekday}")
                        
                        # 天气图标（大号）
                        icon = day.get('iconDay') or day.get('weather_icon') or '🌈'
                        st.markdown(f"<h1 style='text-align: center; margin: 0.5rem 0;'>{icon}</h1>", unsafe_allow_html=True)
                        
                        # 天气描述
                        weather = day.get('textDay') or day.get('weather_day') or '晴'
                        st.markdown(f"**{weather}**")
                        
                        # 温度（带渐变色）
                        temp_max = day.get('tempMax') or day.get('temp_max') or '25'
                        temp_min = day.get('tempMin') or day.get('temp_min') or '15'
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(90deg, #667eea, #764ba2);
                            -webkit-background-clip: text;
                            -webkit-text-fill-color: transparent;
                            font-size: 1.5rem;
                            font-weight: bold;
                            margin: 0.5rem 0;
                        ">
                            {temp_min}° ~ {temp_max}°
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 详细信息
                        details = []
                        if day.get('humidity'):
                            details.append(f"💧 {day['humidity']}%")
                        if day.get('windDirDay') or day.get('wind_dir_day'):
                            wind = day.get('windDirDay') or day.get('wind_dir_day') or ''
                            details.append(f"💨 {wind[:2]}")
                        if day.get('precip') and day.get('precip') != '0':
                            details.append(f"🌧️ {day['precip']}mm")
                        
                        if details:
                            st.markdown(f"""
                            <div style="
                                background: rgba(255, 255, 255, 0.05);
                                border-radius: 8px;
                                padding: 0.5rem;
                                margin-top: 0.5rem;
                                font-size: 0.85rem;
                            ">
                                {' | '.join(details)}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
    
    # 数据来源信息
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