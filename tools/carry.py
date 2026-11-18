#!/usr/bin/env python3
"""Carry this slice's content out of The Undergarden 0.9.6's jar into the package.

The jar is the artefact. Everything this script writes is either a byte-for-byte copy of a jar
file or a conversion of one, and the conversion is the code below, so a reviewer can re-derive
every byte and audit a change. `--check` recomputes the whole mapping in memory and compares it
with the files on disk, which is the package's carry proof; `--write-manifest` records the
result as `carry-manifest.json`.

    python3 tools/carry.py --check
    python3 tools/carry.py --write-manifest

Two conversions beside the plain copies, both from vanilla 26.3's own data:

* 1.21.1 loot tables become 26.3's shape (a `condition` type tag instead of a `condition` name,
  `minecraft:tool/can_silk_touch` for the silk-touch predicate), exactly as the pin's
  `horizon-port-pack/src/carry.rs::upgrade_loot` does it.
* 1.21.1 worldgen JSON becomes 26.3's: `surface_rule` splits out into a `worldgen/material_rule`
  entry with block-id `result_state`s, `aquifers_enabled` becomes the absent `aquifers` object,
  `configured_feature`/`configured_carver` are 26.3's `feature`/`carver`, density-function
  arguments become `input`/`left`/`right`, `shifted_noise` becomes `noise`, the interpolator's
  cell sizes become explicit, and a biome's `effects.sky_color`/`fog_color` become the
  `minecraft:visual/*` attributes (the shape 26.3's own `worldgen/biome/plains.json` uses).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path

PORT = Path(__file__).resolve().parent.parent
JAR = (
    PORT.parent
    / "_shared"
    / "licence-cache"
    / "The_Undergarden-1.21.1-0.9.6.jar"
)
NAMESPACE = "undergarden"

#: The five table rows this slice carries, in the jar's order: the rows whose erosion, humidity
#: and temperature are the origin's 0 at depth 0, the surface rows nearest them by weirdness, and
#: the depth -1 and -2 rows of the same climate column.
BIOMES = [
    "forgotten_field",
    "ancient_sea",
    "dense_forest",
    "smogstem_forest",
    "depths",
]

#: The blocks the carried surfaces and the one carried feature place, with the declaration that
#: reproduces the jar's class: `template` is the vanilla block of the same class, and every
#: `properties` value is the Java block's own (`UGBlocks.java`, read from the upstream repository
#: at d901b87 and unchanged for these blocks since 0.9.6).
BLOCKS = {
    # strength(1.5F, 6.0F), SoundType.BASALT, requiresCorrectToolForDrops
    "depthrock": {
        "template": "minecraft:stone",
        "properties": {
            "hardness": 1.5,
            "explosion_resistance": 6.0,
            "requires_tool": True,
            "sounds": "minecraft:basalt",
        },
    },
    # strength(3.5F, 12F), SoundType.NETHER_BRICKS, requiresCorrectToolForDrops, friction(0.98F)
    "shiverstone": {
        "template": "minecraft:stone",
        "properties": {
            "hardness": 3.5,
            "explosion_resistance": 12.0,
            "requires_tool": True,
            "friction": 0.98,
            "sounds": "minecraft:nether_bricks",
        },
    },
    # strength(0.5F), SoundType.SAND; a plain Block, so dirt's template keeps it from falling as
    # the sand template's FallingBlock would
    "sediment": {
        "template": "minecraft:dirt",
        "properties": {"hardness": 0.5, "explosion_resistance": 0.5, "sounds": "minecraft:sand"},
    },
    # ofFullCopy(Blocks.DIRT)
    "deepsoil": {"template": "minecraft:dirt", "properties": {}},
    # ofFullCopy(deepsoil)
    "coarse_deepsoil": {"template": "minecraft:coarse_dirt", "properties": {}},
    # SpreadingSnowyDirtBlock over ofFullCopy(GRASS_BLOCK): grass_block's own class and `snowy`
    "deepturf_block": {"template": "minecraft:grass_block", "properties": {}},
    # BasicDeepturfBlock, strength(0.6F), SoundType.GRASS
    "ashen_deepturf_block": {
        "template": "minecraft:dirt",
        "properties": {"hardness": 0.6, "explosion_resistance": 0.6, "sounds": "minecraft:grass"},
    },
    # the same class and properties, in the frozen colour
    "frozen_deepturf_block": {
        "template": "minecraft:dirt",
        "properties": {"hardness": 0.6, "explosion_resistance": 0.6, "sounds": "minecraft:grass"},
    },
    # strength(3.0F, 12.0F), the mod's own SoundType.DREADROCK
    "dreadrock": {
        "template": "minecraft:stone",
        "properties": {
            "hardness": 3.0,
            "explosion_resistance": 12.0,
            "requires_tool": True,
            "sounds": "minecraft:deepslate",
        },
    },
    # TallDeepturfBlock extends VegetationBlock (short_grass's own class) with a 12x13x12 box
    "deepturf": {
        "template": "minecraft:short_grass",
        "properties": {},
        "shapes": {"default": [[0.125, 0.0, 0.125, 0.875, 0.8125, 0.875]]},
    },
    # The four blocks the one carried structure's templates are built from.
    # Block with ofFullCopy(Blocks.OAK_PLANKS)
    "smogstem_planks": {"template": "minecraft:oak_planks", "properties": {}},
    # RotatedPillarBlock, strength(2.0F), SoundType.WOOD, ignitedByLava
    "stripped_smogstem_log": {"template": "minecraft:oak_log", "properties": {}},
    # FenceBlock with ofFullCopy(Blocks.OAK_FENCE)
    "smogstem_fence": {"template": "minecraft:oak_fence", "properties": {}},
    # CloggrumLanternBlock is a FaceAttachedHorizontalDirectionalBlock with `face`/`facing` and a
    # wall form; the vanilla lantern is the closest template (floor and ceiling, waterlogged), so
    # the jar's blockstate is replaced by one over the template's states.
    "cloggrum_lantern": {"template": "minecraft:lantern", "properties": {}},
}

#: Vanilla tags the jar adds to, filtered to the carried blocks.
VANILLA_TAGS = {
    "minecraft:tags/block/dirt": [
        "deepturf_block",
        "frozen_deepturf_block",
        "ashen_deepturf_block",
        "deepsoil",
        "coarse_deepsoil",
    ],
    "minecraft:tags/block/animals_spawnable_on": [
        "deepturf_block",
        "frozen_deepturf_block",
        "ashen_deepturf_block",
    ],
    "minecraft:tags/block/bamboo_plantable_on": [
        "deepturf_block",
        "frozen_deepturf_block",
        "ashen_deepturf_block",
        "deepsoil",
        "coarse_deepsoil",
    ],
}

#: The blockstates whose jar form does not fit the template's states.
BLOCKSTATES = {
    # deepturf_block keeps the jar's file: grass_block's `snowy` is SpreadingSnowyDirtBlock's.
    # CloggrumLanternBlock's `face`/`facing` are its own class's states, which `minecraft:lantern`
    # does not have: the blockstate is written over the template's `hanging` and `waterlogged`,
    # and the mod's own floor and ceiling models draw it.
    "cloggrum_lantern": {
        "variants": {
            "hanging=false,waterlogged=false": {
                "model": "undergarden:block/cloggrum_lantern_floor"
            },
            "hanging=false,waterlogged=true": {
                "model": "undergarden:block/cloggrum_lantern_floor"
            },
            "hanging=true,waterlogged=false": {
                "model": "undergarden:block/cloggrum_lantern_ceiling"
            },
            "hanging=true,waterlogged=true": {
                "model": "undergarden:block/cloggrum_lantern_ceiling"
            },
        }
    },
}

#: Models carried beside the block's own (`<id>`), because a blockstate names them.
EXTRA_MODELS = {
    "deepturf_block": ["deepturf_block_snowy"],
    "stripped_smogstem_log": ["stripped_smogstem_log_horizontal"],
    "smogstem_fence": ["smogstem_fence_post", "smogstem_fence_side"],
    "cloggrum_lantern": ["cloggrum_lantern_floor", "cloggrum_lantern_ceiling"],
}

#: The one state with properties the jar's material rule names, and its template's default
#: (`minecraft:grass_block`, whose `snowy=false` is the blockstate's first variant).
DEFAULT_STATES = {
    "undergarden:deepturf_block": {"snowy": "false"},
}

#: Name of the one carried placed feature: the jar's `deepturf_patch` without its 1.21.1
#: `random_patch` wrapper, which 26.3 has no feature type for.
FEATURE = "deepturf_patch"


def fail(message: str) -> None:
    print(f"carry: {message}", file=sys.stderr)
    raise SystemExit(1)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def colour(rgb: int) -> str:
    return f"#{rgb:06x}"


def read_json(data: bytes) -> object:
    return json.loads(data.decode("utf-8"))


def dump(value: object) -> bytes:
    """The deterministic JSON this package writes: two-space indent, sorted keys, a final newline."""
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


# --- loot ---------------------------------------------------------------------------


def upgrade_loot(value: object) -> object:
    """One 1.21.1 loot value in 26.3's shape, as the pin's `upgrade_loot` does it."""
    if isinstance(value, list):
        return [upgrade_loot(item) for item in value]
    if not isinstance(value, dict):
        return value
    out = {}
    for key, item in value.items():
        if key == "conditions":
            terms = [upgrade_condition(term) for term in item]
            out["condition"] = terms[0] if len(terms) == 1 else {
                "type": "minecraft:all_of",
                "terms": terms,
            }
        elif key == "functions":
            out["modifier"] = [upgrade_loot(function) for function in item]
        elif key == "rolls" or key == "bonus_rolls":
            out[key] = type_number(item)
        elif key == "condition":
            out[key] = upgrade_condition(item)
        else:
            out[key] = upgrade_loot(item)
    return out


def type_number(value: object) -> object:
    """A number provider with its `type`, which 26.3 dispatches on and 1.21.1 inferred."""
    if not isinstance(value, dict):
        return value
    out = dict(value)
    if "type" not in out and "min" in out and "max" in out:
        out["type"] = "minecraft:uniform"
    return out


def upgrade_condition(condition: object) -> object:
    if not isinstance(condition, dict):
        return condition
    out = dict(condition)
    if "condition" in out and "type" not in out:
        out["type"] = out.pop("condition")
    for key in ("term",):
        if key in out:
            out[key] = upgrade_condition(out[key])
    if "terms" in out:
        out["terms"] = [upgrade_condition(term) for term in out["terms"]]
    if out.get("type") == "minecraft:match_tool" and silk_touch(out.get("predicate")):
        return "minecraft:tool/can_silk_touch"
    return out


def silk_touch(predicate: object) -> bool:
    if not isinstance(predicate, dict) or list(predicate) != ["predicates"]:
        return False
    inner = predicate["predicates"]
    if not isinstance(inner, dict) or list(inner) != ["minecraft:enchantments"]:
        return False
    list_ = inner["minecraft:enchantments"]
    if not isinstance(list_, list) or len(list_) != 1:
        return False
    entry = list_[0]
    return (
        entry.get("enchantments") == "minecraft:silk_touch"
        and entry.get("levels", {}).get("min", 1) <= 1
        and "max" not in entry.get("levels", {})
    )


# --- worldgen -----------------------------------------------------------------------


def density(node: object) -> object:
    """One 1.21.1 density function in 26.3's shape."""
    if isinstance(node, (int, float)):
        return node
    if isinstance(node, str):
        return node
    if not isinstance(node, dict):
        fail(f"density function {node!r} is not a function")
    kind = node["type"]
    if kind == "minecraft:y_clamped_gradient":
        low, high = sorted((node["from_value"], node["to_value"]))
        return {
            "type": "minecraft:clamp",
            "min": low,
            "max": high,
            "input": {
                "type": "minecraft:gradient",
                "axis": "y",
                "from_coordinate": node["from_y"],
                "from_value": node["from_value"],
                "to_coordinate": node["to_y"],
                "to_value": node["to_value"],
            },
        }
    out: dict[str, object] = {"type": kind}
    for key, value in node.items():
        if key == "type":
            continue
        if key == "argument":
            out["input"] = density(value)
        elif key == "argument1":
            out["left"] = density(value)
        elif key == "argument2":
            out["right"] = density(value)
        elif key == "shift_y":
            continue  # 26.3's shifted noise has no vertical shift
        elif key == "shifted_noise":
            out["type"] = "minecraft:noise"
            out["noise"] = value
        elif kind == "minecraft:shifted_noise" and key == "noise":
            out["noise"] = value
        elif key in ("when_in_range", "when_out_of_range", "input"):
            if isinstance(value, (dict, int, float)) and not isinstance(value, bool):
                out[key] = density(value)
            else:
                out[key] = value
        else:
            out[key] = value
    if kind == "minecraft:shifted_noise" or out.get("type") == "minecraft:noise":
        out["type"] = "minecraft:noise"
    if kind == "minecraft:interpolated":
        # 1.21.1 read the cell size from the noise settings' size_horizontal/size_vertical,
        # here 2 and 2; 26.3 writes it out, and vanilla's own 4/8 for the Nether's 1/2 fix the
        # relation cell = 2^(size + 1).
        out["cell_size_xz"] = 8
        out["cell_size_y"] = 8
    return out


