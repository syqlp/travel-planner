# utils/baidu_voice_recognizer.py
from aip import AipSpeech
import streamlit as st
import tempfile
import os

class BaiduVoiceRecognizer:
    """百度语音识别（国内可用）"""
    
    def __init__(self):
        # 百度AI开放平台申请的API Key（免费申请）
        self.APP_ID = '你的APP_ID'
        self.API_KEY = '你的API_KEY'
        self.SECRET_KEY = '你的SECRET_KEY'
        
        # 初始化客户端
        self.client = AipSpeech(self.APP_ID, self.API_KEY, self.SECRET_KEY)
        
        # 语音识别参数
        self.RATE = 16000  # 采样率
        self.FORMAT = 'wav'  # 格式
        self.DEV_PID = 1537  # 普通话(支持简单的英文识别)
    
    def recognize_from_file(self, audio_file_path):
        """从文件识别语音"""
        try:
            # 读取音频文件
            with open(audio_file_path, 'rb') as fp:
                audio_data = fp.read()
            
            # 调用百度语音识别
            result = self.client.asr(audio_data, self.FORMAT, self.RATE, {
                'dev_pid': self.DEV_PID,
            })
            
            # 解析结果
            if result['err_no'] == 0:
                return True, result['result'][0]
            else:
                error_msg = self._get_error_message(result['err_no'])
                return False, f"识别失败: {error_msg}"
                
        except Exception as e:
            return False, f"识别异常: {str(e)}"
    
    def recognize_from_bytes(self, audio_bytes):
        """从字节数据识别语音"""
        try:
            # 保存到临时文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name
            
            # 识别
            success, result = self.recognize_from_file(tmp_path)
            
            # 删除临时文件
            os.unlink(tmp_path)
            
            return success, result
            
        except Exception as e:
            return False, f"识别失败: {str(e)}"
    
    def _get_error_message(self, err_no):
        """获取错误信息"""
        error_messages = {
            3300: '输入参数不正确',
            3301: '音频质量过差',
            3302: '鉴权失败',
            3303: '语音服务器后端问题',
            3304: '请求GPS过大，超过限额',
            3305: '产品线当前日请求数超过限额',
            3307: '识别无结果',
            3308: '音频过长',
            3309: '音频数据问题',
            3310: '输入的音频文件过大',
            3311: '采样率rate参数不在选项里',
            3312: '音频格式format参数不在选项里'
        }
        return error_messages.get(err_no, f"未知错误: {err_no}")
    
    def parse_travel_demand(self, text):
        """解析旅行需求（与原有逻辑保持一致）"""
        demand = {
            'destination': None,
            'days': 3,
            'people': 2,
            'budget': '舒适型(人均300-600元/天)',
            'styles': []
        }
        
        # ... 使用与原有相同的解析逻辑 ...
        # （这里复制原有parse_voice_demand函数的逻辑）
        
        return demand

# 测试函数
def test_baidu_recognition():
    """测试百度语音识别"""
    print("测试百度语音识别...")
    
    recognizer = BaiduVoiceRecognizer()
    
    # 测试用录音文件（需要先有一个wav文件）
    test_file = "test_recording.wav"
    if os.path.exists(test_file):
        success, result = recognizer.recognize_from_file(test_file)
        if success:
            print(f"✅ 识别成功: {result}")
        else:
            print(f"❌ 识别失败: {result}")
    else:
        print(f"⚠️ 测试文件不存在: {test_file}")