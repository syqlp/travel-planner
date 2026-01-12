# utils/budget_visualizer.py
"""
预算分析结果的可视化展示
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

class BudgetVisualizer:
    """预算可视化展示"""
    
    @staticmethod
    def display_budget_analysis(budget_analysis):
        """显示完整的预算分析结果"""
        if not budget_analysis:
            st.warning("预算分析数据为空")
            return
        
        # 显示概览
        BudgetVisualizer._display_overview(budget_analysis)
        
        # 费用构成饼图
        BudgetVisualizer._display_cost_distribution(budget_analysis)
        
        # 每日费用趋势
        BudgetVisualizer._display_daily_trend(budget_analysis)
        
        # 详细费用表
        BudgetVisualizer._display_detailed_table(budget_analysis)
        
        # 优化建议
        BudgetVisualizer._display_suggestions(budget_analysis)
    
    @staticmethod
    def _display_overview(budget_analysis):
        """显示预算概览"""
        st.markdown("---")
        st.markdown("## 💰 智能预算分析")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="总预算",
                value=f"¥{budget_analysis['总费用']:,.0f}",
                help="整个行程的预计总花费"
            )
        
        with col2:
            st.metric(
                label="人均费用",
                value=f"¥{budget_analysis['人均费用']:,.0f}",
                help="每人平均花费"
            )
        
        with col3:
            st.metric(
                label="日均费用",
                value=f"¥{budget_analysis['日均费用']:,.0f}",
                help="每天平均花费"
            )
        
        with col4:
            status = budget_analysis['预算评估']['状态']
            color = {"预算合理": "green", "预算合理偏低": "lightgreen", 
                    "预算偏低": "orange", "预算略高": "orange", "预算偏高": "red"}
            
            st.metric(
                label="预算评估",
                value=status,
                delta=None,
                delta_color=color.get(status, "normal")
            )
        
        # 预算评估说明
        assessment = budget_analysis['预算评估']
        st.info(f"📊 **预算评估**: {assessment['评估']}")
        st.caption(f"💰 **合理预算范围**: {assessment['合理预算范围']} | 📈 **您的预算**: {assessment['您的预算']}")
    
    @staticmethod
    def _display_cost_distribution(budget_analysis):
        """显示费用构成饼图"""
        st.markdown("### 📊 费用构成分析")
        
        cost_breakdown = budget_analysis['费用明细']
        
        # 准备数据
        categories = list(cost_breakdown.keys())
        values = list(cost_breakdown.values())
        percentages = [v / sum(values) * 100 for v in values]
        
        # 创建两列布局
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 创建饼图
            fig = go.Figure(data=[
                go.Pie(
                    labels=categories,
                    values=values,
                    hole=0.4,
                    textinfo='percent+value',
                    texttemplate='%{label}<br>¥%{value:,.0f}<br>(%{percent})',
                    hoverinfo='label+value+percent',
                    marker=dict(colors=px.colors.qualitative.Set3)
                )
            ])
            
            fig.update_layout(
                title="费用构成分布",
                height=400,
                showlegend=False,
                margin=dict(t=50, b=0, l=0, r=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 显示详细数据
            st.markdown("#### 费用明细")
            for category, value in cost_breakdown.items():
                percentage = value / sum(values) * 100
                st.markdown(f"""
                **{category}**: ¥{value:,.0f}  
                *({percentage:.1f}%)*
                """)
            
            total = sum(values)
            st.markdown(f"""
            ---
            **总计**: ¥{total:,.0f}  
            **人均**: ¥{total/budget_analysis['人数']:,.0f}
            """)
    
    @staticmethod
    def _display_daily_trend(budget_analysis):
        """显示每日费用趋势"""
        daily_breakdown = budget_analysis.get('每日明细', [])
        if not daily_breakdown:
            return
        
        st.markdown("### 📅 每日费用趋势")
        
        # 转换为DataFrame
        df = pd.DataFrame(daily_breakdown)
        
        # 创建堆叠面积图
        categories = ['住宿', '餐饮', '交通', '门票', '购物', '其他']
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
        
        fig = go.Figure()
        
        # 添加堆叠区域
        for i, category in enumerate(categories):
            fig.add_trace(go.Scatter(
                x=df['天数'],
                y=df[category],
                mode='lines',
                name=category,
                stackgroup='one',
                line=dict(width=0.5, color=colors[i]),
                fillcolor=colors[i],
                hovertemplate=f'{category}: ¥%{{y:,.0f}}<br>第%{{x}}天<extra></extra>'
            ))
        
        # 添加总计线
        fig.add_trace(go.Scatter(
            x=df['天数'],
            y=df['小计'],
            mode='lines+markers',
            name='每日总计',
            line=dict(color='#2C3E50', width=3),
            marker=dict(size=8),
            hovertemplate='总计: ¥%{y:,.0f}<br>第%{x}天<extra></extra>'
        ))
        
        fig.update_layout(
            title="每日费用分布趋势",
            xaxis_title="旅行天数",
            yaxis_title="费用 (元)",
            height=400,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 显示每日明细表
        with st.expander("📋 查看每日详细费用", expanded=False):
            display_df = df.copy()
            display_df = display_df.round(2)
            st.dataframe(display_df, use_container_width=True)
    
    @staticmethod
    def _display_detailed_table(budget_analysis):
        """显示详细费用表"""
        st.markdown("### 📋 详细费用估算")
        
        cost_breakdown = budget_analysis['费用明细']
        city_factor = budget_analysis['城市消费系数']
        budget_level = budget_analysis['预算等级']
        
        # 创建详细说明表格
        explanations = [
            {
                "类别": "住宿",
                "估算依据": f"{budget_level}酒店 × {city_factor:.2f}城市系数 × {budget_analysis['天数']-1}晚",
                "单价": f"¥{cost_breakdown['住宿']/(budget_analysis['天数']-1):,.0f}/晚" if budget_analysis['天数'] > 1 else "不适用",
                "小计": f"¥{cost_breakdown['住宿']:,.0f}"
            },
            {
                "类别": "餐饮",
                "估算依据": f"{budget_level}标准 × {city_factor:.2f}城市系数 × {budget_analysis['天数']}天 × {budget_analysis['人数']}人",
                "单价": f"¥{cost_breakdown['餐饮']/(budget_analysis['天数']*budget_analysis['人数']):,.0f}/人天",
                "小计": f"¥{cost_breakdown['餐饮']:,.0f}"
            },
            {
                "类别": "交通",
                "估算依据": f"{budget_level}交通方式 × {city_factor:.2f}城市系数 × {budget_analysis['天数']}天",
                "单价": f"¥{cost_breakdown['交通']/budget_analysis['天数']:,.0f}/天",
                "小计": f"¥{cost_breakdown['交通']:,.0f}"
            },
            {
                "类别": "门票",
                "估算依据": f"平均每天3个景点 × {city_factor:.2f}城市系数 × {budget_analysis['人数']}人",
                "单价": f"¥{cost_breakdown['门票']/(budget_analysis['天数']*budget_analysis['人数']*3):,.0f}/人景点" if budget_analysis['天数'] > 0 else "不适用",
                "小计": f"¥{cost_breakdown['门票']:,.0f}"
            },
            {
                "类别": "购物",
                "估算依据": f"{budget_level}购物预算 × {city_factor:.2f}城市系数",
                "单价": f"¥{cost_breakdown['购物']/budget_analysis['人数']:,.0f}/人",
                "小计": f"¥{cost_breakdown['购物']:,.0f}"
            },
            {
                "类别": "其他",
                "估算依据": "保险 + 通讯 + 应急备用金",
                "单价": "固定费用",
                "小计": f"¥{cost_breakdown['其他']:,.0f}"
            }
        ]
        
        df = pd.DataFrame(explanations)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    @staticmethod
    def _display_suggestions(budget_analysis):
        """显示优化建议"""
        suggestions = budget_analysis.get('优化建议', [])
        if not suggestions:
            return
        
        st.markdown("### 💡 预算优化建议")
        
        for i, suggestion in enumerate(suggestions):
            with st.expander(f"🔍 {suggestion['类别']}优化建议 ({i+1}/{len(suggestions)})", expanded=(i==0)):
                st.markdown(f"**建议**: {suggestion['建议']}")
                st.markdown(f"**预计节省**: {suggestion['预计节省']}")
        
        # 总结
        total_savings = 0
        for suggestion in suggestions:
            if "可节省" in suggestion.get("预计节省", ""):
                try:
                    savings = float(''.join(filter(str.isdigit, suggestion["预计节省"])))
                    total_savings += savings
                except:
                    pass
        
        if total_savings > 0:
            current_total = budget_analysis['总费用']
            new_total = current_total - total_savings
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    label="当前总预算",
                    value=f"¥{current_total:,.0f}",
                    delta=f"-¥{total_savings:,.0f}",
                    delta_color="inverse"
                )
            with col2:
                st.metric(
                    label="优化后预算",
                    value=f"¥{new_total:,.0f}",
                    delta=f"-{(total_savings/current_total*100):.1f}%",
                    delta_color="inverse"
                )