def noise_settings(source: dict) -> dict:
    """The jar's noise settings as a 26.3 entry, its surface rule split out."""
    router = source["noise_router"]
    return {
        "noise": {"height": source["noise"]["height"], "min_y": source["noise"]["min_y"]},
        "default_block": source["default_block"]["Name"],
        "default_fluid": source["default_fluid"]["Name"],
        "sea_level": source["sea_level"],
        "disable_mob_generation": source["disable_mob_generation"],
        "legacy_random_source": source["legacy_random_source"],
        # `aquifers_enabled: false` is 26.3's absent `aquifers` object.
        "material_rule": f"{NAMESPACE}:{NAMESPACE}",
        "noise_router": {
            "chunk_surface_level": 0.0,
            "continents": router["continents"],
            "depth": density(router["depth"]),
            "erosion": router["erosion"],
            "final_density": density(router["final_density"]),
            "ridges": router["ridges"],
            "temperature": density(router["temperature"]),
            "vegetation": density(router["vegetation"]),
        },
        "spawn_target": [],
    }


def carried_biome_ids() -> list[str]:
    return [f"{NAMESPACE}:{biome}" for biome in BIOMES]


def material_rule(source: dict) -> dict:
    """The jar's surface rule as a 26.3 `material_rule` entry, trimmed to the carried biomes."""
    return rule(source["surface_rule"])


