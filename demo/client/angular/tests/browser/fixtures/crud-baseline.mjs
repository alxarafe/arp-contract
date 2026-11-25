// Test-only boundary fixtures for the existing demo HTTP adapter, not a proposed ARP protocol.
export const integer = "18446744073709551615";
export const decimal = "12345678901234567890.123400000000000001";
export const fields = [
    { name: "serial", type: "INTEGER", label: "Serial", nullable: false, key: true, constraints: {} },
    { name: "caption", type: "STRING", label: "Caption", nullable: false, key: false, constraints: {} },
    { name: "amount", type: "DECIMAL", label: "Amount", nullable: true, key: false, constraints: {} },
    { name: "note", type: "STRING", label: "Note", nullable: true, key: false, constraints: {} },
    { name: "enabled", type: "BOOLEAN", label: "Enabled", nullable: false, key: false, constraints: {} },
];
export const record = {
    key: { components: [{ field: "serial", type: "INTEGER", value: integer }] },
    values: { serial: integer, caption: "Original Á", amount: decimal, note: null, enabled: true },
};
export const metadata = {
    demoProtocol: "arp-demo-php-crud/1", target: "baseline.resource", projection: "baseline.public",
    fields, operations: ["LIST", "GET", "CREATE", "UPDATE", "DELETE"],
    pagination: { defaultLimit: 1, maxLimit: 2, maxPage: 2 },
    update: { onConflict: "reload" },
    delete: { privateEvidence: false, confirmation: "complete displayed values" },
};
export const info = {
    runtime: "php", demoProtocol: "arp-demo-php/1", capabilities: ["crud.metadata", "crud.invoke"],
};

// Return fixed responses and observe requests; this fixture does not simulate persistence or validation.
export async function mockCrud(page, options = {}) {
    const calls = [];
    await page.route("**/baseline/demo/**", async route => {
        const request = route.request();
        const body = request.postData() ? request.postDataJSON() : undefined;
        const kind = body?.operation ?? new URL(request.url()).pathname.split("/").at(-1);
        const call = { kind, body, headers: request.headers() };
        calls.push(call);
        let reply = await options.respond?.(call, route);
        if (reply === null) return; // An explicit abort/fulfill was performed by the test.
        reply ??= kind === "info" ? (options.info ?? info)
            : kind === "metadata" ? (options.metadata ?? metadata)
            : kind === "LIST" ? { status: "success", output: { records: [record], page: { next: null } } }
            : kind === "GET" ? { status: "success", output: { found: true, record } }
            : { status: "success", output: {} };
        await route.fulfill({ json: reply });
    });
    const origin = process.env.ARP_DEMO_CLIENT_ORIGIN ?? "http://127.0.0.1:4173";
    return {
        calls,
        url: `${origin}/baseline`,
        async enter() {
            await page.goto("/");
            await page.getByTestId("runtime").selectOption("php");
            await page.getByTestId("instance-url").fill(`${origin}/baseline`);
            await page.locator('[data-capability="crud"]').click();
            await page.getByTestId("crud-token").fill("synthetic-baseline-token");
            await page.getByTestId("crud-connect").click();
        },
    };
}

export function gate() {
    let release;
    const promise = new Promise(resolve => { release = resolve; });
    return { promise, release };
}