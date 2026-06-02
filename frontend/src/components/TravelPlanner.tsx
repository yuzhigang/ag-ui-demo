import { useCallback, useRef, useState } from "react";
import type { AgentStatus, AGUIEvent, ChatMessage, InterruptRequest, Itinerary } from "../types";
import AgentStatusBar from "./AgentStatus";
import ChatPanel from "./ChatPanel";
import EventLog from "./EventLog";
import InterruptPanel from "./InterruptPanel";
import ItineraryCard from "./ItineraryCard";
import { useAGUIRenderer, AGUIComponentTree } from "./AGUIRenderer";
import { PageRenderer } from "./page/PageRenderer";
import type { PageSpec } from "./page/PageSpec";

const AGENT_URL = (import.meta as any).env?.VITE_AGENT_URL || "/api/agent";

interface SSEEvent {
  type: string;
  [key: string]: unknown;
}

function parseSSEEvent(line: string): SSEEvent | null {
  if (!line.startsWith("data: ")) return null;
  try {
    return JSON.parse(line.slice(6));
  } catch {
    return null;
  }
}

let eventCounter = 0;

export function getRenderComponentId(value: Record<string, unknown>): string {
  return (value.componentId || value.component || "") as string;
}

export function shouldClearPageForRenderComponentAction(action: string): boolean {
  return action !== "unmount";
}

