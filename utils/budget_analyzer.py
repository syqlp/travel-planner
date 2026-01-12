# utils/budget_analyzer.py
"""
智能预算分析引擎
分析行程花费，提供优化建议
"""

import streamlit as st
from datetime import datetime
from .budget_database import BudgetDatabase

class BudgetAnalyzer:
    """智能预算分析器"""
    
    def __init__(self, city_name, days, people, budget_level="舒适型"):
        """
        初始化分析器
        Args:
            city_name: 城市名称
            days: 旅行天数
            people: 人数
            budget_level: 预算等级（经济型/舒适型/豪华型）
        """
        self.city_name = city_name
        self.days = days
        self.people = people
        self.budget_level = budget_level
        
        # 获取城市消费系数
        self.cost_factor = BudgetDatabase.get_cost_factor(city_name)
        
        # 获取预算配置
        self.budget_config = BudgetDatabase.BUDGET_LEVELS.get(budget_level, 
                                                             BudgetDatabase.BUDGET_LEVELS["舒适型"])
    
    def analyze_itinerary(self, itinerary_data, attractions_data):
        """
        分析整个行程的花费
        Args:
            itinerary_data: 行程数据（AI生成的行程）
            attractions_data: 景点数据（高德地图返回的真实景点）
        Returns:
            包含详细分析的字典
        """
        # 各部分费用估算
        analysis = {
            "住宿": self._estimate_accommodation(),
            "餐饮": self._estimate_food(),
            "交通": self._estimate_transportation(itinerary_data),
            "门票": self._estimate_tickets(attractions_data),
            "购物": self._estimate_shopping(),
            "其他": self._estimate_other()
        }
        
        # 计算总计
        total_cost = sum(analysis.values())
        
        # 预算评估
        budget_assessment = self._assess_budget(total_cost)
        
        # 生成建议
        suggestions = self._generate_suggestions(analysis, total_cost, budget_assessment)
        
        # 生成每日费用明细
        daily_breakdown = self._generate_daily_breakdown(itinerary_data, attractions_data)
        
        return {
            "城市": self.city_name,
            "天数": self.days,
            "人数": self.people,
            "预算等级": self.budget_level,
            "城市消费系数": self.cost_factor,
            "总费用": total_cost,
            "人均费用": total_cost / self.people if self.people > 0 else 0,
            "日均费用": total_cost / self.days if self.days > 0 else 0,
            "费用明细": analysis,
            "预算评估": budget_assessment,
            "优化建议": suggestions,
            "每日明细": daily_breakdown,
            "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _estimate_accommodation(self):
        """估算住宿费用"""
        hotel_level = self.budget_config["hotel_level"]
        base_prices = BudgetDatabase.BASE_PRICES["住宿"][hotel_level]
        
        # 根据人数选择房型
        if self.people == 1:
            room_type = "单人"
        elif self.people == 2:
            room_type = "双人"
        else:
            room_type = "家庭"
        
        base_cost = base_prices[room_type]
        
        # 考虑城市消费系数
        adjusted_cost = base_cost * self.cost_factor
        
        # 乘以天数（住宿是过夜数，比旅行天数少1）
        nights = max(1, self.days - 1)
        total_cost = adjusted_cost * nights
        
        return round(total_cost, 2)
    
    def _estimate_food(self):
        """估算餐饮费用"""
        food_level = self.budget_config["food_level"]
        base_prices = BudgetDatabase.BASE_PRICES["餐饮"][food_level]
        
        # 全天餐饮费用
        daily_food_cost = base_prices["全天"]
        
        # 考虑城市消费系数
        adjusted_cost = daily_food_cost * self.cost_factor
        
        # 乘以人数和天数
        total_cost = adjusted_cost * self.people * self.days
        
        return round(total_cost, 2)
    
    def _estimate_transportation(self, itinerary_data):
        """估算交通费用"""
        transport_level = self.budget_config["transport_level"]
        
        # 市内交通
        if transport_level == "公共交通为主":
            daily_transport = BudgetDatabase.BASE_PRICES["交通"]["市内"]["公交地铁"]
        elif transport_level == "混合交通":
            daily_transport = (BudgetDatabase.BASE_PRICES["交通"]["市内"]["公交地铁"] + 
                             BudgetDatabase.BASE_PRICES["交通"]["市内"]["出租车"]) / 2
        else:  # 专车/出租车
            daily_transport = BudgetDatabase.BASE_PRICES["交通"]["市内"]["出租车"]
        
        # 考虑城市消费系数
        adjusted_daily = daily_transport * self.cost_factor
        
        # 市内交通总费用
        local_transport_cost = adjusted_daily * self.days * self.people
        
        # 估算城际交通（如果行程中有多个城市）
        # 这里简化处理：根据景点分布估算交通距离
        intercity_cost = self._estimate_intercity_transport(itinerary_data)
        
        total_cost = local_transport_cost + intercity_cost
        
        return round(total_cost, 2)
    
    def _estimate_intercity_transport(self, itinerary_data):
        """估算城际交通费用"""
        # 简化估算：每个景点之间平均10公里
        avg_attractions_per_day = 3
        total_distance = avg_attractions_per_day * self.days * 10  # 公里
        
        # 根据预算等级选择交通方式
        if self.budget_level == "经济型":
            cost_per_km = BudgetDatabase.BASE_PRICES["交通"]["城际"]["高铁二等座"]
        elif self.budget_level == "舒适型":
            cost_per_km = (BudgetDatabase.BASE_PRICES["交通"]["城际"]["高铁二等座"] + 
                          BudgetDatabase.BASE_PRICES["交通"]["城际"]["飞机经济舱"]) / 2
        else:  # 豪华型
            cost_per_km = BudgetDatabase.BASE_PRICES["交通"]["城际"]["飞机经济舱"]
        
        intercity_cost = total_distance * cost_per_km * self.people
        
        return intercity_cost
    
    def _estimate_tickets(self, attractions_data):
        """估算门票费用"""
        total_ticket_cost = 0
        
        # 平均每天参观3个景点
        avg_attractions_per_day = 3
        total_attractions = min(len(attractions_data), avg_attractions_per_day * self.days)
        
        for i in range(total_attractions):
            if i < len(attractions_data):
                attraction = attractions_data[i]
                attraction_name = attraction.get("name", "")
                
                # 识别景点类型
                attraction_type = BudgetDatabase.get_attraction_type(attraction_name)
                
                # 获取基准门票价格
                base_price = BudgetDatabase.BASE_PRICES["门票"].get(attraction_type, 50)
                
                # 考虑城市消费系数
                adjusted_price = base_price * self.cost_factor
                
                # 考虑预算等级（豪华型可能选择更贵的套票）
                if self.budget_level == "豪华型":
                    adjusted_price *= 1.5
                elif self.budget_level == "经济型":
                    adjusted_price *= 0.8
                
                # 乘以人数
                attraction_cost = adjusted_price * self.people
                total_ticket_cost += attraction_cost
        
        return round(total_ticket_cost, 2)
    
    def _estimate_shopping(self):
        """估算购物费用"""
        # 根据预算等级决定购物预算
        shopping_multipliers = {
            "经济型": 0.5,
            "舒适型": 1.0,
            "豪华型": 2.0
        }
        
        multiplier = shopping_multipliers.get(self.budget_level, 1.0)
        
        # 基准购物费用
        base_shopping = BudgetDatabase.BASE_PRICES["购物"]["纪念品"] * 2 + \
                       BudgetDatabase.BASE_PRICES["购物"]["特产"]
        
        adjusted_shopping = base_shopping * self.cost_factor * multiplier * self.people
        
        return round(adjusted_shopping, 2)
    
    def _estimate_other(self):
        """估算其他费用"""
        other_costs = 0
        
        # 保险费用
        insurance = BudgetDatabase.BASE_PRICES["其他"]["保险"] * self.days * self.people
        
        # 通讯费用
        communication = BudgetDatabase.BASE_PRICES["其他"]["通讯"] * self.days
        
        # 应急备用金
        emergency = BudgetDatabase.BASE_PRICES["其他"]["应急"]
        
        other_costs = insurance + communication + emergency
        
        return round(other_costs, 2)
    
    def _assess_budget(self, total_cost):
        """评估预算合理性"""
        # 根据城市和天数估算合理预算范围
        reasonable_ranges = {
            "一线城市": {"经济型": 800, "舒适型": 1500, "豪华型": 3000},
            "新一线城市": {"经济型": 600, "舒适型": 1200, "豪华型": 2500},
            "二线城市": {"经济型": 500, "舒适型": 1000, "豪华型": 2000},
            "三线及以下": {"经济型": 400, "舒适型": 800, "豪华型": 1500}
        }
        
        city_level = BudgetDatabase.get_city_cost_level(self.city_name)
        base_daily = reasonable_ranges[city_level][self.budget_level]
        
        # 计算合理总预算
        reasonable_total = base_daily * self.days * self.people
        
        # 评估
        ratio = total_cost / reasonable_total if reasonable_total > 0 else 1
        
        if ratio < 0.7:
            status = "预算偏低"
            assessment = "您的预算可能过于紧张，建议适当增加预算以确保旅行质量"
        elif ratio < 0.9:
            status = "预算合理偏低"
            assessment = "预算控制得很好，可以享受一次性价比很高的旅行"
        elif ratio <= 1.1:
            status = "预算合理"
            assessment = "预算安排非常合理，可以享受一次舒适的旅行体验"
        elif ratio <= 1.3:
            status = "预算略高"
            assessment = "预算略高于平均水平，但可以享受更好的服务和体验"
        else:
            status = "预算偏高"
            assessment = "预算较高，可以考虑优化部分项目以节约开支"
        
        return {
            "状态": status,
            "评估": assessment,
            "合理预算范围": f"{reasonable_total * 0.9:,.0f} - {reasonable_total * 1.1:,.0f} 元",
            "您的预算": f"{total_cost:,.0f} 元",
            "预算比值": round(ratio, 2)
        }
    
    def _generate_suggestions(self, cost_breakdown, total_cost, budget_assessment):
        """生成优化建议"""
        suggestions = []
        
        # 各部分费用占比
        percentages = {k: v / total_cost * 100 for k, v in cost_breakdown.items()}
        
        # 住宿建议
        if percentages.get("住宿", 0) > 35:
            suggestions.append({
                "类别": "住宿",
                "建议": "住宿费用占比较高，可以考虑：1. 选择经济型酒店 2. 预订民宿或公寓 3. 提前预订享受折扣",
                "预计节省": f"可节省 {cost_breakdown['住宿'] * 0.2:,.0f} 元"
            })
        
        # 餐饮建议
        if percentages.get("餐饮", 0) > 40:
            suggestions.append({
                "类别": "餐饮",
                "建议": "餐饮费用较高，可以尝试：1. 选择当地特色小吃而非高档餐厅 2. 购买当地食材自己烹饪 3. 使用团购或优惠券",
                "预计节省": f"可节省 {cost_breakdown['餐饮'] * 0.15:,.0f} 元"
            })
        
        # 交通建议
        if percentages.get("交通", 0) > 20:
            suggestions.append({
                "类别": "交通",
                "建议": "交通费用可优化：1. 优先使用公共交通 2. 提前购买机票/火车票享受早鸟价 3. 使用拼车服务",
                "预计节省": f"可节省 {cost_breakdown['交通'] * 0.25:,.0f} 元"
            })
        
        # 门票建议
        if percentages.get("门票", 0) > 15:
            suggestions.append({
                "类别": "门票",
                "建议": "门票费用优化：1. 购买景点联票 2. 关注免费开放日 3. 学生证等证件享受优惠 4. 提前网上预订",
                "预计节省": f"可节省 {cost_breakdown['门票'] * 0.3:,.0f} 元"
            })
        
        # 根据预算状态添加建议
        if budget_assessment["状态"] in ["预算偏高", "预算略高"]:
            suggestions.append({
                "类别": "总体预算",
                "建议": "整体预算偏高，建议：1. 选择经济型住宿 2. 减少购物预算 3. 合理安排行程避免重复交通",
                "预计节省": f"可节省 {total_cost * 0.2:,.0f} 元"
            })
        
        # 如果没有特别需要优化的，给出通用建议
        if not suggestions:
            suggestions.append({
                "类别": "总体",
                "建议": "您的预算安排非常合理。建议：1. 预留10%的应急费用 2. 关注机票/酒店促销信息 3. 记录实际花费以便未来参考",
                "预计节省": "保持现状即可"
            })
        
        return suggestions
    
    def _generate_daily_breakdown(self, itinerary_data, attractions_data):
        """生成每日费用明细"""
        daily_breakdown = []
        
        for day in range(1, self.days + 1):
            day_data = {
                "天数": day,
                "住宿": 0,
                "餐饮": 0,
                "交通": 0,
                "门票": 0,
                "购物": 0,
                "其他": 0,
                "小计": 0
            }
            
            # 住宿（只有过夜需要）
            if day < self.days:  # 最后一天不住宿
                hotel_level = self.budget_config["hotel_level"]
                base_prices = BudgetDatabase.BASE_PRICES["住宿"][hotel_level]
                
                if self.people == 1:
                    room_type = "单人"
                elif self.people == 2:
                    room_type = "双人"
                else:
                    room_type = "家庭"
                
                day_data["住宿"] = round(base_prices[room_type] * self.cost_factor, 2)
            
            # 餐饮
            food_level = self.budget_config["food_level"]
            base_prices = BudgetDatabase.BASE_PRICES["餐饮"][food_level]
            day_data["餐饮"] = round(base_prices["全天"] * self.cost_factor * self.people, 2)
            
            # 交通
            transport_level = self.budget_config["transport_level"]
            if transport_level == "公共交通为主":
                daily_transport = BudgetDatabase.BASE_PRICES["交通"]["市内"]["公交地铁"]
            elif transport_level == "混合交通":
                daily_transport = (BudgetDatabase.BASE_PRICES["交通"]["市内"]["公交地铁"] + 
                                 BudgetDatabase.BASE_PRICES["交通"]["市内"]["出租车"]) / 2
            else:
                daily_transport = BudgetDatabase.BASE_PRICES["交通"]["市内"]["出租车"]
            
            day_data["交通"] = round(daily_transport * self.cost_factor * self.people, 2)
            
            # 门票（每天参观3个景点）
            attractions_per_day = 3
            start_idx = (day - 1) * attractions_per_day
            end_idx = min(start_idx + attractions_per_day, len(attractions_data))
            
            for i in range(start_idx, end_idx):
                if i < len(attractions_data):
                    attraction = attractions_data[i]
                    attraction_name = attraction.get("name", "")
                    attraction_type = BudgetDatabase.get_attraction_type(attraction_name)
                    
                    base_price = BudgetDatabase.BASE_PRICES["门票"].get(attraction_type, 50)
                    adjusted_price = base_price * self.cost_factor
                    
                    if self.budget_level == "豪华型":
                        adjusted_price *= 1.5
                    elif self.budget_level == "经济型":
                        adjusted_price *= 0.8
                    
                    day_data["门票"] += adjusted_price * self.people
            
            day_data["门票"] = round(day_data["门票"], 2)
            
            # 购物（最后一天购物）
            if day == self.days:
                shopping_multipliers = {"经济型": 0.5, "舒适型": 1.0, "豪华型": 2.0}
                multiplier = shopping_multipliers.get(self.budget_level, 1.0)
                base_shopping = BudgetDatabase.BASE_PRICES["购物"]["纪念品"] * 2 + \
                               BudgetDatabase.BASE_PRICES["购物"]["特产"]
                day_data["购物"] = round(base_shopping * self.cost_factor * multiplier * self.people, 2)
            
            # 其他（平均分配到每天）
            day_data["其他"] = round(self._estimate_other() / self.days, 2)
            
            # 小计
            day_data["小计"] = round(sum([day_data[k] for k in ["住宿", "餐饮", "交通", "门票", "购物", "其他"]]), 2)
            
            daily_breakdown.append(day_data)
        
        return daily_breakdown