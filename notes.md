# The Undergarden — port notes

**Class + tier:** `content` / `deep` (principal, P0). `ports/_shared/source-map/atm10-sources.csv`
and the ledger row mirror `horizon/docs/modpacks/atm10-mods.csv`.
**Licence:** MIT → rank 0 permissive, read from the jar's `META-INF/neoforge.mods.toml`
(`license = "MIT"`). Local-only until the maintainer approves publishing (`ARCHITECTURE.md` §8);
provenance in [`LICENSE-NOTICE.md`](LICENSE-NOTICE.md).
**Approach:** the tier's own shape from `horizon/docs/modpacks.md` — **carry-over** for everything
the jar states as data (blocks, loot, biomes, noise settings, surface rule, one feature, one
structure) and an **agent port** for the one code half the SDK needs (registering the level and
answering its table), with the numbers in a pure `runtime.rs`.
**Pin:** SDK `0b14f8acfd97fa2c750e42795249dcc981178ca4`, mixins
`e59da9094f0c2fdda6c627fe9eff22dec6a906f0`, `api = "0.2"`, game 26.3, launcher ≥ 0.2.70.
**Delivery:** one flat `.hmod` (`undergarden.hmod`), `version = "0.2.0"`, first publication.

## Provenance

| | |
|---|---|
| jar | `The_Undergarden-1.21.1-0.9.6.jar`, **47,839,987 B**, SHA-256 `49e3db6ce2cf6864e9d45f0633de95bc3ef72cbd5ebffee493fca7198d30ccb0`, in `ports/_shared/licence-cache/` |
| jar's manifest | `modId = "undergarden"`, `version = "0.9.6"`, `authors = "quek"`, `license = "MIT"`, `minecraft = "[1.21]"` |
| upstream repo | `https://github.com/quek04/The-Undergarden` at `d901b87095e6816fa8f83d6c404fde0138b9da4a` (2026-11-14) |

The repository's default branch is **0.9.8 for Minecraft 26.1.2**, not the jar's 0.9.6 for 1.21.1,
and it has no tag or branch for the 1.21.1 line. It was read as an **analysis aid only**, for the
behaviour and property values the jar cannot show (its classes are compiled), and every number
taken from it is named below. Where the two disagree the **jar wins** — it is the artefact.

