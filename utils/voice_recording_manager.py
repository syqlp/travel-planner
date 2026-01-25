# utils/voice_recording_manager.py

import time
import threading
import streamlit as st

class VoiceRecordingManager:
    """语音录音管理器，处理录音和识别的完整流程"""
    
    def __init__(self, voice_recognizer):
        self.voice_recognizer = voice_recognizer
        self.is_recording = False
        self.recording_thread = None
        self.stop_recording_flag = False
        self.recording_result = None
    
    def start_recording(self):
        """开始录音（使用线程）"""
        if self.is_recording:
            return False, "已经在录音中"
        
        self.is_recording = True
        self.stop_recording_flag = False
        self.recording_result = None
        
        # 启动录音线程
        self.recording_thread = threading.Thread(
            target=self._record_audio_thread,
            daemon=True
        )
        self.recording_thread.start()
        
        return True, "开始录音，请说话..."
    
    def stop_recording(self):
        """停止录音并开始识别"""
        if not self.is_recording:
            return False, "没有正在进行的录音"
        
        self.stop_recording_flag = True
        
        # 等待录音线程结束
        if self.recording_thread:
            self.recording_thread.join(timeout=5)
        
        self.is_recording = False
        
        # 处理录音结果
        return self._process_recording_result()
    
    def _record_audio_thread(self):
        """录音线程函数"""
        def stop_callback():
            return self.stop_recording_flag
        
        # 执行录音
        success, result = self.voice_recognizer.record_audio_streaming(stop_callback)
        
        if success:
            self.recording_result = {
                'success': True,
                'audio_file': result,
                'audio_bytes': self.voice_recognizer.audio_bytes
            }
        else:
            self.recording_result = {
                'success': False,
                'error': result
            }
    
    def _process_recording_result(self):
        """处理录音结果"""
        if not self.recording_result:
            return False, "没有录音结果"
        
        if not self.recording_result['success']:
            return False, self.recording_result['error']
        
        # 开始识别
        st.info("正在识别语音内容...")
        success, text = self.voice_recognizer.transcribe_audio()
        
        if success:
            return True, text
        else:
            return False, f"识别失败: {text}"
    
    def get_recording_status(self):
        """获取录音状态"""
        return self.is_recording