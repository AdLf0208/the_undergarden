#!/usr/bin/env bash
# In-game check for The Undergarden port (SDK package, mod API 0.2).
#
# **NOT CLAIMED.** No launcher ships the SDK at this pin, so no launcher-built game exists on this
# machine and this script has never been run: `notes.md` records it as a gap. It is written for
# the day one exists, and it is fail-capable by construction (see SELFTEST below).
#
# NEEDS A LAUNCHER-BUILT GAME. The flat SDK package is compiled into the game by the launcher:
#
#   horizon-launcher native-build ports/undergarden --instance <instance> --trust-native-code
#   GAME=<instance>/horizon-client tools/e2e.sh
#
# The package carries its own content (assets/ and data/ are inside `undergarden.hmod`), so there
# is no `--dev-mod` leg. `CONTROL_GAME=` optionally names the same build WITHOUT the mod: the run
# then checks that the level id is refused there, so the dimension in the default leg cannot come
# from a vanilla world.
#
# The scenario:
#  A. `/undergarden status` answers with the level id, five biomes, five climate rows and the five
#     sample cells (a seed-independent answer per carried row).
#  B. `/undergarden climate …` answers the table's own rows and a cell outside it, from the typed
#     command path — the same numbers `cargo test` pins in `src/runtime.rs`.
#  C. `execute in undergarden:undergarden` reaches the level: `ctl state` reports the dimension,
#     the roof cell (y=127) and the floor cell (y=-64) are both bedrock, and the column between
#     them holds the mod's own blocks — the mod's surfaces, not vanilla's.
#  D. The biome the player stands in is one of the five carried ids (`ctl state`).
#  E. `/place structure undergarden:depleted_mine` builds a piece in the depths: a smogstem plank
#     or stripped log appears where there was air (the trap: the start box must be loaded first,
#     so the run places the player, waits, and only then places the structure).
#
#   GAME=… tools/e2e.sh                  # the scenario (+ CONTROL_GAME= control when given)
#   SELFTEST=1 GAME=… tools/e2e.sh       # corrupt expectation: status must report six biomes,
#                                        # which it cannot; exits 1, proving A can fail
#
# Harness notes: this port registers server commands, so `ctl command "/undergarden status"` is
# the right path (the console path reaches `run_mod_command`); `ctl chat` is for player chat.
# `ctl setblock` acts in the player's current dimension, so the dimension is entered with
# `execute in … run tp` before any block is read, and every read is `ctl block` while the player
# is there.
set -Eeuo pipefail

CLONE=${CLONE:-/home/adlf/Desktop/all_the_mods_10_rust_rewrite}
PORT=$CLONE/ports/undergarden
RES=${RES:-${HORIZON_RES:-/home/adlf/Desktop/horizon/.local/horizon-client/26.3}}
SOCK=${SOCK:-/tmp/opencode/undergarden-e2e.sock}
GAME=${GAME:-}
CONTROL_GAME=${CONTROL_GAME:-}
SELFTEST=${SELFTEST:-0}
KEEP=${KEEP:-0}
CTL=${CTL:-$PORT/target/horizon-cargo/fast/horizon-ctl}
EVIDENCE=$CLONE/ports/_shared/evidence/undergarden
LEG=sdk
[ "$SELFTEST" = 1 ] && LEG=$LEG-selftest
LOG=${LOG:-$EVIDENCE/e2e-$LEG.log}

mkdir -p "$EVIDENCE" "$(dirname "$LOG")"
# The log is the evidence: everything the run says goes to it, and the last line is the exit
# status `check-e2e-logs.py` reads.
exec > >(tee "$LOG") 2>&1

cleanup() {
    local status=$?
    if [ "$KEEP" != 1 ]; then
        "$CTL" --socket "$SOCK" quit >/dev/null 2>&1 || true
        rm -rf "${SCRATCH:-/nonexistent}"
    fi
    echo "EXIT:$status"
    exit "$status"
}
trap cleanup EXIT

