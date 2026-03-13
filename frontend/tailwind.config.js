/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Cyberpunk 2077 brand scale (fortuna classes map to yellow/cyan)
        fortuna: {
          50:  '#080F18',
          100: '#0B1623',
          200: '#1E3048',
          300: '#00F0FF',
          400: '#00CCDD',
          500: '#FCEE09',
          600: '#FCEE09',
          700: '#D4C808',
          800: '#B5AC07',
          900: '#968F06',
        },
        // Cyberpunk 2077 palette — mapped to CSS variables for dark/light theming
        cp: {
          black:    'rgb(var(--cp-black) / <alpha-value>)',
          surface:  'rgb(var(--cp-surface) / <alpha-value>)',
          surface2: 'rgb(var(--cp-surface2) / <alpha-value>)',
          border:   'rgb(var(--cp-border) / <alpha-value>)',
          text:     'rgb(var(--cp-text) / <alpha-value>)',
          muted:    'rgb(var(--cp-muted) / <alpha-value>)',
          yellow:   'rgb(var(--cp-yellow) / <alpha-value>)',
          cyan:     'rgb(var(--cp-cyan) / <alpha-value>)',
          red:      'rgb(var(--cp-red) / <alpha-value>)',
          green:    'rgb(var(--cp-green) / <alpha-value>)',
        },
      },
    },
  },
  plugins: [],
}
