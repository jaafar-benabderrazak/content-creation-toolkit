import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#fef3e2',
          100: '#fde4b8',
          200: '#fcd48a',
          300: '#fbc35c',
          400: '#fab73a',
          500: '#f9ab18',
          600: '#f8a015',
          700: '#f79012',
          800: '#f6800f',
          900: '#f46209',
        },
      },
    },
  },
  plugins: [],
}

export default config

