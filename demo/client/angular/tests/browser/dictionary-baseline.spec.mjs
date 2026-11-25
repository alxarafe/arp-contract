import { test, expect } from "@playwright/test";
import { integer, decimal } from "./fixtures/crud-baseline.mjs";

// Scripted boundary responses only: no dictionary validator or live runtime is implemented here.
const origin = process.env.ARP_DEMO_CLIENT_ORIGIN ?? "http://127.0.0.1:4173";
const elements = [
    { id: "baseline.integer", type: "INTEGER" }, { id: "baseline.decimal", type: "DECIMAL" },
    { id: "baseline.text", type: "STRING" }, { id: "baseline.boolean", type: "BOOLEAN" },
];
async function mockDictionary(page, runtime, capabilities) {
    const calls = [];
    const descriptor = '{"id":"baseline.exact","constraints":{"maximum":18446744073709551615,'
        + '"minimum":1.00000000000000000001}}';
    await page.route("**/dictionary-baseline/demo/**", async route => {
        const request = route.request();
        const path = new URL(request.url()).pathname;
        const body = request.postData() ? request.postDataJSON() : undefined;
        calls.push({ path, body });
        if (path.endsWith("/info")) {
            await route.fulfill({ json: { runtime, demoProtocol: `arp-demo-${runtime}/1`, capabilities } });
        } else if (path.endsWith("/elements")) await route.fulfill({ json: { elements } });
        else if (path.endsWith("/validate")) {
            // Fixed response policy makes raw false/null/empty/exact request assertions independent of normalization.
            const json = body.value === null
                ? { valid: false, issues: [{ code: "DICTIONARY_VALUE_TYPE" }] }
                : { valid: true, normalizedValue: body.value, issues: [] };
            await route.fulfill({ json });
        } else await route.fulfill({ contentType: "application/json", body: descriptor });
    });
    await page.goto("/");
    await page.getByTestId("runtime").selectOption(runtime);
    await page.getByTestId("instance-url").fill(`${origin}/dictionary-baseline`);
    await page.getByTestId("remote-connect").click();
    await expect(page.getByTestId("remote-status")).toHaveText("Conexión confirmada por la última petición");
    return { calls, descriptor };
}

for (const runtime of ["dotnet", "java", "php"]) {
    test(`mock ${runtime} dictionary preserves metadata bytes and exact/empty/boolean/null request kinds`,
        async ({ page }) => {
            const fixture = await mockDictionary(page, runtime,
                ["dictionary.list", "dictionary.describe", "dictionary.validate"]);
            for (const [id, value] of [["integer", integer], ["decimal", decimal], ["text", ""], ["boolean", false]]) {
                await page.getByTestId("remote-element").selectOption(`baseline.${id}`);
                await expect(page.getByTestId("remote-descriptor")).toHaveText(fixture.descriptor);
                if (id === "boolean") await page.getByTestId("remote-value").selectOption("false");
                else await page.getByTestId("remote-value").fill(value);
                await page.getByTestId("remote-validate").click();
                await expect(page.getByTestId("remote-result")).toHaveText(JSON.stringify({
                    valid: true, normalizedValue: value, issues: [],
                }));
            }
            await page.getByTestId("remote-element").selectOption("baseline.text");
            await page.getByTestId("remote-codec").selectOption("null");
            await page.getByTestId("remote-validate").click();
            await expect(page.getByTestId("remote-result")).toHaveText(JSON.stringify({
                valid: false, issues: [{ code: "DICTIONARY_VALUE_TYPE" }],
            }));
            expect(fixture.calls.filter(call => call.path.endsWith("/validate")).map(call => call.body))
                .toEqual([{ value: integer }, { value: decimal }, { value: "" }, { value: false }, { value: null }]);
            await page.getByTestId("remote-codec").selectOption("string");
            await expect(page.getByTestId("remote-result")).toHaveCount(0);
            await page.getByTestId("remote-disconnect").click();
            await expect(page.getByTestId("remote-element")).toHaveCount(0);
            await expect(page.getByTestId("remote-descriptor")).toHaveCount(0);
            await expect(page.getByTestId("remote-result")).toHaveCount(0);
        });

    test(`mock ${runtime} dictionary never calls unadvertised describe or validate`, async ({ page }) => {
        const fixture = await mockDictionary(page, runtime, ["dictionary.list"]);
        await page.getByTestId("remote-element").selectOption("baseline.integer");
        await expect(page.getByTestId("remote-validate")).toBeDisabled();
        await expect(page.getByTestId("remote-descriptor")).toHaveCount(0);
        expect(fixture.calls.map(call => call.path.split("/").at(-1))).toEqual(["info", "elements"]);
    });
}