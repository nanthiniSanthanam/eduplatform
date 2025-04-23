/**
 * Theme Configuration
 * 
 * This file contains theme-related constants that can be used throughout
 * your application for consistent styling.
 * 
 * Last updated: 2025-04-21
 * @author nanthiniSanthanam
 */

// Primary color palette (matches your gradient)
export const PRIMARY_COLORS = {
    50: '#eef5ff',
    100: '#d9e8ff',
    200: '#bbd5ff',
    300: '#8bbaff',
    400: '#5694ff',
    500: '#3d74f4', // Primary brand color from your CSS
    600: '#2a56cf',
    700: '#2342b8', // From your gradient
    800: '#22398b',
    900: '#1e3372',
    950: '#172048',
  };
  
  // Secondary color palette
  export const SECONDARY_COLORS = {
    50: '#fff6ed',
    100: '#ffebd4',
    200: '#ffd3a8',
    300: '#ffb36f',
    400: '#ff9141',
    500: '#ff7425',
    600: '#ed5511',
    700: '#c5400c',
    800: '#9c3410',
    900: '#7e2d12',
    950: '#441407',
  };
  
  // Tertiary color palette (matches your CTA gradient)
  export const TERTIARY_COLORS = {
    50: '#ecfff7',
    100: '#d5fff0',
    200: '#aeffe0',
    300: '#72ffcb',
    400: '#30ebb0',
    500: '#19b29a', // From your CTA gradient
    600: '#0b7268', // From your CTA gradient
    700: '#0a7566',
    800: '#0d5d52',
    900: '#0f4c44',
    950: '#02251e',
  };
  
  // Font families from your CSS
  export const FONTS = {
    sans: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif',
    display: '"Plus Jakarta Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif',
    mono: '"JetBrains Mono", SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
  };
  
  // Z-index values
  export const Z_INDEX = {
    dropdown: 1000,
    sticky: 1020,
    fixed: 1030,
    modal: 1050,
    popover: 1060,
    tooltip: 1070,
  };
  
  // Transition presets (matching your CSS)
  export const TRANSITIONS = {
    fast: 'all 0.2s ease',
    default: 'all 0.3s ease',
    slow: 'all 0.5s ease',
    premium: 'all 0.3s ease', // Matches your btn-premium transition
  };
  
  // Shadow presets
  export const SHADOWS = {
    card: 'var(--shadow-card)', // Will reference the Tailwind shadow-card class you're using
    soft: 'var(--shadow-soft)', // Will reference the Tailwind shadow-soft class you're using
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  };
  
  // Export a default theme object
  export default {
    colors: {
      primary: PRIMARY_COLORS,
      secondary: SECONDARY_COLORS,
      tertiary: TERTIARY_COLORS,
    },
    fonts: FONTS,
    zIndex: Z_INDEX,
    transitions: TRANSITIONS,
    shadows: SHADOWS,
  };