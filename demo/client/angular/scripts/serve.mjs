// Local static preview only: no backend proxy or invented ARP API.
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, resolve, sep } from 'node:path';

const root = resolve(process.env.ARP_DEMO_SITE ?? '/artifacts/site');
const types = {
    '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css',
    '.json': 'application/json', '.yaml': 'text/plain; charset=utf-8', '.md': 'text/plain; charset=utf-8',
    '.txt': 'text/plain; charset=utf-8',
};
const server = createServer(async (request, response) => {
    try {
        const url = new URL(request.url, 'http://localhost');
        const path = decodeURIComponent(url.pathname === '/' ? '/index.html' : url.pathname);
        const file = resolve(root, `.${path}`);
        if (!file.startsWith(`${root}${sep}`)) {
            response.writeHead(403).end();
            return;
        }
        const body = await readFile(file);
        response.writeHead(200, {
            'Content-Type': types[extname(file)] ?? 'application/octet-stream',
            'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
        }).end(body);
    } catch {
        response.writeHead(404).end('Not found');
    }
});
const port = Number(process.env.ARP_DEMO_CLIENT_PORT ?? '4173');
server.listen(port, process.env.ARP_DEMO_HOST ?? '127.0.0.1', () => {
    console.log(`ARP demo: http://127.0.0.1:${port}`);
});
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => server.close());