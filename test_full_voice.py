# test_full_voice.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

print("🎤 完整的语音识别测试")
print("=" * 50)

try:
    from voice_recognizer import VoiceRecognizer
    
    # 创建识别器
    print("1. 创建语音识别器...")
    recognizer = VoiceRecognizer()
    
    # 检查依赖
    print("\n2. 检查依赖...")
    success, message = recognizer.check_dependencies()
    if not success:
        print(f"❌ 依赖检查失败: {message}")
        exit(1)
    print(f"✅ {message}")
    
    # 测试麦克风列表
    print("\n3. 列出麦克风设备...")
    import speech_recognition as sr
    mics = sr.Microphone.list_microphone_names()
    print(f"找到 {len(mics)} 个音频设备:")
    for i, mic in enumerate(mics):
        print(f"  {i}: {mic}")
    
    # 测试录音
    print("\n4. 测试录音（5秒）...")
    print("请说：'我想去北京玩三天'")
    success, message = recognizer.record_audio(duration=5)
    
    if success:
        print(f"✅ {message}")
        
        # 测试转录
        print("\n5. 测试语音识别...")
        transcribe_success, result = recognizer.transcribe_audio()
        
        if transcribe_success:
            print(f"✅ 识别成功!")
            print(f"   结果: {result}")
            
            # 测试解析
            print("\n6. 测试需求解析...")
            demand = recognizer.parse_travel_demand(result)
            print(f"   目的地: {demand['destination']}")
            print(f"   天数: {demand['days']}")
            print(f"   人数: {demand['people']}")
            print(f"   预算: {demand['budget']}")
            print(f"   风格: {demand['styles']}")
        else:
            print(f"❌ 识别失败: {result}")
    else:
        print(f"❌ 录音失败: {message}")
        
except ImportError as e:
    print(f"❌ 导入失败: {e}")
except Exception as e:
    print(f"❌ 测试过程中出现错误: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("测试完成")