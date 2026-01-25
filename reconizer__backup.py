# utils/voice_recognizer_final_baidu.py

import os
import time
import wave
import pyaudio
from datetime import datetime
import streamlit as st

class VoiceRecognizer:
    """修复版语音识别器 - 使用直接录音"""
    
    def __init__(self):
        print("🎤 初始化直接录音识别器")
        
        # 百度API客户端
        try:
            from aip import AipSpeech
            self.client = AipSpeech(
                '121914868',
                'Sy4b9H4mVyl5LtYEXTsZQNqG',
                '2l1JhXNKVnjJ1Ui3HcntaVvVrcYME9PI'
            )
            self.api_available = True
        except Exception as e:
            print(f"❌ 百度API初始化失败: {e}")
            self.api_available = False
            self.client = None
        
        # PyAudio
        try:
            self.p = pyaudio.PyAudio()
            self.pyaudio_available = True
            
            # 选择麦克风设备（使用你的设备索引1）
            self.device_index = 1  # 你的麦克风阵列设备
            
        except Exception as e:
            print(f"❌ PyAudio初始化失败: {e}")
            self.p = None
            self.pyaudio_available = False
        
        # 保留speech_recognition作为备选
        try:
            import speech_recognition as sr
            self.sr = sr
            self.sr_available = True
        except:
            self.sr_available = False
        
        # 录音数据
        self.audio_bytes = None
    
    def check_dependencies(self):
        """检查依赖"""
        if self.api_available and self.pyaudio_available:
            return True, "✅ 直接录音功能就绪"
        elif self.api_available and self.sr_available:
            return True, "✅ 备用录音功能就绪"
        else:
            return False, "❌ 语音功能需要安装依赖"
    
    def record_audio(self, duration=8):
        """录制音频 - 使用直接录音"""
        if not self.pyaudio_available:
            return False, "直接录音功能不可用"
        
        try:
            # 录音参数（严格按照百度要求）
            CHUNK = 1024
            FORMAT = pyaudio.paInt16      # 16位
            CHANNELS = 1                  # 单声道
            RATE = 16000                  # 16kHz
            RECORD_SECONDS = duration
            
            print(f"🎤 开始直接录音: {duration}秒")
            print(f"📊 参数: {RATE}Hz, {CHANNELS}声道, {FORMAT}格式")
            
            # 打开音频流
            stream = self.p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=CHUNK
            )
            
            # 录音
            frames = []
            for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                data = stream.read(CHUNK)
                frames.append(data)
            
            # 停止流
            stream.stop_stream()
            stream.close()
            
            # 合并数据
            self.audio_bytes = b''.join(frames)
            print(f"✅ 录音完成: {len(self.audio_bytes)} 字节")
            
            # 保存录音文件（用于调试）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/recordings/app_{timestamp}.wav"
            os.makedirs("data/recordings", exist_ok=True)
            
            wf = wave.open(filename, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(self.audio_bytes)
            wf.close()
            
            print(f"💾 已保存: {filename}")
            
            return True, "录音成功"
            
        except Exception as e:
            print(f"❌ 直接录音失败: {e}")
            # 尝试备用方法
            return self._record_audio_fallback(duration)
    
    def _record_audio_fallback(self, duration):
        """备用录音方法（使用speech_recognition）"""
        if not self.sr_available:
            return False, "没有可用的录音方法"
        
        try:
            r = self.sr.Recognizer()
            
            with self.sr.Microphone(device_index=self.device_index) as source:
                print("🔄 使用备用录音方法...")
                r.adjust_for_ambient_noise(source, duration=1.0)
                
                audio = r.listen(
                    source,
                    timeout=duration + 5,
                    phrase_time_limit=duration
                )
                
                # 转换为bytes
                self.audio_bytes = audio.get_wav_data()
                print(f"✅ 备用录音完成: {len(self.audio_bytes)} 字节")
                
                return True, "录音成功"
                
        except Exception as e:
            print(f"❌ 备用录音失败: {e}")
            return False, f"录音失败: {str(e)}"
    
    def transcribe_audio(self):
        """转录音频"""
        if not self.audio_bytes:
            return False, "没有录音数据"
        
        if not self.client:
            return False, "百度API不可用"
        
        print("🔍 开始转录音频...")
        
        try:
            # 直接调用百度API
            result = self.client.asr(
                self.audio_bytes,
                'wav',
                16000,
                {
                    'dev_pid': 1537,  # 普通话
                    'cuid': f'travel_planner_{int(time.time())}',
                }
            )
            
            print(f"📋 API返回: {result}")
            
            if result.get('err_no') == 0:
                text = result.get('result', [''])[0]
                if text and text.strip():
                    print(f"✅ 识别成功: '{text}'")
                    return True, text.strip()
                else:
                    print("⚠️ 识别结果为空")
                    return False, "识别结果为空"
            else:
                error_msg = result.get('err_msg', '未知错误')
                print(f"❌ API错误: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            print(f"❌ 转录失败: {e}")
            return False, f"转录失败: {str(e)}"
    
    def parse_travel_demand(self, text):
        """解析旅行需求"""
        import re
        
        demand = {
            'destination': None,
            'days': 3,
            'people': 2,
            'budget': '舒适型(人均300-600元/天)',
            'styles': []
        }
        
        # 目的地
        destinations = ['北京', '上海', '广州', '深圳', '杭州', '成都', '西安', '南京']
        for dest in destinations:
            if dest in text:
                demand['destination'] = dest
                break
        
        # 天数
        day_match = re.search(r'(\d+)\s*天', text)
        if day_match:
            try:
                days = int(day_match.group(1))
                if 1 <= days <= 30:
                    demand['days'] = days
            except:
                pass
        
        # 人数
        people_match = re.search(r'(\d+)\s*人', text)
        if people_match:
            try:
                people = int(people_match.group(1))
                if 1 <= people <= 20:
                    demand['people'] = people
            except:
                pass
        
        # 预算
        if '经济' in text or '便宜' in text:
            demand['budget'] = '经济型(人均300元/天以下)'
        elif '豪华' in text or '奢侈' in text:
            demand['budget'] = '豪华型(人均600元/天以上)'
        
        # 风格
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
        
        if not demand['styles']:
            demand['styles'] = ['🏖️ 休闲放松', '🏞️ 自然风光']
        
        return demand
    
    def cleanup(self):
        """清理资源"""
        if hasattr(self, 'p') and self.p:
            self.p.terminate()
            print("✅ 已清理PyAudio资源")

# 简单测试
def test():
    vr = VoiceRecognizer()
    
    success, msg = vr.check_dependencies()
    print(f"依赖检查: {msg}")
    
    if "就绪" in msg:
        print("\n🎤 测试录音（3秒）...")
        success, msg = vr.record_audio(3)
        
        if success:
            print("\n🔍 测试识别...")
            success, text = vr.transcribe_audio()
            
            if success:
                print(f"\n✅ 识别结果: '{text}'")
                
                parsed = vr.parse_travel_demand(text)
                print(f"\n🎯 解析结果:")
                print(f"  目的地: {parsed['destination']}")
                print(f"  天数: {parsed['days']}")
                print(f"  人数: {parsed['people']}")
                print(f"  预算: {parsed['budget']}")
                print(f"  风格: {parsed['styles']}")
        
        vr.cleanup()

if __name__ == "__main__":
    test()