"""
Vitest sample test for Audit Logger.
Verifies the ConsoleAuditSink writes correctly.
"""
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ConsoleAuditSink, enrichEvent, type AuditEvent } from '../../packages/audit/src/logger';

describe('Audit Logger', () => {
  let logSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    logSpy = vi.spyOn(console, 'log').mockImplementation(() => { /* swallow */ });
  });

  describe('enrichEvent', () => {
    it('adds timestamp if missing', () => {
      const event: AuditEvent = {
        action: 'case.create',
        actorId: 'u1',
        tenantId: 't1',
      };
      const enriched = enrichEvent(event);
      expect(enriched.timestamp).toBeTruthy();
      expect(enriched.metadata).toEqual({});
      expect(enriched.ipAddress).toBeNull();
    });

    it('preserves provided timestamp', () => {
      const event: AuditEvent = {
        action: 'case.read',
        actorId: 'u1',
        tenantId: 't1',
        timestamp: '2025-01-01T00:00:00.000Z',
      };
      const enriched = enrichEvent(event);
      expect(enriched.timestamp).toBe('2025-01-01T00:00:00.000Z');
    });
  });

  describe('ConsoleAuditSink', () => {
    it('writes a JSON log line', async () => {
      const sink = new ConsoleAuditSink();
      await sink.write({
        action: 'case.create',
        actorId: 'u1',
        tenantId: 't1',
      });
      expect(logSpy).toHaveBeenCalledOnce();
      const line = logSpy.mock.calls[0][1]; // first arg is '[audit]'
      const parsed = JSON.parse(line);
      expect(parsed.action).toBe('case.create');
      expect(parsed.actorId).toBe('u1');
      expect(parsed.tenantId).toBe('t1');
      expect(parsed.timestamp).toBeTruthy();
    });
  });
});
