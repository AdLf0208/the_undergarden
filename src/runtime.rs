//! The port's pure logic: the climate table, the depth bands, the surfaces and the readout.
//!
//! No `mod_api` type appears here, so `cargo test` proves every number without the game. The
//! numbers are the jar's own: the five rows of `data/undergarden/dimension/undergarden.json`'s
//! `biome_source.biomes` this slice carries, verbatim, and the three depth bands its
//! `noise_settings` router hands to vanilla's climate sampler.

/// The five biomes this slice carries, in the jar's table order, which is also the tie-break
/// order (vanilla keeps the earlier row when two fitnesses are equal).
pub const BIOMES: [&str; 5] = [
    "undergarden:forgotten_field",
    "undergarden:ancient_sea",
    "undergarden:dense_forest",
    "undergarden:smogstem_forest",
    "undergarden:depths",
];

/// The dimension's id, as `register_dimension` gives it.
pub const DIMENSION: &str = "undergarden:undergarden";
/// The noise settings the dimension reads, carried from the jar.
pub const NOISE_SETTINGS: &str = "undergarden:undergarden";
/// The game's own chunk generator, which the SDK names `NOISE_GENERATOR`.
pub const NOISE_GENERATOR: &str = "minecraft:noise";

/// The lowest block of the dimension (`min_y` of the jar's dimension type).
pub const MIN_Y: i32 = -64;
/// The build height (`height` of the jar's dimension type).
pub const HEIGHT: i32 = 192;
/// The highest block of the dimension, `min_y + height - 1`.
pub const MAX_Y: i32 = MIN_Y + HEIGHT - 1;

/// One row of a multi-noise table: the biome and the climate interval it is chosen for.
///
/// A field is `(min, max)` inside -2 to 2; the jar's single values are `(v, v)`, as vanilla's
/// `Climate.Parameter` reads a number as a point.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Point {
    /// The biome's id.
    pub biome: &'static str,
    /// `temperature`.
    pub temperature: (f32, f32),
    /// `humidity`.
    pub humidity: (f32, f32),
    /// `continentalness`.
    pub continentalness: (f32, f32),
    /// `erosion`.
    pub erosion: (f32, f32),
    /// `depth`.
    pub depth: (f32, f32),
    /// `weirdness`.
    pub weirdness: (f32, f32),
    /// `offset`, which makes the row count as farther away.
    pub offset: f32,
}

/// Where a position sits in the climate space: the six parameters vanilla's sampler computes.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Climate {
    /// `temperature`.
    pub temperature: f32,
    /// `humidity`.
    pub humidity: f32,
    /// `continentalness`.
    pub continentalness: f32,
    /// `erosion`.
    pub erosion: f32,
    /// `depth`, from [`depth_at`].
    pub depth: f32,
    /// `weirdness`.
    pub weirdness: f32,
}

/// Which part of a terrain column a cell is, as vanilla's `stone_depth` conditions name it.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Layer {
    /// The top block of the floor (`stone_depth(offset 0, add_surface_depth false, floor)`).
    Surface,
    /// A block under the floor's top (`stone_depth(offset 0, add_surface_depth true, floor)`).
    UnderSurface,
    /// Neither: the rock the noise generator fills with.
    Filler,
}

/// The jar's table rows this slice carries, in the jar's order.
pub const POINTS: [Point; 5] = [
    Point {
        biome: "undergarden:forgotten_field",
        temperature: (0.0, 0.0),
        humidity: (0.0, 0.0),
        continentalness: (0.0, 0.0),
        erosion: (0.0, 0.0),
        depth: (0.0, 0.0),
        weirdness: (-0.75, -0.75),
        offset: 0.0,
    },
    Point {
        biome: "undergarden:ancient_sea",
        temperature: (0.0, 0.0),
        humidity: (0.0, 0.0),
        continentalness: (0.0, 0.0),
        erosion: (0.0, 0.0),
        depth: (-1.0, -1.0),
        weirdness: (-0.75, -0.75),
        offset: 0.0,
    },
    Point {
        biome: "undergarden:dense_forest",
        temperature: (0.0, 0.0),
        humidity: (0.0, 0.0),
        continentalness: (-0.15, -0.15),
        erosion: (0.0, 0.0),
        depth: (0.0, 0.0),
        weirdness: (0.45, 0.45),
        offset: 0.0,
    },
    Point {
        biome: "undergarden:smogstem_forest",
        temperature: (0.0, 0.0),
        humidity: (0.0, 0.0),
        continentalness: (0.1, 0.1),
        erosion: (0.0, 0.0),
        depth: (0.0, 0.0),
        weirdness: (0.6, 0.6),
        offset: 0.0,
    },
    Point {
        biome: "undergarden:depths",
        temperature: (0.0, 0.0),
        humidity: (0.0, 0.0),
        continentalness: (0.0, 0.0),
        erosion: (0.0, 0.0),
        depth: (-2.0, -2.0),
        weirdness: (0.0, 0.0),
        offset: 0.0,
    },
];