def rule(node: object) -> object:
    if isinstance(node, str):
        return node
    if not isinstance(node, dict):
        fail(f"material rule {node!r} is not a rule")
    kind = node["type"]
    if kind == "minecraft:condition":
        condition = node["if_true"]
        if isinstance(condition, dict) and condition.get("type") == "minecraft:biome":
            kept = [biome for biome in condition["biome_is"] if biome in carried_biome_ids()]
            if not kept:
                return None  # a branch for a biome this slice does not carry
            condition = dict(condition, biome_is=kept)
        return {
            "type": "minecraft:condition",
            "if_true": condition if isinstance(condition, str) else condition,
            "then_run": rule(node["then_run"]),
        }
    if kind == "minecraft:sequence":
        steps = [rule(step) for step in node["sequence"]]
        return {"type": "minecraft:sequence", "sequence": [step for step in steps if step is not None]}
    if kind == "minecraft:block":
        state = node["result_state"]
        name = state["Name"]
        properties = state.get("Properties", {})
        # 26.3 writes a bare block id; a state with non-default properties has no spelling there,
        # so only the template's own default is carried (grass_block's is `snowy=false`).
        if properties and DEFAULT_STATES.get(name) != properties:
            fail(f"surface state {state!r} is not the template's default state")
        return {"type": "minecraft:block", "result_state": name}
    # not, stone_depth, vertical_gradient, y_above and noise_threshold are already 26.3's shape
    return node


