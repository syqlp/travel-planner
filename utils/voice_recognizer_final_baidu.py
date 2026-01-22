# utils/voice_recognizer_final_baidu.py主语音识别器
import streamlit as st
import os
import time
from datetime import datetime

# 导入百度语音
try:
    try:
        from utils.baidu_voice_full import BaiduVoiceFull  # 绝对导入
    except ImportError:
        from baidu_voice_full import BaiduVoiceFull  # 同级目录导入
    BAIDU_AVAILABLE = True
except ImportError:
    BAIDU_AVAILABLE = False

# 导入本地录音
try:
    import speech_recognition as sr
    import pyaudio
    LOCAL_AVAILABLE = True
except ImportError:
    LOCAL_AVAILABLE = False

class VoiceRecognizer:
    """最终版语音识别器 - 使用百度云"""
    
    def __init__(self):
        print("=" * 60)
        print("🎤 语音识别器初始化")
        
        # 初始化百度语音 - 强制创建
        self.baidu = None
        try:
            from utils.baidu_voice_full import BaiduVoiceFull
            self.baidu = BaiduVoiceFull()
            
            print(f"📊 百度语音状态:")
            print(f"  available: {getattr(self.baidu, 'available', False)}")
            print(f"  APP_ID: {getattr(self.baidu, 'APP_ID', '未设置')}")
            
            if hasattr(self.baidu, 'available') and self.baidu.available:
                print("✅ 百度云语音识别器就绪")
            else:
                print("❌ 百度语音识别器配置失败")
                # 尝试手动创建
                try:
                    from aip import AipSpeech
                    print("⚠️ 尝试手动创建AipSpeech客户端...")
                    # 这里可以手动创建
                except:
                    pass
        except ImportError as e:
            print(f"❌ 无法导入百度语音模块: {e}")
        # 初始化本地录音
        self.recognizer = None
        self.microphone = None
        if LOCAL_AVAILABLE:
            try:
                self.recognizer = sr.Recognizer()
                # 尝试多个麦克风设备
                mic_indices = [1, 10, 5, 0]  # 你的设备索引
                for idx in mic_indices:
                    try:
                        self.microphone = sr.Microphone(device_index=idx)
                        print(f"✅ 使用麦克风设备 {idx}")
                        break
                    except:
                        continue
                        
                if self.microphone:
                    print("✅ 本地录音功能就绪")
                else:
                    print("⚠️ 无法找到可用的麦克风")
                    
            except Exception as e:
                print(f"⚠️ 本地录音初始化失败: {e}")
        
        print("=" * 60)
        
        # 使用统计
        self.usage_count = 0
        self.last_used = None
    
    def check_dependencies(self):
        """检查依赖"""
        if self.baidu and hasattr(self.baidu, 'available') and self.baidu.available:
            return True, "✅ 百度云语音识别就绪（5万次免费额度）"
        elif self.recognizer and self.microphone:
            return True, "✅ 本地录音就绪（需要配置百度API）"
        else:
            return False, "❌ 语音功能需要安装依赖"
    
    def record_audio(self, duration=8):
        """录制音频"""
        if not self.recognizer or not self.microphone:
            return False, "录音功能不可用"
        
        try:
            with self.microphone as source:
                print(f"🎤 开始录音: {duration}秒")
                
                # 调整环境噪音
                self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
                
                print("🔊 请开始说话...")
                
                # 开始录音
                audio = self.recognizer.listen(
                    source,
                    timeout=duration + 5,
                    phrase_time_limit=duration
                )
                
                # ⚠️ 关键修复：保存录音数据到实例变量
                self.recording_data = audio
                print(f"✅ 录音完成，数据已保存到 self.recording_data")
                
                # 返回成功和录音对象
                return True, audio  # 返回 audio 对象给调用者
                
        except Exception as e:
            print(f"❌ 录音失败: {str(e)}")
            return False, f"录音失败: {str(e)}"
    
    def recognize(self, audio_data):
        """识别语音 - 使用百度云"""
        if not self.baidu or not self.baidu.available:
            return False, "百度语音识别未配置"
        
        try:
            # 记录使用
            self.usage_count += 1
            self.last_used = datetime.now()
            print(f"📊 第 {self.usage_count} 次识别调用")
            
            # 调用百度识别
            success, result = self.baidu.save_and_recognize(audio_data)
            
            return success, result
            
        except Exception as e:
            return False, f"识别失败: {str(e)}"
    
    def record_and_recognize(self, duration=8):
        """录音并识别"""
        print(f"\n{'='*60}")
        print(f"开始语音识别流程 (时长: {duration}秒)")
        
        # 1. 录音
        success, audio = self.record_audio(duration)
        if not success:
            return False, audio
        
        # 2. 识别
        return self.recognize(audio)
    
    def get_usage_info(self):
        """获取使用信息"""
        return {
            'total_calls': self.usage_count,
            'last_used': self.last_used.strftime('%Y-%m-%d %H:%M:%S') if self.last_used else '从未使用',
            'baidu_available': self.baidu and self.baidu.available,
            'microphone_available': self.microphone is not None
        }
    def transcribe_audio(self):
        """转录音频 - 适配app.py的调用"""
        try:
            # 如果有录音数据，就调用百度识别
            if hasattr(self, 'recording_data') and self.recording_data:
                print("🔍 开始转录音频...")
                success, result = self.recognize(self.recording_data)
                return success, result
            else:
                return False, "没有录音数据"
                
        except Exception as e:
            return False, f"转录失败: {str(e)}"
    
    def save_audio_to_file(self, audio_data, filename=None):
        """保存音频到文件"""
        import wave
        from datetime import datetime
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.wav"
        
        try:
            # 确保目录存在
            os.makedirs("data/recordings", exist_ok=True)
            
            # 保存文件
            if hasattr(audio_data, 'get_wav_data'):
                wav_data = audio_data.get_wav_data()
            else:
                wav_data = audio_data
                
            with open(f"data/recordings/{filename}", "wb") as f:
                f.write(wav_data)
            
            return f"data/recordings/{filename}"
        except Exception as e:
            print(f"保存音频失败: {e}")
            return None
    
    def get_audio_duration(self, audio_data):
        """获取音频时长"""
        try:
            import wave
            import tempfile
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                if hasattr(audio_data, 'get_wav_data'):
                    tmp.write(audio_data.get_wav_data())
                else:
                    tmp.write(audio_data)
                tmp_path = tmp.name
            
            # 读取时长
            with wave.open(tmp_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration = frames / float(rate)
            
            os.unlink(tmp_path)
            return duration
            
        except Exception as e:
            print(f"获取音频时长失败: {e}")
            return 0
    def transcribe_audio(self):
        """转录音频 - 优化识别版"""
        if self.recording_data is None:
            return False, "没有录音数据"
        
        print("🔍 开始转录音频...")
        
        try:
            from aip import AipSpeech
            
            # 你的API密钥
            APP_ID = '121914868'
            API_KEY = 'Sy4b9H4mVyl5LtYEXTsZQNqG'
            SECRET_KEY = '2l1JhXNKVnjJ1Ui3HcntaVvVrcYME9PI'
            
            client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)
            
            # 获取录音数据
            wav_data = self.recording_data.get_wav_data()
            print(f"📊 音频数据: {len(wav_data)} 字节")
            
            # 保存录音用于分析
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_file = f"debug_{timestamp}.wav"
            with open(debug_file, 'wb') as f:
                f.write(wav_data)
            print(f"💾 录音已保存: {debug_file}")
            
            # ⚠️ 关键优化：尝试不同的识别参数
            recognition_results = []
            
            # 参数组合
            param_sets = [
                {'dev_pid': 1537, 'desc': '普通话搜索模型'},  # 默认
                {'dev_pid': 1536, 'desc': '普通话输入法模型'},
                {'dev_pid': 1737, 'desc': '英语'},  # 可能更适合数字
                {'dev_pid': 1637, 'desc': '粤语'},
            ]
            
            for params in param_sets:
                try:
                    print(f"尝试 {params['desc']}...")
                    result = client.asr(wav_data, 'wav', 16000, {
                        'dev_pid': params['dev_pid'],
                        'cuid': f'travel_planner_{timestamp}',
                    })
                    
                    if result.get('err_no') == 0:
                        if result.get('result') and result['result'][0]:
                            text = result['result'][0].strip()
                            if text:
                                recognition_results.append({
                                    'text': text,
                                    'model': params['desc'],
                                    'confidence': self._estimate_confidence(text)
                                })
                                print(f"  ✅ {params['desc']}: {text}")
                except Exception as e:
                    print(f"  ⚠️ {params['desc']}失败: {e}")
            
            # 选择最佳结果
            if recognition_results:
                # 按置信度排序
                recognition_results.sort(key=lambda x: x['confidence'], reverse=True)
                best_result = recognition_results[0]
                
                print(f"🎯 最佳识别结果:")
                print(f"  文本: {best_result['text']}")
                print(f"  模型: {best_result['model']}")
                print(f"  置信度: {best_result['confidence']:.1%}")
                
                return True, best_result['text']
            else:
                print("⚠️ 所有模型都返回空结果")
                # 使用默认模型再试一次
                result = client.asr(wav_data, 'wav', 16000, {'dev_pid': 1537})
                if result.get('err_no') == 0 and result.get('result'):
                    text = result['result'][0]
                    if text:
                        return True, text
                
                return False, "识别失败"
                
        except Exception as e:
            print(f"❌ 转录异常: {e}")
            import traceback
            traceback.print_exc()
            return False, f"转录失败: {str(e)}"

    def _estimate_confidence(self, text):
        """估计识别置信度（简单版）"""
        # 简单的置信度估计
        confidence = 0.5  # 基础置信度
        
        # 旅行相关关键词加分
        travel_keywords = ['北京', '上海', '旅游', '旅行', '天', '人', '预算', '经济', '舒适', '豪华']
        for keyword in travel_keywords:
            if keyword in text:
                confidence += 0.1
        
        # 数字加分（如果是数字的话）
        if any(char.isdigit() for char in text):
            confidence += 0.2
        
        # 确保在0-1范围内
        return min(1.0, max(0.0, confidence))