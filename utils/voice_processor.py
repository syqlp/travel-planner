# utils/voice_processor.py
import streamlit as st
import speech_recognition as sr
import tempfile
import os
from datetime import datetime

class VoiceProcessor:
    """语音处理核心类"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.is_recording = False
        
    def record_and_transcribe(self, duration=5):
        """
        录音并转文字（浏览器端录音）
        返回: (success, text_or_error_message)
        """
        try:
            # 创建临时文件保存录音
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                audio_path = tmp_file.name
            
            # 使用麦克风录音
            with sr.Microphone() as source:
                st.info("🎤 正在录音... 请说话（5秒）")
                
                # 调整环境噪音
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # 录音
                audio = self.recognizer.listen(source, timeout=duration, phrase_time_limit=duration)
                
                # 保存音频文件
                with open(audio_path, "wb") as f:
                    f.write(audio.get_wav_data())
                
                st.success("✅ 录音完成，识别中...")
                
                # 语音识别
                text = self.recognizer.recognize_google(audio, language='zh-CN')
                
                # 清理临时文件
                os.unlink(audio_path)
                
                return True, text
                
        except sr.WaitTimeoutError:
            return False, "录音超时，请重试"
        except sr.UnknownValueError:
            return False, "无法识别语音内容"
        except sr.RequestError as e:
            return False, f"语音服务错误: {str(e)}"
        except Exception as e:
            return False, f"录音失败: {str(e)}"
    
    def parse_travel_demand(self, text):
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
        
        # 简单关键词匹配（可扩展为NLP）
        destinations = ['北京', '上海', '广州', '深圳', '杭州', '成都', 
                       '西安', '南京', '武汉', '长沙', '青岛', '大理', 
                       '丽江', '三亚', '厦门', '重庆', '苏州']
        
        # 提取目的地
        for dest in destinations:
            if dest in text:
                demand['destination'] = dest
                break
        
        # 提取天数
        import re
        day_patterns = [r'(\d+)\s*天', r'玩\s*(\d+)\s*天', r'旅行\s*(\d+)\s*天']
        for pattern in day_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    days = int(match.group(1))
                    if 1 <= days <= 30:
                        demand['days'] = days
                except:
                    pass
        
        # 提取人数
        people_patterns = [r'(\d+)\s*个人', r'(\d+)\s*人', r'(\d+)\s*位']
        for pattern in people_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    people = int(match.group(1))
                    if 1 <= people <= 20:
                        demand['people'] = people
                except:
                    pass
        
        # 提取预算
        if '经济' in text or '便宜' in text or '省钱' in text:
            demand['budget'] = '经济型(人均300元/天以下)'
        elif '豪华' in text or '奢侈' in text or '高端' in text:
            demand['budget'] = '豪华型(人均600元/天以上)'
        
        # 提取风格
        style_keywords = {
            '休闲': '🏖️ 休闲放松',
            '文化': '🎨 文化探索', 
            '美食': '🍜 美食之旅',
            '自然': '🏞️ 自然风光',
            '冒险': '🎢 冒险刺激',
            '亲子': '👨‍👩‍👧‍👦 家庭亲子',
            '浪漫': '💖 情侣浪漫',
            '摄影': '📸 摄影打卡'
        }
        
        for keyword, style in style_keywords.items():
            if keyword in text:
                demand['styles'].append(style)
        
        # 如果没有检测到风格，使用默认
        if not demand['styles']:
            demand['styles'] = ['🏖️ 休闲放松', '🏞️ 自然风光']
        
        return demand