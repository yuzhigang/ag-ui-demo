import random
from agent_framework import tool


@tool(approval_mode="never_require")
def get_weather(city: str, date: str) -> dict:
    """查询指定城市和日期的天气（返回模拟数据）。"""
    conditions = ["晴朗", "多云", "小雨", "阴天", "雷阵雨"]
    condition = random.choice(conditions)
    temperature = random.randint(22, 35)
    return {
        "city": city,
        "date": date,
        "weather": condition,
        "temperature": f"{temperature}°C",
        "humidity": f"{random.randint(40, 90)}%",
    }


@tool(approval_mode="never_require")
def search_hotels(
    city: str, check_in: str, check_out: str, budget: str
) -> list[dict]:
    """搜索指定城市的酒店（返回模拟数据）。

    Args:
        city: 目的地城市
        check_in: 入住日期 (YYYY-MM-DD)
        check_out: 退房日期 (YYYY-MM-DD)
        budget: 预算等级，可选："经济型" | "中等预算" | "豪华"
    """
    hotels_pool = {
        "经济型": [
            {"name": f"{city}快捷酒店", "price": "¥180/晚", "rating": 3.8, "location": "市中心"},
            {"name": f"{city}青年旅舍", "price": "¥120/晚", "rating": 4.0, "location": "火车站附近"},
        ],
        "中等预算": [
            {"name": f"{city}湾假日酒店", "price": "¥580/晚", "rating": 4.6, "location": "海湾度假区"},
            {"name": f"{city}商务酒店", "price": "¥420/晚", "rating": 4.3, "location": "商业区"},
        ],
        "豪华": [
            {"name": f"{city}海景度假村", "price": "¥1800/晚", "rating": 4.9, "location": "海滨"},
            {"name": f"{city}国际大酒店", "price": "¥1200/晚", "rating": 4.8, "location": "市中心"},
        ],
    }
    budget_key = budget if budget in hotels_pool else "中等预算"
    return hotels_pool[budget_key]


@tool(approval_mode="never_require")
def search_attractions(city: str, interest: str = "") -> list[dict]:
    """搜索指定城市的景点和体验活动（返回模拟数据）。

    Args:
        city: 目的地城市
        interest: 兴趣类型，可选："自然" | "文化" | "美食" | "购物" | ""（全部）
    """
    attractions_pool = {
        "自然": [
            {"name": f"{city}国家森林公园", "type": "自然", "rating": 4.7, "duration": "半天", "description": "原始森林徒步，呼吸新鲜空气"},
            {"name": f"{city}海滨浴场", "type": "自然", "rating": 4.5, "duration": "2小时", "description": "阳光沙滩，适合游泳和日光浴"},
        ],
        "文化": [
            {"name": f"{city}古城墙", "type": "文化", "rating": 4.8, "duration": "2小时", "description": "千年历史遗迹，感受文化底蕴"},
            {"name": f"{city}博物馆", "type": "文化", "rating": 4.6, "duration": "3小时", "description": "珍贵文物展览，了解当地历史"},
        ],
        "美食": [
            {"name": f"{city}老街小吃", "type": "美食", "rating": 4.4, "duration": "2小时", "description": "地道街头美食，品尝当地特色"},
            {"name": f"{city}海鲜大排档", "type": "美食", "rating": 4.5, "duration": "2小时", "description": "新鲜海鲜，现点现做"},
        ],
        "购物": [
            {"name": f"{city}步行街", "type": "购物", "rating": 4.3, "duration": "3小时", "description": "汇聚各类品牌，购物天堂"},
            {"name": f"{city}夜市", "type": "购物", "rating": 4.6, "duration": "2小时", "description": "特色小商品，砍价乐趣"},
        ],
    }
    if interest and interest in attractions_pool:
        return attractions_pool[interest]
    # 返回所有类型的景点
    result = []
    for items in attractions_pool.values():
        result.extend(items)
    return result[:4]


@tool(approval_mode="always_require")
def book_flight(
    departure: str, arrival: str, date: str, passenger_name: str
) -> dict:
    """预订航班（需要用户确认）。

    Args:
        departure: 出发城市
        arrival: 目的城市
        date: 出发日期 (YYYY-MM-DD)
        passenger_name: 乘客姓名
    """
    flight_number = f"CA{random.randint(1000, 9999)}"
    return {
        "flight_number": flight_number,
        "departure": departure,
        "arrival": arrival,
        "date": date,
        "passenger": passenger_name,
        "status": "已确认",
        "gate": f"{random.randint(1, 50)}",
        "seat": f"{random.randint(1, 30)}{random.choice('ABCDEF')}",
    }
