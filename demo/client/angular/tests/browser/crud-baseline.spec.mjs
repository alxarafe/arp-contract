import { test, expect } from "@playwright/test";
import { mockCrud, metadata, info, record, integer, decimal, gate } from "./fixtures/crud-baseline.mjs";

// These are browser/mock boundary tests. Real SQL evidence lives in crud.spec.mjs's opt-in workflow.
const input = (page, name) => page.locator(`[data-input="${name}"]`);
const nullToggle = (page, name) => page.locator(`[data-field-editor="${name}"]`).getByRole("checkbox");
async function edit(page) {
    await expect(page.getByTestId("crud-row")).toHaveCount(1);
    await page.getByTestId("crud-get").click();
    await page.getByTestId("crud-edit").click();
}

for (const capabilities of [[], ["crud.metadata"], ["crud.invoke"]]) {
    test(`mock partial capabilities withhold credentials and CRUD: ${capabilities}`, async ({ page }) => {
        const fixture = await mockCrud(page, { info: { ...info, capabilities } });
        await fixture.enter();
        await expect(page.getByTestId("crud-issue")).toBeVisible();
        expect(fixture.calls.map(call => call.kind)).toEqual(["info"]);
        expect(fixture.calls[0].headers.authorization).toBeUndefined();
        await expect(page.getByTestId("crud-token")).toHaveValue("");
        await expect(page.getByTestId("crud-row")).toHaveCount(0);
    });
}

test("mock malformed metadata renders no partial form or operations", async ({ page }) => {
    const invalid = { ...metadata, fields: [...metadata.fields, metadata.fields[0]] };
    const fixture = await mockCrud(page, { metadata: invalid });
    await fixture.enter();
    await expect(page.getByTestId("crud-issue")).toBeVisible();
    expect(fixture.calls.map(call => call.kind)).toEqual(["info", "metadata"]);
    await expect(page.getByTestId("crud-create")).toHaveCount(0);
    await expect(page.getByTestId("crud-editor")).toHaveCount(0);
});

test("mock exact sparse UPDATE preserves baseline, null/empty kinds, DOM and focused input", async ({ page }) => {
    const fixture = await mockCrud(page);
    await fixture.enter();
    await edit(page);
    await expect(input(page, "serial")).toHaveValue(integer);
    await expect(input(page, "serial")).toHaveAttribute("readonly");
    await expect(input(page, "amount")).toHaveValue(decimal);
    await expect(input(page, "note")).toBeDisabled();
    await nullToggle(page, "note").uncheck(); // Explicit empty string is different from its null baseline.
    await input(page, "note").fill("");
    await input(page, "caption").fill("Draft Á");
    await input(page, "caption").focus();
    await input(page, "caption").evaluate(node => { window.__baselineInput = node; });
    for (const language of ["en", "es"]) {
        for (const theme of ["default", "alternative", "cyberpunk", "vintage", "high-contrast"]) {
            // Programmatic select events leave focus on the editor, so replacement/loss is observable.
            await page.getByTestId("language").evaluate((node, value) => {
                node.value = value; node.dispatchEvent(new Event("change", { bubbles: true }));
            }, language);
            await page.getByTestId("theme").evaluate((node, value) => {
                node.value = value; node.dispatchEvent(new Event("change", { bubbles: true }));
            }, theme);
            await expect(page.locator("[data-active-theme]")).toHaveAttribute("data-active-theme", theme);
            await expect(page.locator("html")).toHaveAttribute("lang", language);
            await expect(input(page, "caption")).toBeFocused();
            expect(await input(page, "caption").evaluate(node => node === window.__baselineInput)).toBe(true);
            await expect(input(page, "amount")).toHaveValue(decimal);
            await expect(input(page, "note")).toHaveValue("");
        }
    }
    await input(page, "caption").press("Tab");
    await expect(input(page, "amount")).toBeFocused();
    await page.getByTestId("crud-save").click();
    await expect(page.getByTestId("crud-editor")).toHaveCount(0);
    const writes = fixture.calls.filter(call => call.kind === "UPDATE");
    expect(writes.map(call => call.body)).toEqual([{
        target: metadata.target, operation: "UPDATE",
        inputs: { key: record.key, changes: { caption: "Draft Á", note: "" }, baseline: record.values },
    }]);
    expect(fixture.calls[0].headers.authorization).toBeUndefined();
    expect(fixture.calls[1].headers.authorization).toBe("Bearer synthetic-baseline-token");
});

