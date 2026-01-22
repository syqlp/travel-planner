# test_baidu_api.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🧪 测试百度语音API连接...")

# 方法1：直接测试
from aip import AipSpeech

# 使用你的API密钥
APP_ID = '121914868'
API_KEY = 'Sy4b9H4mVyl5LtYEXTsZQNqG'
SECRET_KEY = '2l1JhXNKVnjJ1Ui3HcntaVvVrcYME9PI'

print(f"📊 使用配置:")
print(f"  APP_ID: {APP_ID}")
print(f"  API_KEY: {API_KEY[:10]}...")
print(f"  SECRET_KEY: {SECRET_KEY[:10]}...")

try:
    # 创建客户端
    client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)
    print("✅ 百度语音客户端创建成功")
    
    # 测试API调用
    print("🔍 测试API连接...")
    
    # 创建一个极短的静音音频测试
    import wave
    import tempfile
    
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        tmp_path = tmp.name
    
    # 创建0.1秒静音音频
    with wave.open(tmp_path, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b'\x00' * 3200)  # 0.1秒
    
    with open(tmp_path, 'rb') as f:
        audio_data = f.read()
    
    os.unlink(tmp_path)
    
    # 调用API
    result = client.asr(audio_data, 'wav', 16000, {
        'dev_pid': 1537,  # 普通话
    })
    
    print(f"📋 API返回结果: {result}")
    
    if 'err_no' in result:
        if result['err_no'] == 0:
            print("✅ 百度语音API连接正常")
        elif result['err_no'] == 3301:  # 音频质量差（正常）
            print("✅ 百度语音API连接正常（测试音频质量差）")
        else:
            error_msg = {
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
            }.get(result['err_no'], f"未知错误代码: {result['err_no']}")
            print(f"⚠️ API错误: {error_msg}")
    
    # 测试 utils/baidu_voice_full.py
    print("\n🔍 测试 BaiduVoiceFull 类...")
    from utils.baidu_voice_full import BaiduVoiceFull
    
    baidu_voice = BaiduVoiceFull()
    print(f"BaiduVoiceFull 可用: {baidu_voice.available}")
    
    if baidu_voice.available:
        # 测试录音并识别
        print("\n🎤 测试完整流程...")
        
        # 创建一个测试录音
        import speech_recognition as sr
        r = sr.Recognizer()
        
        print("请说一句话进行测试（2秒）...")
        with sr.Microphone() as source:
            audio = r.listen(source, timeout=5, phrase_time_limit=2)
        
        print("✅ 录音完成")
        
        # 使用百度识别
        success, text = baidu_voice.save_and_recognize(audio)
        print(f"识别结果: {success} - {text}")
        
except Exception as e:
    print(f"❌ 测试失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()