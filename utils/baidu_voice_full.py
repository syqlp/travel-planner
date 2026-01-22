# utils/baidu_voice_full.py
import os
import json
import base64
import time
from datetime import datetime
from aip import AipSpeech
import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()  # 这会加载项目根目录的 .env 文件
    print("✅ .env 文件已加载")
except ImportError:
    print("⚠️ 未安装 python-dotenv，将使用系统环境变量")
    
class BaiduVoiceFull:
    """百度云语音识别完整版"""
    
    def __init__(self):
        # 从环境变量获取配置
        self.APP_ID = '121914868'  
        self.API_KEY = 'Sy4b9H4mVyl5LtYEXTsZQNqG'  
        self.SECRET_KEY = '2l1JhXNKVnjJ1Ui3HcntaVvVrcYME9PI'  
        
        # 检查配置
        if not all([self.APP_ID, self.API_KEY, self.SECRET_KEY]):
            st.warning("⚠️ 百度语音API配置不完整")
            self.available = False
            return
        
        try:
            # 初始化百度语音客户端
            self.client = AipSpeech(self.APP_ID, self.API_KEY, self.SECRET_KEY)
            self.available = True
            
            # 测试连接
            success, message = self.test_connection()
            if success:
                print(f"✅ 连接测试成功: {message}")
            else:
                print(f"⚠️ 连接测试警告: {message}")
                
        except Exception as e:
            st.error(f"❌ 百度语音初始化失败: {e}")
            self.available = False
    
    def test_connection(self):
        """测试连接"""
        try:
            # 创建极短的测试音频
            import wave
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp_path = tmp.name
            
            # 创建0.2秒静音
            with wave.open(tmp_path, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                wav_file.writeframes(b'\x00' * 6400)  # 0.2秒
            
            with open(tmp_path, 'rb') as f:
                audio_data = f.read()
            
            os.unlink(tmp_path)
            
            # 测试调用短语音识别
            result = self.client.asr(audio_data, 'wav', 16000, {
                'dev_pid': 1537,  # 1537: 普通话
            })
            
            if 'err_no' in result:
                if result['err_no'] == 0:
                    return True, "API正常"
                elif result['err_no'] == 3301:  # 音频质量差（正常）
                    return True, "连接正常（测试音频质量差）"
                else:
                    error_msg = self._get_error_message(result['err_no'])
                    return False, f"API错误: {error_msg}"
            return True, "连接测试通过"
            
        except Exception as e:
            return False, f"连接测试失败: {str(e)}"
    
    def recognize_short_speech(self, audio_data, sample_rate=16000):
        """
        短语音识别 - 修复版
        """
        if not self.available:
            return False, "百度语音API未配置"
        
        try:
            print(f"🔍 调用短语音识别...")
            print(f"📊 音频参数:")
            print(f"  • 数据大小: {len(audio_data)} 字节")
            print(f"  • 采样率: {sample_rate} Hz")
            
            # ⚠️ 关键修复：检查音频数据是否有效
            if len(audio_data) < 1000:
                return False, "音频数据过少"
            
            # 记录开始时间
            start_time = time.time()
            
            # 调用百度短语音识别API
            result = self.client.asr(audio_data, 'wav', sample_rate, {
                'dev_pid': 1537,  # 1537: 普通话
                # 添加更多参数
                'cuid': 'travel_planner_app',
                'token': None,
            })
            
            elapsed_time = time.time() - start_time
            print(f"⏱️ 识别耗时: {elapsed_time:.2f}秒")
            print(f"📋 API返回: {result}")
            
            # 解析结果
            if result.get('err_no') == 0:
                if result.get('result') and len(result['result']) > 0:
                    text = result['result'][0]
                    if text and text.strip():
                        print(f"✅ 识别成功: {text}")
                        return True, text
                    else:
                        print("⚠️ 识别结果为空字符串")
                        # 尝试其他语言模型
                        return self._try_alternative_recognition(audio_data, sample_rate)
                else:
                    return False, "API返回结果格式错误"
            else:
                error_msg = self._get_error_message(result.get('err_no', 0))
                print(f"❌ 识别失败: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            print(f"❌ 识别异常: {e}")
            return False, f"识别异常: {str(e)}"

    def _try_alternative_recognition(self, audio_data, sample_rate):
        """尝试其他识别方式"""
        print("🔄 尝试其他识别参数...")
        
        # 尝试不同的语言模型
        language_models = [
            {'dev_pid': 1537, 'desc': '普通话'},  # 标准普通话
            {'dev_pid': 1737, 'desc': '英语'},    # 英语
            {'dev_pid': 1637, 'desc': '粤语'},    # 粤语
            {'dev_pid': 1837, 'desc': '四川话'},  # 四川话
        ]
        
        for model in language_models:
            try:
                print(f"尝试 {model['desc']} 模型...")
                result = self.client.asr(audio_data, 'wav', sample_rate, {
                    'dev_pid': model['dev_pid'],
                    'cuid': 'travel_planner_app',
                })
                
                if result.get('err_no') == 0 and result.get('result') and result['result'][0]:
                    text = result['result'][0]
                    print(f"✅ 使用{model['desc']}模型识别成功: {text}")
                    return True, text
            except Exception as e:
                print(f"⚠️ {model['desc']}模型尝试失败: {e}")
        
        return False, "所有识别尝试都失败"
    
    def recognize_realtime_stream(self, audio_data, sample_rate=16000):
        """
        实时语音识别（你的10小时免费额度）
        适合：持续语音流识别
        """
        if not self.available:
            return False, "百度语音API未配置"
        
        # 注意：实时语音识别需要不同的调用方式
        # 这里简化处理，使用短语音识别API
        # 实际项目中可能需要使用websocket
        return self.recognize_short_speech(audio_data, sample_rate)
    
    def recognize_audio_file(self, file_path):
        """
        音频文件转写（你的10小时免费额度）
        适合：上传完整音频文件
        """
        if not self.available:
            return False, "百度语音API未配置"
        
        try:
            print(f"🔍 调用音频文件转写（免费额度10小时）...")
            
            # 读取音频文件
            with open(file_path, 'rb') as f:
                audio_data = f.read()
            
            # 文件大小检查（百度API限制）
            if len(audio_data) > 10 * 1024 * 1024:  # 10MB限制
                return False, "音频文件过大（需小于10MB）"
            
            # 使用短语音识别API（对于文件）
            return self.recognize_short_speech(audio_data)
            
        except Exception as e:
            print(f"❌ 文件转写异常: {e}")
            return False, f"文件转写失败: {str(e)}"
    
    def save_and_recognize(self, audio_data, save_file=True):
        """
        保存录音并识别（推荐方法）
        """
        try:
            # 保存录音文件
            if save_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"data/recordings/recording_{timestamp}.wav"
                os.makedirs("data/recordings", exist_ok=True)
                
                # 如果是speech_recognition的AudioData对象
                if hasattr(audio_data, 'get_wav_data'):
                    wav_data = audio_data.get_wav_data()
                    with open(filename, 'wb') as f:
                        f.write(wav_data)
                    data_for_recognition = wav_data
                else:
                    with open(filename, 'wb') as f:
                        f.write(audio_data)
                    data_for_recognition = audio_data
                
                print(f"💾 录音文件已保存: {filename}")
            else:
                # 不保存文件，直接使用数据
                if hasattr(audio_data, 'get_wav_data'):
                    data_for_recognition = audio_data.get_wav_data()
                else:
                    data_for_recognition = audio_data
            
            # 调用短语音识别
            success, result = self.recognize_short_speech(data_for_recognition)
            
            return success, result
            
        except Exception as e:
            print(f"❌ 保存识别异常: {e}")
            return False, f"保存识别失败: {str(e)}"
    
    def get_quota_info(self):
        """获取额度信息"""
        return {
            'short_speech': {
                'name': '短语音识别-中文普通话',
                'quota': '50,000次',
                'expire': '2026-01-22',
                'usage': '适合一句话识别'
            },
            'realtime': {
                'name': '实时语音识别-中文普通话',
                'quota': '10小时',
                'expire': '2026-01-22',
                'usage': '适合持续语音流'
            },
            'file_transcribe': {
                'name': '音频文件转写-中文普通话',
                'quota': '10小时',
                'expire': '2026-01-22',
                'usage': '适合上传音频文件'
            }
        }
    
    def _get_error_message(self, err_no):
        """获取错误信息"""
        errors = {
            3300: '输入参数不正确',
            3301: '音频质量过差',
            3302: '鉴权失败',
            3303: '语音服务器后端问题',
            3304: '请求GPS过大，超过限额',
            3305: '产品线当前日请求数超过限额',
            3307: '识别无结果',
            3308: '音频过长（超过60秒）',
            3309: '音频数据问题',
            3310: '输入的音频文件过大（超过10MB）',
            3311: '采样率参数不在选项里',
            3312: '音频格式参数不在选项里'
        }
        return errors.get(err_no, f"未知错误代码: {err_no}")