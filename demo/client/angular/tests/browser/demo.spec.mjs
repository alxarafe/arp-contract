import { test, expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';

const clientOrigin = process.env.ARP_DEMO_CLIENT_ORIGIN ?? 'http://127.0.0.1:4173';
const capabilities = ['dictionary', 'entities', 'projections', 'crud', 'services'];

test('runtime selection retains independent URLs without calling a fabricated API', async ({ page }) => {
    const remote = [];
    page.on('request', request => {
        if (!request.url().startsWith(`${clientOrigin}/`)) remote.push(request.url());
    });
    await page.goto('/');
    await expect(page.getByTestId('runtime-label')).toHaveText('.NET');
    await expect(page.getByTestId('theme')).toHaveValue('default');
    await page.getByTestId('instance-url').fill('http://localhost:8001/demo');
    await page.getByTestId('instance-url').press('Tab');
    await page.getByTestId('runtime').selectOption('java');
    await expect(page.getByTestId('runtime-label')).toHaveText('Java');
    await expect(page.getByTestId('instance-url')).toHaveValue('');
    await page.getByTestId('instance-url').fill('http://localhost:8002');
    await page.getByTestId('instance-url').press('Tab');
    await page.getByTestId('runtime').selectOption('php');
    await expect(page.getByTestId('runtime-label')).toHaveText('PHP');
    await page.getByTestId('runtime').selectOption('dotnet');
    await expect(page.getByTestId('instance-url')).toHaveValue('http://localhost:8001/demo');
    await expect(page.getByTestId('connection-status')).toContainText('Adaptador explícito');
    expect(remote).toEqual([]);
});

for (const language of ['es', 'en']) {
    test(`all packaged themes activate in ${language}`, async ({ page }, info) => {
        const errors = [];
        page.on('pageerror', error => errors.push(error.message));
        await page.goto('/');
        await page.getByTestId('language').selectOption(language);
        for (const id of ['default', 'alternative', 'cyberpunk', 'vintage', 'high-contrast']) {
            await page.getByTestId('theme').selectOption(id);
            await expect(page.locator('[data-active-theme]')).toHaveAttribute('data-active-theme', id);
            const shell = id === 'cyberpunk' ? 'aur-cyberpunk-shell' : 'aur-default-shell';
            await expect(page.locator(shell)).toBeVisible();
            await expect(page.locator('aur-theme-shell')).toHaveClass(new RegExp(`theme-${id}`));
            await expect(page.getByTestId('source-content')).toContainText('arp.dictionary/v1');
            await expect(page.getByTestId('execute')).toHaveText(
                language === 'es' ? 'Ejecutar en runtime' : 'Execute in runtime');
            await page.screenshot({ path: `/artifacts/browser/${info.project.name}-${language}-${id}.png`,
                fullPage: true });
        }
        expect(errors).toEqual([]);
    });
}

test('capabilities display evidence and never offer unavailable execution', async ({ page }) => {
    await page.goto('/');
    for (const runtime of ['dotnet', 'java', 'php']) {
        await page.getByTestId('runtime').selectOption(runtime);
        for (const id of capabilities) {
            await page.locator(`[data-capability="${id}"]`).click();
            await expect(page.locator(`[data-capability="${id}"]`)).toHaveAttribute('aria-pressed', 'true');
            await expect(page.getByTestId('execute')).toBeDisabled();
            await expect(page.getByTestId('source-content')).not.toHaveText('');
        }
    }
    await expect(page.getByTestId('source-content')).toContainText('ARP-SERVICES-002');
    await expect(page.getByTestId('capability-detail')).toContainText('no es un dispatcher');
});

test('assets preserve original fixture bytes including exact numeric metadata', async ({ request }) => {
    for (const path of [
        'fixtures/dictionary/v1/catalog.json', 'fixtures/dictionary/v1/values.json',
        'fixtures/services/v1/invocation-cases.json', 'examples/demo/cds/public.yaml',
    ]) {
        const response = await request.get(`/contract/${path}`);
        expect(response.ok()).toBeTruthy();
        expect(await response.body()).toEqual(await readFile(`/contract/${path}`));
    }
});

test('loading errors are explicit and switching away clears stale content', async ({ page }) => {
    await page.route('**/contract/fixtures/services/v1/invocation-cases.json', route => route.fulfill({ status: 404 }));
    await page.goto('/');
    await page.locator('[data-capability="services"]').click();
    await expect(page.getByRole('alert').filter({ hasText: 'No se pudo cargar el archivo' })).toBeVisible();
    await expect(page.getByTestId('source-content')).toHaveText('');
    await page.locator('[data-capability="dictionary"]').click();
    await expect(page.getByTestId('source-content')).toContainText('arp.dictionary/v1');
});

test('URL configuration rejects credentials and non-HTTP schemes', async ({ page }) => {
    await page.goto('/');
    await page.getByTestId('instance-url').fill('https://user:secret@example.invalid');
    await expect(page.getByRole('alert').filter({ hasText: 'sin credenciales' })).toBeVisible();
    await expect(page.getByTestId('connection-status')).toContainText('Sin URL configurada');
    await page.getByTestId('instance-url').fill('file:///tmp/runtime');
    await expect(page.getByTestId('connection-status')).toContainText('Sin URL configurada');
    await page.getByTestId('instance-url').fill('http://localhost:8001');
    await expect(page.getByTestId('connection-status')).toContainText('URL configurada');
});
test('Spanish is initial and language changes immediately without a reload', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('language')).toHaveValue('es');
    await expect(page.locator('html')).toHaveAttribute('lang', 'es');
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Del contrato a la ejecución');
    await page.evaluate(() => { window.__languageStateProbe = 'retained'; });
    await page.getByTestId('language').selectOption('en');
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('From contract to execution');
    await expect(page.locator('html')).toHaveAttribute('lang', 'en');
    await expect(page).toHaveTitle('ARP · Capability explorer');
    await expect(page.locator('aur-theme-shell nav')).toContainText('Dictionary and validation');
    await expect(page.getByTestId('connection-status')).toContainText('Explicit demo adapter');
    await expect(page.getByRole('link', { name: 'Download original file' })).toBeVisible();
    await page.getByTestId('language').selectOption('es');
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Del contrato a la ejecución');
    await expect(page).toHaveTitle('ARP · Explorador de capacidades');
    expect(await page.evaluate(() => window.__languageStateProbe)).toBe('retained');
});

