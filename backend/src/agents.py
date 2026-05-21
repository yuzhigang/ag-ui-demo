import os
from agent_framework import Agent
from agent_framework.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

from .tools import get_weather, search_hotels

load_dotenv()

chat_client = OpenAIChatCompletionClient(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
    model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
)


triage_agent = Agent(
    id="triage_agent",
    name="triage_agent",
    instructions=(
        "你是旅行规划助手的调度员。你的任务是理解用户需求并路由到正确的专家。\n"
        "路由规则：\n"
        "1. 如果用户提到天气、气温、下雨等，转交给 weather_agent。\n"
        "2. 如果用户提到酒店、住宿、宾馆等，转交给 hotel_agent。\n"
        "3. 如果天气和酒店信息都已收集完毕，转交给 summary_agent 生成旅行计划。\n"
        "4. 不要重复询问已确认的信息。\n"
        "5. 每次只处理一个请求，完成后再处理下一个。"
    ),
    client=chat_client,
    require_per_service_call_history_persistence=True,
)


weather_agent = Agent(
    id="weather_agent",
    name="weather_agent",
    instructions=(
        "你是天气查询专家。\n"
        "1. 从用户对话中提取目的地城市和日期。\n"
        "2. 调用 get_weather(city, date) 查询天气。\n"
        "3. 向用户汇报天气结果。\n"
        "4. 完成后将对话交回 triage_agent。"
    ),
    client=chat_client,
    tools=[get_weather],
    require_per_service_call_history_persistence=True,
)


hotel_agent = Agent(
    id="hotel_agent",
    name="hotel_agent",
    instructions=(
        "你是酒店推荐专家。\n"
        "1. 从用户对话中提取目的地城市、入住日期、退房日期。\n"
        "2. 确定预算等级：如果用户说便宜/经济/省钱→'经济型'；"
        "如果用户说中等/一般/普通→'中等预算'；如果用户说高档/豪华/贵→'豪华'。\n"
        "3. 调用 search_hotels(city, check_in, check_out, budget) 搜索酒店。\n"
        "4. 向用户展示 1-2 家推荐酒店。\n"
        "5. 完成后将对话交回 triage_agent。"
    ),
    client=chat_client,
    tools=[search_hotels],
    require_per_service_call_history_persistence=True,
)


summary_agent = Agent(
    id="summary_agent",
    name="summary_agent",
    instructions=(
        "你是旅行计划整合专家。\n"
        "1. 根据已收集的天气信息和酒店信息，生成完整的旅行计划。\n"
        "2. 计划应包含：目的地、日期范围、天气情况、推荐酒店。\n"
        "3. 以友好、有条理的方式呈现计划。\n"
        "4. 最后说'旅行计划已生成，祝您旅途愉快！'结束对话。"
    ),
    client=chat_client,
    require_per_service_call_history_persistence=True,
)