test("mock CREATE sends current full-field initialization and exact scalar kinds", async ({ page }) => {
    const fixture = await mockCrud(page);
    await fixture.enter();
    await expect(page.getByTestId("crud-create")).toBeVisible();
    await page.getByTestId("crud-create").click();
    await expect(input(page, "amount")).toBeDisabled();
    await expect(input(page, "note")).toBeDisabled();
    await expect(input(page, "enabled")).not.toBeChecked();
    await input(page, "serial").fill(integer);
    await input(page, "caption").fill("New");
    await nullToggle(page, "amount").uncheck();
    await input(page, "amount").fill(decimal);
    await page.getByTestId("crud-save").click();
    await expect(page.getByTestId("crud-editor")).toHaveCount(0);
    expect(fixture.calls.filter(call => call.kind === "CREATE").map(call => call.body)).toEqual([{
        target: metadata.target, operation: "CREATE",
        inputs: { values: { serial: integer, caption: "New", amount: decimal, note: null, enabled: false } },
    }]);
});

test("mock rejection retains exact invalid draft and permits explicit correction", async ({ page }) => {
    const fixture = await mockCrud(page, {
        respond: call => call.kind === "UPDATE" ? { status: "rejected", output: { code: "INVALID_VALUE" } } : undefined,
    });
    await fixture.enter();
    await edit(page);
    await input(page, "amount").fill("1e-");
    await page.getByTestId("crud-save").click();
    await expect(page.getByTestId("crud-result")).toContainText("INVALID_VALUE");
    await expect(input(page, "amount")).toHaveValue("1e-");
    await expect(input(page, "caption")).toHaveValue(record.values.caption);
    await expect(page.getByTestId("crud-save")).toBeEnabled();
    await input(page, "amount").fill(decimal);
    await expect(input(page, "amount")).toHaveValue(decimal);
    expect(fixture.calls.filter(call => call.kind === "UPDATE")[0].body.inputs.changes).toEqual({ amount: "1e-" });
});

for (const outcome of ["conflict", "network-loss", "malformed"]) {
    test(`mock ${outcome} blocks repeat writes and preserves the complete draft`, async ({ page }) => {
        const fixture = await mockCrud(page, { respond: async (call, route) => {
            if (call.kind !== "UPDATE") return;
            if (outcome === "network-loss") { await route.abort("failed"); return null; }
            if (outcome === "malformed") { await route.fulfill({ body: "{broken" }); return null; }
            return { status: "conflict", output: { code: "CONCURRENT_CHANGE" } };
        } });
        await fixture.enter();
        await edit(page);
        await input(page, "caption").fill("Do not lose");
        await page.getByTestId("crud-save").click();
        await expect(page.getByTestId("crud-issue")).toBeVisible();
        await expect(page.getByTestId("crud-save")).toBeDisabled();
        await expect(input(page, "caption")).toHaveValue("Do not lose");
        await expect(input(page, "amount")).toHaveValue(decimal);
        await expect(nullToggle(page, "note")).toBeChecked();
        await expect(input(page, "enabled")).toBeChecked();
        await page.getByTestId("crud-save").dispatchEvent("click");
        expect(fixture.calls.filter(call => call.kind === "UPDATE")).toHaveLength(1);
        await page.getByTestId("crud-reload").click();
        await expect(page.locator('[data-detail="caption"]')).toHaveText(record.values.caption);
        await expect(page.getByTestId("crud-edit")).toBeEnabled();
    });
}

test("mock in-flight save locks controls and suppresses duplicate submissions", async ({ page }) => {
    const received = gate();
    const response = gate();
    const fixture = await mockCrud(page, { respond: async call => {
        if (call.kind === "UPDATE") { received.release(); await response.promise; }
    } });
    try {
        await fixture.enter();
        await edit(page);
        await input(page, "caption").fill("Pending");
        await page.getByTestId("crud-save").click();
        await received.promise;
        await expect(page.getByTestId("crud-save")).toBeDisabled();
        await expect(input(page, "caption")).toBeDisabled();
        await page.getByTestId("crud-save").dispatchEvent("click");
        expect(fixture.calls.filter(call => call.kind === "UPDATE")).toHaveLength(1);
        response.release();
        await expect(page.getByTestId("crud-editor")).toHaveCount(0);
        expect(fixture.calls.filter(call => call.kind === "UPDATE")).toHaveLength(1);
    } finally { response.release(); }
});

