/**
 * Safe numeric formatting utilities for Breathe ESG Platform.
 *
 * DRF serializes DecimalField values as strings (e.g. "12.345600").
 * The frontend TypeScript types say `number` but the runtime value is a string.
 * Every utility here converts safely before calling Number methods, so no page
 * can crash due to `value.toFixed is not a function`.
 */

/**
 * Safely convert any API value to a finite number.
 * Returns `fallback` (default 0) for null, undefined, NaN, Infinity, or
 * non-numeric strings.
 */
export function safeNumber(value: unknown, fallback = 0): number {
  if (value === null || value === undefined) return fallback
  const n = typeof value === 'number' ? value : Number(value)
  return Number.isFinite(n) ? n : fallback
}

/**
 * Format a number to a fixed number of decimal places, safely.
 * Returns `fallback` string (default '—') when value is null/undefined/NaN.
 */
export function safeFmt(value: unknown, decimals = 2, fallback = '—'): string {
  if (value === null || value === undefined) return fallback
  const n = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(n)) return fallback
  return n.toFixed(decimals)
}

/**
 * Format an emissions value (kgCO₂e).
 * Auto-scales to tonnes when value >= 1000.
 * Returns '—' for null/undefined/invalid.
 */
export function fmtEmissions(value: unknown, unit = 'kgCO₂e'): string {
  if (value === null || value === undefined) return '—'
  const n = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(n)) return '—'
  if (n >= 1000) return `${(n / 1000).toFixed(2)} tCO₂e`
  return `${n.toFixed(2)} ${unit}`
}

/**
 * Format a quantity with unit, safely.
 * Returns '—' when value is null/undefined/invalid.
 */
export function fmtQuantity(value: unknown, unit: string, decimals = 2): string {
  if (value === null || value === undefined) return '—'
  const n = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(n)) return '—'
  return `${n.toFixed(decimals)} ${unit}`.trim()
}

/**
 * Format a file size in bytes to a human-readable string.
 */
export function fmtFileSize(bytes: unknown): string {
  const n = safeNumber(bytes)
  if (n === 0) return '0 KB'
  if (n >= 1024 * 1024) return `${(n / (1024 * 1024)).toFixed(1)} MB`
  return `${(n / 1024).toFixed(0)} KB`
}

/**
 * Percentage formatter — clamps to [0, 100].
 */
export function fmtPct(numerator: unknown, denominator: unknown, decimals = 0): string {
  const num = safeNumber(numerator)
  const den = safeNumber(denominator)
  if (den === 0) return '0%'
  const pct = Math.min((num / den) * 100, 100)
  return `${pct.toFixed(decimals)}%`
}
