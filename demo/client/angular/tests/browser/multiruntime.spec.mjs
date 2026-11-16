import { test, expect } from '@playwright/test';

const hosts = JSON.parse(process.env.ARP_DEMO_HOSTS ?? '{}');

for (const [runtime, url] of Object.entries(hosts)) {
    test.describe(runtime, () => {
        async function connect(page) {
            await page.goto('/');
            await page.getByTestId('runtime').selectOption(runtime);
            await page.getByTestId('instance-url').fill(url);
            await page.getByTestId('remote-connect').click();
            await expect(page.getByTestId('remote-status')).toContainText('Conexión confirmada');
        }
        async function element(page, id) {
            const response = page.waitForResponse(response =>
                response.url().endsWith(`/demo/dictionary/elements/${encodeURIComponent(id)}`));
            await page.getByTestId('remote-element').selectOption(id);
            const original = await (await response).text();
            await expect(page.getByTestId('remote-descriptor')).toHaveText(original);
            await expect(page.getByTestId('remote-validate')).toBeEnabled();
        }
        async function validate(page) {
            await page.getByTestId('remote-validate').click();
            await expect(page.getByTestId('remote-result')).not.toHaveText('');
            return JSON.parse(await page.getByTestId('remote-result').textContent());
        }

        test('real host dictionary preserves exact descriptors and scalar values', async ({ page }, info) => {
            await connect(page);
            await expect(page.getByTestId('remote-element').locator('option')).toHaveCount(19);
            await element(page, 'portable.equivalent');
            const descriptor = await page.getByTestId('remote-descriptor').textContent();
            const token = descriptor.match(/"maximumLength"\s*:\s*([0-9.eE+-]+)/)[1];
            const [mantissa, exponent = '0'] = token.toLowerCase().split('e');
            const fraction = mantissa.split('.')[1] ?? '';
            const coefficient = BigInt(mantissa.replace('.', ''));
            const scale = BigInt(exponent) - BigInt(fraction.length);
            const exact = scale >= 0n ? coefficient * 10n ** scale : coefficient / 10n ** -scale;
            expect(exact).toBe(10n ** 127n);
            await element(page, 'test.int64');
            await page.getByTestId('remote-value').fill('9223372036854775807');
            expect(await validate(page)).toEqual({ valid: true, normalizedValue: '9223372036854775807', issues: [] });
            await element(page, 'test.decimal');
            await page.getByTestId('remote-value').fill('12345678901234567890.123400');
            expect((await validate(page)).normalizedValue).toBe('12345678901234567890.1234');
            await element(page, 'test.int8');
            await page.getByTestId('remote-value').fill('128');
            const rejected = await validate(page);
            expect(rejected.valid).toBe(false);
            expect(rejected.issues[0].code).toBe('DICTIONARY_VALUE_CONSTRAINT');
            expect(rejected).not.toHaveProperty('normalizedValue');
            await page.getByTestId('remote-value').fill('12');
            await expect(page.getByTestId('remote-result')).toHaveCount(0);
            expect((await validate(page)).normalizedValue).toBe('12');
            await page.screenshot({ path: `/artifacts/browser/${info.project.name}-live-${runtime}.png`,
                fullPage: true });
        });

        test('boolean, null and empty string keep distinct kinds through the real host', async ({ page }) => {
            await connect(page);
            await element(page, 'test.boolean');
            await page.getByTestId('remote-value').selectOption('false');
            expect((await validate(page)).normalizedValue).toBe(false);
            await page.getByTestId('remote-codec').selectOption('string');
            await page.getByTestId('remote-value').fill('true');
            expect((await validate(page)).valid).toBe(false);
            await element(page, 'test.string');
            expect((await validate(page)).normalizedValue).toBe('');
            await page.getByTestId('remote-codec').selectOption('null');
            expect((await validate(page)).valid).toBe(false);
        });

        test('live validation remains available across all themes and both languages', async ({ page }) => {
            await connect(page);
            await element(page, 'test.int64');
            await page.getByTestId('remote-value').fill('9223372036854775807');
            for (const language of ['es', 'en']) {
                await page.getByTestId('language').selectOption(language);
                for (const theme of ['default', 'alternative', 'cyberpunk', 'vintage', 'high-contrast']) {
                    await page.getByTestId('theme').selectOption(theme);
                    await expect(page.getByTestId('remote-element')).toHaveValue('test.int64');
                    expect((await validate(page)).normalizedValue).toBe('9223372036854775807');
                    await expect(page.getByTestId('remote-status')).toContainText(
                        language === 'en' ? 'Connection confirmed' : 'Conexión confirmada');
                }
            }
        });

        test('runtime or URL changes invalidate connection; refused connections are real errors', async ({ page }) => {
            await connect(page);
            await element(page, 'test.int8');
            await page.getByTestId('remote-disconnect').click();
            await expect(page.getByTestId('remote-status')).toHaveText('Sin conexión');
            await expect(page.getByTestId('remote-element')).toHaveCount(0);
            await page.getByTestId('remote-connect').click();
            await expect(page.getByTestId('remote-status')).toContainText('Conexión confirmada');
            await page.getByTestId('runtime').selectOption(runtime === 'java' ? 'php' : 'java');
            await expect(page.getByTestId('remote-status')).toHaveText('Sin conexión');
            await page.getByTestId('runtime').selectOption(runtime);
            await expect(page.getByTestId('remote-status')).toHaveText('Sin conexión');
            await page.getByTestId('instance-url').fill('http://127.0.0.1:65534');
            await page.getByTestId('remote-connect').click();
            await expect(page.getByTestId('remote-status')).toHaveText('Conexión no disponible');
            await expect(page.getByTestId('remote-element')).toHaveCount(0);
        });
    });
}

