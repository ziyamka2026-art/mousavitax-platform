// Tests for the document code generator
import { describe, it, expect } from 'vitest';
import {
  TYPE_ABBREVIATIONS,
  TYPE_LABELS,
  generateCodePreview,
  inferTypeFromFilename,
  isValidCodeFormat,
  extractTypeFromCode,
  extractSeqFromCode,
  getTypeLabel,
  type DocumentType,
} from '../../packages/registry/src';

describe('Document Code Generator', () => {
  describe('TYPE_ABBREVIATIONS', () => {
    it('has 7 supported types', () => {
      expect(Object.keys(TYPE_ABBREVIATIONS)).toHaveLength(7);
    });

    it('uses 3-letter codes', () => {
      Object.values(TYPE_ABBREVIATIONS).forEach((code) => {
        expect(code).toHaveLength(3);
        expect(code).toMatch(/^[A-Z]{3}$/);
      });
    });

    it('maps correctly', () => {
      expect(TYPE_ABBREVIATIONS.law).toBe('LAW');
      expect(TYPE_ABBREVIATIONS.circular).toBe('CIR');
      expect(TYPE_ABBREVIATIONS.judgment).toBe('JUD');
      expect(TYPE_ABBREVIATIONS.contract).toBe('CNT');
      expect(TYPE_ABBREVIATIONS.appeal).toBe('APL');
      expect(TYPE_ABBREVIATIONS.tax_case).toBe('TAX');
      expect(TYPE_ABBREVIATIONS.general).toBe('GEN');
    });
  });

  describe('TYPE_LABELS', () => {
    it('has Persian labels for all 7 codes', () => {
      expect(Object.keys(TYPE_LABELS)).toHaveLength(7);
      expect(TYPE_LABELS.LAW).toBe('قانون');
      expect(TYPE_LABELS.CIR).toBe('بخشنامه');
      expect(TYPE_LABELS.JUD).toBe('رأی');
      expect(TYPE_LABELS.CNT).toBe('قرارداد');
      expect(TYPE_LABELS.APL).toBe('لایحه اعتراض');
      expect(TYPE_LABELS.TAX).toBe('پرونده مالیاتی');
      expect(TYPE_LABELS.GEN).toBe('عمومی');
    });
  });

  describe('generateCodePreview', () => {
    it('formats with zero-padded sequence', () => {
      expect(generateCodePreview('law', 1)).toBe('MKA-LAW-001');
      expect(generateCodePreview('law', 42)).toBe('MKA-LAW-042');
      expect(generateCodePreview('circular', 999)).toBe('MKA-CIR-999');
    });

    it('falls back to GEN for unknown types', () => {
      expect(generateCodePreview('unknown', 5)).toBe('MKA-GEN-005');
    });

    it('accepts string type name', () => {
      expect(generateCodePreview('judgment', 10)).toBe('MKA-JUD-010');
    });

    it('pads to 3 digits even for 4-digit numbers', () => {
      expect(generateCodePreview('law', 1000)).toBe('MKA-LAW-1000');
    });
  });

  describe('isValidCodeFormat', () => {
    it('accepts valid codes (case-insensitive)', () => {
      expect(isValidCodeFormat('MKA-LAW-001')).toBe(true);
      expect(isValidCodeFormat('MKA-cir-002')).toBe(true);
      expect(isValidCodeFormat('MKA-GEN-999')).toBe(true);
    });

    it('rejects invalid formats', () => {
      expect(isValidCodeFormat('LAW-001')).toBe(false);
      expect(isValidCodeFormat('MKA-LAW-01')).toBe(false);
      expect(isValidCodeFormat('MKA-LAW-0001')).toBe(false);
      expect(isValidCodeFormat('MKA-ABCD-001')).toBe(false);
      expect(isValidCodeFormat('')).toBe(false);
      expect(isValidCodeFormat('MKA-LAW-ABC')).toBe(false);
    });
  });

  describe('extractTypeFromCode', () => {
    it('returns the type abbreviation', () => {
      expect(extractTypeFromCode('MKA-LAW-042')).toBe('LAW');
      expect(extractTypeFromCode('MKA-CIR-007')).toBe('CIR');
      expect(extractTypeFromCode('MKA-jud-100')).toBe('JUD');
    });

    it('returns null for invalid codes', () => {
      expect(extractTypeFromCode('invalid')).toBeNull();
      expect(extractTypeFromCode('MKA-ABCD-001')).toBeNull();
    });
  });

  describe('extractSeqFromCode', () => {
    it('returns the sequence number as integer', () => {
      expect(extractSeqFromCode('MKA-LAW-001')).toBe(1);
      expect(extractSeqFromCode('MKA-LAW-042')).toBe(42);
      expect(extractSeqFromCode('MKA-LAW-999')).toBe(999);
    });

    it('returns null for invalid codes', () => {
      expect(extractSeqFromCode('invalid')).toBeNull();
      expect(extractSeqFromCode('MKA-LAW-ABC')).toBeNull();
    });
  });

  describe('getTypeLabel', () => {
    it('returns Persian label for known codes', () => {
      expect(getTypeLabel('LAW')).toBe('قانون');
      expect(getTypeLabel('CIR')).toBe('بخشنامه');
    });

    it('returns "نامشخص" for unknown codes', () => {
      expect(getTypeLabel('XYZ')).toBe('نامشخص');
    });

    it('is case-insensitive', () => {
      expect(getTypeLabel('law')).toBe('قانون');
      expect(getTypeLabel('Law')).toBe('قانون');
    });
  });

  describe('inferTypeFromFilename', () => {
    it('detects circulars', () => {
      expect(inferTypeFromFilename('بخشنامه ۲۰۰.۹۹.۵۲۲.pdf')).toBe('circular');
      expect(inferTypeFromFilename('circular_2024.pdf')).toBe('circular');
    });

    it('detects judgments', () => {
      expect(inferTypeFromFilename('رأی هیئت بدوی.pdf')).toBe('judgment');
      expect(inferTypeFromFilename('حکم شماره ۱۲۳.docx')).toBe('judgment');
      expect(inferTypeFromFilename('judgment-2024.pdf')).toBe('judgment');
    });

    it('detects contracts', () => {
      expect(inferTypeFromFilename('قرارداد اجاره.pdf')).toBe('contract');
      expect(inferTypeFromFilename('موافقت‌نامه.pdf')).toBe('contract');
      expect(inferTypeFromFilename('contract.docx')).toBe('contract');
    });

    it('detects appeals', () => {
      expect(inferTypeFromFilename('لایحه اعتراض.pdf')).toBe('appeal');
      expect(inferTypeFromFilename('appeal_draft.docx')).toBe('appeal');
    });

    it('detects tax cases', () => {
      expect(inferTypeFromFilename('پرونده مالیاتی ۱۴۰۳.pdf')).toBe('tax_case');
      expect(inferTypeFromFilename('tax_case_2024.pdf')).toBe('tax_case');
    });

    it('detects laws', () => {
      expect(inferTypeFromFilename('قانون مالیات‌های مستقیم.pdf')).toBe('law');
      expect(inferTypeFromFilename('ماده ۲۵۱ مکرر.pdf')).toBe('law');
      expect(inferTypeFromFilename('law_2024.pdf')).toBe('law');
    });

    it('falls back to general', () => {
      expect(inferTypeFromFilename('document.pdf')).toBe('general');
      expect(inferTypeFromFilename('photo.jpg')).toBe('general');
      expect(inferTypeFromFilename('')).toBe('general');
    });

    it('handles mixed Latin + Persian', () => {
      expect(inferTypeFromFilename('Circular بخشنامه.pdf')).toBe('circular');
      expect(inferTypeFromFilename('appeal لایحه.pdf')).toBe('appeal');
    });
  });
});
