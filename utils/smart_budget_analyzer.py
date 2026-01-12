# utils/smart_budget_analyzer.py
"""
智能预算分析器 - 处理各种输入格式，健壮性更强
"""

import streamlit as st
import re
from datetime import datetime

class SmartBudgetAnalyzer:
    """智能预算分析器 - 处理各种用户输入"""
    
    @staticmethod
    def analyze(user_input, city_name, attractions_count=0):
        """
        智能分析预算
        Args:
            user_input: 用户输入的字典，包含days, people, budget等
            city_name: 城市名称
            attractions_count: 景点数量
        """
        try:
            # 安全获取参数
            days = int(user_input.get('days', 1))
            people = int(user_input.get('people', 1))
            budget_str = str(user_input.get('budget', '舒适型'))
            
            # 标准化预算等级
            budget_level = SmartBudgetAnalyzer._extract_budget_level(budget_str)
            
            # 分析预算
            analysis = SmartBudgetAnalyzer._perform_analysis(
                city_name, days, people, budget_level, attractions_count
            )
            
            # 记录原始预算输入
            analysis['原始预算输入'] = budget_str
            if budget_str != budget_level:
                analysis['预算等级识别'] = f"{budget_str} → {budget_level}"
            
            return analysis
            
        except Exception as e:
            # 返回错误信息，但不中断程序
            return {
                "城市": city_name,
                "错误": f"预算分析失败: {str(e)}",
                "建议": "请输入明确的预算等级（经济型/舒适型/豪华型）",
                "示例": "舒适型 或 舒适型(人均300-600元/天)"
            }
    
    @staticmethod
    def _extract_budget_level(budget_str):
        """智能提取预算等级"""
        if not budget_str or not isinstance(budget_str, str):
            return "舒适型"
        
        # 清理字符串
        budget_str = budget_str.strip()
        
        # 直接匹配
        if "经济型" in budget_str:
            return "经济型"
        elif "舒适型" in budget_str:
            return "舒适型"
        elif "豪华型" in budget_str:
            return "豪华型"
        
        # 移除括号内容
        clean_str = re.sub(r'\([^)]*\)', '', budget_str).strip()
        
        # 关键词匹配
        keywords = {
            "经济型": ["经济", "便宜", "省钱", "低预算", "预算有限", "节俭"],
            "舒适型": ["舒适", "中等", "标准", "适中", "一般", "正常"],
            "豪华型": ["豪华", "高端", "奢侈", "高预算", "不差钱", "享受"]
        }
        
        for level, words in keywords.items():
            for word in words:
                if word in clean_str:
                    return level
        
        # 数字判断（如果有价格范围）
        price_pattern = r'(\d+)\s*[元\-~]\s*(\d+)'
        match = re.search(price_pattern, budget_str)
        if match:
            try:
                min_price = int(match.group(1))
                max_price = int(match.group(2))
                avg_price = (min_price + max_price) / 2
                
                if avg_price < 300:
                    return "经济型"
                elif avg_price < 800:
                    return "舒适型"
                else:
                    return "豪华型"
            except:
                pass
        
        return "舒适型"  # 默认
    
    @staticmethod
    def _perform_analysis(city_name, days, people, budget_level, attractions_count):
        """执行预算分析"""
        # 城市消费系数
        city_factors = {
            "北京": 1.2, "上海": 1.2, "广州": 1.0, "深圳": 1.1,
            "成都": 0.8, "杭州": 0.9, "重庆": 0.7, "西安": 0.7,
            "default": 0.6
        }
        
        city_factor = city_factors.get(city_name, city_factors["default"])
        
        # 基准每日费用（元/人）
        base_daily = {
            "经济型": 200,
            "舒适型": 400, 
            "豪华型": 800
        }
        
        daily_per_person = base_daily.get(budget_level, 400) * city_factor
        
        # 计算总费用
        total_cost = daily_per_person * days * people
        
        # 费用构成（根据预算等级调整比例）
        if budget_level == "经济型":
            breakdown = {
                "住宿": total_cost * 0.30,
                "餐饮": total_cost * 0.35,
                "交通": total_cost * 0.20,
                "门票": total_cost * 0.10,
                "其他": total_cost * 0.05
            }
        elif budget_level == "舒适型":
            breakdown = {
                "住宿": total_cost * 0.35,
                "餐饮": total_cost * 0.30,
                "交通": total_cost * 0.15,
                "门票": total_cost * 0.12,
                "购物": total_cost * 0.05,
                "其他": total_cost * 0.03
            }
        else:  # 豪华型
            breakdown = {
                "住宿": total_cost * 0.40,
                "餐饮": total_cost * 0.25,
                "交通": total_cost * 0.15,
                "门票": total_cost * 0.10,
                "购物": total_cost * 0.05,
                "娱乐": total_cost * 0.05
            }
        
        # 预算评估
        assessment = SmartBudgetAnalyzer._assess_budget(total_cost, budget_level, days, people)
        
        # 优化建议
        suggestions = SmartBudgetAnalyzer._generate_suggestions(budget_level, city_name, days)
        
        return {
            "城市": city_name,
            "天数": days,
            "人数": people,
            "预算等级": budget_level,
            "城市消费系数": round(city_factor, 2),
            "人均日均费用": round(daily_per_person, 2),
            "总费用": round(total_cost, 2),
            "人均费用": round(total_cost / people, 2) if people > 0 else 0,
            "日均费用": round(total_cost / days, 2) if days > 0 else 0,
            "费用明细": {k: round(v, 2) for k, v in breakdown.items()},
            "预算评估": assessment,
            "优化建议": suggestions,
            "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    @staticmethod
    def _assess_budget(total_cost, budget_level, days, people):
        """评估预算合理性"""
        reasonable_daily = {
            "经济型": 150,
            "舒适型": 300,
            "豪华型": 600
        }
        
        base_daily = reasonable_daily.get(budget_level, 300)
        reasonable_total = base_daily * days * people
        
        ratio = total_cost / reasonable_total if reasonable_total > 0 else 1
        
        if ratio < 0.7:
            status = "预算偏低"
            advice = "预算可能过于紧张，考虑增加预算或选择更经济的目的地"
        elif ratio < 0.9:
            status = "预算合理偏低"
            advice = "预算控制良好，适合追求性价比的旅行者"
        elif ratio <= 1.1:
            status = "预算合理"
            advice = "预算安排合理，可以享受舒适的旅行体验"
        elif ratio <= 1.3:
            status = "预算略高"
            advice = "预算略高，可以考虑优化某些项目"
        else:
            status = "预算偏高"
            advice = "预算较高，建议重新评估或选择高端旅行体验"
        
        return {
            "状态": status,
            "建议": advice,
            "合理范围": f"¥{reasonable_total*0.9:,.0f} - ¥{reasonable_total*1.1:,.0f}",
            "当前预算": f"¥{total_cost:,.0f}",
            "比值": round(ratio, 2)
        }
    
    @staticmethod
    def _generate_suggestions(budget_level, city_name, days):
        """生成优化建议"""
        suggestions = []
        
        # 通用建议
        suggestions.append({
            "类别": "通用",
            "建议": "提前规划行程，关注机票酒店促销信息",
            "预计节省": "10-20%"
        })
        
        # 根据预算等级的建议
        if budget_level == "经济型":
            suggestions.extend([
                {
                    "类别": "住宿",
                    "建议": "选择经济型酒店或青年旅社，多人间更划算",
                    "预计节省": "30-50%"
                },
                {
                    "类别": "餐饮",
                    "建议": "尝试当地小吃街，避免景区内用餐",
                    "预计节省": "20-40%"
                }
            ])
        elif budget_level == "舒适型":
            suggestions.extend([
                {
                    "类别": "住宿",
                    "建议": "提前30天预订酒店，通常有早鸟优惠",
                    "预计节省": "15-25%"
                },
                {
                    "类别": "门票",
                    "建议": "购买景点联票，关注学生/老人优惠",
                    "预计节省": "10-30%"
                }
            ])
        else:  # 豪华型
            suggestions.extend([
                {
                    "类别": "服务",
                    "建议": "考虑私人导游或定制服务，提升体验",
                    "预计增加价值": "50-100%"
                },
                {
                    "类别": "住宿",
                    "建议": "选择特色精品酒店或度假村",
                    "预计增加体验": "高端享受"
                }
            ])
        
        # 根据天数的建议
        if days > 7:
            suggestions.append({
                "类别": "长途",
                "建议": "考虑购买多日通票，租车可能更经济",
                "预计节省": "15-30%"
            })
        
        return suggestions
    
    @staticmethod
    def display(analysis):
        """显示分析结果"""
        if '错误' in analysis:
            st.warning(f"⚠️ {analysis['错误']}")
            if '建议' in analysis:
                st.info(f"💡 {analysis['建议']}")
            if '示例' in analysis:
                st.caption(f"📝 示例格式: {analysis['示例']}")
            return
        
        st.markdown("---")
        st.markdown("## 💰 智能预算分析")
        
        # 显示识别信息
        if '预算等级识别' in analysis:
            st.info(f"🔍 {analysis['预算等级识别']}")
        
        # 概览卡片
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("总预算", f"¥{analysis['总费用']:,.0f}")
        
        with col2:
            st.metric("人均费用", f"¥{analysis['人均费用']:,.0f}")
        
        with col3:
            st.metric("日均费用", f"¥{analysis['日均费用']:,.0f}")
        
        # 基本信息
        st.caption(f"📍 {analysis['城市']} (系数: {analysis['城市消费系数']}) | 📅 {analysis['天数']}天 | 👥 {analysis['人数']}人 | 💼 {analysis['预算等级']}")
        
        # 费用构成
        st.markdown("### 📊 费用构成")
        
        cost_breakdown = analysis['费用明细']
        total = analysis['总费用']
        
        for category, amount in cost_breakdown.items():
            percentage = (amount / total * 100) if total > 0 else 0
            st.markdown(f"""
            <div style="margin: 10px 0;">
                <div style="display: flex; justify-content: space-between;">
                    <span><strong>{category}</strong></span>
                    <span>¥{amount:,.0f} ({percentage:.1f}%)</span>
                </div>
                <div style="background: #e0e0e0; height: 8px; border-radius: 4px; margin-top: 2px;">
                    <div style="background: #4CAF50; width: {min(percentage, 100)}%; height: 100%; border-radius: 4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # 预算评估
        assessment = analysis['预算评估']
        st.markdown("### 📈 预算评估")
        
        status_color = {
            "预算合理": "#28a745",
            "预算合理偏低": "#17a2b8",
            "预算偏低": "#ffc107",
            "预算略高": "#fd7e14",
            "预算偏高": "#dc3545"
        }.get(assessment['状态'], "#6c757d")
        
        st.markdown(f"""
        <div style="
            background-color: {status_color}20;
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid {status_color};
            margin: 10px 0;
        ">
            <h4 style="margin: 0; color: {status_color};">{assessment['状态']}</h4>
            <p style="margin: 5px 0 0 0;">{assessment['建议']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.caption(f"💰 **合理预算范围**: {assessment['合理范围']} | 📊 **当前预算**: {assessment['当前预算']} (比值: {assessment['比值']})")
        
        # 优化建议
        st.markdown("### 💡 优化建议")
        
        for i, suggestion in enumerate(analysis['优化建议']):
            with st.expander(f"📌 {suggestion['类别']}建议 ({i+1}/{len(analysis['优化建议'])})", expanded=(i<2)):
                st.write(f"**建议**: {suggestion['建议']}")
                if '预计节省' in suggestion:
                    st.write(f"**预计节省**: {suggestion['预计节省']}")
                elif '预计增加价值' in suggestion:
                    st.write(f"**预计增加价值**: {suggestion['预计增加价值']}")
                elif '预计增加体验' in suggestion:
                    st.write(f"**预计增加体验**: {suggestion['预计增加体验']}")
        
        # 显示分析时间
        st.caption(f"⏰ 分析时间: {analysis.get('分析时间', '')}")