/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html",
  ],

  theme: {

    // Add container configuration here
    container: {
      center: true,
      padding: {
        DEFAULT: '1rem',
        sm: '2rem',
        lg: '4rem',
        xl: '5rem',
      },
      // Increase max widths for larger screens
      screens: {
        sm: '640px',
        md: '768px',
        lg: '1024px',
        xl: '1280px',
        '2xl': '1536px',  
        '3xl': '1600px',
        '4xl': '1700px',},
    },

    extend: {
      colors: {
        primary: {
          50: '#eef4ff',
          100: '#daeaff',
          200: '#bdd6ff',
          300: '#90bbff',
          400: '#6096fc',
          500: '#3d74f4', /* Main brand color - updated for better contrast */
          600: '#2855db',
          700: '#2342b8',
          800: '#1f3896',
          900: '#1e327a',
        },
        secondary: {
          50: '#fff8f0',
          100: '#fff0e1',
          200: '#ffdec1',
          300: '#ffc68e',
          400: '#ffa352',
          500: '#ff7425', /* Secondary color - updated for better contrast */
          600: '#fa5d14',
          700: '#d5470f',
          800: '#a83c14',
          900: '#883515',
        },
        tertiary: {
          50: '#edfcf8',
          100: '#d2f7ed',
          200: '#a8eddd',
          300: '#73dec9',
          400: '#40c8b2',
          500: '#19b29a', /* Tertiary color */
          600: '#0c8f7c',
          700: '#0b7268',
          800: '#0d5b54',
          900: '#0e4b47',
        },
        success: '#10b981',
        warning: '#f59e0b',
        error: '#ef4444',
        info: '#0ea5e9',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
        display: ['"Plus Jakarta Sans"', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      boxShadow: {
        'soft': '0 2px 15px -3px rgba(0, 0, 0, 0.07), 0 10px 20px -2px rgba(0, 0, 0, 0.04)',
        'card': '0 7px 15px rgba(0, 0, 0, 0.03), 0 3px 8px rgba(0, 0, 0, 0.05)',
        'testimonial': '0 20px 25px -5px rgba(0, 0, 0, 0.05), 0 10px 10px -5px rgba(0, 0, 0, 0.01)',
      },
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.5rem',
        '3xl': '2rem',
      },
      animation: {
        'fade-in-up': 'fadeInUp 0.6s ease-out forwards',
        'fade-in': 'fadeIn 0.6s ease-out forwards',
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
    }
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/line-clamp'),
    require('@tailwindcss/typography'),
  ],
}