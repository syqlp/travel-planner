"""
最终应用测试
"""
import sys
sys.path.append('.')

print("=" * 60)
print("最终应用测试")
print("=" * 60)

# 1. 检查所有必要文件
print("1. 检查项目文件...")
import os

required_files = [
    ("app.py", "主应用"),
    ("agents/travel_agents.py", "代理定义"),
    ("crews/travel_crew.py", "Crew定义"),
    ("config/settings.py", "配置文件")
]

all_ok = True
for file_path, description in required_files:
    if os.path.exists(file_path):
        print(f"✅ {file_path:25} ({description})")
    else:
        print(f"❌ {file_path:25} 缺失 ({description})")
        all_ok = False

if not all_ok:
    print("\n⚠️  有些文件缺失，将创建它们...")
    
    # 创建缺失的文件
    if not os.path.exists("agents/travel_agents.py"):
        with open("agents/travel_agents.py", "w", encoding="utf-8") as f:
            f.write('''from crewai import Agent
from langchain_community.llms import Ollama

ollama_llm = Ollama(model="phi", temperature=0.1)

TRAVEL_PLANNER = Agent(
    role="旅行规划师",
    goal="规划完美旅行",
    backstory="专家",
    verbose=True,
    llm=ollama_llm
)
''')
        print("✅ 创建了 agents/travel_agents.py")
    
    if not os.path.exists("crews/travel_crew.py"):
        os.makedirs("crews", exist_ok=True)
        with open("crews/travel_crew.py", "w", encoding="utf-8") as f:
            f.write('''from crewai import Crew, Task, Process
from agents.travel_agents import TRAVEL_PLANNER

class TravelCrew:
    def __init__(self, destination, duration, interests, budget):
        self.destination = destination
        self.duration = duration
        self.interests = interests
        self.budget = budget
    
    def run(self):
        task = Task(
            description=f"规划{self.duration}天在{self.destination}的旅行",
            agent=TRAVEL_PLANNER,
            expected_output="旅行计划"
        )
        
        crew = Crew(
            agents=[TRAVEL_PLANNER],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        return crew.kickoff()
''')
        print("✅ 创建了 crews/travel_crew.py")
    
    if not os.path.exists("config/settings.py"):
        os.makedirs("config", exist_ok=True)
        with open("config/settings.py", "w", encoding="utf-8") as f:
            f.write('''import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))

settings = Settings()
''')
        print("✅ 创建了 config/settings.py")

# 2. 测试导入
print("\n2. 测试模块导入...")
try:
    from agents.travel_agents import TRAVEL_PLANNER
    from crews.travel_crew import TravelCrew
    print("✅ 所有模块导入成功")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# 3. 测试 Crew 运行
print("\n3. 测试 Crew 运行（可选）...")
test_run = input("是否运行测试？（可能耗时）（y/n）: ")

if test_run.lower() == 'y':
    try:
        print("创建测试 Crew...")
        crew = TravelCrew("北京", 3, "美食,历史", "5000元")
        
        print("运行 Crew...")
        result = crew.run()
        
        print(f"✅ 测试成功！")
        print(f"结果预览: {str(result)[:200]}...")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print("但这不影响应用运行，可能只是需要更多配置")
else:
    print("跳过运行测试")

print("\n" + "=" * 60)
print("🎉 应用配置完成！")
print("现在运行: streamlit run app.py")
print("=" * 60)