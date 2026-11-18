# The Undergarden — a Horizon port

**The Undergarden** is a Minecraft mod. Repository for the Undergarden, a Minecraft dimension mod. This repository is a **port of it to [Horizon](https://github.com/horizon-rust/horizon)**, the Rust engine for Minecraft Java 26.3. It carries the complete source of the port plus the content files it ships, and installs as a single `.hmod` package.

Upstream: [quek04/undergarden](https://github.com/quek04/undergarden) — licence **MIT**.

| | |
|---|---|
| Upstream mod | The Undergarden ([source](https://github.com/quek04/undergarden)) |
| Ported to | Horizon 0b14f8a, Minecraft Java 26.3, mod API `0.2` |
| Package | `undergarden.hmod` (install it with the Horizon launcher) |
| Licence | **MIT** — the upstream mod's licence; see [Licence and credit](#licence-and-credit) |

## What this port implements

### What this slice does

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

## Not yet ported

- **`blocked(undergarden:noise)` — the Java chunk generator.** `data/undergarden/dimension/undergarden.json:1`
- **`blocked(undergarden:undergarden_cave)` — the Java carver.**
- **`blocked(undergarden:bigger_jigsaw)` — three of the four structures.**
- **`blocked(undergarden:boulder)` — the two rock features.**
- **`minecraft:random_patch` has no 26.3 feature type.** The jar's `deepturf_patch`
- **No mobs.** The biomes' `spawners` (`…/biome/forgotten_field.json:… "spawners"`) and the
- **The custom `effects` id.** `dimension_type/undergarden.json` names
- **Java block behaviour beyond a template.** Four small ones, all recorded rather than faked:

## Installing

1. Install the [Horizon launcher](https://github.com/horizon-rust/horizon/releases) (0.2.70 or newer).
2. Add `undergarden.hmod` to the instance's mods.
3. The package is pinned to a specific Horizon build; the launcher checks that pin.

## Licence and credit

The Undergarden was created by its upstream authors; the code, models and assets in the original mod
remain theirs and are used here under **MIT**. The Rust in this repository is a clean-room
rewrite for Horizon, not a translation of the original source.

- `LICENSE` — the upstream licence text.
- `LICENSE-NOTICE.md` — what this port carries and where it came from.
- The upstream project: https://github.com/quek04/undergarden

## Technical details

```
horizon-mod.toml   package manifest (id, version, api, [native] pin)
Cargo.toml         the crate; depends on `horizon-mod-api` from the fetched SDK
src/               lib.rs (the one `impl Hooks`), runtime.rs (pure logic + tests), glue
assets/ data/      the content the package ships
tools/             content generators and the e2e scenario
```

- Build: `cargo horizon-mod build` (packages; it does not compile against the game).
- Test: `cargo test`, `cargo clippy --all-targets -- -D warnings`.
- In-game: `ports/tools/launcher-game.sh run undergarden` in the campaign tree, or install the
  `.hmod` and play; the harness scenario is `tools/e2e.sh`.

This repository is generated from the campaign's port at `ports/undergarden/`; the port's own
`notes.md` is the full record (decisions, traps, evidence).