/// How far `value` is outside `interval`, squared, as vanilla's `Climate.Parameter.distance`.
#[must_use]
pub fn distance(interval: (f32, f32), value: f32) -> f32 {
    let (min, max) = interval;
    let outside = if value < min {
        min - value
    } else if value > max {
        value - max
    } else {
        0.0
    };
    outside * outside
}

/// One row's fitness for `climate`: the six squared distances plus its `offset`.
///
/// Vanilla's `Climate.ParameterPoint.fitness` is the same sum in fixed point, and the row with
/// the lowest fitness wins.
#[must_use]
pub fn fitness(point: &Point, climate: &Climate) -> f32 {
    distance(point.temperature, climate.temperature)
        + distance(point.humidity, climate.humidity)
        + distance(point.continentalness, climate.continentalness)
        + distance(point.erosion, climate.erosion)
        + distance(point.depth, climate.depth)
        + distance(point.weirdness, climate.weirdness)
        + point.offset
}

/// The biome a climate cell answers: the row with the lowest fitness, the earlier row on a tie.
#[must_use]
pub fn biome_at(climate: &Climate) -> &'static str {
    let mut best = &POINTS[0];
    let mut best_fitness = fitness(best, climate);
    for point in &POINTS[1..] {
        let candidate = fitness(point, climate);
        if candidate < best_fitness {
            best = point;
            best_fitness = candidate;
        }
    }
    best.biome
}

/// The `depth` the jar's noise router gives a block column at height `y`.
///
/// Its `noise_router.depth` is two nested `range_choice`s on `minecraft:y`: 0 to 32 is -1, -64
/// to 0 is -2, everything else is 0.
#[must_use]
pub fn depth_at(y: i32) -> f32 {
    if (0..32).contains(&y) {
        -1.0
    } else if (MIN_Y..0).contains(&y) {
        -2.0
    } else {
        0.0
    }
}

/// The block the jar's material rule leaves at `layer` of a column at height `y` in `biome`.
///
/// The rule order is the jar's: bedrock floor and roof, depthrock under the roof, the sediment
/// band between y 0 and 32, the per-biome branches, the deepturf cover and the deepsoil under
/// it, and the noise default block (depthrock) everywhere else.
#[must_use]
pub fn block_at(layer: Layer, y: i32, biome: &str) -> &'static str {
    // The two bedrock rules come first and ignore the layer: a vertical gradient of five
    // blocks is drawn at each end, and the model takes its deterministic arm.
    if y <= MIN_Y || y >= MAX_Y {
        return "minecraft:bedrock";
    }
    // `SurfaceRules.yBlockCheck(VerticalAnchor.belowTop(5), 0)` fills depthrock under the roof.
    if y > MAX_Y - 5 {
        return "undergarden:depthrock";
    }
    // `stoneDepthCheck(0, true, FLOOR)` inside `yBlockCheck(absolute 0)` and
    // `not(yBlockCheck(absolute 33))`.
    if (0..=32).contains(&y) {
        return match layer {
            Layer::Filler => "undergarden:depthrock",
            Layer::Surface | Layer::UnderSurface => "undergarden:sediment",
        };
    }
    if let Some(block) = biome_branch(layer, biome) {
        return block;
    }
    match layer {
        // `stoneDepthCheck(0, false, FLOOR)` above y 0 is the deepturf cover, and
        // `stoneDepthCheck(0, true, FLOOR)` above y 0 is the deepsoil under it.
        Layer::Surface if y >= 0 => "undergarden:deepturf_block",
        Layer::UnderSurface if y >= 0 => "undergarden:deepsoil",
        // Below y 0 no cover rule holds; the noise default block is depthrock.
        Layer::Surface | Layer::UnderSurface | Layer::Filler => "undergarden:depthrock",
    }
}

