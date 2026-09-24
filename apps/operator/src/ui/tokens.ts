// Visual tokens (technical spec §7.1). Kept free of React Native imports so the contrast check can import it.

export const space = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32, xxxl: 48 } as const;

export const type = {
  display: { fontSize: 64, lineHeight: 72, fontWeight: '700' as const },
  valueL: { fontSize: 48, lineHeight: 56, fontWeight: '700' as const },
  title: { fontSize: 32, lineHeight: 40, fontWeight: '600' as const },
  heading: { fontSize: 24, lineHeight: 32, fontWeight: '600' as const },
  body: { fontSize: 20, lineHeight: 28, fontWeight: '400' as const },
  label: { fontSize: 18, lineHeight: 24, fontWeight: '500' as const },
  caption: { fontSize: 16, lineHeight: 22, fontWeight: '400' as const },
};

export interface Palette {
  bg: string;
  surface: string;
  surfaceAlt: string;
  text: string;
  textMuted: string;
  border: string;
  focus: string;
  primaryBg: string;
  onPrimary: string;
  status: Record<StatusTone, { bg: string; fg: string }>;
  provenance: Record<'observed' | 'reported' | 'inferred' | 'reviewed', string>;
}

export type StatusTone = 'ok' | 'info' | 'caution' | 'warning' | 'critical' | 'unavailable';

export const day: Palette = {
  bg: '#FFFFFF', surface: '#F1F3F5', surfaceAlt: '#E3E7EB', text: '#0B0B0B', textMuted: '#3A3F44', border: '#6B7280',
  focus: '#0047FF', primaryBg: '#0B0B0B', onPrimary: '#FFFFFF',
  status: {
    ok: { bg: '#0A7D32', fg: '#FFFFFF' }, info: { bg: '#0B5CAD', fg: '#FFFFFF' }, caution: { bg: '#FFC400', fg: '#000000' },
    warning: { bg: '#E65100', fg: '#FFFFFF' }, critical: { bg: '#B00020', fg: '#FFFFFF' }, unavailable: { bg: '#5F6368', fg: '#FFFFFF' },
  },
  provenance: { observed: '#1E3A8A', reported: '#065F46', inferred: '#6B21A8', reviewed: '#92400E' },
};

export const night: Palette = {
  bg: '#000000', surface: '#111418', surfaceAlt: '#1C2127', text: '#E8E8E8', textMuted: '#A7ADB4', border: '#3C434B',
  focus: '#5B8CFF', primaryBg: '#E8E8E8', onPrimary: '#000000',
  status: {
    ok: { bg: '#3DDC84', fg: '#000000' }, info: { bg: '#7FB2FF', fg: '#000000' }, caution: { bg: '#FFD54F', fg: '#000000' },
    warning: { bg: '#FF8A50', fg: '#000000' }, critical: { bg: '#FF5370', fg: '#000000' }, unavailable: { bg: '#9AA0A6', fg: '#000000' },
  },
  provenance: { observed: '#1E3A8A', reported: '#065F46', inferred: '#6B21A8', reviewed: '#92400E' },
};

export const levelTone: Record<string, StatusTone> = {
  INFO: 'info', CAUTION: 'caution', WARNING: 'warning', CRITICAL: 'critical', ADVISORY: 'warning',
};
