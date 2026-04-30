/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        neev: {
          bg: '#0a0a0f',
          card: '#111118',
          border: '#1e1e2e',
          purple: '#7c3aed',
          violet: '#8b5cf6',
          pink: '#ec4899',
          text: '#e2e8f0',
          muted: '#64748b',
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
