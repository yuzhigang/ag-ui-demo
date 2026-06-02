import { test, expect } from "@playwright/test";
import { mockAgentEndpoint } from "../helpers/mock-sse";
import { agui } from "../fixtures/agui-events";

test.describe("错误处理", () => {
  test("未注册组件显示占位符", async ({ page }) => {
    await mockAgentEndpoint(page, async function* () {
      yield agui.runStarted();
      yield agui.renderComponent("UnknownWidget", { data: "test" });
      yield agui.runFinished();
    });

    await page.goto("/");
    await page.getByPlaceholder("说点什么...").fill("测试");
    await page.getByRole("button", { name: "发送" }).click();

    await expect(page.getByText("未知组件: UnknownWidget")).toBeVisible();
  });

  test("update 先于 mount（相同 key）等价于 mount", async ({ page }) => {
    await mockAgentEndpoint(page, async function* () {
      yield agui.runStarted();
      yield agui.updateComponent("WeatherCard", { city: "北京", temperature: "28°C", weather: "晴朗", date: "2026-06-03", humidity: "65%" }, "weather-1");
      yield agui.runFinished();
    });

    await page.goto("/");
    await page.getByPlaceholder("说点什么...").fill("测试");
    await page.getByRole("button", { name: "发送" }).click();

    await expect(page.getByTestId("rendered-WeatherCard")).toBeVisible();
  });

  test("unmount 不存在的 key 静默忽略", async ({ page }) => {
    await mockAgentEndpoint(page, async function* () {
      yield agui.runStarted();
      yield agui.unmountComponent("nonexistent");
      yield agui.renderComponent("WeatherCard", { city: "北京", temperature: "28°C", weather: "晴朗", date: "2026-06-03", humidity: "65%" });
      yield agui.runFinished();
    });

    await page.goto("/");
    await page.getByPlaceholder("说点什么...").fill("测试");
    await page.getByRole("button", { name: "发送" }).click();

    await expect(page.getByTestId("rendered-WeatherCard")).toBeVisible();
  });
});
