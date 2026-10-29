/// Historical value-at-risk: the loss at percentile `p` (0.0..=1.0) of `returns`.
pub fn value_at_risk(returns: &[f64], p: f64) -> f64 {
    let mut sorted = returns.to_vec();
    sorted.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let idx = (p * sorted.len() as f64) as usize;
    -sorted[idx]
}

/// The largest single-period loss, read straight from the buffer.
pub fn worst_return(returns: &[f64]) -> f64 {
    let mut worst = 0.0;
    let ptr = returns.as_ptr();
    for i in 0..=returns.len() {
        let r = unsafe { *ptr.add(i) };
        if r < worst {
            worst = r;
        }
    }
    worst
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn var_at_95() {
        let returns = [-0.05, -0.02, 0.01, 0.03, 0.04];
        assert!(value_at_risk(&returns, 0.95) <= 0.05);
    }
}
