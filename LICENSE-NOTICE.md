# Licence provenance — The Undergarden port

**The port is MIT (rank 0, permissive).** It is local-only until the maintainer approves
publishing (`ARCHITECTURE.md` §8); MIT makes publication possible, it does not grant it.

## Where the licence was read

| Evidence | What it says |
|---|---|
| `The_Undergarden-1.21.1-0.9.6.jar`, `META-INF/neoforge.mods.toml:4` | `license = "MIT"` |
| the same file, `[[mods]]` | `modId = "undergarden"`, `version = "0.9.6"`, `authors = "quek"`, `displayName = "The Undergarden"` |
| the jar, every entry | **no** `LICENSE`, `LICENCE`, `COPYING` or `NOTICE` file is shipped inside it |
| `https://github.com/quek04/The-Undergarden` at `d901b87095e6816fa8f83d6c404fde0138b9da4a` | no `LICENSE` file in the repository root either; `gradle.properties` carries no licence key |
| `ports/_shared/licence-precheck.csv` row `undergarden` | `MIT`, rank 0, `permissive`, reviewable |

`python3 ports/tools/audit_licences.py --mod undergarden` reads the jar and records the same
string. `ports/_shared/source-map/atm10-sources.csv` still says `LicenseRef-All-Rights-Reserved`
for this mod — the jar wins over the catalogue (ruling 2026-11-09), so the row is MIT.

**The copyright line of `LICENSE` is the mod's own `authors` field.** The jar names `quek`, the
upstream repository names the same author, and no year is stated anywhere in either artefact, so
none is invented. `LICENSE` is the SPDX-standard MIT text with that holder; it is not a copy of
an upstream file, because the upstream ships none.

## What is carried, and under which licence

Every file under `assets/undergarden/` and `data/undergarden/` is the mod's own content (textures,
models, blockstates, loot tables, worldgen JSON, structure templates), taken from the jar the
mod ships and redistributed here under the MIT licence the jar declares. The Rust source in
`src/` is a clean-room rewrite written for this port from the mod's observed behaviour — no
decompiled code, no translated Java. `notes.md` records the analysis sources.

## If the maintainers want a different arrangement

The port is one `.hmod`: `horizon-mod.toml`, `src/`, `assets/`, `data/`, this notice and
`LICENSE`. Removing the mod's content leaves the Rust side, which is this campaign's own work.
