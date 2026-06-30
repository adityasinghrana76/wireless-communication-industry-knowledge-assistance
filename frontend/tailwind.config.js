/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#14213d',
        signal: '#0f766e',
        copper: '#b45309'
      }
    }
  },
  plugins: []
};
