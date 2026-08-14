#!/bin/bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "用法: $0 /path/to/HBuilderX/plugins" >&2
  exit 1
fi

SOURCE=$(cd "$1" && pwd)
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
TARGET="$SCRIPT_DIR/core/plugins"
mkdir -p "$TARGET"

for name in about compile-dart-sass compile-less compile-node-sass node npm uni_modules uni_helpers uniapp-cli uniapp-cli-vite; do
  if [ -e "$SOURCE/$name" ]; then
    rm -rf "$TARGET/$name"
    cp -a "$SOURCE/$name" "$TARGET/$name"
  else
    echo "提示：HBuilderX plugins 中不存在 $name"
  fi
done

if [ -f "$TARGET/uniapp-cli-vite/package.json" ]; then
  node "$(dirname "$0")/patch-core.mjs" "$TARGET/uniapp-cli-vite/package.json"
fi
if [ -f "$TARGET/uniapp-cli/package.json" ]; then
  node "$(dirname "$0")/patch-core.mjs" "$TARGET/uniapp-cli/package.json" vue2
fi
echo "Core 已准备到 $TARGET；请检查来源许可后执行 docker build。"
