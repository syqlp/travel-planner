# main.py - 主程序
from crews.travel_crew import TravelCrew

def main():
    print("🤖 智能旅行规划系统")
    print("="*50)
    
    # 初始化
    planner = TravelCrew()
    
    # 测试查询
    test_queries = [
        "新疆3日游",
        "乌鲁木齐周边有什么好玩的",
        "预算5000元的新疆旅行"
    ]
    
    for query in test_queries:
        print(f"\n📝 规划: {query}")
        print("-"*40)
        
        try:
            result = planner.plan(query)
            print(f"✅ 成功！")
            print(f"结果预览: {str(result)[:200]}...")
        except Exception as e:
            print(f"❌ 失败: {e}")
    
    print("\n" + "="*50)
    print("🎉 系统测试完成！")
    print("="*50)

if __name__ == "__main__":
    main()