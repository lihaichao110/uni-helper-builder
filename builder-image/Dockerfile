FROM node:20-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends bash git python3 make g++ ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g yarn pnpm

COPY core/ /opt/core/
COPY build-wgt.sh /usr/local/bin/build-wgt
RUN chmod 0555 /usr/local/bin/build-wgt \
    && if [ -f /opt/core/plugins/package.json ]; then cd /opt/core/plugins && npm install --omit=optional; fi \
    && if [ -f /opt/core/plugins/uniapp-cli-vite/package.json ]; then cd /opt/core/plugins/uniapp-cli-vite && yarn install --frozen-lockfile || yarn install; fi \
    && if [ -f /opt/core/plugins/uniapp-cli/package.json ]; then cd /opt/core/plugins/uniapp-cli && npm install --force; fi \
    && chown -R node:node /opt/core

USER node
WORKDIR /workspace
CMD ["build-wgt"]

