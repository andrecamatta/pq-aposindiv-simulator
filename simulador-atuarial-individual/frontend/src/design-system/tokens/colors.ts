// S-Tier Design System Color Tokens
// Professional color palette inspired by Stripe, Linear, and Airbnb

export const colors = {
  // Primary Brand Colors - Inspired by ActuarialSim reference
  primary: {
    50: '#eff8ff',
    100: '#ddf0ff',
    200: '#b3e1ff',
    300: '#7dcbff',
    400: '#38b0ff',
    500: '#13a4ec', // Main brand color from reference
    600: '#0e7bb8',
    700: '#0d6195',
    800: '#0f527a',
    900: '#134566',
    950: '#0c2b44',
  },
  
  // Perfect Neutral Scale
  gray: {
    50: '#f8fafc',
    100: '#f1f5f9',
    200: '#e2e8f0',
    300: '#cbd5e1',
    400: '#94a3b8',
    500: '#64748b',
    600: '#475569',
    700: '#334155',
    800: '#1e293b',
    900: '#0f172a',
    950: '#020617',
  },

  // Semantic Colors
  success: {
    50: '#ecfdf5',
    100: '#d1fae5',
    200: '#a7f3d0',
    300: '#6ee7b7',
    400: '#34d399',
    500: '#10b981',
    600: '#059669',
    700: '#047857',
    800: '#065f46',
    900: '#064e3b',
    950: '#022c22',
  },

  error: {
    50: '#fef2f2',
    100: '#fee2e2',
    200: '#fecaca',
    300: '#fca5a5',
    400: '#f87171',
    500: '#ef4444',
    600: '#dc2626',
    700: '#b91c1c',
    800: '#991b1b',
    900: '#7f1d1d',
    950: '#450a0a',
  },

  warning: {
    50: '#fffbeb',
    100: '#fef3c7',
    200: '#fde68a',
    300: '#fcd34d',
    400: '#fbbf24',
    500: '#f59e0b',
    600: '#d97706',
    700: '#b45309',
    800: '#92400e',
    900: '#78350f',
    950: '#451a03',
  },

  info: {
    50: '#f0f9ff',
    100: '#e0f2fe',
    200: '#bae6fd',
    300: '#7dd3fc',
    400: '#38bdf8',
    500: '#0ea5e9',
    600: '#0284c7',
    700: '#0369a1',
    800: '#075985',
    900: '#0c4a6e',
    950: '#082f49',
  },
} as const;

// Semantic aliases for better developer experience
export const semanticColors = {
  // Background colors
  background: {
    primary: colors.gray[50],
    secondary: colors.gray[100],
    tertiary: colors.gray[200],
    inverse: colors.gray[900],
  },
  
  // Text colors
  text: {
    primary: colors.gray[900],
    secondary: colors.gray[600],
    tertiary: colors.gray[500],
    inverse: colors.gray[50],
    placeholder: colors.gray[400],
  },
  
  // Border colors
  border: {
    primary: colors.gray[200],
    secondary: colors.gray[300],
    tertiary: colors.gray[400],
    focus: colors.primary[500],
  },
  
  // Surface colors (for cards, modals, etc.)
  surface: {
    primary: colors.gray[50],
    secondary: '#ffffff',
    tertiary: colors.gray[100],
  },
} as const;

export type ColorToken = keyof typeof colors;
export type SemanticColorToken = keyof typeof semanticColors;