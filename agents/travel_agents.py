# agents/travel_agents.py
"""
旅行代理定义 - 适配 CrewAI 0.28.8
"""
from crewai import Agent
from langchain_community.llms import Ollama

# 创建 Ollama LLM 实例
ollama_llm = Ollama(
    model="phi",
    temperature=0.1,
    base_url="http://localhost:11434"
)

def create_travel_planner():
    """创建旅行规划师代理"""
    return Agent(
        role="资深旅行规划师",
        goal="为用户制定完美的旅行计划，考虑预算、兴趣和时间限制",
        backstory="""你是一位有20年经验的旅行规划专家，曾为数百名客户设计过个性化的旅行方案。
        你擅长发现隐藏的宝石、优化行程安排，并在预算内提供最大价值。""",
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        llm=ollama_llm  # 关键：直接传递 LLM 实例
    )

def create_cultural_expert():
    """创建文化专家代理"""
    return Agent(
        role="文化体验专家",
        goal="推荐当地文化体验、美食和历史遗迹",
        backstory="""你是一位人类学家和美食家，对世界各地的文化有深入研究。
        你特别擅长推荐真实的当地体验，帮助游客深入理解目的地文化。""",
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        llm=ollama_llm
    )

def create_budget_advisor():
    """创建预算顾问代理"""
    return Agent(
        role="旅行预算优化专家",
        goal="在用户预算内优化旅行开支，找到性价比最高的选项",
        backstory="""你是一位前旅行公司的财务总监，现在专门帮助个人旅行者优化预算。
        你知道如何找到优惠、避开旅游陷阱，让每一分钱都花得值。""",
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        llm=ollama_llm
    )

# 导出代理实例
TRAVEL_PLANNER = create_travel_planner()
CULTURAL_EXPERT = create_cultural_expert()
BUDGET_ADVISOR = create_budget_advisor()