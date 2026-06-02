export function sseEvent(data: object): string {
  return `data: ${JSON.stringify(data)}\n\n`;
}

export const agui = {
  runStarted: () => sseEvent({ type: "RUN_STARTED" }),

  textDelta: (delta: string) =>
    sseEvent({ type: "TEXT_MESSAGE_CONTENT", delta }),

  textEnd: () => sseEvent({ type: "TEXT_MESSAGE_END" }),

  toolCallStart: (id: string, name: string) =>
    sseEvent({ type: "TOOL_CALL_START", toolCallId: id, toolCallName: name }),

  toolCallResult: (id: string, content: unknown) =>
    sseEvent({ type: "TOOL_CALL_RESULT", toolCallId: id, content }),

  renderComponent: (component: string, props: object, key?: string) =>
    sseEvent({
      type: "CUSTOM",
      name: "render_component",
      value: { component, props, key, action: "mount" },
    }),

  updateComponent: (component: string, props: object, key: string) =>
    sseEvent({
      type: "CUSTOM",
      name: "render_component",
      value: { component, props, key, action: "update" },
    }),

  unmountComponent: (key: string) =>
    sseEvent({
      type: "CUSTOM",
      name: "render_component",
      value: { key, action: "unmount" },
    }),

  runFinished: () => sseEvent({ type: "RUN_FINISHED" }),
};
