import { test, expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';

const capabilities = ['dictionary', 'entities', 'projections', 'crud', 'services'];

test('runtime selection retains independent URLs without calling a fabricated API', async ({ page }) => {
    const remote = [];
    page.on('request', request => {
        if (!request.url().startsWith('http://127.0.0.1:4173/')) remote.push(request.url());
    });
    await page.goto('/');
    await expect(page.getByTestId('runtime-label')).toHaveText('.NET');
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
    await expect(page.getByTestId('connection-status')).toContainText('Sin adaptador');
    expect(remote).toEqual([]);
});

test('all packaged themes activate through the real theme shell', async ({ page }, info) => {
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto('/');
    for (const id of ['default', 'alternative', 'cyberpunk', 'vintage', 'high-contrast']) {
        await page.getByTestId('theme').selectOption(id);
        await expect(page.locator('[data-active-theme]')).toHaveAttribute('data-active-theme', id);
        const shell = id === 'cyberpunk' ? 'aur-cyberpunk-shell' : 'aur-default-shell';
        await expect(page.locator(shell)).toBeVisible();
        await expect(page.locator('aur-theme-shell')).toHaveClass(new RegExp(`theme-${id}`));
        await expect(page.getByTestId('source-content')).toContainText('arp.dictionary/v1');
        await page.screenshot({ path: `/artifacts/browser/${info.project.name}-${id}.png`, fullPage: true });
    }
    expect(errors).toEqual([]);
});

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