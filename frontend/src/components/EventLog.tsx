import { useState } from "react";
import type { AGUIEvent } from "../types";

interface EventLogProps {
  events: AGUIEvent[];
  onClear?: () => void;
}

const eventTypeColors: Record<string, string> = {
  RUN_STARTED: "bg-emerald-50 text-emerald-700 border-emerald-200",
  TEXT_MESSAGE_START: "bg-blue-50 text-blue-700 border-blue-200",
  TEXT_MESSAGE_CONTENT: "bg-sky-50 text-sky-700 border-sky-200",
  TEXT_MESSAGE_END: "bg-blue-50 text-blue-700 border-blue-200",
  TOOL_CALL_START: "bg-amber-50 text-amber-700 border-amber-200",
  TOOL_CALL_ARGS: "bg-yellow-50 text-yellow-700 border-yellow-200",
  TOOL_CALL_END: "bg-amber-50 text-amber-700 border-amber-200",
  CUSTOM: "bg-purple-50 text-purple-700 border-purple-200",
  STATE_SNAPSHOT: "bg-pink-50 text-pink-700 border-pink-200",
  STATE_DELTA: "bg-rose-50 text-rose-700 border-rose-200",
  MESSAGES_SNAPSHOT: "bg-indigo-50 text-indigo-700 border-indigo-200",
  RUN_FINISHED: "bg-emerald-50 text-emerald-700 border-emerald-200",
  RUN_ERROR: "bg-red-50 text-red-700 border-red-200",
  INTERRUPT: "bg-orange-50 text-orange-700 border-orange-200",
};

function formatTime(ts: number): string {
  const d = new Date(ts);
  return `${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}:${d.getSeconds().toString().padStart(2, "0")}.${d.getMilliseconds().toString().padStart(3, "0")}`;
}

function EventPayload({ raw }: { raw: Record<string, unknown> }) {
  const [expanded, setExpanded] = useState(false);
  const preview = JSON.stringify(raw).slice(0, 120);
  const isLong = JSON.stringify(raw).length > 120;

  if (!expanded) {
    return (
      <button
        onClick={() => setExpanded(true)}
        className="text-left text-xs font-mono text-gray-500 mt-1 hover:text-gray-700 w-full"
      >
        {isLong ? `${preview}...` : preview}
        {isLong && <span className="text-blue-500 ml-1">[展开]</span>}
      </button>
    );
  }

  return (
    <div className="mt-1">
      <button
        onClick={() => setExpanded(false)}
        className="text-xs text-blue-500 hover:text-blue-700 mb-1"
      >
        [收起]
      </button>
      <pre className="text-xs font-mono text-gray-600 bg-gray-50 rounded p-2 overflow-x-auto">
        {JSON.stringify(raw, null, 2)}
      </pre>
    </div>
  );
}

export default function EventLog({ events, onClear }: EventLogProps) {
  const [filter, setFilter] = useState<string>("all");
  const [autoScroll, setAutoScroll] = useState(true);

  const filtered =
    filter === "all"
      ? events
      : events.filter((e) => e.type === filter);

  const eventTypes = Array.from(new Set(events.map((e) => e.type))).sort();

  return (
    <div className="flex flex-col h-full border rounded-xl bg-white shadow-sm overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b bg-gray-50">
        <h2 className="text-sm font-semibold text-gray-700">AG-UI 事件流</h2>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-1 text-xs text-gray-500 cursor-pointer">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              className="rounded"
            />
            自动滚动
          </label>
          {onClear && (
            <button
              onClick={onClear}
              className="text-xs text-gray-500 hover:text-red-500 transition-colors"
            >
              清除
            </button>
          )}
          <span className="text-xs text-gray-400">{events.length} 事件</span>
        </div>
      </div>

      <div className="px-3 py-2 border-b flex gap-1 flex-wrap">
        <button
          onClick={() => setFilter("all")}
          className={`text-xs px-2 py-0.5 rounded-full transition-colors ${
            filter === "all"
              ? "bg-gray-800 text-white"
              : "bg-gray-100 text-gray-600 hover:bg-gray-200"
          }`}
        >
          全部
        </button>
        {eventTypes.map((type) => (
          <button
            key={type}
            onClick={() => setFilter(type)}
            className={`text-xs px-2 py-0.5 rounded-full transition-colors ${
              filter === type
                ? "bg-gray-800 text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {type}
          </button>
        ))}
      </div>

      <div
        className="flex-1 overflow-y-auto p-2 space-y-1"
        ref={(el) => {
          if (el && autoScroll) {
            el.scrollTop = el.scrollHeight;
          }
        }}
      >
        {filtered.length === 0 && (
          <p className="text-xs text-gray-400 text-center py-8">暂无事件</p>
        )}
        {filtered.map((event) => {
          const colorClass =
            eventTypeColors[event.type] ||
            "bg-gray-50 text-gray-700 border-gray-200";
          return (
            <div
              key={event.id}
              className={`border rounded-lg px-2.5 py-1.5 ${colorClass}`}
            >
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono opacity-60">
                  {formatTime(event.timestamp)}
                </span>
                <span className="text-xs font-semibold">{event.type}</span>
              </div>
              <EventPayload raw={event.raw} />
            </div>
          );
        })}
      </div>
    </div>
  );
}
