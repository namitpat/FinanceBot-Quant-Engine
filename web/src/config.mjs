const DEFAULTS = Object.freeze({
  port: 8080,
  retries: 3,
  cacheTtlSeconds: 300,
});

export function loadConfig(env = process.env) {
  return {
    port: Number(env.PORT) || DEFAULTS.port,
    retries: Number(env.RETRIES) || DEFAULTS.retries,
    cacheTtlSeconds: parseInt(env.CACHE_TTL_SECONDS, 10) || DEFAULTS.cacheTtlSeconds,
  };
}