async function chooseHost(page, runtime) {
    await page.getByTestId('runtime').selectOption(runtime);
    await page.getByTestId('instance-url').fill(hosts[runtime]);
    await page.getByTestId('remote-connect').click();
    await expect(page.getByTestId('remote-status')).toContainText('Conexión confirmada');
    await expect(page.getByTestId('remote-element').locator('option')).toHaveCount(19);
}

test('successive runtime changes preserve exact observed results and clear previous state', async ({ page }) => {
    await page.goto('/');
    const results = [];
    for (const runtime of ['dotnet', 'java', 'php', 'dotnet', 'php', 'java']) {
        await chooseHost(page, runtime);
        await expect(page.getByTestId('remote-descriptor')).toHaveCount(0);
        await expect(page.getByTestId('remote-result')).toHaveCount(0);
        await page.getByTestId('remote-element').selectOption('test.decimal');
        await expect(page.getByTestId('remote-descriptor')).toContainText('test.decimal');
        await expect(page.getByTestId('remote-value')).toHaveValue('');
        await page.getByTestId('remote-value').fill('12345678901234567890.123400');
        const response = page.waitForResponse(response => response.url().endsWith('/test.decimal/validate'));
        await page.getByTestId('remote-validate').click();
        const original = await (await response).text();
        await expect(page.getByTestId('remote-result')).toHaveText(original);
        results.push(JSON.parse(original));
    }
    for (const result of results) expect(result).toEqual({
        valid: true, normalizedValue: '12345678901234567890.1234', issues: [],
    });
});

test('a real host with the wrong identity never enables operations', async ({ page }) => {
    await page.goto('/');
    const requests = [];
    page.on('request', request => { if (request.url().includes('/demo/dictionary/')) requests.push(request.url()); });
    await page.getByTestId('runtime').selectOption('java');
    await page.getByTestId('instance-url').fill(hosts.dotnet);
    await page.getByTestId('remote-connect').click();
    await expect(page.getByRole('alert').filter({ hasText: 'identidad o el protocolo' })).toBeVisible();
    await expect(page.getByTestId('remote-element')).toHaveCount(0);
    expect(requests).toEqual([]);
    // The URL stays the same; changing only the selected runtime must still invalidate state.
    await page.getByTestId('runtime').selectOption('dotnet');
    await page.getByTestId('instance-url').fill(hosts.dotnet);
    await page.getByTestId('remote-connect').click();
    await expect(page.getByTestId('remote-status')).toContainText('Conexión confirmada');
    await page.getByTestId('runtime').selectOption('java');
    await expect(page.getByTestId('remote-status')).toHaveText('Sin conexión');
});

