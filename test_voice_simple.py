# test_voice_simple.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 测试语音识别器
from utils.voice_recognizer_final_baidu import VoiceRecognizer

def test_voice_recognizer():
    print("🧪 测试语音识别器...")
    
    vr = VoiceRecognizer()
    
    # 测试依赖检查
    success, msg = vr.check_dependencies()
    print(f"依赖检查: {success} - {msg}")
    
    if success:
        # 测试录音
        print("🎤 测试录音（2秒）...")
        success, msg = vr.record_audio(duration=2)
        print(f"录音结果: {success} - {msg}")
        
        # 检查录音数据
        print(f"是否有录音数据: {hasattr(vr, 'recording_data')}")
        if hasattr(vr, 'recording_data') and vr.recording_data:
            print(f"录音数据类型: {type(vr.recording_data)}")
            
            # 测试转录
            print("🔍 测试转录...")
            transcribe_success, result = vr.transcribe_audio()
            print(f"转录结果: {transcribe_success} - {result}")
        else:
            print("❌ 没有录音数据")
    else:
        print("⚠️ 跳过录音测试，依赖不满足")

if __name__ == "__main__":
    test_voice_recognizer()