def biome(source: dict, name: str) -> dict:
    """One 1.21.1 biome as 26.3's entry: colours in attributes, no mobs, carried features only."""
    effects = source.get("effects", {})
    features: list[list[str]] = [[] for _ in range(11)]
    for slot, entries in enumerate(source.get("features") or []):
        kept = [entry for entry in entries if entry == f"{NAMESPACE}:{FEATURE}"]
        if kept and slot < len(features):
            features[slot] = kept
    attributes = {
        "minecraft:visual/sky_color": colour(effects["sky_color"]),
        "minecraft:visual/fog_color": colour(effects["fog_color"]),
        "minecraft:visual/water_fog_color": colour(effects["water_fog_color"]),
    }
    out = {
        "temperature": source["temperature"],
        "downfall": source["downfall"],
        "has_precipitation": source["has_precipitation"],
        "effects": {
            "water_color": colour(effects["water_color"]),
            "grass_color": colour(effects["grass_color"]),
            "foliage_color": colour(effects["foliage_color"]),
        },
        "attributes": attributes,
        # The one carver this slice's biomes name is `undergarden:undergarden_cave`, whose type is
        # a Java CaveWorldCarver: recorded as a gap, not carried.
        "carvers": [],
        "features": features,
    }
    del name
    return out


def feature() -> dict:
    """The configured half of `/feature`: one deepturf where the jar's random_patch placed many.

    1.21.1's `minecraft:random_patch` has no 26.3 feature type (26.3's own patches spread with
    placement modifiers instead), so the jar's 64-tries-in-a-7x3x7-box wrapper is dropped and the
    placement below does the spreading.
    """
    return {
        "type": "minecraft:simple_block",
        "to_place": {"id": f"{NAMESPACE}:deepturf"},
    }


