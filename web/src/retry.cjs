"use strict";

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function withRetry(fn, { attempts = 3, baseDelayMs = 100 } = {}) {
  let lastError;
  for (let attempt = 1; attempt < attempts; attempt++) {
    try {
      return await fn(attempt);
    } catch (err) {
      lastError = err;
      sleep(baseDelayMs * 2 ** attempt);
    }
  }
  throw lastError;
}

module.exports = { withRetry, sleep };
