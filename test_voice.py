# test_voice.py
import os
import sys
sys.path.append('.')

from utils.voice_recognizer_final_baidu import VoiceRecognizer

def test_voice_recognition():
    print("=== 语音识别测试 ===")
    
    # 1. 初始化
    print("1. 初始化语音识别器...")
    vr = VoiceRecognizer()
    
    # 2. 检查依赖
    print("2. 检查依赖...")
    success, msg = vr.check_dependencies()
    print(f"   结果: {msg}")
    
    if not success:
        print("❌ 依赖检查失败")
        return
    
    # 3. 录音测试
    print("\n3. 开始录音测试（3秒）...")
    print("   请说：'北京三天两个人'")
    success, filename = vr.record_audio_fixed(duration=3)
    
    if success:
        print(f"   ✅ 录音成功: {filename}")
        
        # 4. 识别测试
        print("\n4. 开始识别...")
        success, text = vr.transcribe_audio()
        
        if success:
            print(f"   ✅ 识别成功: '{text}'")
            
            # 5. 解析测试
            print("\n5. 解析结果...")
            parsed = vr.parse_travel_demand(text)
            print(f"   目的地: {parsed['destination']}")
            print(f"   天数: {parsed['days']}")
            print(f"   人数: {parsed['people']}")
            print(f"   预算: {parsed['budget']}")
            print(f"   风格: {parsed['styles']}")
        else:
            print(f"   ❌ 识别失败: {text}")
    else:
        print(f"   ❌ 录音失败: {filename}")
    
    # 清理
    vr.cleanup()
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_voice_recognition()