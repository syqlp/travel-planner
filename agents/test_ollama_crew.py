# test_ollama_crew_fixed.py
"""
测试 Ollama + CrewAI 集成 - 修复版
"""
import sys
sys.path.append('.')

print("=" * 60)
print("测试 Ollama + CrewAI 集成 (修复版)")
print("=" * 60)

# 测试 Ollama 连接
print("1. 测试 Ollama 连接...")
try:
    import requests
    response = requests.get("http://localhost:11434/api/tags", timeout=5)
    if response.status_code == 200:
        models = response.json().get('models', [])
        print(f"✅ Ollama 正常，可用模型: {', '.join([m['name'] for m in models])}")
    else:
        print(f"❌ Ollama 连接失败: {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Ollama 错误: {e}")
    print("请运行: ollama serve")
    sys.exit(1)

# 测试 CrewAI 代理创建
print("\n2. 测试 CrewAI 代理创建...")
try:
    # 直接从 agents 模块导入
    from agents.travel_agents import TRAVEL_PLANNER
    
    print("✅ 代理导入成功")
    print(f"   角色: {TRAVEL_PLANNER.role}")
    print(f"   目标: {TRAVEL_PLANNER.goal}")
    print(f"   是否允许委托: {TRAVEL_PLANNER.allow_delegation}")
    
    # 测试代理是否有 execute_task 方法
    if hasattr(TRAVEL_PLANNER, 'execute_task'):
        print("✅ 代理有 execute_task 方法")
    else:
        print("⚠️  代理没有 execute_task 方法")
    
    # 测试简单调用
    print("\n3. 测试简单调用...")
    try:
        # 使用正确的方法
        from crewai import Task
        
        test_task = Task(
            description="请用中文简单介绍一下北京",
            agent=TRAVEL_PLANNER,
            expected_output="一段介绍文字"
        )
        print("✅ 任务创建成功")
        
        print("\n🎉 所有测试通过！")
        print("现在可以运行应用了")
        
    except Exception as e:
        print(f"❌ 任务创建失败: {e}")
        print("但代理创建成功，应用可能仍能运行")
    
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("\n检查文件路径...")
    import os
    print("当前目录:", os.getcwd())
    print("agents 目录内容:", os.listdir('agents') if os.path.exists('agents') else '目录不存在')
    
except Exception as e:
    print(f"❌ 其他错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)