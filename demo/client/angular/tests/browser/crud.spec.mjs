import { test, expect } from "@playwright/test";

const host = process.env.ARP_CRUD_HOST;
const token = process.env.ARP_CRUD_TOKEN;
const origin = process.env.ARP_DEMO_CLIENT_ORIGIN ?? "http://127.0.0.1:4173";
test.skip(!host || !token, "Requires the isolated PHP/MariaDB demo");
// Never trace a credential or record password input in screenshots/attachments.
test.use({ trace: "off", screenshot: "off", video: "off" });

const key = id => ({ components: [{ field: "id", type: "INTEGER", value: String(id) }] });
async function invoke(request, operation, inputs) {
    const response = await request.post(`${host}/demo/crud/invoke`, {
        headers: { Authorization: `Bearer ${token}`, Origin: origin },
        data: { target: "demo.items", operation, inputs },
    });
    return { status: response.status(), body: await response.json() };
}
async function enter(page, credential = token) {
    await page.goto("/");
    await page.getByTestId("runtime").selectOption("php");
    await page.getByTestId("instance-url").fill(host);
    await page.locator('[data-capability="crud"]').click();
    await page.getByTestId("crud-token").fill(credential);
    await page.getByTestId("crud-connect").click();
}
const row = (page, id) => page.getByTestId("crud-row").filter({
    has: page.locator(`[data-field="id"]`, { hasText: new RegExp(`^${id}$`) }),
});

for (const language of ["es", "en"]) {
    test(`real Angular HTTP MariaDB lifecycle and conflict handling (${language})`, async ({ page, request }, info) => {
        const initial = (await invoke(request, "LIST", { limit: 100 })).body.output.records;
        expect(initial).toHaveLength(30);
        const id = language === "es" ? "90001" : "90002";
        const errors = [];
        page.on("pageerror", error => errors.push(error.message));
        try {
            await enter(page);
            await expect(page.getByTestId("crud-row")).toHaveCount(10);
            await page.getByTestId("language").selectOption(language);
            expect(await page.getByTestId("crud-token").count()).toBe(0);
            for (const expected of [2, 3]) {
                await page.getByTestId("crud-next").click();
                await expect(page.getByTestId("crud-page")).toContainText(String(expected));
                await expect(page.getByTestId("crud-row")).toHaveCount(10);
            }
            await expect(page.getByTestId("crud-next")).toBeDisabled();
            await page.getByTestId("crud-previous").click();
            await page.getByTestId("crud-previous").click();
            await row(page, "3").getByTestId("crud-get").click();
            await expect(page.locator('[data-detail="code"]')).toHaveText("CÓDIGO-03");
            await page.getByTestId("crud-cancel").click();
            await page.getByTestId("crud-create").click();
            await page.locator('[data-input="id"]').fill(id);
            await page.locator('[data-input="code"]').fill("WEB-Á");
            await page.locator('[data-input="rating"]').fill("11");
            await page.getByTestId("crud-save").click();
            await expect(page.getByTestId("crud-result")).toContainText("INVALID_VALUE");
            await page.locator('[data-input="rating"]').fill("5");
            for (const theme of ["default", "alternative", "cyberpunk", "vintage", "high-contrast"]) {
                await page.getByTestId("theme").selectOption(theme);
                await expect(page.locator("[data-active-theme]")).toHaveAttribute("data-active-theme", theme);
                await expect(page.locator('[data-input="id"]')).toHaveValue(id);
                await expect(page.locator('[data-input="code"]')).toHaveValue("WEB-Á");
                await page.screenshot({ path: `/artifacts/browser/crud-${info.project.name}-${language}-${theme}.png`,
                    fullPage: true });
            }
            await page.getByTestId("crud-save").click();
            await expect(page.getByTestId("crud-editor")).toHaveCount(0);
            expect((await invoke(request, "GET", { key: key(id) })).body.output.record.values)
                .toEqual({ id, code: "WEB-Á", rating: "5" });
            for (let index = 0; index < 3; index++) await page.getByTestId("crud-next").click();
            await row(page, id).getByTestId("crud-get").click();
            await page.getByTestId("crud-edit").click();
            await expect(page.locator('[data-input="id"]')).toHaveAttribute("readonly");
            await page.locator('[data-input="rating"]').fill("6");
            await page.getByTestId("crud-save").click();
            await expect(page.getByTestId("crud-editor")).toHaveCount(0);
            expect((await invoke(request, "GET", { key: key(id) })).body.output.record.values)
                .toEqual({ id, code: "WEB-Á", rating: "6" });
            await row(page, id).getByTestId("crud-get").click();
            await page.getByTestId("crud-edit").click();
            await page.locator('[data-input="rating"]').fill("7");
            expect((await invoke(request, "UPDATE", { key: key(id), changes: { rating: "8" },
                baseline: { rating: "6" } })).status).toBe(200);
            await page.getByTestId("crud-save").click();
            await expect(page.getByTestId("crud-result")).toContainText("CONCURRENT_CHANGE");
            await expect(page.getByTestId("crud-save")).toBeDisabled();
            await page.getByTestId("crud-reload").click();
            await expect(page.locator('[data-detail="rating"]')).toHaveText("8");
            await page.getByTestId("crud-cancel").click();
            await row(page, id).getByTestId("crud-delete").click();
            await expect(page.getByTestId("crud-confirm-delete")).toBeDisabled();
            await expect(page.locator('[data-detail="rating"]')).toHaveText("8");
            await invoke(request, "UPDATE", { key: key(id), changes: { rating: "9" }, baseline: { rating: "8" } });
            await page.getByTestId("crud-consent").check();
            await page.getByTestId("crud-confirm-delete").click();
            await expect(page.getByTestId("crud-result")).toContainText("DEMO_DELETE_CONCURRENT_CHANGE");
            await expect(page.getByTestId("crud-confirm-delete")).toBeDisabled();
            await page.getByTestId("crud-reload").click();
            await expect(page.locator('[data-detail="rating"]')).toHaveText("9");
            await page.getByTestId("crud-cancel").click();
            await row(page, id).getByTestId("crud-delete").click();
            await expect(page.getByTestId("crud-consent")).not.toBeChecked();
            await page.getByTestId("crud-consent").check();
            await page.getByTestId("crud-confirm-delete").click();
            await expect(page.getByTestId("crud-editor")).toHaveCount(0);
            expect((await invoke(request, "GET", { key: key(id) })).body.output.found).toBe(false);
            expect((await invoke(request, "LIST", { limit: 100 })).body.output.records).toEqual(initial);
            const storage = await page.evaluate(() => [JSON.stringify(localStorage), JSON.stringify(sessionStorage)]);
            expect(storage.some(value => value.includes(token))).toBe(false);
            await page.reload();
            await page.locator('[data-capability="crud"]').click();
            await expect(page.getByTestId("crud-token")).toHaveValue("");
            expect(errors).toEqual([]);
        } finally {
            // Delete only this test's own temporary record; never touch a CSV row.
            const found = (await invoke(request, "GET", { key: key(id) })).body.output;
            if (found?.found) await invoke(request, "DELETE", { key: key(id), confirmedValues: found.record.values });
        }
    });
}

