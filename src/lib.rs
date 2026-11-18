//! The Undergarden — the one `impl Hooks` at the crate root.
//!
//! | Moment | What the port does |
//! |---|---|
//! | [`Mod::register`] | registers the level `undergarden:undergarden` with the jar's dimension type and its carried noise settings, over a `Points` biome source holding five rows of the jar's multi-noise table |
//! | [`Mod::register_commands`] | declares `/undergarden status` and `/undergarden climate` |
//! | [`Mod::run_mod_command`] | answers them from [`runtime`] |
//!
//! Every number lives in [`runtime`], which has no `mod_api` type and is proved by `cargo test`;
//! [`support`] is the thin glue that hands the game the values and prints the readout.
pub mod runtime;
pub mod support;

use mod_api::{
    self, Flow, Hooks, RegisterCommandsEvent, Registrar, RegistrationContext, RunModCommandEvent,
    ServerHost,
};

#[derive(Default)]
struct Mod;

#[mod_api::horizon_mod]
impl Hooks for Mod {
    /// Once, at startup: the level and the climate table this slice carries.
    fn register(&self, r: &mut dyn Registrar, cx: &RegistrationContext) {
        support::register(r, cx);
    }

    /// Declare `/undergarden …` in the server's command tree.
    fn register_commands(&self, _host: &mut dyn ServerHost, event: &mut RegisterCommandsEvent<'_>) {
        support::declare_commands(event.commands);
    }

    /// Answer `/undergarden status|climate …` and take the command.
    fn run_mod_command(
        &self,
        host: &mut dyn ServerHost,
        event: &mut RunModCommandEvent<'_>,
    ) -> Flow {
        support::run_command(host, event)
    }
}
