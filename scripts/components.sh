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

clone_or_update Kex-agent-ai https://github.com/devdownin/Kex-agent-ai.git
clone_or_update Kafkaexplorer https://github.com/devdownin/Kafkaexplorer.git
clone_or_update kafkaconsumerautotune https://github.com/devdownin/kafkaconsumerautotune.git
clone_or_update SpectraLLM https://github.com/devdownin/SpectraLLM.git
echo "Components available in $DIR"