export default function TravelPlanner() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [status, setStatus] = useState<AgentStatus>("idle");
  const [itinerary, setItinerary] = useState<Itinerary>({});
  const [currentResponse, setCurrentResponse] = useState("");
  const [activeTool, setActiveTool] = useState<string | null>(null);
  const [events, setEvents] = useState<AGUIEvent[]>([]);
  const [toolArgs, setToolArgs] = useState<string>("");
  const [interrupts, setInterrupts] = useState<InterruptRequest[]>([]);
  const [currentPage, setCurrentPage] = useState<PageSpec | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const { items: renderedItems, render: handleRenderComponent, clear: clearRendered } = useAGUIRenderer();

  const addEvent = useCallback((type: string, raw: Record<string, unknown>) => {
    const event: AGUIEvent = {
      id: `evt-${++eventCounter}`,
      timestamp: Date.now(),
      type,
      raw,
    };
    setEvents((prev) => [...prev, event]);
  }, []);

  const handleSend = useCallback(async (userText: string, resumePayload?: Record<string, unknown>) => {
    if (abortRef.current) {
      abortRef.current.abort();
    }
    abortRef.current = new AbortController();

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: userText,
    };
    if (!resumePayload) {
      setMessages((prev) => [...prev, userMsg]);
    }
    setStatus("thinking");
    setCurrentResponse("");
    setActiveTool(null);
    setToolArgs("");
    setInterrupts([]);

    // 构建 resume 时需要补充 assistant tool_call 消息，否则后端无法匹配 approval
    const resumeToolCalls: Array<{
      id: string;
      role: string;
      content?: string;
      tool_calls: Array<{ id: string; type: string; function: { name: string; arguments: string } }>;
    }> = [];
    if (resumePayload) {
      const resume = (resumePayload as any).resume;
      const interrupts = resume?.interrupts || [];
      for (const interrupt of interrupts) {
        const fn = interrupt?.value?.function_call;
        if (fn?.call_id) {
          resumeToolCalls.push({
            id: crypto.randomUUID(),
            role: "assistant",
            tool_calls: [
              {
                id: fn.call_id,
                type: "function",
                function: {
                  name: fn.name,
                  arguments:
                    typeof fn.arguments === "string"
                      ? fn.arguments
                      : JSON.stringify(fn.arguments),
                },
              },
            ],
          });
        }
      }
    }

    const allMessages = resumePayload
      ? [
          ...messages.map((m) => ({ id: m.id, role: m.role, content: m.content })),
          ...resumeToolCalls,
        ]
      : [
          ...messages.map((m) => ({
            id: m.id,
            role: m.role,
            content: m.content,
          })),
          { id: userMsg.id, role: "user" as const, content: userText },
        ];

    let assistantContent = "";
    const openToolCalls = new Map<string, string>();

    try {
      const res = await fetch(AGENT_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
        body: JSON.stringify({
          threadId: "travel-demo-thread",
          messages: allMessages,
          ...(resumePayload || {}),
        }),
        signal: abortRef.current.signal,
      });

      if (!res.body) {
        throw new Error("No response body");
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;

          const event = parseSSEEvent(trimmed);
          if (!event) continue;

          // 记录所有事件到日志
          addEvent(event.type, event as Record<string, unknown>);

          switch (event.type) {
            case "RUN_STARTED":
              setStatus("thinking");
              openToolCalls.clear();
              clearRendered();  // 新对话轮次清空已有渲染组件
              break;

            case "TEXT_MESSAGE_START":
              break;

            case "TEXT_MESSAGE_CONTENT": {
              const delta = (event.delta as string) || "";
              assistantContent += delta;
              setCurrentResponse(assistantContent);
              break;
            }

            case "TEXT_MESSAGE_END":
              if (assistantContent) {
                const content = assistantContent;
                setMessages((prev) => [
                  ...prev,
                  { id: crypto.randomUUID(), role: "assistant", content },
                ]);
                setCurrentResponse("");
                assistantContent = "";
              }
              break;

            case "TOOL_CALL_START": {
              const toolCallId = (event.toolCallId as string) || "";
              const toolCallName = (event.toolCallName as string) || "";
              openToolCalls.set(toolCallId, toolCallName);
              setStatus("tool_call");
              setActiveTool(toolCallName);
              setToolArgs("");
              break;
            }

            case "TOOL_CALL_ARGS": {
              const delta = (event.delta as string) || "";
              setToolArgs((prev) => prev + delta);
              break;
            }

            case "TOOL_CALL_END": {
              // 不在这里删除 openToolCalls，因为 TOOL_CALL_RESULT 可能稍后到达
              // 需要保留 callId -> toolName 的映射来解析结果
              if (openToolCalls.size === 0) {
                setStatus("thinking");
                setActiveTool(null);
              }
              break;
            }

            case "TOOL_CALL_RESULT": {
              const toolCallId = (event.toolCallId as string) || "";
              const toolName = openToolCalls.get(toolCallId) || "";
              // AG-UI TOOL_CALL_RESULT 结果在 content 字段中
              const resultRaw = (event.content as string | object) || "";
              try {
                const result =
                  typeof resultRaw === "string" ? JSON.parse(resultRaw) : resultRaw;
                if (toolName === "get_weather" && result?.city) {
                  setItinerary((prev) => ({
                    ...prev,
                    city: result.city,
                    weather: result,
                  }));
                } else if (toolName === "search_hotels" && Array.isArray(result)) {
                  setItinerary((prev) => ({ ...prev, hotels: result }));
                } else if (toolName === "search_attractions" && Array.isArray(result)) {
                  setItinerary((prev) => ({ ...prev, attractions: result }));
                } else if (toolName === "book_flight" && result?.flight_number) {
                  setItinerary((prev) => ({ ...prev, flight: result }));
                }
              } catch {
              }
              openToolCalls.delete(toolCallId);
              if (openToolCalls.size === 0) {
                setStatus("thinking");
                setActiveTool(null);
              }
              break;
            }

            case "CUSTOM": {
              const name = (event.name as string) || "";
              if (name === "render_component") {
                const value = event.value as Record<string, unknown>;
                const action = (value.action as string) || "mount";
                const componentId = getRenderComponentId(value);
                if (action === "unmount") {
                  handleRenderComponent({
                    componentId: "",
                    props: {},
                    key: value.key as string,
                    action: "unmount",
                  });
                } else {
                  if (shouldClearPageForRenderComponentAction(action)) {
                    setCurrentPage(null);
                  }
                  handleRenderComponent({
                    componentId,
                    props: (value.props as Record<string, unknown>) || {},
                    key: value.key as string | undefined,
                    action: action as "mount" | "update",
                  });
                }
              } else if (name === "render_page") {
                setCurrentPage(event.value as PageSpec);
                clearRendered();
              } else if (name === "workflow_output") {
                const value = event.value as any;
                const contents = value?.contents || [];
                for (const content of contents) {
                  if (content.type === "function_result" && content.result) {
                    const callId = content.call_id;
                    const toolName = openToolCalls.get(callId) || "";
                    try {
                      const result =
                        typeof content.result === "string"
                          ? JSON.parse(content.result)
                          : content.result;
                      if (toolName === "get_weather" && result?.city) {
                        setItinerary((prev) => ({
                          ...prev,
                          city: result.city,
                          weather: result,
                        }));
                      } else if (
                        toolName === "search_hotels" &&
                        Array.isArray(result)
                      ) {
                        setItinerary((prev) => ({
                          ...prev,
                          hotels: result,
                        }));
                      } else if (
                        toolName === "search_attractions" &&
                        Array.isArray(result)
                      ) {
                        setItinerary((prev) => ({
                          ...prev,
                          attractions: result,
                        }));
                      } else if (toolName === "book_flight" && result?.flight_number) {
                        setItinerary((prev) => ({
                          ...prev,
                          flight: result,
                        }));
                      }
                    } catch {
                      // ignore parse errors
                    }
                    openToolCalls.delete(callId);
                  }
                }
                if (openToolCalls.size === 0) {
                  setStatus("thinking");
                  setActiveTool(null);
                }
              }
              break;
            }

            case "STATE_SNAPSHOT": {
              const snapshot = event.snapshot as Record<string, unknown> | undefined;
              if (snapshot?.itinerary) {
                setItinerary((prev) => ({
                  ...prev,
                  ...(snapshot.itinerary as Itinerary),
                }));
              }
              break;
            }

            case "STATE_DELTA": {
              const delta = event.delta as Array<{ op: string; path: string; value: unknown }> | undefined;
              if (delta) {
                for (const patch of delta) {
                  if (patch.op === "replace" && patch.path === "/itinerary") {
                    setItinerary((prev) => ({
                      ...prev,
                      ...(patch.value as Itinerary),
                    }));
                  }
                }
              }
              break;
            }

            case "INTERRUPT": {
              setStatus("interrupt");
              break;
            }

            case "RUN_FINISHED": {
              const finishedInterrupts = event.interrupt as InterruptRequest[] | undefined;
              if (finishedInterrupts && finishedInterrupts.length > 0) {
                setStatus("interrupt");
                setInterrupts(finishedInterrupts);
              } else {
                setStatus("idle");
                if (assistantContent) {
                  const content = assistantContent;
                  setMessages((prev) => [
                    ...prev,
                    { id: crypto.randomUUID(), role: "assistant", content },
                  ]);
                  setCurrentResponse("");
                  assistantContent = "";
                }
              }
              break;
            }

            case "RUN_ERROR": {
              const msg = (event.message as string) || "Agent run failed";
              console.error("Run error:", msg);
              setStatus("error");
              break;
            }
          }
        }
      }
    } catch (err) {
      if ((err as Error).name === "AbortError") return;
      console.error("Request error:", err);
      setStatus("error");
    } finally {
      abortRef.current = null;
    }
  }, [messages, addEvent]);

  const clearEvents = useCallback(() => {
    setEvents([]);
  }, []);

  const handleConfirmInterrupt = useCallback((interrupt: InterruptRequest) => {
    const fn = interrupt.value?.function_call;
    if (!fn) return;
    const resumePayload = {
      resume: {
        interrupts: [
          {
            id: interrupt.id,
            value: {
              accepted: true,
              function_call: {
                call_id: fn.call_id,
                name: fn.name,
                arguments: fn.arguments,
              },
            },
          },
        ],
      },
    };
    setInterrupts([]);
    handleSend("__RESUME__", resumePayload);
  }, [handleSend]);

  const handleRejectInterrupt = useCallback((interrupt: InterruptRequest) => {
    const fn = interrupt.value?.function_call;
    if (!fn) return;
    const resumePayload = {
      resume: {
        interrupts: [
          {
            id: interrupt.id,
            value: {
              accepted: false,
              function_call: {
                call_id: fn.call_id,
                name: fn.name,
                arguments: fn.arguments,
              },
            },
          },
        ],
      },
    };
    setInterrupts([]);
    handleSend("__RESUME__", resumePayload);
  }, [handleSend]);

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-slate-50 to-gray-100">
      {/* Interrupt Overlay */}
      <InterruptPanel
        interrupts={interrupts}
        onConfirm={handleConfirmInterrupt}
        onReject={handleRejectInterrupt}
      />

      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3 bg-white/80 backdrop-blur border-b shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-md">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064" />
            </svg>
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-800">旅行规划助手</h1>
            <p className="text-xs text-gray-500">Powered by Microsoft Agent Framework + AG-UI</p>
          </div>
        </div>
        <AgentStatusBar status={status} activeTool={activeTool} toolArgs={toolArgs} />
      </header>

      {/* Main Content */}
      <div className="flex-1 flex flex-col md:flex-row gap-4 p-4 overflow-y-auto md:overflow-hidden min-h-0">
        {/* Chat Panel */}
        <div className="flex-1 flex flex-col min-w-0 min-h-[520px] md:min-h-0">
          <div className="flex-1 min-h-0 overflow-y-auto">
            <ChatPanel
              messages={messages}
              currentResponse={currentResponse}
              onSend={handleSend}
            />
          </div>
          {/* 生成式 UI 渲染区域 */}
          <div className="max-h-[40%] overflow-y-auto border-t border-gray-200">
            <AGUIComponentTree items={renderedItems} />
            <PageRenderer page={currentPage} />
          </div>
        </div>

        {/* Right Sidebar */}
        <div className="w-full md:w-96 flex flex-col gap-4 min-h-[360px] md:min-h-0 md:overflow-hidden">
          <ItineraryCard itinerary={itinerary} />
          <div className="flex-1 min-h-0">
            <EventLog events={events} onClear={clearEvents} />
          </div>
        </div>
      </div>
    </div>
  );
}
