"""Agent factory: builds Agent and AgentFrameworkAgent from YAML config."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from agent_framework import tool

from .config.models import (
    MemberConfig,
    ResolvedAgentConfig,
)

if TYPE_CHECKING:
    from .config.registry import ResourceRegistry

logger = logging.getLogger(__name__)


class AgentFactory:
    """Factory that constructs Agent instances from configuration."""

    def __init__(self, *, registry: ResourceRegistry) -> None:
        self._registry = registry

    def _build_member_instructions(
        self,
        base_instructions: str,
        member: MemberConfig,
    ) -> str:
        """Combine base instructions with member role context."""
        parts = [base_instructions]

        if member.role_description:
            parts.append(f"\n你在本群中的职责：{member.role_description}")

        if member.instructions_suffix:
            parts.append(f"\n{member.instructions_suffix}")

        if member.response_mode:
            mode_desc = {
                "mention_only": "你只在被@时响应。",
                "reactive": "你只在被点名时响应。",
                "proactive": "你可以主动发言。",
                "silent": "你只观察，不发言。",
            }.get(member.response_mode, "")
            if mode_desc:
                parts.append(f"\n响应规则：{mode_desc}")

        return "\n".join(parts)

    def _build_admin_instructions(self, config: ResolvedAgentConfig) -> str:
        """Build admin instructions with member list, workflows, and capabilities."""
        parts = [
            f"你是「{config.name}」的管理员，负责协调群成员协作完成用户需求。",
            "",
            "## 群成员",
            "",
        ]

        for member in config.members or []:
            desc = f"- {member.display_name or member.agent_id}({member.agent_id})"
            if member.role_description:
                desc += f"：{member.role_description}"
            parts.append(desc)

        if config.workflows:
            parts.extend(["", "## 工作流列表"])
            for wf in config.workflows:
                parts.append(f"- {wf.id}：{wf.description}")
            parts.extend([
                "",
                "工作流选择：",
                "1. 分析用户需求，判断最匹配的工作流",
                "2. 调用 load_workflow_graph(workflow_id) 加载对应工作流",
                "3. 按工作流的 graph 固定执行",
                "4. 如果不确定，先调用 list_workflows() 查看所有选项",
            ])

        if config.capabilities:
            parts.extend([
                "",
                "## 能力范围",
                "",
                config.capabilities,
                "",
                "如果用户问题超出以上范围，请直接说明无法处理。",
            ])

        parts.extend([
            "",
            "## 执行规则",
            "",
            "- 加载工作流后，严格按 graph 的 edges 执行，不要跳过或增加步骤",
            "- 单步能完成的任务不要拆解给多个成员",
            "- 同一轮对话中，同一成员最多调用一次",
        ])

        return "\n".join(parts)
