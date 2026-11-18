# The Undergarden — a ceiling dimension for Horizon

A partial port of **The Undergarden 0.9.6** (quek, MIT) for Minecraft Java **26.3** on Horizon's
SDK (`api = "0.2"`, build `0b14f8ac…`, launcher ≥ 0.2.70). One flat `.hmod` carries the code and
the content.

## What this slice does

- Registers the level **`undergarden:undergarden`** with the jar's dimension type: a bedrock
  ceiling, fixed time, `min_y -64`, height 192, coordinate scale 4, ambient light 0.1, no
  skylight, no raids.
- Carries the jar's **noise settings** as 26.3 data (`worldgen/noise_settings` plus
  `worldgen/material_rule`), so the level's terrain and the mod's **surfaces** — depthrock,
  sediment, deepsoil, coarse deepsoil, the three deepturf blocks, dreadrock, shiverstone — are the
  mod's own.
- Answers its **multi-noise table** for five of the mod's biomes
  (`forgotten_field`, `ancient_sea`, `dense_forest`, `smogstem_forest`, `depths`) through the
  registrar's own `Points` biome source, so the table is data, not a rewrite.
- Carries 14 blocks with their blockstates, models, textures, loot tables, lang, the vanilla tags
  they join and the one pure-data feature family (`deepturf_patch`).
- Carries the one structure whose structure type is vanilla's jigsaw, **`depleted_mine`**, with its
  two template pools, processor list, structure set, biome tags and 18 templates.
- Adds **`/undergarden status`** and **`/undergarden climate …`**, which answer the registered
  level id, the biome and row counts, and one seed-independent cell per row.

## What it does not do (recorded in `notes.md`)

The other 16 biomes, every mob, the Java chunk generator (`undergarden:noise`), the Java carver,
the three `undergarden:bigger_jigsaw` structures, ores, trees, crops, progression and the custom
`effects` id. A Java type the game cannot express is a stated gap, never a vanilla substitute.

## Build and verify

```sh
ports/tools/build-slot.sh run --job undergarden-ladder --port ports/undergarden \
    --step build -- ports/undergarden/tools/check.sh
```

`tools/check.sh` runs `cargo test`, clippy, `cargo fmt --check`, `cargo horizon-mod build`, then
`check` and `fits` on the package, and finally `tools/carry.py --check`, which proves every
carried byte is what the mapping derives from the jar.

`tools/e2e.sh` is the in-game scenario. **It has not been run**: no launcher ships the SDK at this
pin, so no launcher-built game exists here. It is written and fail-capable (`SELFTEST=1`).

## Licence

MIT (rank 0), read from the jar's `META-INF/neoforge.mods.toml`. Local-only until the maintainer
approves publishing. `LICENSE` and `LICENSE-NOTICE.md` record the provenance.
