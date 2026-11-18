#!/usr/bin/env bash
# The SDK ladder for this port, inside one build-slot lease:
#
#   ports/tools/build-slot.sh run --job undergarden-port --port ports/undergarden \
#       --step build -- ports/undergarden/tools/check.sh
#
# The launcher builds the package from `horizon-mod.toml`; this script proves the crate
# compiles against the pinned SDK, that the package is well formed, that it still fits the
# build it declares, and that every carried byte is what `tools/carry.py` derives from the jar.
# It runs from the port directory (the slot runner starts in the campaign root) and never
# passes `--target-dir`.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

# `/tmp` is a full tmpfs on this box; rustdoc and rustc need scratch space beside the crate.
export TMPDIR=${TMPDIR:-$PWD/target/tmp}
mkdir -p "$TMPDIR"

status=0
step() {
    echo "== $*"
    "$@" || status=1
}

step env CARGO_INCREMENTAL=0 cargo test --offline
step env CARGO_INCREMENTAL=0 cargo clippy --offline --all-targets -- -D warnings
step env CARGO_INCREMENTAL=0 cargo fmt --check
# `cargo test` writes a root Cargo.lock, and the packer would ship it: the package carries the
# crate's sources and content, never the lock (the launcher resolves against its own SDK).
rm -f Cargo.lock
step env CARGO_INCREMENTAL=0 cargo horizon-mod build
# The deliverable is the port root's copy of what was just built: `check` and `fits` below must
# see the bytes this run produced, not a previous run's.
step cp target/horizon-mod/undergarden.hmod ./undergarden.hmod
# Always name the file: `check` with no argument compiles wasm instead of checking the package.
step cargo horizon-mod check undergarden.hmod
step cargo horizon-mod fits undergarden.hmod
step python3 tools/carry.py --check
echo "== package"
stat -c '%s bytes  %n' undergarden.hmod || status=1
sha256sum undergarden.hmod || status=1
echo "CHECK_EXIT:$status"
exit $status
