//! The glue: the registrar call and the command answers, with every decision in [`crate::runtime`].

use crate::runtime::{self, Climate, POINTS};
use mod_api::{
    self, BiomePoint, BiomeSourceKind, Command, DimensionSettings, Flow, Registrar,
    RegistrationContext, RunModCommandEvent, ServerHost, Text,
};

/// The mod's id, which is also its resource namespace.
const MOD_ID: &str = "undergarden";

/// The dimension's settings, decoded from the jar's `dimension_type/undergarden.json`.
fn settings() -> DimensionSettings {
    DimensionSettings {
        min_y: runtime::MIN_Y,
        height: runtime::HEIGHT,
        logical_height: runtime::HEIGHT,
        has_skylight: false,
        has_ceiling: true,
        generator: runtime::NOISE_GENERATOR.to_owned(),
        noise_settings: runtime::NOISE_SETTINGS.to_owned(),
        biome: runtime::BIOMES[0].to_owned(),
        biome_source: BiomeSourceKind::Points,
        mod_biome_source: None,
        biomes: Vec::new(),
        biome_points: POINTS.iter().map(biome_point).collect(),
        biome_scale: 2,
        biome_preset: "minecraft:overworld".to_owned(),
        has_fixed_time: true,
        has_ender_dragon_fight: false,
        coordinate_scale: 4.0,
        ambient_light: 0.1,
        infiniburn: "#minecraft:infiniburn_overworld".to_owned(),
        monster_spawn_light_level: (0, 7),
        monster_spawn_block_light_limit: 0,
        skybox: "none".to_owned(),
        cardinal_light: "nether".to_owned(),
        water_evaporates: false,
        fast_lava: false,
        respawn_anchor_works: false,
        nether_portal_spawns_piglin: true,
        piglins_zombify: false,
        snow_golem_melts: false,
        can_start_raid: false,
        sky_light_level: 4.0,
        sea_level: None,
        bed_can_sleep: "when_dark".to_owned(),
        bed_can_set_spawn: "always".to_owned(),
        bed_destroy_on_use: false,
        bed_destroy_on_leave: false,
        straw_bed_can_sleep: "when_dark".to_owned(),
        straw_bed_can_set_spawn: "never".to_owned(),
        straw_bed_destroy_on_use: false,
        straw_bed_destroy_on_leave: true,
        sky_color: Some("#121909".to_owned()),
        fog_color: Some("#121909".to_owned()),
        cloud_height: None,
        day_cycle: "none".to_owned(),
    }
}

/// One carried table row as the registrar's climate point.
fn biome_point(point: &runtime::Point) -> BiomePoint {
    BiomePoint {
        biome: point.biome.to_owned(),
        temperature: point.temperature,
        humidity: point.humidity,
        continentalness: point.continentalness,
        erosion: point.erosion,
        depth: point.depth,
        weirdness: point.weirdness,
        offset: point.offset,
    }
}

/// Register the level once, at startup.
pub fn register(r: &mut dyn Registrar, _cx: &RegistrationContext) {
    r.register_dimension(runtime::DIMENSION, settings());
}

/// The commands, each usage on its own.
pub fn declare_commands(commands: &mut Vec<Command>) {
    for usage in ["undergarden", "undergarden status", "undergarden climate"] {
        commands.push(Command::new(usage));
    }
    commands.push(Command::new(
        "undergarden climate <continentalness:number> <erosion:number> <humidity:number> \
         <temperature:number> <weirdness:number> <depth:number>",
    ));
}

/// Answer `/undergarden …` and take it; `Flow::Continue` for a line that is not ours.
pub fn run_command(host: &mut dyn ServerHost, event: &mut RunModCommandEvent<'_>) -> Flow {
    let invocation = event.command;
    let path: Vec<&str> = invocation.literals.iter().map(String::as_str).collect();
    let lines = match path.as_slice() {
        ["undergarden"] => usage(),
        ["undergarden", "status"] => runtime::status_lines(),
        ["undergarden", "climate"] => match climate_argument(invocation) {
            Some(climate) => vec![runtime::cell_line(&climate)],
            None => usage(),
        },
        _ => return Flow::Continue,
    };
    for line in lines {
        let _ = host.commands().feedback(Text::literal(line));
    }
    Flow::Cancel
}

/// The six numbers of `/undergarden climate`, or none when one is missing or not a number.
fn climate_argument(invocation: &mod_api::CommandInvocation) -> Option<Climate> {
    let number = |name: &str| match invocation.argument(name) {
        Some(mod_api::CommandArgumentValue::Number(value)) => Some(*value as f32),
        _ => None,
    };
    Some(Climate {
        continentalness: number("continentalness")?,
        erosion: number("erosion")?,
        humidity: number("humidity")?,
        temperature: number("temperature")?,
        weirdness: number("weirdness")?,
        depth: number("depth")?,
    })
}

/// `/undergarden` with no subcommand.
fn usage() -> Vec<String> {
    vec![
        format!("{MOD_ID}: /undergarden status"),
        format!(
            "{MOD_ID}: /undergarden climate <continentalness> <erosion> <humidity> \
             <temperature> <weirdness> <depth>"
        ),
    ]
}