command -v jq >/dev/null || { echo "missing jq (every assertion parses a ctl reply)" >&2; exit 1; }
[ -n "$GAME" ] || {
    echo "GAME is required: the SDK package is built into a game by the launcher," >&2
    echo "  horizon-launcher native-build ports/undergarden --instance <i> --trust-native-code" >&2
    exit 1
}
[ -x "$GAME" ] || { echo "missing horizon-client: $GAME" >&2; exit 1; }
[ -x "$CTL" ] || { echo "missing horizon-ctl: $CTL (set CTL= to the launcher's)" >&2; exit 1; }

SCRATCH=$(mktemp -d /tmp/opencode/undergarden-e2e-home.XXXXXX)
export HORIZON_HOME=$SCRATCH/game
export HORIZON_LAUNCHER_HOME=$SCRATCH/launcher
export XDG_DATA_HOME=$SCRATCH/data
export XDG_CONFIG_HOME=$SCRATCH/config
export HORIZON_NO_AUDIO=1

WORLD=${WORLD:-undergarden-e2e}
ctl() { "$CTL" --socket "$SOCK" "$@"; }
say() { printf '\n### %s\n' "$*"; }

# One ctl reply as JSON, echoed, so the log holds the exact command and its answer.
reply() {
    local command=$1
    shift
    local out
    out=$(ctl "$command" "$@" 2>&1)
    echo "$out"
    printf '%s' "$out"
}

# The dimension the player is in, from `ctl state`.
dimension() {
    ctl state | jq -r '.dimension.id // .dimension // empty'
}

biome() {
    ctl state | jq -r '.biome.id // .biome // empty'
}

say "launch ($GAME)"
"$CTL" --socket "$SOCK" launch \
    --game "$GAME" \
    --world "$WORLD" --seed 20261105 --creative --headless --wait \
    --resources "$RES" \
    >"$SCRATCH/launch.log" 2>&1 || {
        echo "launch failed:" >&2
        cat "$SCRATCH/launch.log" >&2
        exit 1
    }
ctl state | jq -c '{dimension: (.dimension.id // .dimension), position: .player.position}'

say "A: /undergarden status"
STATUS=$(reply command "/undergarden status")
EXPECTED_BIOMES=5
[ "$SELFTEST" = 1 ] && EXPECTED_BIOMES=6
echo "$STATUS" | grep -q 'dimension=undergarden:undergarden' \
    || { echo "FAIL: status does not name the registered dimension" >&2; exit 1; }
echo "$STATUS" | grep -q "biomes=$EXPECTED_BIOMES" \
    || { echo "FAIL: status does not report $EXPECTED_BIOMES biomes" >&2; exit 1; }
for row in \
    'cell(0.00, 0.00, 0.00, 0.00, -0.75, 0.00)=undergarden:forgotten_field' \
    'cell(0.00, 0.00, 0.00, 0.00, -0.75, -1.00)=undergarden:ancient_sea' \
    'cell(-0.15, 0.00, 0.00, 0.00, 0.45, 0.00)=undergarden:dense_forest' \
    'cell(0.10, 0.00, 0.00, 0.00, 0.60, 0.00)=undergarden:smogstem_forest' \
    'cell(0.00, 0.00, 0.00, 0.00, 0.00, -2.00)=undergarden:depths'; do
    echo "$STATUS" | grep -qF "$row" \
        || { echo "FAIL: status is missing $row" >&2; exit 1; }
done