def placed_feature() -> dict:
    """The placed half: the jar's column scan and floor filter, then a trapezoid spread."""
    return {
        "feature": f"{NAMESPACE}:{FEATURE}",
        "placement": [
            {"type": "minecraft:count", "count": 100},
            {"type": "minecraft:in_square"},
            {
                "type": "minecraft:height_range",
                "height": {
                    "type": "minecraft:uniform",
                    "min_inclusive": {"above_bottom": 0},
                    "max_inclusive": {"below_top": 0},
                },
            },
            {
                "type": "minecraft:block_predicate_filter",
                "predicate": {
                    "type": "minecraft:matching_blocks",
                    "blocks": [
                        f"{NAMESPACE}:deepturf_block",
                        f"{NAMESPACE}:deepsoil",
                        f"{NAMESPACE}:coarse_deepsoil",
                    ],
                    "offset": [0, -1, 0],
                },
            },
            {"type": "minecraft:biome"},
            {
                "type": "minecraft:offset",
                "x": {"type": "minecraft:trapezoid", "min": -7, "max": 7, "plateau": 0},
                "y": {"type": "minecraft:trapezoid", "min": -3, "max": 3, "plateau": 0},
                "z": {"type": "minecraft:trapezoid", "min": -7, "max": 7, "plateau": 0},
            },
        ],
    }


#: The one structure this slice carries: the jar's only structure whose type is vanilla's jigsaw
#: (`minecraft:jigsaw`). The other four are `undergarden:bigger_jigsaw`, a Java structure type.
STRUCTURE = "depleted_mine"


def structure(source: dict) -> dict:
    """The jar's `depleted_mine` with its spawn override emptied.

    The override names `undergarden:forgotten`, a mob this slice does not carry, so it cannot be
    spelled here; the pin does not read `spawn_overrides` for a carried structure either.
    """
    out = dict(source)
    out["spawn_overrides"] = {}
    return out


def biome_tag(source: dict) -> dict:
    """A biome tag trimmed to the biomes this slice carries, keeping the carried tag references."""
    carried = set(carried_biome_ids())
    carried_tags = {f"#{NAMESPACE}:is_depths_biome"}
    values = [
        value
        for value in source["values"]
        if value in carried or value in carried_tags
    ]
    return {"values": values}


# --- assets -------------------------------------------------------------------------


def item_definition(block: str) -> dict:
    """26.3's item model definition, which points at the carried item model."""
    return {"model": {"type": "minecraft:model", "model": f"{NAMESPACE}:item/{block}"}}


