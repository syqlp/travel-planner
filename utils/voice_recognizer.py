# utils/voice_recognizer.py
import streamlit as st
import tempfile
import os
import time
from datetime import datetime
import wave
import numpy as np

# 尝试导入语音识别库
try:
    import speech_recognition as sr
    import pyaudio
    VOICE_LIB_AVAILABLE = True
except ImportError as e:
    VOICE_LIB_AVAILABLE = False
    st.error(f"❌ 语音库导入失败: {e}")
    st.info("请运行: pip install SpeechRecognition pyaudio")

class VoiceRecognizer:
    """真正的语音识别器"""
    
    def __init__(self):
        if VOICE_LIB_AVAILABLE:
            try:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
                self.mic_available = True
            except Exception as e:
                self.mic_available = False
                print(f"⚠️ 麦克风初始化失败: {e}")
        else:
            self.mic_available = False
        
        self.is_recording = False
        self.recording_data = None
    
    def check_dependencies(self):
        """检查依赖是否可用"""
        if not VOICE_LIB_AVAILABLE:
            return False, "请安装 SpeechRecognition 和 PyAudio\n运行: pip install SpeechRecognition pyaudio"
        if not self.mic_available:
            return False, "麦克风不可用或未连接"
        return True, "依赖检查通过"
    
    def record_audio(self, duration=10):
        """录制音频 - 详细调试版"""
        success, message = self.check_dependencies()
        if not success:
            print(f"❌ 依赖检查失败: {message}")
            return False, message
        
        try:
            print(f"🎤 正在初始化麦克风...")
            with self.microphone as source:
                print(f"✅ 麦克风初始化成功")
                print(f"⏱️ 设置录音时长: {duration}秒")
                
                # 调整环境噪音
                print("🔄 正在调整环境噪音（2秒）...")
                self.recognizer.adjust_for_ambient_noise(source, duration=2.0)
                print("✅ 环境噪音调整完成")
                
                print("🔊 请开始说话...")
                
                # 添加超时和重试机制
                try:
                    print(f"⏺️ 开始录音...")
                    audio = self.recognizer.listen(
                        source, 
                        timeout=duration + 5,  # 增加超时时间
                        phrase_time_limit=duration
                    )
                    
                    # 检查录音数据
                    if audio:
                        audio_data = audio.get_wav_data()
                        print(f"✅ 录音成功！获取到 {len(audio_data)} 字节数据")
                        
                        # 保存录音数据
                        self.recording_data = audio
                        
                        # 测试录音质量
                        if len(audio_data) < 1000:  # 数据太少
                            print(f"⚠️ 录音数据过少: {len(audio_data)} 字节")
                            return False, "录音数据过少，请重新尝试"
                        
                        return True, "录音成功"
                    else:
                        print(f"❌ 录音失败：未获取到音频数据")
                        return False, "未获取到音频数据"
                        
                except sr.WaitTimeoutError as e:
                    print(f"❌ 录音超时: {e}")
                    return False, "录音超时：请在提示后立即开始说话"
                except Exception as e:
                    print(f"❌ 录音异常: {type(e).__name__}: {e}")
                    return False, f"录音失败: {str(e)}"
                
        except Exception as e:
            print(f"❌ 麦克风访问失败: {type(e).__name__}: {e}")
            return False, f"麦克风访问失败: {str(e)}"
    
    def transcribe_audio(self, audio_data=None):
        """转录音频到文字 - 详细调试版"""
        if audio_data is None:
            audio_data = self.recording_data
            
        if audio_data is None:
            print("❌ 没有录音数据可供识别")
            return False, "没有录音数据"
        
        try:
            print("🔄 正在识别语音...")
            
            # 检查录音数据
            wav_data = audio_data.get_wav_data()
            print(f"📊 音频数据大小: {len(wav_data)} 字节")
            
            if len(wav_data) < 1000:
                print("⚠️ 音频数据过少，可能录音失败")
                return False, "音频数据过少"
            
            # 尝试识别
            print("🔍 调用Google语音识别API...")
            text = self.recognizer.recognize_google(audio_data, language='zh-CN')
            
            if text:
                print(f"✅ 识别成功: {text}")
                return True, text
            else:
                print("❌ 识别返回空结果")
                return False, "识别返回空结果"
                
        except sr.UnknownValueError:
            print("❌ Google语音识别无法理解音频")
            return False, "无法识别语音内容，请说得更清晰些"
        except sr.RequestError as e:
            print(f"❌ Google语音识别服务错误: {e}")
            return False, f"语音识别服务错误: 请检查网络连接"
        except Exception as e:
            print(f"❌ 转录异常: {type(e).__name__}: {e}")
            return False, f"转录失败: {str(e)}"
    
    def save_audio_to_file(self, audio_data, filename=None):
        """保存音频到文件"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.wav"
        
        with open(filename, "wb") as f:
            f.write(audio_data.get_wav_data())
        
        return filename
    
    def get_audio_duration(self, audio_data):
        """获取音频时长"""
        try:
            # 创建一个临时文件
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_data.get_wav_data())
                tmp_path = tmp.name
            
            # 读取音频文件信息
            with wave.open(tmp_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration = frames / float(rate)
            
            # 删除临时文件
            os.unlink(tmp_path)
            
            return duration
        except Exception as e:
            print(f"获取音频时长失败: {e}")
            return 0
    
    def parse_travel_demand(self, text):
        """解析旅行需求"""
        return self._parse_voice_demand(text)
    
    def _parse_voice_demand(self, text):
        """解析语音文本，提取旅行需求"""
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