/// The jar's per-biome surface branches for the carried biomes, or none.
fn biome_branch(layer: Layer, biome: &str) -> Option<&'static str> {
    match layer {
        Layer::Filler => None,
        Layer::Surface | Layer::UnderSurface => match biome {
            // Depths and infected depths mix coarse deepsoil by a powder-snow noise; the model
            // takes the branch's other arm, dreadrock, which covers the biome either way.
            "undergarden:depths" | "undergarden:infected_depths" => Some("undergarden:dreadrock"),
            // The icy pair of branches: shiverstone whatever the surface rule put there.
            "undergarden:frostfields"
            | "undergarden:icy_sea"
            | "undergarden:frosty_smogstem_forest" => Some("undergarden:shiverstone"),
            _ => None,
        },
    }
}

/// One cell's answer, in the readout's shape.
#[must_use]
pub fn cell_line(climate: &Climate) -> String {
    format!(
        "undergarden: cell({:.2}, {:.2}, {:.2}, {:.2}, {:.2}, {:.2})={}",
        climate.continentalness,
        climate.erosion,
        climate.humidity,
        climate.temperature,
        climate.weirdness,
        climate.depth,
        biome_at(climate),
    )
}

/// The `/undergarden status` readout: the dimension, the counts and five cell answers.
#[must_use]
pub fn status_lines() -> Vec<String> {
    let mut lines = vec![
        format!(
            "undergarden: dimension={DIMENSION} generator={NOISE_GENERATOR} \
             settings={NOISE_SETTINGS}"
        ),
        format!(
            "undergarden: min_y={MIN_Y} height={HEIGHT} max_y={MAX_Y} ceiling=true \
             fixed_time=true coordinate_scale=4"
        ),
        format!(
            "undergarden: biomes={} points={} depth_bands=-2.0({MIN_Y}..0) -1.0(0..32) 0.0(32..)",
            BIOMES.len(),
            POINTS.len(),
        ),
    ];
    lines.extend(sample_cells().iter().map(|(climate, _)| cell_line(climate)));
    lines
}

