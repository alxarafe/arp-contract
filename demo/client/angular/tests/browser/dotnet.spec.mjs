import { test, expect } from '@playwright/test';

const url = process.env.ARP_DOTNET_DEMO_URL;
async function connect(page) {
    await page.goto('/');
    await page.getByTestId('instance-url').fill(url);
    await page.getByTestId('remote-connect').click();
    await expect(page.getByTestId('remote-status')).toContainText('Conexión confirmada');
}
async function element(page, id) {
    await page.getByTestId('remote-element').selectOption(id);
    await expect(page.getByTestId('remote-descriptor')).toContainText(`"id":"${id}"`);
    await expect(page.getByTestId('remote-validate')).toBeEnabled();
}
async function validate(page) {
    await page.getByTestId('remote-validate').click();
    await expect(page.getByTestId('remote-result')).not.toHaveText('');
    return JSON.parse(await page.getByTestId('remote-result').textContent());
}

test('real .NET dictionary preserves exact descriptors and scalar values', async ({ page }, info) => {
    await connect(page);
    await expect(page.getByTestId('remote-element').locator('option')).toHaveCount(19);
    await element(page, 'portable.equivalent');
    await expect(page.getByTestId('remote-descriptor')).toContainText('1e127');
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
    await page.screenshot({ path: `/artifacts/browser/${info.project.name}-live-dotnet.png`, fullPage: true });
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
    await page.getByTestId('runtime').selectOption('java');
    await expect(page.getByTestId('remote-connect')).toHaveCount(0);
    await page.getByTestId('runtime').selectOption('dotnet');
    await expect(page.getByTestId('remote-status')).toHaveText('Sin conexión');
    await page.getByTestId('instance-url').fill('http://127.0.0.1:65534');
    await page.getByTestId('remote-connect').click();
    await expect(page.getByTestId('remote-status')).toHaveText('Conexión no disponible');
    await expect(page.getByTestId('remote-element')).toHaveCount(0);
});