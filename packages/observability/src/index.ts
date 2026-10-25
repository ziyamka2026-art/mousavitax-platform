/**
 * Observability — MousaviTax AI Platform
 *
 * Wraps OpenTelemetry tracing, Sentry error reporting, and structured logging
 * into a single instrument() helper that's safe to use in any async function.
 *
 * @package packages/observability
 */

import { trace, context, SpanStatusCode } from '@opentelemetry/api';

// ---------------------------------------------------------------------------
// Logger — structured JSON to stdout (Vercel captures it)
// ---------------------------------------------------------------------------

export type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'fatal';

const LEVEL_PRIORITY: Record<LogLevel, number> = {
  debug: 10, info: 20, warn: 30, error: 40, fatal: 50,
};

class Logger {
  private minLevel: LogLevel = 'info';

  constructor() {
    const envLevel = (process.env.LOG_LEVEL as LogLevel) ?? 'info';
    if (envLevel in LEVEL_PRIORITY) this.minLevel = envLevel;
  }

  private shouldLog(level: LogLevel): boolean {
    return LEVEL_PRIORITY[level] >= LEVEL_PRIORITY[this.minLevel];
  }

  log(level: LogLevel, message: string, fields: Record<string, unknown> = {}): void {
    if (!this.shouldLog(level)) return;

    const record = {
      ts: new Date().toISOString(),
      level,
      message,
      env: process.env.NODE_ENV ?? 'development',
      service: 'mousavitax',
      ...fields,
      // active span context (if any)
      traceId: tryGetSpan()?.spanContext().traceId,
      spanId: tryGetSpan()?.spanContext().spanId,
    };

    const line = JSON.stringify(record);
    if (level === 'error' || level === 'fatal') {
      // eslint-disable-next-line no-console
      console.error(line);
    } else if (level === 'warn') {
      // eslint-disable-next-line no-console
      console.warn(line);
    } else {
      // eslint-disable-next-line no-console
      console.log(line);
    }
  }

  debug(message: string, fields?: Record<string, unknown>) { this.log('debug', message, fields); }
  info(message: string, fields?: Record<string, unknown>) { this.log('info', message, fields); }
  warn(message: string, fields?: Record<string, unknown>) { this.log('warn', message, fields); }
  error(message: string, fields?: Record<string, unknown>) { this.log('error', message, fields); }
  fatal(message: string, fields?: Record<string, unknown>) { this.log('fatal', message, fields); }
}

function tryGetSpan() {
  try {
    const span = trace.getSpan(context.active());
    return span ?? null;
  } catch {
    return null;
  }
}

export const logger = new Logger();

// ---------------------------------------------------------------------------
// Tracing — wraps an async function in a span
// ---------------------------------------------------------------------------

/**
 * Instrument an async function with a tracing span + error reporting.
 *
 * @example
 *   const result = await instrument('case.create', async () => {
 *     return await createCaseInDb(payload);
 *   });
 */
export async function instrument<T>(
  name: string,
  fn: () => Promise<T>,
  attributes: Record<string, string | number | boolean> = {},
): Promise<T> {
  const tracer = trace.getTracer('mousavitax');
  return tracer.startActiveSpan(name, async (span) => {
    Object.entries(attributes).forEach(([k, v]) => {
      span.setAttribute(k, v);
    });

    try {
      const result = await fn();
      span.setStatus({ code: SpanStatusCode.OK });
      return result;
    } catch (err) {
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: err instanceof Error ? err.message : String(err),
      });
      span.recordException(err as Error);
      reportError(err as Error, { span: name, attributes });
      throw err;
    } finally {
      span.end();
    }
  });
}

/**
 * Synchronous variant — for non-async code paths.
 */
export function instrumentSync<T>(
  name: string,
  fn: () => T,
  attributes: Record<string, string | number | boolean> = {},
): T {
  const tracer = trace.getTracer('mousavitax');
  return tracer.startActiveSpan(name, (span) => {
    Object.entries(attributes).forEach(([k, v]) => {
      span.setAttribute(k, v);
    });
    try {
      const result = fn();
      span.setStatus({ code: SpanStatusCode.OK });
      return result;
    } catch (err) {
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: err instanceof Error ? err.message : String(err),
      });
      span.recordException(err as Error);
      reportError(err as Error, { span: name, attributes });
      throw err;
    } finally {
      span.end();
    }
  });
}

// ---------------------------------------------------------------------------
// Sentry integration (optional — only loads if SENTRY_DSN is set)
// ---------------------------------------------------------------------------

let sentryInitialized = false;

function initSentry() {
  if (sentryInitialized) return;
  const dsn = process.env.SENTRY_DSN;
  if (!dsn) return;

  // Lazy import to avoid bundling Sentry when not configured
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const Sentry = require('@sentry/node');
  Sentry.init({
    dsn,
    environment: process.env.NODE_ENV ?? 'development',
    tracesSampleRate: 1.0,
    profilesSampleRate: 0.1,
  });
  sentryInitialized = true;
}

function reportError(
  err: Error,
  context: Record<string, unknown> = {},
): void {
  initSentry();
  if (!sentryInitialized) return;
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const Sentry = require('@sentry/node');
  Sentry.captureException(err, { extra: context });
}

// ---------------------------------------------------------------------------
// Metrics — lightweight counter helper (Vercel-friendly stdout-based)
// ---------------------------------------------------------------------------

const counters: Record<string, number> = {};

export function incrementCounter(name: string, by: number = 1): void {
  counters[name] = (counters[name] ?? 0) + by;
  // Flush on every 100 increments to keep memory bounded
  if (counters[name] % 100 === 0) {
    logger.info('metric.counter', { name, value: counters[name] });
  }
}

export function getCounter(name: string): number {
  return counters[name] ?? 0;
}

// ---------------------------------------------------------------------------
// Health check — used by /api/health
// ---------------------------------------------------------------------------

export interface HealthStatus {
  status: 'ok' | 'degraded' | 'down';
  checks: Record<string, { ok: boolean; latency_ms?: number; error?: string }>;
  timestamp: string;
  version: string;
}

export async function healthCheck(): Promise<HealthStatus> {
  const checks: HealthStatus['checks'] = {};

  // Database ping
  try {
    const start = Date.now();
    const supabaseUrl = process.env.SUPABASE_URL ?? process.env.NEXT_PUBLIC_SUPABASE_URL;
    if (!supabaseUrl) {
      checks.database = { ok: false, error: 'SUPABASE_URL not configured' };
    } else {
      const res = await fetch(`${supabaseUrl}/rest/v1/`, { method: 'GET', signal: AbortSignal.timeout(2000) });
      checks.database = { ok: res.ok || res.status === 401, latency_ms: Date.now() - start };
    }
  } catch (err) {
    checks.database = { ok: false, error: (err as Error).message };
  }

  // LLM ping
  const llmProvider = process.env.LLM_PROVIDER;
  checks.llm = { ok: !!llmProvider, latency_ms: 0 };

  const allOk = Object.values(checks).every(c => c.ok);
  return {
    status: allOk ? 'ok' : 'degraded',
    checks,
    timestamp: new Date().toISOString(),
    version: process.env.npm_package_version ?? '0.0.0',
  };
}

export default {
  logger,
  instrument,
  instrumentSync,
  incrementCounter,
  getCounter,
  healthCheck,
};