/// The five sample cells `/undergarden status` answers, as `(climate, biome)`.
#[must_use]
pub fn sample_cells() -> [(Climate, &'static str); 5] {
    let mut cells = [(sample(0.0, 0.0, 0.0, 0.0, 0.0, 0.0), ""); 5];
    for (slot, point) in cells.iter_mut().zip(POINTS.iter()) {
        *slot = (midpoint(point), point.biome);
    }
    cells
}

/// The middle of a row's climate intervals.
#[must_use]
pub fn midpoint(point: &Point) -> Climate {
    let middle = |(min, max): (f32, f32)| (min + max) / 2.0;
    Climate {
        temperature: middle(point.temperature),
        humidity: middle(point.humidity),
        continentalness: middle(point.continentalness),
        erosion: middle(point.erosion),
        depth: middle(point.depth),
        weirdness: middle(point.weirdness),
    }
}

/// A climate cell from its six parameters, in the table's column order.
#[must_use]
pub fn sample(
    continentalness: f32,
    erosion: f32,
    humidity: f32,
    temperature: f32,
    weirdness: f32,
    depth: f32,
) -> Climate {
    Climate {
        temperature,
        humidity,
        continentalness,
        erosion,
        depth,
        weirdness,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_table_carries_the_jars_five_rows_exactly() {
        let jar = [
            ("undergarden:forgotten_field", 0.0, 0.0, 0.0, -0.75),
            ("undergarden:ancient_sea", 0.0, -1.0, 0.0, -0.75),
            ("undergarden:dense_forest", -0.15, 0.0, 0.0, 0.45),
            ("undergarden:smogstem_forest", 0.1, 0.0, 0.0, 0.6),
            ("undergarden:depths", 0.0, -2.0, 0.0, 0.0),
        ];
        assert_eq!(POINTS.len(), jar.len(), "one carried row per table entry");
        for (point, (biome, continentalness, depth, erosion, weirdness)) in POINTS.iter().zip(jar) {
            assert_eq!(point.biome, biome, "row order follows the jar");
            assert_eq!(point.continentalness, (continentalness, continentalness));
            assert_eq!(point.depth, (depth, depth));
            assert_eq!(point.erosion, (erosion, erosion));
            assert_eq!(point.weirdness, (weirdness, weirdness));
            assert_eq!(point.temperature, (0.0, 0.0), "{biome} temperature");
            assert_eq!(point.humidity, (0.0, 0.0), "{biome} humidity");
            assert_eq!(point.offset, 0.0, "{biome} offset");
        }
    }

    #[test]
    fn the_possible_biomes_are_the_five_carried_rows() {
        assert_eq!(BIOMES.len(), POINTS.len());
        for (biome, point) in BIOMES.iter().zip(POINTS.iter()) {
            assert_eq!(*biome, point.biome);
            assert!(biome.starts_with("undergarden:"), "{biome}");
        }
        let mut unique = BIOMES.to_vec();
        unique.sort_unstable();
        unique.dedup();
        assert_eq!(unique.len(), BIOMES.len(), "no biome repeats");
    }

    #[test]
    fn depth_follows_the_routers_range_choice() {
        assert_eq!(
            depth_at(-65),
            0.0,
            "below the floor is the out-of-range arm"
        );
        assert_eq!(depth_at(-64), -2.0, "the deepest band starts at min_y");
        assert_eq!(depth_at(-1), -2.0);
        assert_eq!(depth_at(0), -1.0, "0 to 32 is the sea band");
        assert_eq!(depth_at(31), -1.0);
        assert_eq!(depth_at(32), 0.0, "32 leaves the sea band");
        assert_eq!(depth_at(MAX_Y), 0.0);
        assert_eq!(depth_at(4096), 0.0);
    }

    #[test]
    fn every_carried_row_answers_itself() {
        for point in &POINTS {
            let climate = midpoint(point);
            assert_eq!(biome_at(&climate), point.biome, "{}", point.biome);
        }
    }

    #[test]
    fn a_cell_outside_the_table_answers_the_nearest_covered_biome() {
        assert_eq!(
            biome_at(&sample(1.0, 0.0, 0.0, 0.0, 1.0, 0.0)),
            "undergarden:smogstem_forest"
        );
        // A cell in the far corner of the climate space: dense_forest sits 21.825 away,
        // smogstem_forest 22.37, so the corner answers the nearer one even though neither
        // covers it.
        assert_eq!(
            biome_at(&sample(-2.0, 2.0, 2.0, 2.0, 2.0, 2.0)),
            "undergarden:dense_forest"
        );
        assert_eq!(
            biome_at(&sample(0.0, 0.0, 2.0, 2.0, 0.0, -2.0)),
            "undergarden:depths"
        );
    }

    #[test]
    fn a_tie_keeps_the_earlier_row() {
        // The only distance between these two rows is depth: 0 and -1, so -0.5 is a tie.
        let tie = sample(0.0, 0.0, 0.0, 0.0, -0.75, -0.5);
        assert_eq!(fitness(&POINTS[0], &tie), fitness(&POINTS[1], &tie));
        assert_eq!(biome_at(&tie), "undergarden:forgotten_field");
    }

    #[test]
    fn an_offset_counts_as_farther_away() {
        // The two surface rows sit symmetrically about this cell: dense_forest is 0.125 short
        // of its continentalness and 0.075 over its weirdness, smogstem_forest the same the
        // other way, so their fitnesses are equal and the earlier row wins.
        let dense = POINTS[2];
        let smogstem = POINTS[3];
        let between = sample(-0.025, 0.0, 0.0, 0.0, 0.525, 0.0);
        let dense_fitness = fitness(&dense, &between);
        let smogstem_fitness = fitness(&smogstem, &between);
        assert!(
            (dense_fitness - smogstem_fitness).abs() < 1e-6,
            "{dense_fitness} vs {smogstem_fitness}"
        );
        assert_eq!(
            biome_at(&between),
            dense.biome,
            "a tie keeps the earlier row"
        );
        let mut offset = dense;
        offset.offset = 0.5;
        assert_eq!(
            fitness(&offset, &between),
            dense_fitness + 0.5,
            "an offset adds to the row's sum"
        );
        assert!(
            fitness(&offset, &between) > fitness(&smogstem, &between),
            "half a unit of offset outweighs a tie"
        );
    }

    #[test]
    fn bedrock_caps_both_ends_of_the_column() {
        for layer in [Layer::Surface, Layer::UnderSurface, Layer::Filler] {
            assert_eq!(block_at(layer, MIN_Y, BIOMES[0]), "minecraft:bedrock");
            assert_eq!(block_at(layer, MAX_Y, BIOMES[0]), "minecraft:bedrock");
        }
        assert_eq!(
            block_at(Layer::Surface, -63, BIOMES[0]),
            "undergarden:depthrock"
        );
        assert_eq!(
            block_at(Layer::Surface, 126, BIOMES[0]),
            "undergarden:depthrock"
        );
    }

    #[test]
    fn the_filler_is_depthrock_everywhere_between() {
        assert_eq!(
            block_at(Layer::Filler, 0, BIOMES[0]),
            "undergarden:depthrock"
        );
        assert_eq!(
            block_at(Layer::Filler, 64, BIOMES[2]),
            "undergarden:depthrock"
        );
        assert_eq!(
            block_at(Layer::Filler, -20, BIOMES[4]),
            "undergarden:depthrock"
        );
    }

    #[test]
    fn the_sediment_band_covers_y_0_to_32() {
        for biome in [BIOMES[0], BIOMES[2], BIOMES[3]] {
            assert_eq!(block_at(Layer::Surface, 0, biome), "undergarden:sediment");
            assert_eq!(block_at(Layer::Surface, 32, biome), "undergarden:sediment");
            assert_eq!(
                block_at(Layer::Surface, 33, biome),
                "undergarden:deepturf_block"
            );
            assert_eq!(
                block_at(Layer::UnderSurface, 0, biome),
                "undergarden:sediment"
            );
        }
    }

    #[test]
    fn deepturf_covers_the_floor_and_deepsoil_sits_under_it() {
        assert_eq!(
            block_at(Layer::Surface, 60, BIOMES[0]),
            "undergarden:deepturf_block"
        );
        assert_eq!(
            block_at(Layer::UnderSurface, 60, BIOMES[0]),
            "undergarden:deepsoil"
        );
        assert_eq!(
            block_at(Layer::Surface, -1, BIOMES[0]),
            "undergarden:depthrock",
            "the cover rule needs y >= 0, so the floor below 0 is the default block"
        );
    }

    #[test]
    fn the_depths_biome_is_dreadrock() {
        assert_eq!(
            block_at(Layer::Surface, 60, BIOMES[4]),
            "undergarden:dreadrock"
        );
        assert_eq!(
            block_at(Layer::UnderSurface, -20, BIOMES[4]),
            "undergarden:dreadrock"
        );
    }

    #[test]
    fn status_names_the_dimension_the_counts_and_the_cells() {
        let lines = status_lines();
        let joined = lines.join("\n");
        assert!(
            lines
                .iter()
                .any(|line| line.contains("dimension=undergarden:undergarden")),
            "{joined}"
        );
        assert!(
            lines.iter().any(|line| line.contains("biomes=5")),
            "{joined}"
        );
        assert!(
            lines.iter().any(|line| line.contains("points=5")),
            "{joined}"
        );
        for (climate, biome) in sample_cells() {
            assert!(
                lines.iter().any(|line| line.contains(biome)
                    && line.contains(&format!("{:.2}", climate.weirdness))),
                "no cell line for {biome} in {joined}"
            );
        }
    }

    #[test]
    fn the_sample_cells_are_seed_independent_and_one_per_row() {
        let cells = sample_cells();
        assert_eq!(cells.len(), POINTS.len());
        for ((climate, biome), point) in cells.iter().zip(POINTS.iter()) {
            assert_eq!(*biome, point.biome);
            assert_eq!(*climate, midpoint(point));
        }
        let first = sample_cells();
        let second = sample_cells();
        assert_eq!(first, second, "the same call always answers the same cells");
    }
}
