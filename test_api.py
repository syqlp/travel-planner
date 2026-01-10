import requests
try:
    # 测试百度（应该能访问）
    r1 = requests.get('https://www.baidu.com', timeout=5)
    print(f'百度: {r1.status_code}')
    
    # 测试和风天气
    r2 = requests.get('https://geoapi.qweather.com', timeout=5)
    print(f'和风天气: {r2.status_code}')
except Exception as e:
    print(f'错误: {e}')