test('language persists across reloads and later pages; invalid stored values default to Spanish', async ({ page }) => {
    await page.goto('/');
    await page.getByTestId('language').selectOption('en');
    expect(await page.evaluate(() => localStorage.getItem('arp-demo.language'))).toBe('en');
    await page.reload();
    await expect(page.getByTestId('language')).toHaveValue('en');
    const next = await page.context().newPage();
    await next.goto('/');
    await expect(next.getByRole('heading', { level: 1 })).toHaveText('From contract to execution');
    await next.close();
    await page.evaluate(() => localStorage.setItem('arp-demo.language', 'fr'));
    await page.reload();
    await expect(page.getByTestId('language')).toHaveValue('es');
});

test('language switches preserve runtime, URLs, theme, file, fixture bytes and draft errors', async ({ page }) => {
    await page.goto('/');
    await page.getByTestId('instance-url').fill('http://localhost:8001');
    await page.getByTestId('runtime').selectOption('java');
    await page.getByTestId('instance-url').fill('http://localhost:8002');
    await page.getByTestId('theme').selectOption('cyberpunk');
    const file = 'fixtures/dictionary/v1/values.json';
    await page.getByTestId('source').selectOption(file);
    await expect(page.getByTestId('source-content')).toContainText('type-BOOLEAN');
    const original = await page.getByTestId('source-content').textContent();
    const assetRequests = [];
    page.on('request', request => {
        if (request.url().includes('/contract/')) assetRequests.push(request.url());
    });
    await page.getByTestId('instance-url').fill('invalid-draft');
    await page.getByTestId('language').selectOption('en');
    await expect(page.getByRole('alert').filter({ hasText: 'without credentials' })).toBeVisible();
    await expect(page.getByTestId('instance-url')).toHaveValue('invalid-draft');
    await expect(page.getByTestId('runtime')).toHaveValue('java');
    await expect(page.getByTestId('theme')).toHaveValue('cyberpunk');
    await expect(page.getByTestId('source')).toHaveValue(file);
    expect(await page.getByTestId('source-content').textContent()).toBe(original);
    await page.getByTestId('language').selectOption('es');
    await expect(page.getByRole('alert').filter({ hasText: 'sin credenciales' })).toBeVisible();
    expect(await page.getByTestId('source-content').textContent()).toBe(original);
    expect(assetRequests).toEqual([]);
    await page.getByTestId('runtime').selectOption('dotnet');
    await expect(page.getByTestId('instance-url')).toHaveValue('http://localhost:8001');
    await page.getByTestId('runtime').selectOption('java');
    await expect(page.getByTestId('instance-url')).toHaveValue('http://localhost:8002');
});

test('existing source errors translate and fixture exploration continues in English', async ({ page }) => {
    await page.route('**/contract/fixtures/services/v1/invocation-cases.json', route => route.fulfill({ status: 404 }));
    await page.goto('/');
    await page.locator('[data-capability="services"]').click();
    await expect(page.getByRole('alert').filter({ hasText: 'archivo del contrato' })).toBeVisible();
    await page.getByTestId('language').selectOption('en');
    await expect(page.getByRole('alert').filter({ hasText: 'contract file could not be loaded' })).toBeVisible();
    for (const id of ['dictionary', 'entities', 'projections', 'crud']) {
        await page.locator(`[data-capability="${id}"]`).click();
        await expect(page.getByTestId('source-content')).not.toHaveText('');
        await expect(page.getByTestId('execute')).toBeDisabled();
    }
});

test('blocked localStorage does not prevent session-local language selection', async ({ page }) => {
    await page.addInitScript(() => {
        for (const method of ['getItem', 'setItem']) {
            Object.defineProperty(Storage.prototype, method, { value() { throw new Error('Blocked'); } });
        }
    });
    await page.goto('/');
    await expect(page.getByTestId('language')).toHaveValue('es');
    await page.getByTestId('language').selectOption('en');
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('From contract to execution');
});