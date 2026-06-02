import { test, expect } from "@playwright/test";
import { mockAgentEndpoint } from "../helpers/mock-sse";
import { agui } from "../fixtures/agui-events";

test.describe("生成式页面渲染", () => {
  test("renders a complete grid page from render_page", async ({ page }) => {
    await mockAgentEndpoint(page, async function* () {
      yield agui.runStarted();
      yield agui.renderComponent("ProgressBar", { step: 1, total: 2 }, "progress");
      yield agui.renderPage({
        version: "1",
        title: "北京三日旅行方案",
        layout: {
          kind: "grid",
          columns: 12,
          gap: "md",
          items: [
            {
              key: "weather",
              componentId: "WeatherCard",
              span: 4,
              props: {
                city: "北京",
                temperature: "28°C",
                weather: "晴朗",
                date: "2026-06-03",
                humidity: "65%",
              },
            },
            {
              key: "hotels",
              componentId: "HotelList",
              span: 8,
              props: {
                hotels: [
                  { name: "酒店A", price: "¥580/晚", rating: 4.6, location: "市中心" },
                ],
              },
            },
            {
              key: "attractions",
              componentId: "AttractionList",
              span: 12,
              props: {
                attractions: [
                  {
                    name: "故宫",
                    type: "历史",
                    description: "明清皇家宫殿建筑群",
                    duration: "3小时",
                    rating: 4.8,
                  },
                ],
              },
            },
          ],
        },
      });
      yield agui.runFinished();
    });

    await page.goto("/");
    await page.getByPlaceholder("说点什么...").fill("北京三日旅行方案");
    await page.getByRole("button", { name: "发送" }).click();

    await expect(page.getByRole("heading", { name: "北京三日旅行方案" })).toBeVisible();
    await expect(page.getByTestId("rendered-WeatherCard")).toBeVisible();
    await expect(page.getByTestId("rendered-HotelList")).toBeVisible();
    await expect(page.getByTestId("rendered-AttractionList")).toBeVisible();
    await expect(page.getByText("1 / 2")).not.toBeVisible();
  });

  test("renders generated page items full width on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await mockAgentEndpoint(page, async function* () {
      yield agui.runStarted();
      yield agui.renderPage({
        version: "1",
        layout: {
          kind: "grid",
          columns: 12,
          items: [
            {
              key: "weather-mobile",
              componentId: "WeatherCard",
              span: 4,
              props: {
                city: "北京",
                temperature: "28°C",
                weather: "晴朗",
                date: "2026-06-03",
                humidity: "65%",
              },
            },
          ],
        },
      });
      yield agui.runFinished();
    });

    await page.goto("/");
    await page.getByPlaceholder("说点什么...").fill("移动端天气");
    await page.getByPlaceholder("说点什么...").press("Enter");

    const gridItem = page.getByTestId("page-grid-item-weather-mobile");
    await expect(gridItem).toBeVisible();
    await expect(gridItem).toHaveClass(/col-span-12/);

    const itemBox = await gridItem.boundingBox();
    const gridBox = await page.getByTestId("generated-page-grid").boundingBox();
    expect(itemBox).not.toBeNull();
    expect(gridBox).not.toBeNull();
    expect(Math.abs(itemBox!.width - gridBox!.width)).toBeLessThanOrEqual(2);
  });
});
