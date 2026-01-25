# utils/voice_recognizer_bypass.py
import os
import time
import wave
import pyaudio
from datetime import datetime

class VoiceRecognizerBypass:
    """绕过speech_recognition，直接录音"""
    
    def __init__(self):
        print("🎤 初始化直接录音识别器")
        
        # 百度API
        try:
            from aip import AipSpeech
            self.client = AipSpeech(
                '121914868',
                'Sy4b9H4mVyl5LtYEXTsZQNqG',
                '2l1JhXNKVnjJ1Ui3HcntaVvVrcYME9PI'
            )
            print("✅ 百度API客户端就绪")
        except Exception as e:
            print(f"❌ 百度API初始化失败: {e}")
            self.client = None
        
        # PyAudio
        try:
            self.p = pyaudio.PyAudio()
            print(f"✅ PyAudio就绪，版本: {pyaudio.__version__}")
            
            # 显示可用设备
            self._list_input_devices()
            
        except Exception as e:
            print(f"❌ PyAudio初始化失败: {e}")
            self.p = None
    
    def _list_input_devices(self):
        """列出输入设备"""
        print("\n📊 可用录音设备:")
        for i in range(self.p.get_device_count()):
            info = self.p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"  [{i}] {info['name']} (输入通道: {info['maxInputChannels']})")
        
        # 默认设备
        try:
            default = self.p.get_default_input_device_info()
            print(f"\n🎤 默认输入设备: [{default['index']}] {default['name']}")
            self.default_device = default['index']
        except:
            self.default_device = 1  # 你的设备索引
    
    def record_direct(self, duration=5, device_index=None):
        """直接录音，确保格式正确"""
        if not self.p:
            return False, "PyAudio不可用"
        
        # 录音参数（严格按照百度API要求）
        CHUNK = 1024
        FORMAT = pyaudio.paInt16      # 16位
        CHANNELS = 1                  # 单声道
        RATE = 16000                  # 16kHz
        RECORD_SECONDS = duration
        
        if device_index is None:
            device_index = self.default_device
        
        print(f"\n🎤 开始直接录音")
        print(f"📊 参数: {RATE}Hz, {CHANNELS}声道, {FORMAT}格式")
        print(f"📱 设备: {device_index}")
        print(f"⏱️ 时长: {duration}秒")
        
        try:
            # 打开音频流
            stream = self.p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=CHUNK
            )
            
            print("🔴 正在录音...")
            
            frames = []
            for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                data = stream.read(CHUNK)
                frames.append(data)
            
            print("✅ 录音完成")
            
            # 停止流
            stream.stop_stream()
            stream.close()
            
            # 合并数据
            audio_bytes = b''.join(frames)
            print(f"📊 录音数据: {len(audio_bytes)} 字节")
            
            # 保存为WAV文件（验证格式）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/recordings/direct_{timestamp}.wav"
            os.makedirs("data/recordings", exist_ok=True)
            
            wf = wave.open(filename, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(audio_bytes)
            wf.close()
            
            print(f"💾 已保存: {filename}")
            
            # 验证文件格式
            self._verify_wav_format(filename)
            
            return True, audio_bytes
            
        except Exception as e:
            print(f"❌ 录音失败: {e}")
            return False, str(e)
    
    def _verify_wav_format(self, filename):
        """验证WAV文件格式"""
        try:
            with wave.open(filename, 'rb') as wf:
                params = wf.getparams()
                print(f"🔍 格式验证:")
                print(f"  声道数: {params.nchannels} {'✅' if params.nchannels == 1 else '❌'}")
                print(f"  采样宽度: {params.sampwidth} {'✅' if params.sampwidth == 2 else '❌'}")
                print(f"  采样率: {params.framerate} {'✅' if params.framerate == 16000 else '❌'}")
                print(f"  帧数: {params.nframes}")
                
                # 读取一点数据验证
                wf.rewind()
                sample = wf.readframes(10)
                print(f"  数据示例: {sample[:20]}...")
        except Exception as e:
            print(f"⚠️ 格式验证失败: {e}")
    
    def recognize_direct(self, audio_bytes):
        """直接识别音频"""
        if not self.client:
            return False, "百度API不可用"
        
        print("\n🔍 调用百度语音识别...")
        
        try:
            # 直接调用API
            result = self.client.asr(
                audio_bytes,
                'wav',
                16000,  # 必须与录音采样率一致
                {
                    'dev_pid': 1537,  # 普通话
                    'cuid': 'direct_recorder_v1'
                }
            )
            
            print(f"📋 API返回: {result}")
            
            if result.get('err_no') == 0:
                text = result.get('result', [''])[0]
                if text:
                    print(f"✅ 识别成功: '{text}'")
                    return True, text
                else:
                    print("⚠️ 识别结果为空")
                    return False, "识别结果为空"
            else:
                error_msg = result.get('err_msg', '未知错误')
                print(f"❌ API错误: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            print(f"❌ 识别失败: {e}")
            return False, str(e)
    
    def record_and_recognize(self, duration=5):
        """录音并识别"""
        print("\n" + "="*60)
        print("🎯 直接录音识别测试")
        print("="*60)
        
        print("💡 请清晰说: '我要去北京旅游三天'")
        print("📢 每个字清晰发音，适当停顿")
        
        input("\n按回车开始录音...")
        
        # 录音
        success, audio_bytes = self.record_direct(duration)
        if not success:
            return False, audio_bytes
        
        # 识别
        return self.recognize_direct(audio_bytes)
    
    def cleanup(self):
        """清理资源"""
        if self.p:
            self.p.terminate()
            print("✅ 已清理PyAudio资源")

# 测试函数
def test_bypass_recognition():
    """测试直接录音识别"""
    print("🧪 测试直接录音识别")
    
    vr = VoiceRecognizerBypass()
    
    try:
        # 测试录音和识别
        success, result = vr.record_and_recognize(duration=3)
        
        if success:
            print(f"\n🎉 最终识别结果: '{result}'")
            
            # 简单的解析测试
            if '北京' in result:
                print("✅ 成功识别到'北京'")
            if '三' in result or '3' in result:
                print("✅ 成功识别到天数信息")
        else:
            print(f"\n❌ 识别失败: {result}")
            
    finally:
        vr.cleanup()

if __name__ == "__main__":
    test_bypass_recognition()