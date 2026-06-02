import { test, expect } from "@playwright/test";
import { mockAgentEndpoint } from "../helpers/mock-sse";
import { agui } from "../fixtures/agui-events";

test.describe("多组件与生命周期", () => {
  test("多组件同时渲染", async ({ page }) => {
    await mockAgentEndpoint(page, async function* () {
      yield agui.runStarted();
      yield agui.renderComponent("WeatherCard", { city: "北京", temperature: "28°C", weather: "晴朗", date: "2026-06-03", humidity: "65%" }, "weather-1");
      yield agui.renderComponent("HotelList", { hotels: [{ name: "酒店A", price: "¥580/晚", rating: 4.6, location: "市中心" }] }, "hotels-1");
      yield agui.runFinished();
    });

    await page.goto("/");
    await page.getByPlaceholder("说点什么...").fill("规划行程");
    await page.getByRole("button", { name: "发送" }).click();

    await expect(page.getByTestId("rendered-WeatherCard")).toBeVisible();
    await expect(page.getByTestId("rendered-HotelList")).toBeVisible();
  });

  test("组件更新", async ({ page }) => {
    await mockAgentEndpoint(page, async function* () {
      yield agui.runStarted();
      yield agui.renderComponent("ProgressBar", { step: 1, total: 3 }, "progress");
      yield agui.updateComponent("ProgressBar", { step: 2, total: 3 }, "progress");
      yield agui.updateComponent("ProgressBar", { step: 3, total: 3 }, "progress");
      yield agui.runFinished();
    });

    await page.goto("/");
    await page.getByPlaceholder("说点什么...").fill("开始规划");
    await page.getByRole("button", { name: "发送" }).click();

    await expect(page.getByText("3 / 3")).toBeVisible();
  });

  test("组件卸载", async ({ page }) => {
    await mockAgentEndpoint(page, async function* () {
      yield agui.runStarted();
      yield agui.renderComponent("WeatherCard", { city: "北京", temperature: "28°C", weather: "晴朗", date: "2026-06-03", humidity: "65%" }, "weather-1");
      yield agui.unmountComponent("weather-1");
      yield agui.runFinished();
    });

    await page.goto("/");
    await page.getByPlaceholder("说点什么...").fill("测试卸载");
    await page.getByRole("button", { name: "发送" }).click();

    await expect(page.getByTestId("rendered-WeatherCard")).not.toBeVisible();
  });
});
