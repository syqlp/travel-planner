# utils/audio_recorder.py
import streamlit as st
from streamlit_audiorec import streamlit_audiorec
import tempfile
import base64

class AudioRecorder:
    """音频录制组件（基于streamlit-audiorec）"""
    
    @staticmethod
    def render_recorder():
        """
        渲染录音组件
        返回: 录音文件的base64编码或None
        """
        st.markdown("### 🎤 语音输入")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # 录音组件
            audio_bytes = streamlit_audiorec()
            
            if audio_bytes:
                # 显示音频播放器
                audio_html = f"""
                <audio controls autoplay style="width: 100%;">
                    <source src="data:audio/wav;base64,{base64.b64encode(audio_bytes).decode()}" type="audio/wav">
                </audio>
                """
                st.markdown(audio_html, unsafe_allow_html=True)
                
                # 保存到临时文件供识别使用
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                    tmp_file.write(audio_bytes)
                    tmp_path = tmp_file.name
                
                return tmp_path, audio_bytes
        
        with col2:
            # 录音提示
            st.info("""
            **录音提示：**
            1. 点击下方录音按钮
            2. 说出您的需求
            3. 点击停止按钮
            4. 自动识别并填充
            """)
        
        return None, None
    
    @staticmethod
    def save_audio_file(audio_bytes, filename="recording.wav"):
        """保存音频文件"""
        with open(filename, "wb") as f:
            f.write(audio_bytes)
        return filename