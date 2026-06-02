import type { Page } from "@playwright/test";

export async function mockAgentEndpoint(
  page: Page,
  eventGenerator: () => AsyncGenerator<string>
) {
  await page.route("/api/agent", async (route) => {
    const events: string[] = [];
    for await (const event of eventGenerator()) {
      events.push(event);
    }
    const body = events.join("");

    route.fulfill({
      status: 200,
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
      },
      body,
    });
  });
}
