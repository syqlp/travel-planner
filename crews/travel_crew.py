"""
旅行规划 Crew
"""
from crewai import Crew, Task, Process
from agents.travel_agents import TRAVEL_PLANNER, CULTURAL_EXPERT, BUDGET_ADVISOR

class TravelCrew:
    def __init__(self, destination, duration, interests, budget):
        self.destination = destination
        self.duration = duration
        self.interests = interests
        self.budget = budget
    
    def create_tasks(self):
        plan_task = Task(
            description=f"为{self.duration}天在{self.destination}的旅行制定详细行程，兴趣：{self.interests}，预算：{self.budget}",
            agent=TRAVEL_PLANNER,
            expected_output="每日详细行程安排"
        )
        
        culture_task = Task(
            description=f"为{self.destination}推荐文化体验，基于兴趣：{self.interests}",
            agent=CULTURAL_EXPERT,
            expected_output="文化体验推荐清单"
        )
        
        budget_task = Task(
            description=f"为{self.duration}天的{self.destination}旅行优化{self.budget}预算",
            agent=BUDGET_ADVISOR,
            context=[plan_task, culture_task],
            expected_output="详细的预算分配表"
        )
        
        return [plan_task, culture_task, budget_task]
    
    def run(self):
        tasks = self.create_tasks()
        crew = Crew(
            agents=[TRAVEL_PLANNER, CULTURAL_EXPERT, BUDGET_ADVISOR],
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )
        return crew.kickoff()