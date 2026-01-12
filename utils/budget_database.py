# utils/budget_database.py
"""
智能预算分析系统的核心数据库
包含全国各城市、各类型的消费水平数据
"""

class BudgetDatabase:
    """预算数据库 - 存储全国消费水平数据"""
    
    # 城市消费等级（按经济水平划分）
    CITY_COST_LEVELS = {
        "一线城市": ["北京", "上海", "深圳", "广州"],
        "新一线城市": ["成都", "杭州", "重庆", "西安", "苏州", "武汉", "南京", "天津", "郑州", "长沙", "东莞", "佛山", "宁波", "青岛", "沈阳"],
        "二线城市": ["昆明", "合肥", "福州", "厦门", "哈尔滨", "济南", "温州", "南宁", "长春", "泉州", "石家庄", "贵阳", "南昌", "金华", "常州", "南通", "嘉兴", "太原", "徐州", "惠州", "珠海"],
        "三线及以下": ["其他所有城市"]  # 默认类别
    }
    
    # 消费水平系数（基准：北京=1.0）
    CITY_COST_FACTORS = {
        "一线城市": 1.0,
        "新一线城市": 0.75,
        "二线城市": 0.6,
        "三线及以下": 0.45
    }
    
    # 预算等级定义
    BUDGET_LEVELS = {
        "经济型": {
            "description": "精打细算，性价比优先",
            "multiplier": 0.7,
            "hotel_level": "经济型",
            "food_level": "经济",
            "transport_level": "公共交通为主"
        },
        "舒适型": {
            "description": "舒适体验，合理消费",
            "multiplier": 1.0,
            "hotel_level": "舒适型",
            "food_level": "中等",
            "transport_level": "混合交通"
        },
        "豪华型": {
            "description": "高端体验，不计成本",
            "multiplier": 1.8,
            "hotel_level": "豪华型",
            "food_level": "高档",
            "transport_level": "专车/出租车"
        }
    }
    
    # 基准消费价格（以北京舒适型为基准）
    BASE_PRICES = {
        "住宿": {
            "经济型": {"单人": 150, "双人": 200, "家庭": 300},
            "舒适型": {"单人": 300, "双人": 400, "家庭": 600},
            "豪华型": {"单人": 600, "双人": 800, "家庭": 1200}
        },
        "餐饮": {
            "经济": {"早餐": 15, "午餐": 30, "晚餐": 40, "全天": 85},
            "中等": {"早餐": 30, "午餐": 60, "晚餐": 80, "全天": 170},
            "高档": {"早餐": 60, "午餐": 120, "晚餐": 160, "全天": 340}
        },
        "交通": {
            "市内": {"公交地铁": 20, "出租车": 80, "租车": 200},
            "城际": {"高铁二等座": 0.5, "飞机经济舱": 0.8},  # 元/公里
        },
        "门票": {
            "公园": 30,
            "博物馆": 60,
            "历史遗迹": 80,
            "主题公园": 200,
            "自然景观": 100,
            "动物园": 60,
            "水族馆": 120,
            "游乐园": 180
        },
        "购物": {
            "纪念品": 50,
            "特产": 100,
            "奢侈品": 1000
        },
        "其他": {
            "保险": 20,
            "通讯": 30,
            "应急": 100
        }
    }
    
    # 景点类型映射
    ATTRACTION_TYPES = {
        "公园": "公园",
        "博物馆": "博物馆", 
        "纪念馆": "博物馆",
        "展览馆": "博物馆",
        "古迹": "历史遗迹",
        "遗址": "历史遗迹",
        "古镇": "历史遗迹",
        "主题公园": "主题公园",
        "游乐场": "游乐园",
        "动物园": "动物园",
        "植物园": "公园",
        "水族馆": "水族馆",
        "海洋馆": "水族馆",
        "山": "自然景观",
        "湖": "自然景观", 
        "河": "自然景观",
        "瀑布": "自然景观",
        "海滩": "自然景观",
        "森林": "自然景观"
    }
    
    @classmethod
    def get_city_cost_level(cls, city_name):
        """获取城市消费等级"""
        for level, cities in cls.CITY_COST_LEVELS.items():
            for city in cities:
                if city in city_name:
                    return level
        return "三线及以下"
    
    @classmethod
    def get_cost_factor(cls, city_name):
        """获取城市消费系数"""
        level = cls.get_city_cost_level(city_name)
        return cls.CITY_COST_FACTORS.get(level, 0.45)
    
    @classmethod
    def get_attraction_type(cls, attraction_name):
        """识别景点类型"""
        for keyword, attraction_type in cls.ATTRACTION_TYPES.items():
            if keyword in attraction_name:
                return attraction_type
        return "公园"  # 默认类型