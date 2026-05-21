import type { AgentStatus } from "../types";

interface AgentStatusProps {
  status: AgentStatus;
  activeTool?: string | null;
  toolArgs?: string;
}

export default function AgentStatusBar({ status, activeTool, toolArgs }: AgentStatusProps) {
  const statusConfig: Record<
    AgentStatus,
    { text: string; color: string; dot: string }
  > = {
    idle: { text: "等待输入", color: "bg-gray-100 text-gray-600", dot: "bg-gray-400" },
    thinking: { text: "思考中...", color: "bg-blue-50 text-blue-700", dot: "bg-blue-500 animate-pulse" },
    tool_call: { text: activeTool ? `正在调用: ${activeTool}...` : "正在调用工具...", color: "bg-amber-50 text-amber-700", dot: "bg-amber-500 animate-pulse" },
    error: { text: "出错了", color: "bg-red-50 text-red-700", dot: "bg-red-500" },
    interrupt: { text: "等待确认", color: "bg-orange-50 text-orange-700", dot: "bg-orange-500 animate-pulse" },
  };

  const config = statusConfig[status];

  return (
    <div className="flex flex-col items-end gap-1">
      <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium ${config.color} border shadow-sm`}>
        <span className={`w-2 h-2 rounded-full ${config.dot}`} />
        <span>{config.text}</span>
      </div>
      {status === "tool_call" && toolArgs && (
        <p className="text-xs text-gray-400 font-mono max-w-xs truncate">
          参数: {toolArgs}
        </p>
      )}
    </div>
  );
}
