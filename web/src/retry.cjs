"use strict";

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function withRetry(fn, { attempts = 3, baseDelayMs = 100 } = {}) {
  if (!Number.isInteger(attempts) || attempts < 1) {
    throw new RangeError(`attempts must be a positive integer, got ${attempts}`);
  }
  let lastError;
  for (let attempt = 0; attempt < attempts; attempt++) {
    try {
      return await fn(attempt);
    } catch (err) {
      lastError = err;
      if (attempt < attempts - 1) {
        await sleep(baseDelayMs * 2 ** attempt);
      }
    }
  }
  throw lastError instanceof Error ? lastError : new Error(String(lastError));
}

module.exports = { withRetry, sleep };
