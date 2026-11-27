const DEFAULTS = Object.freeze({
  port: 8080,
  retries: 3,
  cacheTtlSeconds: 300,
});

function readInt(env, key, fallback) {
  const raw = env[key];
  if (raw === undefined || raw === "") return fallback;
  const value = Number(raw);
  if (!Number.isInteger(value) || value < 0) {
    throw new RangeError(`${key} must be a non-negative integer, got ${raw}`);
  }
  return value;
}

export function loadConfig(env = process.env) {
  return {
    port: readInt(env, "PORT", DEFAULTS.port),
    retries: readInt(env, "RETRIES", DEFAULTS.retries),
    cacheTtlSeconds: readInt(env, "CACHE_TTL_SECONDS", DEFAULTS.cacheTtlSeconds),
  };
}
