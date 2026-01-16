# agents/simple_agent.py - 修正版
from crewai import Agent
from .test_ollama_crew import OllamaLLMWrapper

def create_travel_agent(model="phi"):
    """创建旅行规划Agent"""
    wrapper = OllamaLLMWrapper(model)
    
    return Agent(
        role="智能旅行规划师",
        goal="为用户制定完美的旅行计划",
        backstory="资深旅行规划专家，熟悉新疆旅游资源",
        llm=wrapper.get_config(),
        verbose=True,
        max_iter=2,
        memory=True
    )