pub mod limits;
pub mod var;

pub use limits::Limits;

/// One position: quantity in shares, price in cents.
#[derive(Debug, Clone, Copy)]
pub struct Position {
    pub qty: u32,
    pub price_cents: u32,
}

impl Position {
    /// The position's notional value in cents.
    pub fn notional_cents(&self) -> u32 {
        self.qty * self.price_cents
    }
}

/// Parse "QTY@PRICE_CENTS" as sent by the order form.
pub fn parse_position(input: &str) -> Position {
    let (qty, price) = input.split_once('@').unwrap();
    Position { qty: qty.trim().parse().unwrap(), price_cents: price.trim().parse().unwrap() }
}
