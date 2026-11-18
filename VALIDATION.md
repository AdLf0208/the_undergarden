# Validation — undergarden 0.2.0 (first publication)

Run through the shared registry, one lease per step, `CARGO_INCREMENTAL=0`, `TMPDIR` beside the
crate (this box's `/tmp` tmpfs was full and rustdoc failed with `StorageFull` until it was):

```sh
ports/tools/build-slot.sh run --job undergarden-final --port ports/undergarden \
    --step build -- ports/undergarden/tools/check.sh
```

| step | result |
|---|---|
| `cargo test --offline` | 14 passed, 0 failed; doc-tests 0 |
| `cargo clippy --offline --all-targets -- -D warnings` | 0 warnings |
| `cargo fmt --check` | clean |
| `cargo horizon-mod build` (after `rm -f Cargo.lock`) | `undergarden.hmod` |
| `cargo horizon-mod check undergarden.hmod` | exit 0 — native-mod, format `native-1/0b14f8ac…/e59da909…`, 87,829 B, `719ccce2…` |
| `cargo horizon-mod fits undergarden.hmod` | exit 0 — `0b14f8a made for` |
| `python3 tools/carry.py --check` | 146 files match the mapping from the jar |
| the build run twice in one lease | byte-identical (`719ccce2…` both times) |

## Package

`ports/undergarden/undergarden.hmod` — **87,829 B**, SHA-256
`719ccce22aed9f7199f8942223b839a05de58ba5f1ac1933c515ebe2d011c3f4`, **155 entries**:
`horizon-mod.toml`, `Cargo.toml`, `src/{lib,runtime,support}.rs`, `assets/undergarden/**` (81),
`data/undergarden/**` (62) and the three `data/minecraft/tags/block/**` files (65 data files in
all), `LICENSE`, `LICENSE-NOTICE.md`, `README.md`, `uses.json`.
**No `Cargo.lock`.** `uses.json` records `handle:Registrar::register_dimension`,
`hook:register_commands`, `hook:run_mod_command` and `method:Commands::feedback`, which is the code
half wired to the SDK.

The full listing is `ports/_shared/evidence/undergarden/package.txt`; the jar measurement is
`inventory.txt`; the artefact reference checks (table ↔ biomes, surface-rule blocks, tags) are
`references.txt`; the ladder's own output is `ladder.log`.

## Not run

`tools/e2e.sh` — **no in-game claim**. No launcher at this pin ships the SDK (`9f42064` predates the
mod-API merge and has no `sdk.json`), so there is no launcher-built game to run it against.
`check-e2e-logs.py undergarden --strict` reports `logs=0`, which is the honest state.

## Gate

`python3 ports/tools/check-skills.py --notes ports/undergarden --strict` → `SKILLS GATE: PASS`.
