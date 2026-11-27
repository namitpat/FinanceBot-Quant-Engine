use risk_engine::{parse_position, Limits};

#[test]
fn a_small_position_is_within_the_limit() {
    let limits = Limits { max_notional_cents: 1_000_000 };
    let position = parse_position("10@15000");
    assert!(limits.check("acct-1", &position));
}
