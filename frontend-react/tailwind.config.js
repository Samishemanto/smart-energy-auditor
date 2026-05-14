/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg:      '#060B17',
        surface: '#0C1525',
        border:  '#1A2840',
        teal:    '#00C9B8',
        blue:    '#1D4ED8',
        muted:   '#4B6280',
        subtle:  '#64748B',
        text:    '#F1F5F9',
        textSub: '#94A3B8',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
