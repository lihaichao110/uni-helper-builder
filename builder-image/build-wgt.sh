#!/bin/bash
set -euo pipefail

HBUILDER_DIR=/opt/core
UNI_INPUT_DIR=${UNI_INPUT_DIR:-/workspace}
UNI_OUTPUT_DIR=${UNI_OUTPUT_DIR:-/workspace/wgt-dist}
VUE_VERSION=${VUE_VERSION:-3}
NODE_MEMORY_MB=${NODE_MEMORY_MB:-2048}
UNI_HBUILDERX_PLUGINS="$HBUILDER_DIR/plugins"
UNI_NPM_DIR="$UNI_HBUILDERX_PLUGINS/npm"
UNI_NODE_DIR="$UNI_HBUILDERX_PLUGINS/node"
export HBUILDER_DIR UNI_INPUT_DIR UNI_OUTPUT_DIR UNI_HBUILDERX_PLUGINS UNI_NPM_DIR UNI_NODE_DIR
export NODE_ENV=production
export PATH="$PATH:$UNI_INPUT_DIR/node_modules/.bin"

rm -rf "$UNI_OUTPUT_DIR"
mkdir -p "$UNI_OUTPUT_DIR"

if [ "$VUE_VERSION" = "2" ]; then
  UNI_CLI_CONTEXT="$UNI_HBUILDERX_PLUGINS/uniapp-cli"
  UNI_CLI="$UNI_CLI_CONTEXT/bin/uniapp-cli.js"
  if [ ! -f "$UNI_CLI" ]; then
    echo "缺少 Vue 2 HBuilderX Core：$UNI_CLI" >&2
    exit 20
  fi
  export UNI_CLI_CONTEXT UNI_PLATFORM=app-plus UNI_APP_PRODUCTION_TYPE=LOCAL_PACKAGING
  export VUE_CLI_TRANSPILE_BABEL_RUNTIME=true
  cd "$UNI_CLI_CONTEXT"
  exec node "--max-old-space-size=$NODE_MEMORY_MB" --no-warnings "$UNI_CLI"
fi

UNI_CLI_CONTEXT="$UNI_HBUILDERX_PLUGINS/uniapp-cli-vite"
UNI_CLI="$UNI_CLI_CONTEXT/node_modules/@dcloudio/vite-plugin-uni/bin/uni.js"
if [ ! -f "$UNI_CLI" ]; then
  echo "缺少 Vue 3 HBuilderX Core：$UNI_CLI" >&2
  exit 21
fi
export UNI_CLI_CONTEXT VITE_ROOT_DIR="$UNI_INPUT_DIR"
cd "$UNI_CLI_CONTEXT"
exec node "--max-old-space-size=$NODE_MEMORY_MB" --no-warnings "$UNI_CLI" build --platform app --outDir "$UNI_OUTPUT_DIR"

