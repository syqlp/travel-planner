# test_qweather_api.py
import requests
import json

API_KEY = "f02a3e6aff14430781b28d46f85664f8"

def test_all_endpoints():
    """测试所有可能的API端点"""
    
    test_cases = [
        {
            "name": "V2 GeoAPI",
            "url": "https://geoapi.qweather.com/v2/city/lookup",
            "params": {"location": "北京", "key": API_KEY, "range": "cn", "number": 1}
        },
        {
            "name": "V7 API Geo", 
            "url": "https://api.qweather.com/v7/geo/city/lookup",
            "params": {"location": "北京", "key": API_KEY, "range": "cn", "number": 1}
        },
        {
            "name": "DevAPI V2",
            "url": "https://devapi.qweather.com/v2/city/lookup",
            "params": {"location": "北京", "key": API_KEY, "range": "cn", "number": 1}
        },
        {
            "name": "DevAPI V7 Geo",
            "url": "https://devapi.qweather.com/v7/geo/city/lookup",
            "params": {"location": "北京", "key": API_KEY, "range": "cn", "number": 1}
        }
    ]
    
    print("🔍 测试和风天气所有API端点")
    print("="*70)
    
    for test in test_cases:
        print(f"\n📡 测试: {test['name']}")
        print(f"URL: {test['url']}")
        print(f"参数: {test['params']}")
        
        try:
            response = requests.get(test['url'], params=test['params'], timeout=8)
            print(f"状态码: {response.status_code}")
            print(f"内容类型: {response.headers.get('content-type', '未知')}")
            
            # 显示响应前200字符
            preview = response.text[:200]
            print(f"响应预览: {preview}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ JSON解析成功")
                    print(f"   代码: {data.get('code', 'N/A')}")
                    print(f"   消息: {data.get('message', 'N/A')}")
                    
                    if data.get("code") == "200":
                        print(f"🎉 成功! 找到 {len(data.get('location', []))} 个城市")
                        return test['url'], test['params']
                except json.JSONDecodeError:
                    print(f"⚠️  返回200但非JSON格式")
            else:
                print(f"⚠️  状态码: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")
    
    print("\n" + "="*70)
    print("❌ 所有端点测试失败")
    return None, None

def test_weather_endpoint(city_id="101010100"):
    """测试天气端点"""
    print(f"\n🌤️ 测试天气API (城市ID: {city_id})")
    print("-"*50)
    
    endpoints = [
        ("API V7", "https://api.qweather.com/v7/weather/3d"),
        ("DevAPI V7", "https://devapi.qweather.com/v7/weather/3d"),
    ]
    
    for name, url in endpoints:
        print(f"\n测试: {name}")
        params = {"location": city_id, "key": API_KEY}
        
        try:
            response = requests.get(url, params=params, timeout=8)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ 成功! 代码: {data.get('code')}")
                    print(f"   消息: {data.get('message')}")
                    if data.get("code") == "200":
                        print(f"   预报天数: {len(data.get('daily', []))}")
                        return url
                except:
                    print(f"响应: {response.text[:100]}")
            else:
                print(f"响应: {response.text[:100]}")
                
        except Exception as e:
            print(f"❌ 异常: {str(e)}")
    
    return None

if __name__ == "__main__":
    print(f"使用API密钥: {API_KEY[:8]}...")
    
    # 测试城市搜索
    geo_url, geo_params = test_all_endpoints()
    
    if geo_url:
        print(f"\n🎯 可用的地理编码端点: {geo_url}")
        
        # 测试获取城市ID
        response = requests.get(geo_url, params=geo_params, timeout=10)
        data = response.json()
        if data.get("code") == "200" and data.get("location"):
            city_id = data["location"][0]["id"]
            print(f"获取到城市ID: {city_id}")
            
            # 测试天气API
            weather_url = test_weather_endpoint(city_id)
            if weather_url:
                print(f"\n🎯 可用的天气端点: {weather_url}")
                
                # 总结
                print("\n" + "="*70)
                print("✅ 配置建议:")
                print(f"地理编码URL: {geo_url.replace('/city/lookup', '')}")
                print(f"天气API URL: {weather_url.replace('/3d', '')}")
            else:
                print("\n⚠️ 天气API测试失败")
    else:
        print("\n❌ 未找到可用的地理编码端点")
        print("\n💡 可能原因:")
        print("1. API密钥无效或未激活地理编码服务")
        print("2. 需要访问 https://dev.qweather.com/ 激活服务")
        print("3. API版本变更，需要更新端点")