def block_declaration(block: str) -> dict:
    spec = BLOCKS[block]
    out: dict[str, object] = {"template": spec["template"], "item": True}
    if spec["properties"]:
        out["properties"] = spec["properties"]
    if "shapes" in spec:
        out["shapes"] = spec["shapes"]
    return out


def model_textures(model: dict) -> list[str]:
    return [
        value
        for value in (model.get("textures") or {}).values()
        if isinstance(value, str) and value.startswith(f"{NAMESPACE}:")
    ]


def texture_path(name: str) -> str:
    _, path = name.split(":", 1)
    return f"assets/{NAMESPACE}/textures/{path}.png"


# --- the mapping --------------------------------------------------------------------


def build() -> dict[str, bytes]:
    """Every file this package carries, path → bytes."""
    if not JAR.is_file():
        fail(f"missing the jar: {JAR}")
    files: dict[str, bytes] = {}
    jar = zipfile.ZipFile(JAR)
    names = set(jar.namelist())

    def put(path: str, data: bytes) -> None:
        files[path] = data

    def copy(path: str) -> None:
        if path not in names:
            fail(f"the jar has no {path}")
        put(path, jar.read(path))

    def jsonfile(path: str) -> dict:
        if path not in names:
            fail(f"the jar has no {path}")
        return read_json(jar.read(path))

    lang = jsonfile(f"assets/{NAMESPACE}/lang/en_us.json")
    carried_lang = {}

    for block in BLOCKS:
        # The blockstate: the jar's own, or the written one where the template's states differ.
        blockstate = f"assets/{NAMESPACE}/blockstates/{block}.json"
        if block in BLOCKSTATES:
            put(blockstate, dump(BLOCKSTATES[block]))
        else:
            copy(blockstate)
        # The jar's models; a block drawn by parts (a fence, a lantern) has no block model.
        models = []
        block_model = f"assets/{NAMESPACE}/models/block/{block}.json"
        if block_model in names:
            copy(block_model)
            models.append(block_model)
        for extra in EXTRA_MODELS.get(block, []):
            copy(f"assets/{NAMESPACE}/models/block/{extra}.json")
            models.append(f"assets/{NAMESPACE}/models/block/{extra}.json")
        copy(f"assets/{NAMESPACE}/models/item/{block}.json")
        put(f"assets/{NAMESPACE}/items/{block}.json", dump(item_definition(block)))
        # The item model's sprites are the block's textures or an item sprite of their own.
        models.append(f"assets/{NAMESPACE}/models/item/{block}.json")
        for model in models:
            data = jsonfile(model)
            for texture in model_textures(data):
                path = texture_path(texture)
                if path in names:
                    copy(path)
                elif not texture.startswith("minecraft:"):
                    fail(f"{model} names the missing texture {texture}")

        put(
            f"data/{NAMESPACE}/loot_table/blocks/{block}.json",
            dump(upgrade_loot(jsonfile(f"data/{NAMESPACE}/loot_table/blocks/{block}.json"))),
        )
        put(f"data/{NAMESPACE}/horizon/block/{block}.json", dump(block_declaration(block)))

        for key in (f"block.{NAMESPACE}.{block}", f"item.{NAMESPACE}.{block}"):
            if key in lang:
                carried_lang[key] = lang[key]

    put(f"assets/{NAMESPACE}/lang/en_us.json", dump(carried_lang))

    for tag, members in VANILLA_TAGS.items():
        namespace, path = tag.split(":", 1)
        put(f"data/{namespace}/{path}.json", dump({"values": [f"{NAMESPACE}:{block}" for block in members]}))

    put(
        f"data/{NAMESPACE}/worldgen/noise_settings/{NAMESPACE}.json",
        dump(noise_settings(jsonfile(f"data/{NAMESPACE}/worldgen/noise_settings/{NAMESPACE}.json"))),
    )
    put(
        f"data/{NAMESPACE}/worldgen/material_rule/{NAMESPACE}.json",
        dump(material_rule(jsonfile(f"data/{NAMESPACE}/worldgen/noise_settings/{NAMESPACE}.json"))),
    )
    for name in BIOMES:
        put(
            f"data/{NAMESPACE}/worldgen/biome/{name}.json",
            dump(biome(jsonfile(f"data/{NAMESPACE}/worldgen/biome/{name}.json"), name)),
        )
    put(f"data/{NAMESPACE}/worldgen/feature/{FEATURE}.json", dump(feature()))
    put(f"data/{NAMESPACE}/worldgen/placed_feature/{FEATURE}.json", dump(placed_feature()))

    # The one structure, its pools, its processor list, its set, its biome tags and its templates.
    put(
        f"data/{NAMESPACE}/worldgen/structure/{STRUCTURE}.json",
        dump(structure(jsonfile(f"data/{NAMESPACE}/worldgen/structure/{STRUCTURE}.json"))),
    )
    copy(f"data/{NAMESPACE}/worldgen/structure_set/{STRUCTURE}.json")
    copy(f"data/{NAMESPACE}/worldgen/processor_list/{STRUCTURE}_lantern_processor.json")
    for pool in ("walkway_pool", "clutter_pool"):
        copy(f"data/{NAMESPACE}/worldgen/template_pool/{STRUCTURE}/{pool}.json")
    for name in sorted(names):
        if name.startswith(f"data/{NAMESPACE}/structure/{STRUCTURE}/") and name.endswith(".nbt"):
            copy(name)
    for tag in (f"has_structure/{STRUCTURE}", "is_depths_biome"):
        put(
            f"data/{NAMESPACE}/tags/worldgen/biome/{tag}.json",
            dump(biome_tag(jsonfile(f"data/{NAMESPACE}/tags/worldgen/biome/{tag}.json"))),
        )
    return files


