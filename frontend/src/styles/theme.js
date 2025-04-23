/**
 * Theme Configuration
 * 
 * This file contains theme-related constants that can be used throughout
 * your application. It provides a single source of truth for your theme colors,
 * spacing, breakpoints, etc.
 * 
 * Last updated: 2025-04-21
 * @author nanthiniSanthanam
 */

// Primary color palette
export const PRIMARY_COLORS = {
    50: '#eef5ff',
    100: '#d9e8ff',
    200: '#bbd5ff',
    300: '#8bbaff',
    400: '#5694ff',
    500: '#3d74f4', // Primary brand color
    600: '#2a56cf',
    700: '#2344a9',
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
    500: '#ff7425', // Secondary brand color
    600: '#ed5511',
    700: '#c5400c',
    800: '#9c3410',
    900: '#7e2d12',
    950: '#441407',
  };
  
  // Tertiary color palette
  export const TERTIARY_COLORS = {
    50: '#ecfff7',
    100: '#d5fff0',
    200: '#aeffe0',
    300: '#72ffcb',
    400: '#30ebb0',
    500: '#19b29a', // Tertiary brand color
    600: '#099380',
    700: '#0a7566',
    800: '#0d5d52',
    900: '#0f4c44',
    950: '#02251e',
  };
  
  // Breakpoints (matching Tailwind defaults)
  export const BREAKPOINTS = {
    xs: '480px',
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  };
  
  // Font families
  export const FONTS = {
    sans: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif',
    display: '"Poppins", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif',
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
  
  // Transition presets
  export const TRANSITIONS = {
    fast: 'all 0.2s ease',
    default: 'all 0.3s ease',
    slow: 'all 0.5s ease',
  };
  
  // Export a default theme object
  export default {
    colors: {
      primary: PRIMARY_COLORS,
      secondary: SECONDARY_COLORS,
      tertiary: TERTIARY_COLORS,
    },
    breakpoints: BREAKPOINTS,
    fonts: FONTS,
    zIndex: Z_INDEX,
    transitions: TRANSITIONS,
  };