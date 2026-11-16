#!/usr/bin/env bash
set -euo pipefail
# All mutable work lives in the disposable container; reference repositories are read-only.
mkdir /tmp/aur /tmp/client
cp /aur/package*.json /aur/angular.json /aur/tsconfig.json /aur/README.md /aur/LICENSE /aur/NOTICE /tmp/aur/
cp -R /aur/projects /aur/scripts /aur/packages /aur/docs /tmp/aur/
cd /tmp/aur
npm ci --no-audit --no-fund
npm run pack
cp /source/package*.json /source/angular.json /source/tsconfig.json /tmp/client/
cp -R /source/src /source/scripts /source/config /tmp/client/
cd /tmp/client
npm ci --no-audit --no-fund
node scripts/install-packages.mjs
npm run build
mkdir -p /artifacts/site
cp -R dist/browser/. /artifacts/site/