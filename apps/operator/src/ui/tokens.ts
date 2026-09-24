// Throughline's "quiet field instrument" visual system. This module stays free of
// React Native imports so build-time contrast checks can consume it.

export const space = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32, xxxl: 48 } as const;
export const radius = { flag: 2, control: 4, overlay: 8 } as const;
export const fonts = { ui: 'Noto Sans', instrument: 'Barlow Semi Condensed' } as const;

export const type = {
  instrumentXL: { fontFamily: fonts.instrument, fontSize: 96, lineHeight: 96, fontWeight: '700' as const, fontVariant: ['tabular-nums'] as 'tabular-nums'[] },
  display: { fontFamily: fonts.instrument, fontSize: 64, lineHeight: 68, fontWeight: '700' as const, fontVariant: ['tabular-nums'] as 'tabular-nums'[] },
  valueL: { fontFamily: fonts.instrument, fontSize: 48, lineHeight: 52, fontWeight: '700' as const, fontVariant: ['tabular-nums'] as 'tabular-nums'[] },
  title: { fontFamily: fonts.instrument, fontSize: 32, lineHeight: 38, fontWeight: '600' as const },
  heading: { fontFamily: fonts.ui, fontSize: 24, lineHeight: 30, fontWeight: '600' as const },
  body: { fontFamily: fonts.ui, fontSize: 20, lineHeight: 28, fontWeight: '400' as const },
  label: { fontFamily: fonts.ui, fontSize: 18, lineHeight: 24, fontWeight: '600' as const },
  caption: { fontFamily: fonts.ui, fontSize: 16, lineHeight: 22, fontWeight: '400' as const },
};

export interface Palette {
  bg: string; surface: string; surfaceAlt: string; rail: string; text: string; textMuted: string; border: string;
  focus: string; attention: string; primaryBg: string; onPrimary: string;
  status: Record<StatusTone, { bg: string; fg: string }>;
  provenance: Record<'observed' | 'reported' | 'inferred' | 'reviewed', string>;
}

export type StatusTone = 'ok' | 'info' | 'caution' | 'warning' | 'critical' | 'unavailable';

export const day: Palette = {
  bg: '#F4F6F5', surface: '#FFFFFF', surfaceAlt: '#E8ECEA', rail: '#232B30', text: '#080A0B', textMuted: '#4D585E', border: '#9CA6AA',
  focus: '#005EA8', attention: '#FFC400', primaryBg: '#232B30', onPrimary: '#FFFFFF',
  status: {
    ok: { bg: '#16723A', fg: '#FFFFFF' }, info: { bg: '#1D5E91', fg: '#FFFFFF' }, caution: { bg: '#FFC400', fg: '#080A0B' },
    warning: { bg: '#C84D00', fg: '#FFFFFF' }, critical: { bg: '#A50F26', fg: '#FFFFFF' }, unavailable: { bg: '#59636A', fg: '#FFFFFF' },
  },
  provenance: { observed: '#1D5E91', reported: '#16723A', inferred: '#6941A5', reviewed: '#825500' },
};

export const night: Palette = {
  bg: '#080A0B', surface: '#151B1E', surfaceAlt: '#232B30', rail: '#232B30', text: '#FFFFFF', textMuted: '#B8C0C3', border: '#59636A',
  focus: '#62B5F5', attention: '#FFC400', primaryBg: '#232B30', onPrimary: '#FFFFFF',
  status: {
    ok: { bg: '#16723A', fg: '#FFFFFF' }, info: { bg: '#1D5E91', fg: '#FFFFFF' }, caution: { bg: '#FFC400', fg: '#080A0B' },
    warning: { bg: '#C84D00', fg: '#FFFFFF' }, critical: { bg: '#A50F26', fg: '#FFFFFF' }, unavailable: { bg: '#59636A', fg: '#FFFFFF' },
  },
  provenance: { observed: '#1D5E91', reported: '#16723A', inferred: '#6941A5', reviewed: '#825500' },
};

export const levelTone: Record<string, StatusTone> = {
  INFO: 'info', CAUTION: 'caution', WARNING: 'warning', CRITICAL: 'critical', ADVISORY: 'warning',
};
