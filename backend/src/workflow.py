from datetime import date, timedelta

from agent_framework import Agent
from agent_framework.ag_ui import AgentFrameworkAgent

from .agents import chat_client
from .tools import book_flight, get_weather, search_attractions, search_hotels


def _build_instructions() -> str:
    today = date.today()
    tomorrow = today + timedelta(days=1)
    day_after_tomorrow = today + timedelta(days=2)

    return (
        "你是旅行规划助手，专门帮助用户规划旅行。\n"
        "\n"
        f"今天是 {today.isoformat()}。\n"
        f"明天是 {tomorrow.isoformat()}。\n"
        f"后天是 {day_after_tomorrow.isoformat()}。\n"
        "\n"
        "你的工作流程：\n"
        "1. 热情问候用户，了解他们的旅行目的地和日期\n"
        "2. 如果需要天气信息，调用 get_weather(city, date) 查询天气\n"
        "3. 如果需要酒店信息，调用 search_hotels(city, check_in, check_out, budget) 搜索酒店\n"
        "4. 如果需要景点推荐，调用 search_attractions(city, interest) 搜索景点\n"
        "5. 如果用户想预订航班，不要询问确认，直接调用 book_flight(departure, arrival, date, passenger_name) 工具，系统会自动处理用户确认流程\n"
        "6. 根据收集到的信息，给出完整的旅行建议\n"
        "7. 最后以友好的方式结束对话\n"
        "\n"
        "日期处理规则（非常重要）：\n"
        "- 所有工具要求的日期格式为 YYYY-MM-DD\n"
        "- 如果用户说'明天'，使用明天日期\n"
        "- 如果用户说'后天'，使用后天日期\n"
        "- 如果用户说'今天'，使用今天日期\n"
        "- 如果用户说'下周'，使用今天日期 + 7 天\n"
        "- 如果用户只说了月份和日期（如'5月25日'），默认使用今年\n"
        "- 绝不要将'明天'、'后天'等相对日期直接传给工具\n"
        "\n"
        "注意事项：\n"
        "- 酒店预算默认为'中等预算'，除非用户特别说明\n"
        "- 景点兴趣默认为空字符串，返回所有类型\n"
        "- book_flight 工具设置了自动确认流程，你只需直接调用，不要在文本中询问用户是否确认\n"
        "- 保持回答简洁友好，使用中文"
    )


def create_travel_workflow():
    """构建旅行规划 Agent，使用 AgentFrameworkAgent 展示更多 AG-UI 事件。"""
    travel_agent = Agent(
        id="travel_agent",
        name="travel_agent",
        instructions=_build_instructions(),
        client=chat_client,
        tools=[get_weather, search_hotels, search_attractions, book_flight],
    )

    # 使用 AgentFrameworkAgent 启用 STATE_SNAPSHOT / STATE_DELTA 事件
    return AgentFrameworkAgent(
        agent=travel_agent,
        name="TravelPlanner",
        description="旅行规划 Agent 工作流演示",
        state_schema={
            "itinerary": {
                "type": "object",
                "description": "当前行程信息",
            },
            "tools_called": {
                "type": "array",
                "description": "已调用的工具列表",
            },
        },
        # predict_state_config 会触发 STATE_DELTA 事件，
        # 但当前版本需要 tool_argument 为有效字符串，暂时注释
        # predict_state_config={
        #     "itinerary": {
        #         "tool": "search_hotels",
        #         "tool_argument": "city",
        #     },
        # },
    )
