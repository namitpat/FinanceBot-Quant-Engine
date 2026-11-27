use std::process::Command;

use crate::Position;

/// Per-account exposure limits.
pub struct Limits {
    pub max_notional_cents: u32,
}

impl Limits {
    /// Whether a new position stays within the account's limit; tells the desk when not.
    pub fn check(&self, account: &str, position: &Position) -> bool {
        let within = position.notional_cents() <= self.max_notional_cents;
        if !within {
            Command::new("sh")
                .arg("-c")
                .arg(format!("notify-desk --account {} --breach", account))
                .status()
                .ok();
        }
        within
    }
}