test("wrong token, unsupported runtime and disconnect never leave usable credentials", async ({ page }) => {
    await enter(page, "invalid");
    await expect(page.getByTestId("crud-result")).toContainText("DEMO_UNAUTHORIZED");
    await expect(page.getByTestId("crud-token")).toHaveValue("");
    await page.getByTestId("crud-token").fill(token);
    await page.getByTestId("crud-connect").click();
    await expect(page.getByTestId("crud-row")).toHaveCount(10);
    await page.getByTestId("runtime").selectOption("java");
    await expect(page.getByTestId("crud-token")).toHaveValue("");
    await page.getByTestId("instance-url").fill(host);
    await page.getByTestId("crud-token").fill(token);
    const credentials = [];
    page.on("request", request => {
        if (request.headers().authorization) credentials.push(request.url());
    });
    await page.getByTestId("crud-connect").click();
    await expect(page.getByTestId("crud-issue")).toContainText("compatible");
    expect(credentials).toEqual([]);
});

test("disconnect, URL changes and a real HTTP authorization rejection clear the session", async ({ page }) => {
    await enter(page);
    await expect(page.getByTestId("crud-row")).toHaveCount(10);
    await page.getByTestId("crud-disconnect").click();
    await expect(page.getByTestId("crud-token")).toHaveValue("");
    await page.getByTestId("crud-token").fill(token);
    await page.getByTestId("crud-connect").click();
    await expect(page.getByTestId("crud-row")).toHaveCount(10);
    await page.getByTestId("instance-url").fill(host + "/");
    await expect(page.getByTestId("crud-token")).toHaveValue("");
    await expect(page.getByTestId("crud-row")).toHaveCount(0);
    await page.getByTestId("crud-token").fill(token);
    await page.getByTestId("crud-connect").click();
    await expect(page.getByTestId("crud-row")).toHaveCount(10);
    // The real server rejects this request. No synthetic response substitutes for authorization.
    await page.route("**/demo/crud/invoke", route => route.continue({
        headers: { ...route.request().headers(), authorization: "Bearer revoked" },
    }));
    await page.getByTestId("crud-refresh").click();
    await expect(page.getByTestId("crud-result")).toContainText("DEMO_UNAUTHORIZED");
    await expect(page.getByTestId("crud-token")).toHaveValue("");
    await expect(page.getByTestId("crud-row")).toHaveCount(0);
});
