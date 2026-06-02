import { test, expect } from "@playwright/test";
import { mockAgentEndpoint } from "../helpers/mock-sse";
import { agui } from "../fixtures/agui-events";

test.describe("单组件渲染", () => {
  test("天气卡片", async ({ page }) => {
    await mockAgentEndpoint(page, async function* () {
      yield agui.runStarted();
      yield agui.textDelta("正在为您查询天气...");
      yield agui.toolCallStart("call_1", "get_weather");
      yield agui.toolCallResult("call_1", { city: "北京", temperature: "28°C" });
      yield agui.renderComponent("WeatherCard", {
        city: "北京",
        temperature: "28°C",
        weather: "晴朗",
        date: "2026-06-03",
        humidity: "65%",
      });
      yield agui.textEnd();
      yield agui.runFinished();
    });

    await page.goto("/");
    await page.getByPlaceholder("说点什么...").fill("北京天气");
    await page.getByRole("button", { name: "发送" }).click();

    const card = page.getByTestId("rendered-WeatherCard");
    await expect(card).toBeVisible();
    await expect(card.getByText("北京")).toBeVisible();
    await expect(card.getByText("28°C")).toBeVisible();
  });

  test("RUN_STARTED 清空已有组件", async ({ page }) => {
    await mockAgentEndpoint(page, async function* () {
      yield agui.runStarted();
      yield agui.renderComponent("WeatherCard", { city: "北京", temperature: "28°C", weather: "晴朗", date: "2026-06-03", humidity: "65%" });
      yield agui.runFinished();
    });

    await page.goto("/");
    await page.getByPlaceholder("说点什么...").fill("第一次");
    await page.getByRole("button", { name: "发送" }).click();
    await expect(page.getByTestId("rendered-WeatherCard")).toBeVisible();

    // 第二次对话，RUN_STARTED 应清空
    await mockAgentEndpoint(page, async function* () {
      yield agui.runStarted();
      yield agui.runFinished();
    });
    await page.getByPlaceholder("说点什么...").fill("第二次");
    await page.getByRole("button", { name: "发送" }).click();
    await expect(page.getByTestId("rendered-WeatherCard")).not.toBeVisible();
  });
});
