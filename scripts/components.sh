#!/usr/bin/env sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
DIR="$ROOT/.components"
mkdir -p "$DIR"

clone_or_update() {
  name="$1"; url="$2"
  if [ -d "$DIR/$name/.git" ]; then
    echo "Updating $name"
    git -C "$DIR/$name" pull --ff-only
  else
    echo "Cloning $name"
    git clone --depth 1 "$url" "$DIR/$name"
  fi
}

# Reuse an existing checkout after the repository rename, including local changes.
# If both directories exist, keep both and use the new one.
if [ -d "$DIR/Kex-agent-ai/.git" ] && [ ! -e "$DIR/Kex-anHarness" ] && [ ! -L "$DIR/Kex-anHarness" ]; then
  mv "$DIR/Kex-agent-ai" "$DIR/Kex-anHarness"
fi
if [ -d "$DIR/Kex-anHarness/.git" ]; then
  git -C "$DIR/Kex-anHarness" remote set-url origin https://github.com/devdownin/Kex-anHarness.git
fi
clone_or_update Kex-anHarness https://github.com/devdownin/Kex-anHarness.git
clone_or_update Kafkaexplorer https://github.com/devdownin/Kafkaexplorer.git
clone_or_update kafkaconsumerautotune https://github.com/devdownin/kafkaconsumerautotune.git
clone_or_update SpectraLLM https://github.com/devdownin/SpectraLLM.git
echo "Components available in $DIR"
