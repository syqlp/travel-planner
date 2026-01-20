# utils/voice_synthesizer.py
import edge_tts
import asyncio
import tempfile
import base64
from typing import Optional

class VoiceSynthesizer:
    """语音合成器（使用Edge-TTS）"""
    
    def __init__(self):
        self.voice = "zh-CN-XiaoxiaoNeural"  # 年轻女声
        self.rate = "+0%"  # 语速
        self.volume = "+0%"  # 音量
    
    async def synthesize_async(self, text: str) -> Optional[bytes]:
        """异步语音合成"""
        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=self.rate,
                volume=self.volume
            )
            
            # 保存到临时文件
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            await communicate.save(tmp_path)
            
            # 读取文件内容
            with open(tmp_path, "rb") as f:
                audio_data = f.read()
            
            # 清理临时文件
            import os
            os.unlink(tmp_path)
            
            return audio_data
            
        except Exception as e:
            print(f"语音合成失败: {e}")
            return None
    
    def synthesize(self, text: str) -> Optional[str]:
        """同步语音合成（返回base64编码）"""
        try:
            # 解决asyncio事件循环问题
            import nest_asyncio
            nest_asyncio.apply()
            
            # 运行异步函数
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            audio_data = loop.run_until_complete(self.synthesize_async(text))
            loop.close()
            
            if audio_data:
                return base64.b64encode(audio_data).decode()
            return None
            
        except Exception as e:
            st.error(f"语音合成失败: {str(e)}")
            return None
    
    def create_audio_player(self, audio_base64: str, autoplay: bool = True) -> str:
        """创建音频播放器HTML"""
        audio_html = f"""
        <audio id="voicePlayer" {'autoplay' if autoplay else ''} controls style="width: 100%;">
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            您的浏览器不支持音频播放
        </audio>
        """
        return audio_html