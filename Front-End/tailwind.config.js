export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: { sans: ['"Atkinson Hyperlegible"', 'system-ui', 'sans-serif'] },
      colors: {
        ink: '#0F2A33',
        teal: { DEFAULT: '#0E7C86', dark: '#0A5F67', soft: '#D8EEF0' },
        mist: '#EEF4F4',
        signal: '#D6342C',
        amber: '#E0A100',
        ok: '#2E8B57',
      },
    },
  },
  plugins: [],
};