Files read there: `world/gen/UGNoiseBasedChunkGenerator.java` (the generator's whole body),
`registry/UGDimensions.java` (the dimension type and noise settings bootstrap),
`registry/UGBlocks.java` (block ids, classes and `Properties`), `block/TallDeepturfBlock.java`,
`block/CloggrumLanternBlock.java`. The clone under `/tmp/opencode/` is deleted; nothing from the
repository is copied, and the port is a clean-room Rust rewrite of the behaviour.

## The jar, measured (`ports/_shared/evidence/undergarden/inventory.txt`)

3,880 files, 47,839,987 B, **427 classes**, and:

| family | files | | family | files |
|---|---:|---|---|---:|
| `assets/undergarden/blockstates` | 238 | | `data/undergarden/loot_table` | 261 |
| `assets/undergarden/models` | 774 | | `data/undergarden/recipe` | 340 |
| `assets/undergarden/textures` | 489 | | `data/undergarden/structure` (`.nbt`) | 142 |
| `assets/undergarden/sounds` | 312 | | `data/undergarden/tags` | 43 |
| `assets/undergarden/lang` | 11 | | `data/undergarden/advancement` | 377 |
| `assets/undergarden/particles` | 23 | | `data/undergarden/dimension(_type)` | 2 |

`data/undergarden/worldgen`, **175 files**: `biome` 20, `configured_carver` 1,
`configured_feature` 60, `noise_settings` 1, `placed_feature` 65, `processor_list` 5,
`structure` 4, `structure_set` 4, `template_pool` 15.

**The brief's counts were high and the artefact wins:** 35 → **20** `worldgen/biome` files, 206 →
**175** worldgen JSONs, "10 structure files" → **4 structures + 4 structure sets**, 239 → **238**
blockstates. The number that did match is the mod's 427 classes and the full-dimension shape.

## The slice's boundary

In (the ceiling in the brief):

1. **The level exists and is enterable** — `undergarden:undergarden` registered through
   `Registrar::register_dimension` with the jar's dimension type: `min_y -64`, `height 192`,
   `logical_height 192`, `has_ceiling`, fixed time, no skylight, `coordinate_scale 4.0`,
   `ambient_light 0.1`, monster light 0–7 / block-light limit 0, `infiniburn` the Overworld's,
   no raids, piglins do not zombify, `skybox` none, `cardinal_light` nether, sky light level 4.
   Registering it makes the level and its type pack entries *below every data pack*, so a pack can
   still replace either.
2. **The biome source is the jar's table, as data** — `BiomeSourceKind::Points`, the SDK's
   `minecraft:multi_noise` with an **inline `biomes` list**, for five rows. **Carried as data;
   no `BiomeSource` trait implementation was written** (the brief's "say which of the two").
3. **The surfaces and the blocks they place** — the jar's `noise_settings` and its surface rule as
   26.3 data (a `worldgen/material_rule` entry), and the 9 blocks the rule names plus the one
   plant a carried feature places: **14 blocks** carrying 14 blockstates, 18 block models, 14 item models, 20 textures,
   loot tables, lang, the three vanilla tags the jar adds to, and the four 26.3 item-model
   definitions.
4. **One data-defined structure** — `undergarden:depleted_mine`, whose type is vanilla's
   `minecraft:jigsaw`: 18 templates, 2 template pools, 1 processor list, its structure set and the
   two biome tags, trimmed to the carried biome.
5. **`/undergarden status`** — the level id, the biome/row counts, the depth bands and one
   seed-independent cell per carried row, plus `/undergarden climate <six numbers>` for any cell.
6. **`src/runtime.rs`** — the table, `depth_at`, `biome_at` (vanilla's fitness: the six squared
   distances plus the row's offset), the surface model and the readout; 14 tests, no `mod_api` type.

Out, and recorded under *Gaps* below: the other 15 biomes, every mob, the Java generator, carver
and structure types, ores, trees, crops, the progression and the custom effects id.

## The biome source, and its stated simplification

`minecraft:multi_noise` is a vanilla *type*, so the table is data. The SDK's `Points` kind writes
exactly the jar's shape back out — `"type": "minecraft:multi_noise"` with an inline `biomes` list
of `Climate.ParameterPoint`s — and vanilla's sampler then computes the climate and picks the
nearest row. `possible_biomes` is the five ids.

The five rows carried, verbatim from
`data/undergarden/dimension/undergarden.json` (`generator.biome_source.biomes`), in the jar's own
order (which is also the tie-break order):

| biome | continentalness | erosion | humidity | temperature | weirdness | depth | offset |
|---|---:|---:|---:|---:|---:|---:|---:|
| `undergarden:forgotten_field` | 0.0 | 0.0 | 0.0 | 0.0 | −0.75 | 0.0 | 0.0 |
| `undergarden:ancient_sea` | 0.0 | 0.0 | 0.0 | 0.0 | −0.75 | −1.0 | 0.0 |
| `undergarden:dense_forest` | −0.15 | 0.0 | 0.0 | 0.0 | 0.45 | 0.0 | 0.0 |
| `undergarden:smogstem_forest` | 0.1 | 0.0 | 0.0 | 0.0 | 0.6 | 0.0 | 0.0 |
| `undergarden:depths` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | −2.0 | 0.0 |

They are the table's **origin column**: the rows whose erosion, humidity and temperature are the
origin's `0.0` at depth 0 and at the router's two deeper bands, plus the two surface rows at that
same erosion nearest the origin by weirdness (`dense_forest`, `smogstem_forest`). The jar's own
order is kept because vanilla's nearest-row test is a strict `<`, so an exact tie answers the
earlier row.

**Simplification, stated:** cells outside these five points answer the **nearest carried row**
(vanilla's fitness over the rows that exist). Nothing is mapped to a vanilla biome and no cell
falls through to an unregistered one; the dimension therefore generates with five biomes where the
jar has 20, and which of the five a given cell gets is decided by the same fitness the jar's 30-row
table uses. `src/runtime.rs`'s `biome_at` is that same function, tested at each row, at a tie, at
an offset and at cells outside the table.

The depth bands are the jar's, not vanilla's: `noise_settings.underground.noise_router.depth` is
two `range_choice`s on `minecraft:y` — **0 ≤ y < 32 → −1.0**, **−64 ≤ y < 0 → −2.0**, else **0.0** —
so the sea rows sit under y 32 (the jar's `sea_level`) and the depths rows under y 0.
`runtime::depth_at` is that function, tested at both boundaries and outside them.

## 1.21.1 → 26.3 conversions (all in `tools/carry.py`, reversible by reading it)

Every carried file is either a byte-for-byte jar copy or one of these conversions. The conversion
is code, not a hand edit, so `tools/carry.py --check` re-derives all 146 files and compares them.

| 1.21.1 | 26.3 | evidence for the target shape |
|---|---|---|
| `data/<ns>/loot_table/…` with `conditions: [{"condition": …}]` | one `condition` object with a `type`, `minecraft:tool/can_silk_touch` for the silk-touch predicate, `modifier` for `functions` | the pin's own `horizon-port-pack/src/carry.rs::upgrade_loot` |
| biome `effects.sky_color`/`fog_color`/`water_fog_color` | the `minecraft:visual/*` attributes; `effects` keeps `water_color`, `grass_color`, `foliage_color` | `worldgen/biome/plains.json` and `horizon-client-render/src/biome.rs:239-248` |
| biome `spawners`/`spawn_costs`/`creature_spawn_probability` | the `minecraft:gameplay/natural_mob_spawns` attribute | same (not carried: the mobs are out of the slice) |
| biome `carvers: {"air": id}` | `carvers: [id]` | `plains.json` |
| `worldgen/configured_feature`, `worldgen/configured_carver` | `worldgen/feature`, `worldgen/carver` | `horizon-world/src/worldgen/overrides.rs:29` ("26.3's names") |
| `noise_settings.surface_rule` | a `worldgen/material_rule` entry, `"material_rule": "…"`, with block-id `result_state` strings | `worldgen/material_rule/overworld.json`, `bedrock_floor.json` |
| `noise_settings.aquifers_enabled: false` | the absent `aquifers` object | `worldgen/noise_settings/nether.json` |
| `noise_settings.noise.{size_horizontal,size_vertical}` | the interpolator's explicit `cell_size_xz`/`cell_size_y` (**8/8**, from the jar's 2/2 and vanilla's 1/2 → 4/8) | `nether.json`'s `interpolated` |
| a 15-key `noise_router` | 26.3's 8 keys (`chunk_surface_level` 0.0, `continents`, `depth`, `erosion`, `final_density`, `ridges`, `temperature`, `vegetation`) | `nether.json` |
| density `argument`/`argument1`/`argument2` | `input`/`left`/`right` | `density_function/overworld/*.json` |
| `minecraft:shifted_noise` (with `shift_y`) | `minecraft:noise` with `shift_x`/`shift_z` | `density_function/overworld/temperature.json` |
| `minecraft:y_clamped_gradient` | `minecraft:clamp` over `minecraft:gradient` | `density_function/overworld/caves/*.json`, `end/islands.json` |
| a block declared in Java | `data/<ns>/horizon/block/<id>.json` naming a vanilla **template** of the same class | `docs/mods.md` §"Content mods (API 0.2)" |
| a block item | `assets/<ns>/items/<id>.json`, 26.3's item-model definition, pointing at the carried item model | `assets/minecraft/items/stone.json` |

## Jar → package map

| jar | package |
|---|---|
| `data/undergarden/dimension/undergarden.json`, `dimension_type/undergarden.json` | `src/support.rs::settings()` — the registrar writes both entries |
| `dimension.…biome_source.biomes` (30 rows) | `src/runtime.rs::POINTS` (5 rows) → `BiomePoint`s in `settings()` |
| `data/undergarden/worldgen/noise_settings/undergarden.json` | `data/undergarden/worldgen/noise_settings/undergarden.json` (converted) + `…/material_rule/undergarden.json` (the surface rule, converted, trimmed to the carried biomes) |
| `data/undergarden/worldgen/biome/{forgotten_field,ancient_sea,dense_forest,smogstem_forest,depths}.json` | the same five paths, converted |
| `data/undergarden/worldgen/configured_feature/deepturf_patch.json`, `placed_feature/deepturf_patch.json` | `data/undergarden/worldgen/feature/deepturf_patch.json`, `placed_feature/deepturf_patch.json` (re-shaped, see Gaps 5) |
| `data/undergarden/worldgen/structure/depleted_mine.json` + `structure_set` + 2 `template_pool` + 1 `processor_list` + `structure/depleted_mine/**/*.nbt` (18) | the same paths (`spawn_overrides` emptied) |
| `data/undergarden/tags/worldgen/biome/is_depths_biome.json`, `…/has_structure/depleted_mine.json` | the same paths, trimmed to `undergarden:depths` |
| `data/minecraft/tags/block/{dirt,animals_spawnable_on,bamboo_plantable_on}.json` | the same three paths, filtered to the carried blocks |
| `assets/undergarden/blockstates/{14}.json`, `models/block/**` (18), `models/item/**` (14), `textures/**` (20), `lang/en_us.json`, `data/…/loot_table/blocks/{14}.json` | the same paths (loot converted); the lang file keeps the 14 carried keys |
| 14 Java block classes | `data/undergarden/horizon/block/{14}.json` — template + the class's own numbers |
| — | `src/lib.rs`, `src/runtime.rs`, `src/support.rs`, `horizon-mod.toml`, `Cargo.toml` |

The 14 blocks: `depthrock`, `shiverstone`, `sediment`, `deepsoil`, `coarse_deepsoil`,
`deepturf_block`, `ashen_deepturf_block`, `frozen_deepturf_block`, `dreadrock`, `deepturf` (the one
plant), `smogstem_planks`, `stripped_smogstem_log`, `smogstem_fence`, `cloggrum_lantern`. Nine are
what the surface rule names, one is what the carried feature places, four are what the carried
structure's templates are built from.

Templates, each the vanilla block of the same class (`block-behaviours.json` of the prepared 26.3
resources gave the class chains): `stone` for depthrock/shiverstone/dreadrock, `dirt` for
sediment/deepsoil/ashen/frozen deepturf, `coarse_dirt` for coarse deepsoil, `grass_block` for
deepturf_block (both are `SpreadingSnowyDirtBlock`, with the `snowy` state the jar's blockstate
uses), `short_grass` for deepturf (`VegetationBlock`), `oak_planks`/`oak_log`/`oak_fence`/`lantern`.

## Verification

| step | command | result |
|---|---|---|
| unit tests | `cargo test --offline` | **14 passed**, 0 failed (1 doc-test harness, 0 cases) |
| lints | `cargo clippy --offline --all-targets -- -D warnings` | **0 warnings** |
| format | `cargo fmt --check` | clean |
| package | `cargo horizon-mod build` | `undergarden.hmod`, **87,829 B**, SHA-256 `719ccce22aed9f7199f8942223b839a05de58ba5f1ac1933c515ebe2d011c3f4`, **155 entries** |
| reproducible | the build run twice in one lease | byte-identical (`719ccce2…` both times) |
| registry check | `cargo horizon-mod check undergarden.hmod` | exit 0 — `undergarden 0.2.0 (native-mod, format native-1/0b14f8ac…/e59da909…, for 26.3)` |
| fits | `cargo horizon-mod fits undergarden.hmod` | exit 0 — `0b14f8a made for` |
| carry proof | `python3 tools/carry.py --check` | **146 files** match the mapping from the jar |
| in game | `tools/e2e.sh` | **not run: no launcher ships the SDK at this pin** |

The package holds `horizon-mod.toml`, `Cargo.toml`, `src/`, `assets/`, `data/`, `LICENSE`,
`LICENSE-NOTICE.md` and the generated `uses.json`, and **no `Cargo.lock`** (the ladder deletes the
root one `cargo test` writes before packing). Logs:
`ports/_shared/evidence/undergarden/{ladder.log,package.txt,inventory.txt,references.txt}`.

`tools/e2e.sh` is written for a launcher-built game and **is not claimed**. It is fail-capable by
construction: `SELFTEST=1` corrupts the expected biome count, so a run that passed for the wrong
reason still exits 1.

Skills: superpowers/using-superpowers,brainstorming,writing-plans,test-driven-development,verification-before-completion; BeautifulRust/rust-best-practices,rust-port

## Gaps (each with the artefact's file and line)

1. **`blocked(undergarden:noise)` — the Java chunk generator.** `data/undergarden/dimension/undergarden.json:1`
   names `"generator": {"type": "undergarden:noise", …}`;
   `world/gen/UGNoiseBasedChunkGenerator.java:14-37` shows the class is a `NoiseBasedChunkGenerator`
   whose only change is the fluid picker (`globalFluidPicker = y <= 0 ? air : water`). The SDK
   names only the built-in `minecraft:noise` (`world/dimension.rs:10`), and the *shape* — a
   noise-based generator fed by the carried `noise_settings` — is exactly expressible, so the port
   uses `minecraft:noise` and records the difference: below y 0 the game's own fluid picker runs
   instead of the mod's "air". Faithful terrain, surface rule, depth bands and sea level (32) come
   from the carried settings.
2. **`blocked(undergarden:undergarden_cave)` — the Java carver.**
   `data/undergarden/worldgen/configured_carver/undergarden_cave.json:1` is
   `"type": "undergarden:undergarden_cave"` (a `CaveWorldCarver` subclass), and 26.3's carver shape
   also gained a `count` (`worldgen/carver/cave.json`). The five carried biomes therefore have
   `"carvers": []`: no caves are carved, and the world is the noise generator's rock plus the
   material rule.
3. **`blocked(undergarden:bigger_jigsaw)` — three of the four structures.**
   `…/worldgen/structure/{catacombs,denizen_camp,forgotten_vestige}.json:1` each name
   `"type": "undergarden:bigger_jigsaw"`; only `depleted_mine.json:1` is `minecraft:jigsaw` and is
   the one carried.
4. **`blocked(undergarden:boulder)` — the two rock features.**
   `…/configured_feature/{depthrock_rock,shiverstone_rock}.json:1` are
   `{"type": "undergarden:boulder"}`, a Java feature type; `docs/modpacks.md:170` carries only the
   vanilla feature types. Dropped rather than substituted.
5. **`minecraft:random_patch` has no 26.3 feature type.** The jar's `deepturf_patch`
   (`…/configured_feature/deepturf_patch.json:1`) is a `random_patch` of 64 tries in a 7×3×7 box
   around a `simple_block`. 26.3's own patches (`worldgen/feature/grass.json`,
   `placed_feature/patch_grass_plain.json`) spread with placement modifiers instead, so the carried
   feature is the inner `simple_block` and the spreading is a `count` + `in_square` +
   `height_range` + floor filter + `biome` + trapezoid `offset` in the placed half. **Deviation:**
   one plant per attempt with a trapezoid spread, not 64 tries per patch cell; the density is
   comparable, the per-attempt clustering is not reproduced.
6. **No mobs.** The biomes' `spawners` (`…/biome/forgotten_field.json:… "spawners"`) and the
   structure's `spawn_overrides` (`…/structure/depleted_mine.json:1`) name `undergarden:forgotten`
   and 15 more entity types; no entity type is carried, so the spawn lists are omitted and the
   override is emptied. The attribute the game reads for natural spawns
   (`minecraft:gameplay/natural_mob_spawns`) is therefore absent and the level has no natural mobs.
7. **The custom `effects` id.** `dimension_type/undergarden.json` names
   `"effects": "undergarden:undergarden"`, a 1.21 `DimensionSpecialEffects` id with no 26.3
   equivalent in the SDK. Its two colours are reproduced from the only place the jar spells them
   (the biomes' `effects`): `sky_color`/`fog_color` `#121909`. Music, ambience, mood sounds, the
   ash particle and the fog distances are not carried.
8. **Java block behaviour beyond a template.** Four small ones, all recorded rather than faked:
   `deepturf_block`'s spreading onto deepsoil (`SpreadingDeepturfBlock`; on the `grass_block`
   template the game spreads vanilla grass onto vanilla dirt, of which this level has none);
   `ashen`/`frozen_deepturf_block`'s random ticks (`BasicDeepturfBlock`, on `dirt` with no
   `random_ticks`); `deepsoil`'s farmland conversion (`DeepsoilBlock`); `cloggrum_lantern`'s wall
   placement (`CloggrumLanternBlock extends FaceAttachedHorizontalDirectionalBlock`, `face`+`facing`)
   — the carried blockstate is written over the vanilla lantern's `hanging`/`waterlogged` and draws
   the mod's own floor and ceiling models, so it stands and hangs but does not attach to walls.
9. **The other 15 biomes, ores, trees, crops, the progression and the GUI** — out of the slice by
   the brief's ceiling, not by an API gap. They are the next slices.
10. **No in-game run.** No launcher at this pin ships the SDK, so no launcher-built game exists
    here; `tools/e2e.sh` is written and unclaimed. The load-time questions this leaves open are the
    ones only a game can answer: that the converted `noise_settings`/`material_rule` build a
    generator, that the five biomes resolve, and that the carried structure places.

## Upstream defects fixed

**None found in this slice's scope.** How that was checked, against the artefact rather than by
reading:

- The dimension's table and its biome registry agree: all **30** rows name one of the **20**
  `worldgen/biome` files, and all 20 biomes appear in the table (`references.txt`).
- The surface rule names exactly **9** mod blocks, and every one exists as a blockstate in the jar;
  no `result_state` names a block the jar does not register.
- The one carried structure's biome tag resolves
  (`#undergarden:is_depths_biome` → four existing biomes), and its start height band
  (−31…−54) lies inside the depth −2 band its biome is chosen for.
- The biome table's depth values are the router's own: every row is keyed to one of the three
  bands `0.0` / `−1.0` / `−2.0` that `noise_router.depth` produces, so no row is unreachable.

Two things that *look* like defects and are not: the four biomes the table never names are absent
because every one of the 20 is named; and `deepturf_patch`'s three-block floor filter (it omits the
ashen and frozen deepturf blocks) is the mod's design — those two biomes have their own patch
features, which this slice does not carry.

## Traps this port paid for (new ones first)

1. **`cargo test` writes a root `Cargo.lock` and the packer ships it.** The ladder deletes it
   before `cargo horizon-mod build`, or the package carries a lock the brief forbids.
2. **This box's `/tmp` tmpfs was 100 % full**, and `rustdoc` failed with `StorageFull` *after* the
   14 tests passed — a green test run that is not a green `cargo test`. The ladder exports
   `TMPDIR` beside the crate so the doctest step has scratch space.
3. **A tag reference is not a biome id.** Filtering a carried biome tag to "values that are carried
   biomes" emptied `has_structure/depleted_mine` (its only value is `#undergarden:is_depths_biome`),
   which would have left the structure with no biome. Tag references to carried tags are kept.
4. **26.3 splits what 1.21.1 kept together**: the surface rule is now its own registry entry
   (`worldgen/material_rule`), `aquifers` is an object (absent = off) and the noise router has 8
   keys, so a verbatim carry of `noise_settings` cannot load.
5. **`result_state` is a block id string in 26.3**, not a `{Name, Properties}` object; the jar sets
   `snowy=false` on one surface state, which is the template's default, so the id alone is exact —
   the converter refuses any state that is not the template's default rather than dropping it.
6. **A blockstate's states must be the template's.** `cloggrum_lantern`'s jar blockstate is keyed by
   `face`, which `minecraft:lantern` does not have; carrying it verbatim would have been a load
   error, so it is rewritten over the template's states.
7. **A fence and a lantern have no `models/block/<id>.json`**: their blockstates name parts. The
   carry copies the parts (`_post`, `_side`, `_floor`, `_ceiling`) instead.
8. The brief's inventory counts are high (see above); the jar's are the ones in this file.

## Next slices

1. **Biomes** — the remaining 15 rows and their JSONs, with the features and spawns they need (ores,
   trees, mushrooms), which is where the mod's own look actually comes from.
2. **The carver** — revisit only if the SDK gains a carver type a mod may register
   (`blocked(undergarden:undergarden_cave)`); until then caves stay out.
3. **The three `bigger_jigsaw` structures** — revisit when a Java structure type can be expressed,
   or carry their templates with a vanilla jigsaw shape if the pieces allow it (they were built for
   the bigger type's own connector placement).
4. **Mobs** — the Forgotten, the Rotspawn and the rest, with the biomes' spawn lists restored and
   the structure's `spawn_overrides` back.
5. **In game** — run `tools/e2e.sh` on the first launcher that ships the SDK, and record the
   transcript here.