for (const capabilities of [[], ['dictionary.list'], ['dictionary.list', 'dictionary.validate']]) {
    test(`negative negotiation: only advertised operations are enabled: ${capabilities}`, async ({ page }) => {
        // Deliberate envelope fault injection, not evidence of backend execution/conformance.
        await page.route('**/demo/info', async route => {
            const response = await route.fetch();
            await route.fulfill({ response, json: { ...await response.json(), capabilities } });
        });
        const paths = [];
        page.on('request', request => { if (request.url().includes('/demo/dictionary/')) paths.push(request.url()); });
        await page.goto('/');
        await page.getByTestId('instance-url').fill(hosts.dotnet);
        await page.getByTestId('remote-connect').click();
        await expect(page.getByTestId('remote-status')).toContainText('Conexión confirmada');
        if (!capabilities.includes('dictionary.list')) {
            await expect(page.getByTestId('remote-element')).toBeDisabled();
            expect(paths).toEqual([]);
        } else {
            await page.getByTestId('remote-element').selectOption('test.int8');
            await expect(page.getByTestId('remote-descriptor')).toHaveCount(0);
            const button = page.getByTestId('remote-validate');
            if (capabilities.includes('dictionary.validate')) {
                await expect(button).toBeEnabled();
                await page.getByTestId('remote-value').fill('12');
                await button.click();
                await expect(page.getByTestId('remote-result')).toContainText('12');
            } else await expect(button).toBeDisabled();
            expect(paths.some(path => path.endsWith('/test.int8'))).toBe(false);
        }
    });
}

for (const stage of ['info', 'list', 'descriptor', 'validate']) {
    for (const change of ['runtime', 'url']) {
        test(`abort delayed real ${stage} response on ${change} change`, async ({ page }) => {
            await page.addInitScript(() => {
                window.__abortedPaths = [];
                const original = window.fetch;
                window.fetch = (url, init) => {
                    init?.signal?.addEventListener('abort', () => window.__abortedPaths.push(String(url)));
                    return original(url, init);
                };
            });
            await page.goto('/');
            await page.getByTestId('instance-url').fill(hosts.dotnet);
            if (stage === 'descriptor' || stage === 'validate') {
                await page.getByTestId('remote-connect').click();
                await expect(page.getByTestId('remote-status')).toContainText('Conexión confirmada');
            }
            if (stage === 'validate') {
                await page.getByTestId('remote-element').selectOption('test.int64');
                await expect(page.getByTestId('remote-validate')).toBeEnabled();
                await page.getByTestId('remote-value').fill('9223372036854775807');
            }
            const suffix = { info: '/demo/info', list: '/demo/dictionary/elements',
                descriptor: '/test.int64', validate: '/test.int64/validate' }[stage];
            let release;
            const gate = new Promise(resolve => { release = resolve; });
            let captured;
            const ready = new Promise(resolve => { captured = resolve; });
            let delivered;
            const done = new Promise(resolve => { delivered = resolve; });
            await page.route(`**${suffix}`, async route => {
                const response = await route.fetch(); // Execute the real host, delay only delivery to Angular.
                captured();
                await gate;
                await route.fulfill({ response }).catch(() => {}); // An aborted browser request may be gone.
                delivered();
            });
            if (stage === 'descriptor') await page.getByTestId('remote-element').selectOption('test.int64');
            else if (stage === 'validate') await page.getByTestId('remote-validate').click();
            else await page.getByTestId('remote-connect').click();
            await ready;
            if (change === 'runtime') await page.getByTestId('runtime').selectOption('java');
            else await page.getByTestId('instance-url').fill(hosts.dotnet + '/');
            await expect(page.getByTestId('remote-status')).toHaveText('Sin conexión');
            expect(await page.evaluate(suffix => window.__abortedPaths.some(path => path.endsWith(suffix)), suffix))
                .toBe(true);
            release();
            await done;
            await expect(page.getByTestId('remote-status')).toHaveText('Sin conexión');
            await expect(page.getByTestId('remote-element')).toHaveCount(0);
            await expect(page.getByTestId('remote-descriptor')).toHaveCount(0);
            await expect(page.getByTestId('remote-result')).toHaveCount(0);
        });
    }
}