# --- the manifest -------------------------------------------------------------------


def manifest_path() -> Path:
    return PORT / "carry-manifest.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write the mapping into the package")
    parser.add_argument("--check", action="store_true", help="compare the package with the mapping")
    parser.add_argument("--write-manifest", action="store_true", help="record the carry proof")
    parser.add_argument("--list", action="store_true", help="print the mapping")
    args = parser.parse_args()

    expected = build()
    jar_hash = sha256(JAR.read_bytes())

    if args.write:
        for path, data in sorted(expected.items()):
            target = PORT / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        print(f"carry: wrote {len(expected)} files from {JAR.name}")
        return

    if args.list:
        for path in sorted(expected):
            print(f"{len(expected[path]):>8}  {sha256(expected[path])[:16]}  {path}")
        print(f"{len(expected)} files from {JAR.name} sha256 {jar_hash}")
        return

    if args.check:
        status = 0
        for path, data in sorted(expected.items()):
            target = PORT / path
            if not target.is_file():
                print(f"MISSING  {path}", file=sys.stderr)
                status = 1
                continue
            if target.read_bytes() != data:
                print(f"DIFFERS  {path}", file=sys.stderr)
                status = 1
        recorded = manifest_path()
        if recorded.is_file():
            manifest = read_json(recorded.read_bytes())
            if manifest.get("jar", {}).get("sha256") != jar_hash:
                print("the jar's sha256 is not the one the manifest recorded", file=sys.stderr)
                status = 1
            for path, entry in manifest.get("files", {}).items():
                if path not in expected:
                    print(f"EXTRA    {path}", file=sys.stderr)
                    status = 1
                elif sha256(expected[path]) != entry["sha256"]:
                    print(f"CHANGED  {path}", file=sys.stderr)
                    status = 1
        else:
            print("no carry-manifest.json: run --write-manifest", file=sys.stderr)
            status = 1
        if status == 0:
            print(f"carry: {len(expected)} files match the mapping from {JAR.name}")
        raise SystemExit(status)

    if args.write_manifest:
        manifest = {
            "jar": {"name": JAR.name, "bytes": JAR.stat().st_size, "sha256": jar_hash},
            "files": {
                path: {"bytes": len(data), "sha256": sha256(data)}
                for path, data in sorted(expected.items())
            },
        }
        manifest_path().write_bytes(dump(manifest))
        print(f"carry: {len(expected)} files recorded in {manifest_path()}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
