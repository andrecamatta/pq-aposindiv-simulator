// S-Tier Typography System
// Professional typography scale with perfect line heights and spacing

export const typography = {
  // Font Families
  fontFamily: {
    sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
    mono: ['JetBrains Mono', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
  },

  // Font Sizes with line heights
  fontSize: {
    xs: { fontSize: '0.75rem', lineHeight: '1rem' },      // 12px / 16px
    sm: { fontSize: '0.875rem', lineHeight: '1.25rem' },  // 14px / 20px
    base: { fontSize: '1rem', lineHeight: '1.5rem' },     // 16px / 24px
    lg: { fontSize: '1.125rem', lineHeight: '1.75rem' },  // 18px / 28px
    xl: { fontSize: '1.25rem', lineHeight: '1.75rem' },   // 20px / 28px
    '2xl': { fontSize: '1.5rem', lineHeight: '2rem' },    // 24px / 32px
    '3xl': { fontSize: '1.875rem', lineHeight: '2.25rem' }, // 30px / 36px
    '4xl': { fontSize: '2.25rem', lineHeight: '2.5rem' }, // 36px / 40px
    '5xl': { fontSize: '3rem', lineHeight: '1' },         // 48px
    '6xl': { fontSize: '3.75rem', lineHeight: '1' },      // 60px
  },

  // Font Weights
  fontWeight: {
    thin: '100',
    extralight: '200',
    light: '300',
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
    extrabold: '800',
    black: '900',
  },

  // Letter Spacing
  letterSpacing: {
    tighter: '-0.05em',
    tight: '-0.025em',
    normal: '0em',
    wide: '0.025em',
    wider: '0.05em',
    widest: '0.1em',
  },
} as const;

// Semantic Typography Styles
export const textStyles = {
  // Headings
  heading: {
    h1: {
      fontSize: typography.fontSize['4xl'].fontSize,
      lineHeight: typography.fontSize['4xl'].lineHeight,
      fontWeight: typography.fontWeight.bold,
      letterSpacing: typography.letterSpacing.tight,
    },
    h2: {
      fontSize: typography.fontSize['3xl'].fontSize,
      lineHeight: typography.fontSize['3xl'].lineHeight,
      fontWeight: typography.fontWeight.bold,
      letterSpacing: typography.letterSpacing.tight,
    },
    h3: {
      fontSize: typography.fontSize['2xl'].fontSize,
      lineHeight: typography.fontSize['2xl'].lineHeight,
      fontWeight: typography.fontWeight.semibold,
      letterSpacing: typography.letterSpacing.tight,
    },
    h4: {
      fontSize: typography.fontSize.xl.fontSize,
      lineHeight: typography.fontSize.xl.lineHeight,
      fontWeight: typography.fontWeight.semibold,
      letterSpacing: typography.letterSpacing.normal,
    },
    h5: {
      fontSize: typography.fontSize.lg.fontSize,
      lineHeight: typography.fontSize.lg.lineHeight,
      fontWeight: typography.fontWeight.semibold,
      letterSpacing: typography.letterSpacing.normal,
    },
    h6: {
      fontSize: typography.fontSize.base.fontSize,
      lineHeight: typography.fontSize.base.lineHeight,
      fontWeight: typography.fontWeight.semibold,
      letterSpacing: typography.letterSpacing.normal,
    },
  },

  // Body Text
  body: {
    large: {
      fontSize: typography.fontSize.lg.fontSize,
      lineHeight: typography.fontSize.lg.lineHeight,
      fontWeight: typography.fontWeight.normal,
    },
    medium: {
      fontSize: typography.fontSize.base.fontSize,
      lineHeight: typography.fontSize.base.lineHeight,
      fontWeight: typography.fontWeight.normal,
    },
    small: {
      fontSize: typography.fontSize.sm.fontSize,
      lineHeight: typography.fontSize.sm.lineHeight,
      fontWeight: typography.fontWeight.normal,
    },
  },

  // UI Text
  ui: {
    caption: {
      fontSize: typography.fontSize.xs.fontSize,
      lineHeight: typography.fontSize.xs.lineHeight,
      fontWeight: typography.fontWeight.normal,
      letterSpacing: typography.letterSpacing.wide,
    },
    label: {
      fontSize: typography.fontSize.sm.fontSize,
      lineHeight: typography.fontSize.sm.lineHeight,
      fontWeight: typography.fontWeight.medium,
    },
    button: {
      fontSize: typography.fontSize.sm.fontSize,
      lineHeight: typography.fontSize.sm.lineHeight,
      fontWeight: typography.fontWeight.medium,
      letterSpacing: typography.letterSpacing.wide,
    },
  },

  // Code
  code: {
    inline: {
      fontSize: typography.fontSize.sm.fontSize,
      lineHeight: typography.fontSize.sm.lineHeight,
      fontFamily: typography.fontFamily.mono,
      fontWeight: typography.fontWeight.normal,
    },
    block: {
      fontSize: typography.fontSize.sm.fontSize,
      lineHeight: '1.6',
      fontFamily: typography.fontFamily.mono,
      fontWeight: typography.fontWeight.normal,
    },
  },
} as const;

export type TypographyToken = keyof typeof typography;
export type TextStyleToken = keyof typeof textStyles;