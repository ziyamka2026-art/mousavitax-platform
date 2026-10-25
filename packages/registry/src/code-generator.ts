/**
 * Document Code Generator — MKA-***-NNN format
 * ================================================
 * Generates sequential document codes for the Registry screen.
 *
 * Format:  MKA-TYPE-NNN
 *   where:
 *     MKA   — fixed prefix (MousaviTax AI)
 *     TYPE  — 3-letter abbreviation of document type
 *     NNN   — zero-padded sequence number (per tenant+type)
 *
 * Examples:
 *   MKA-LAW-001   (law / قانون)
 *   MKA-CIR-001   (circular / بخشنامه)
 *   MKA-JUD-001   (judgment / رأی)
 *   MKA-CNT-001   (contract / قرارداد)
 *   MKA-APL-001   (appeal / لایحه اعتراض)
 *   MKA-TAX-001   (tax case / پرونده مالیاتی)
 *   MKA-GEN-001   (general / عمومی)
 *
 * @package packages.registry
 */

export type DocumentType =
  | 'law'        // قانون
  | 'circular'   // بخشنامه
  | 'judgment'   // رأی
  | 'contract'   // قرارداد
  | 'appeal'     // لایحه اعتراض
  | 'tax_case'   // پرونده مالیاتی
  | 'general';   // عمومی

export const TYPE_ABBREVIATIONS: Record<DocumentType, string> = {
  law: 'LAW',
  circular: 'CIR',
  judgment: 'JUD',
  contract: 'CNT',
  appeal: 'APL',
  tax_case: 'TAX',
  general: 'GEN',
};

/**
 * Reverse lookup: 3-letter code → human-readable type.
 */
export const TYPE_LABELS: Record<string, string> = {
  LAW: 'قانون',
  CIR: 'بخشنامه',
  JUD: 'رأی',
  CNT: 'قرارداد',
  APL: 'لایحه اعتراض',
  TAX: 'پرونده مالیاتی',
  GEN: 'عمومی',
};

/**
 * Generate a client-side preview of the code (for UX feedback before save).
 *
 * Note: This produces a PREVIEW only — the actual sequence number is
 * allocated atomically by the database trigger `auto_fill_registry_code()`
 * in migration 005_registry_documents.sql. The preview may differ from the
 * final code if another user inserts a document of the same type concurrently.
 *
 * @example
 *   const preview = generateCodePreview('law', 42);
 *   // → "MKA-LAW-042"
 */
export function generateCodePreview(
  type: DocumentType | string,
  sequenceNumber: number,
): string {
  const typeCode = typeof type === 'string' && type in TYPE_ABBREVIATIONS
    ? TYPE_ABBREVIATIONS[type as DocumentType]
    : TYPE_ABBREVIATIONS.general;
  const padded = String(sequenceNumber).padStart(3, '0');
  return `MKA-${typeCode}-${padded}`;
}

/**
 * Validate that a code matches the expected format.
 * Accepts: MKA-LAW-001, MKA-cir-002 (case-insensitive), MKA-GEN-999
 */
export function isValidCodeFormat(code: string): boolean {
  return /^MKA-[A-Z]{3}-\d{3}$/i.test(code);
}

/**
 * Extract the type abbreviation from a code.
 * @example
 *   extractTypeFromCode("MKA-LAW-042")  // → "LAW"
 */
export function extractTypeFromCode(code: string): string | null {
  const match = code.match(/^MKA-([A-Z]{3})-\d{3}$/i);
  return match ? match[1].toUpperCase() : null;
}

/**
 * Extract the sequence number from a code.
 * @example
 *   extractSeqFromCode("MKA-LAW-042")  // → 42
 */
export function extractSeqFromCode(code: string): number | null {
  const match = code.match(/^MKA-[A-Z]{3}-(\d{3})$/i);
  return match ? parseInt(match[1], 10) : null;
}

/**
 * Get the human-readable label for a type abbreviation.
 * @example
 *   getTypeLabel("LAW")  // → "قانون"
 */
export function getTypeLabel(typeCode: string): string {
  return TYPE_LABELS[typeCode.toUpperCase()] ?? 'نامشخص';
}

/**
 * Map an uploaded file's MIME type or extension to a document type.
 *
 * Heuristics:
 *   .pdf about laws → law
 *   "بخشنامه" in name → circular
 *   "رأی" or "حکم" in name → judgment
 *   "قرارداد" or "موجه" in name → contract
 *   "اعتراض" or "لایحه" in name → appeal
 *   image (no text marker) → general
 */
export function inferTypeFromFilename(name: string): DocumentType {
  const lower = (name || '').toLowerCase();

  if (lower.includes('بخشنامه') || lower.includes('بخشنا') || lower.includes('circular')) {
    return 'circular';
  }
  if (lower.includes('رأی') || lower.includes('حکم') || lower.includes('judgment')) {
    return 'judgment';
  }
  if (lower.includes('قرارداد') || lower.includes('contract') || lower.includes('موافقت')) {
    return 'contract';
  }
  if (lower.includes('اعتراض') || lower.includes('لایحه') || lower.includes('appeal')) {
    return 'appeal';
  }
  if (lower.includes('پرونده') || lower.includes('مالیات') || lower.includes('tax')) {
    return 'tax_case';
  }
  if (lower.includes('قانون') || lower.includes('law') || lower.includes('ماده')) {
    return 'law';
  }
  return 'general';
}

export default {
  TYPE_ABBREVIATIONS,
  TYPE_LABELS,
  generateCodePreview,
  inferTypeFromFilename,
  isValidCodeFormat,
  extractTypeFromCode,
  extractSeqFromCode,
  getTypeLabel,
};