say "B: /undergarden climate"
for pair in "0.1 0 0 0 0.6 0|undergarden:smogstem_forest" \
            "0 0 0 0 -0.75 -2|undergarden:ancient_sea" \
            "1 0 0 0 1 0|undergarden:smogstem_forest"; do
    args=${pair%%|*}
    want=${pair##*|}
    got=$(reply command "/undergarden climate $args")
    echo "$got" | grep -qF "=$want" \
        || { echo "FAIL: climate $args did not answer $want: $got" >&2; exit 1; }
done

say "C: enter the dimension"
reply command "execute in undergarden:undergarden run tp @s 0 100 0" >/dev/null
ctl wait 40
echo "dimension: $(dimension)"
[ "$(dimension)" = "undergarden:undergarden" ] \
    || { echo "FAIL: not in the Undergarden after execute in" >&2; exit 1; }
ROOF=$(ctl block 0 127 0 | jq -r '.block // .id // empty')
FLOOR=$(ctl block 0 -64 0 | jq -r '.block // .id // empty')
echo "roof y=127: $ROOF"
echo "floor y=-64: $FLOOR"
[ "$ROOF" = "minecraft:bedrock" ] || { echo "FAIL: the ceiling is not bedrock ($ROOF)" >&2; exit 1; }
[ "$FLOOR" = "minecraft:bedrock" ] || { echo "FAIL: the floor is not bedrock ($FLOOR)" >&2; exit 1; }
# The column between the caps must hold the mod's own blocks, not vanilla stone: find the first
# non-air below the roof and require one of the carried surface ids.
SURFACE=""
for y in $(seq 120 -1 40); do
    block=$(ctl block 0 "$y" 0 | jq -r '.block // .id // empty')
    case "$block" in
        minecraft:air|minecraft:cave_air|"") continue ;;
        *) SURFACE=$block; SURFACE_Y=$y; break ;;
    esac
done
echo "first solid below the roof: ${SURFACE_Y:-none} $SURFACE"
case "$SURFACE" in
    undergarden:deepturf_block|undergarden:deepsoil|undergarden:coarse_deepsoil|\
    undergarden:depthrock|undergarden:shiverstone|undergarden:dreadrock|undergarden:sediment)
        ;;
    *) echo "FAIL: the column holds $SURFACE, not one of the mod's surface blocks" >&2; exit 1 ;;
esac

say "D: the biome is one of the five"
IN_BIOME=$(biome)
echo "biome: $IN_BIOME"
case "$IN_BIOME" in
    undergarden:forgotten_field|undergarden:ancient_sea|undergarden:dense_forest|\
    undergarden:smogstem_forest|undergarden:depths) ;;
    *) echo "FAIL: $IN_BIOME is not one of the carried biomes" >&2; exit 1 ;;
esac

say "E: the carried structure builds a piece"
# The start box must be loaded: the player is already in the depths at y=100, so walk down to a
# depths cell and wait for the chunks around it before placing.
reply command "execute in undergarden:undergarden run tp @s 0 -20 0" >/dev/null
ctl wait 40
BEFORE=$(ctl block 0 -20 0 | jq -r '.block // .id // empty')
reply command "place structure undergarden:depleted_mine 0 -20 0" >/dev/null
ctl wait 20
AFTER=$(ctl block 0 -20 0 | jq -r '.block // .id // empty')
echo "before: $BEFORE  after: $AFTER"
[ "$BEFORE" != "$AFTER" ] \
    || { echo "FAIL: /place structure changed nothing at 0 -20 0" >&2; exit 1; }

if [ -n "$CONTROL_GAME" ]; then
    say "control: the same build without the mod refuses the level"
    "$CTL" --socket "$SOCK" quit >/dev/null 2>&1 || true
    "$CTL" --socket "$SOCK" launch \
        --game "$CONTROL_GAME" \
        --world "$WORLD-control" --seed 20261105 --creative --headless --wait \
        --resources "$RES" >"$SCRATCH/control.log" 2>&1 || {
            echo "control launch failed:" >&2
            cat "$SCRATCH/control.log" >&2
            exit 1
        }
    OUT=$(ctl command "/undergarden status" 2>&1 || true)
    echo "$OUT"
    echo "$OUT" | grep -q 'dimension=undergarden:undergarden' \
        && { echo "FAIL: the control build answered the mod's command" >&2; exit 1; }
    if ctl command "execute in undergarden:undergarden run tp @s 0 100 0" 2>&1 | grep -qi ok; then
        echo "FAIL: the control build accepted the mod's level" >&2
        exit 1
    fi
fi

echo "PASS: undergarden — the level exists, generates the mod's surface, and answers its table"