test("mock DELETE cancels without writing and sends only the consented displayed snapshot", async ({ page }) => {
    const fixture = await mockCrud(page);
    await fixture.enter();
    await expect(page.getByTestId("crud-row")).toHaveCount(1);
    await page.getByTestId("crud-delete").click();
    await expect(page.getByTestId("crud-confirm-delete")).toBeDisabled();
    await page.getByTestId("crud-cancel").click();
    expect(fixture.calls.filter(call => call.kind === "DELETE")).toHaveLength(0);
    await page.getByTestId("crud-delete").click();
    await page.getByTestId("crud-consent").check();
    await page.getByTestId("crud-confirm-delete").click();
    await expect(page.getByTestId("crud-editor")).toHaveCount(0);
    expect(fixture.calls.filter(call => call.kind === "DELETE").map(call => call.body.inputs))
        .toEqual([{ key: record.key, confirmedValues: record.values }]);
    expect(fixture.calls.filter(call => call.kind === "GET")).toHaveLength(2);
});

for (const stage of ["info", "metadata", "LIST", "GET", "UPDATE"]) {
    test(`mock non-cooperative late ${stage} cannot restore a replaced session`, async ({ page }) => {
        // Observe cancellation, but deliberately let this test transport deliver despite it: exercise sequence checks.
        await page.addInitScript(() => {
            window.__baselineAborted = [];
            window.__baselineRead = [];
            const original = window.fetch;
            window.fetch = async (url, init) => {
                if (!String(url).includes("/baseline/demo/")) return original(url, init);
                const kind = init?.body ? JSON.parse(init.body).operation : String(url).split("/").at(-1);
                init?.signal?.addEventListener("abort", () => window.__baselineAborted.push(kind));
                const result = await original(url, { ...init, signal: undefined });
                const body = await result.text();
                window.__baselineRead.push(kind);
                return new Response(body, { status: result.status, headers: result.headers });
            };
        });
        const received = gate();
        const response = gate();
        const requests = [];
        page.on("request", request => {
            if (new URL(request.url()).pathname.includes("/demo/")) requests.push(request.url());
        });
        const fixture = await mockCrud(page, { respond: async call => {
            if (call.kind === stage) { received.release(); await response.promise; }
        } });
        try {
            await fixture.enter();
            if (stage === "GET") {
                await expect(page.getByTestId("crud-row")).toHaveCount(1);
                await page.getByTestId("crud-get").click();
            } else if (stage === "UPDATE") {
                await edit(page);
                await input(page, "caption").fill("Pending old session");
                await page.getByTestId("crud-save").click();
            }
            await received.promise;
            // Runtime and URL replacement both invalidate the existing session; neither sends another request.
            if (stage === "GET" || stage === "metadata") {
                await page.getByTestId("instance-url").fill(fixture.url + "/changed");
            } else await page.getByTestId("runtime").selectOption("java");
            await expect(page.getByTestId("crud-token")).toHaveValue("");
            await expect.poll(() => page.evaluate(kind => window.__baselineAborted.includes(kind), stage)).toBe(true);
            if (stage === "UPDATE") {
                await page.getByTestId("runtime").selectOption("php");
                await page.getByTestId("crud-token").fill("replacement-synthetic-token");
                await page.getByTestId("crud-connect").click();
                await expect(page.getByTestId("crud-row")).toHaveCount(1);
                await page.getByTestId("crud-create").click();
                await input(page, "serial").fill("2");
                await input(page, "caption").fill("Replacement session draft");
            }
            const dispatched = requests.length;
            response.release();
            await expect.poll(() => page.evaluate(kind => window.__baselineRead.includes(kind), stage)).toBe(true);
            // Let the delivered fetch continuation and Angular render finish; no elapsed-time sleep.
            await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => resolve())));
            if (stage === "UPDATE") {
                await expect(page.getByTestId("crud-row")).toHaveCount(1);
                await expect(input(page, "serial")).toHaveValue("2");
                await expect(input(page, "caption")).toHaveValue("Replacement session draft");
            } else {
                await expect(page.getByTestId("crud-row")).toHaveCount(0);
                await expect(page.getByTestId("crud-editor")).toHaveCount(0);
                await expect(page.getByTestId("crud-status")).toHaveText("Sin conexión");
            }
            await expect(page.getByTestId("crud-result")).toHaveCount(0);
            expect(requests).toHaveLength(dispatched); // No stale follow-up request, even to a cleared target.
            expect(requests).toHaveLength(fixture.calls.length);
        } finally { response.release(); }
    });
}