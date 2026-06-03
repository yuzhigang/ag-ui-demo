import logging
import os

import uvicorn
from agent_framework.ag_ui import add_agent_framework_fastapi_endpoint
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .ui.agui_runtime import AGUIPageRuntime
from .workflow import COMPONENT_CATALOG, create_travel_workflow

load_dotenv()

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="旅行规划 AG-UI Demo",
        description="Microsoft Agent Framework + AG-UI 多 Agent 工作流演示",
        version="0.1.0",
    )

    cors_origins = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    travel_agent = AGUIPageRuntime(
        create_travel_workflow(),
        catalog=COMPONENT_CATALOG,
    )

    add_agent_framework_fastapi_endpoint(
        app=app,
        agent=travel_agent,
        path="/api/agent",
    )

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    print(f"AG-UI demo backend running at http://{host}:{port}")
    print(f"AG-UI endpoint: POST /api/agent")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
