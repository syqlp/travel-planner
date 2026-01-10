# debug_weather.py
import requests
import os
import sys

def test_api_directly():
    """直接测试和风天气API"""
    
    # 1. 检查API密钥
    api_key = os.getenv("QWEATHER_API_KEY", "")
    if not api_key:
        print("❌ 错误: QWEATHER_API_KEY 环境变量未设置")
        print("请设置环境变量: export QWEATHER_API_KEY='你的密钥'")
        return False
    
    print(f"✅ API密钥: {api_key[:8]}...")
    
    # 2. 测试搜索长沙市
    url = "https://geoapi.qweather.com/v2/city/lookup"
    params = {
        "location": "长沙市",
        "key": api_key,
        "range": "cn",
        "number": 5,
        "lang": "zh"
    }
    
    print(f"\n🌍 测试搜索: '长沙市'")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"状态码: {response.status_code}")
        
        data = response.json()
        print(f"API返回代码: {data.get('code')}")
        print(f"API返回消息: {data.get('message')}")
        
        if data.get("code") == "200":
            locations = data.get("location", [])
            print(f"✅ 找到 {len(locations)} 个结果:")
            for i, loc in enumerate(locations[:3]):
                print(f"  {i+1}. {loc.get('name')} ({loc.get('adm1')})")
                print(f"     ID: {loc.get('id')}")
                print(f"     坐标: {loc.get('lon')}, {loc.get('lat')}")
            
            # 选择第一个结果测试天气
            if locations:
                city_id = locations[0]["id"]
                print(f"\n🌤️ 测试获取天气 (ID: {city_id})")
                
                weather_url = "https://devapi.qweather.com/v7/weather/3d"
                weather_params = {
                    "location": city_id,
                    "key": api_key,
                    "lang": "zh"
                }
                
                weather_response = requests.get(weather_url, params=weather_params, timeout=10)
                weather_data = weather_response.json()
                
                if weather_data.get("code") == "200":
                    print(f"✅ 天气数据获取成功")
                    print(f"   更新: {weather_data.get('updateTime')}")
                    print(f"   预报天数: {len(weather_data.get('daily', []))}")
                    
                    # 显示第一天的天气
                    if weather_data.get("daily"):
                        first_day = weather_data["daily"][0]
                        print(f"\n📅 第一天预报:")
                        print(f"   日期: {first_day.get('fxDate')}")
                        print(f"   白天: {first_day.get('textDay')}")
                        print(f"   夜间: {first_day.get('textNight')}")
                        print(f"   温度: {first_day.get('tempMin')}°C ~ {first_day.get('tempMax')}°C")
                    
                    return True
                else:
                    print(f"❌ 天气获取失败: {weather_data.get('message')}")
                    return False
            else:
                print("❌ 没有找到城市")
                return False
        else:
            print(f"❌ 城市搜索失败: {data.get('message')}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return False

def test_weather_service():
    """测试天气服务类"""
    print("\n" + "="*60)
    print("测试 WeatherService 类")
    print("="*60)
    
    try:
        from utils.weather_service_pro import QWeatherService
        
        service = QWeatherService()
        print(f"✅ WeatherService 创建成功")
        print(f"   服务API密钥: {service.api_key[:8] if service.api_key else '未设置'}...")
        
        # 测试搜索
        print(f"\n🔍 测试搜索长沙市:")
        locations = service.search_city("长沙市")
        
        if locations:
            print(f"✅ 搜索成功: 找到 {len(locations)} 个城市")
            for loc in locations[:2]:
                print(f"   - {loc.get('name')} (ID: {loc.get('id')})")
        else:
            print("❌ 搜索失败")
            
        # 测试智能匹配
        print(f"\n🤖 测试智能匹配:")
        city_match = service.find_best_city_match("长沙市")
        
        if city_match:
            print(f"✅ 匹配成功:")
            print(f"   城市: {city_match.get('name')}")
            print(f"   ID: {city_match.get('id')}")
            print(f"   省份: {city_match.get('adm1')}")
        else:
            print("❌ 匹配失败")
            
    except ImportError as e:
        print(f"❌ 导入失败: {str(e)}")
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🌤️ 和风天气API调试工具")
    print("-" * 40)
    
    # 测试1: 直接API调用
    api_success = test_api_directly()
    
    # 测试2: 服务类
    test_weather_service()
    
    if api_success:
        print("\n🎉 所有测试完成！")
    else:
        print("\n⚠️  API测试失败，请检查:")
        print("  1. API密钥是否正确")
        print("  2. 网络连接是否正常")
        print("  3. 密钥是否有地理编码权限")