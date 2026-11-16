import { defineConfig } from '@playwright/test';

const baseURL = process.env.ARP_DEMO_CLIENT_ORIGIN ?? 'http://127.0.0.1:4173';

export default defineConfig({
    testDir: '.',
    testMatch: '*.spec.mjs',
    testIgnore: process.env.ARP_DEMO_HOSTS ? [] : ['multiruntime.spec.mjs'],
    workers: 1,
    retries: 0,
    forbidOnly: true,
    outputDir: '/artifacts/browser/results',
    reporter: [['list'], ['json', { outputFile: '/artifacts/browser/results.json' }]],
    use: {
        baseURL,
        browserName: 'chromium',
        trace: 'retain-on-failure',
    },
    projects: [
        { name: 'desktop', use: { viewport: { width: 1440, height: 1000 } } },
        { name: 'mobile', use: { viewport: { width: 390, height: 844 } } },
    ],
    webServer: { command: 'node /scripts/serve.mjs', url: baseURL },
});