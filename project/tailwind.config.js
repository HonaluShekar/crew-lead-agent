/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Operations console foundation
        console: {
          950: '#0a0f1a',
          900: '#0f1623',
          850: '#131c2b',
          800: '#1a2435',
          750: '#212d42',
          700: '#283447',
          600: '#3a4860',
          500: '#52617a',
        },
        accent: {
          DEFAULT: '#3b82f6',
          soft: '#60a5fa',
          deep: '#1d4ed8',
        },
        severity: {
          critical: '#ef4444',
          high: '#f97316',
          medium: '#f59e0b',
          low: '#64748b',
        },
        status: {
          ok: '#22c55e',
          warn: '#f59e0b',
          error: '#ef4444',
          info: '#3b82f6',
          idle: '#64748b',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      boxShadow: {
        'console': '0 1px 0 0 rgba(255,255,255,0.04) inset, 0 8px 24px -12px rgba(0,0,0,0.6)',
        'glow-blue': '0 0 0 1px rgba(59,130,246,0.35), 0 0 20px -4px rgba(59,130,246,0.35)',
        'glow-red': '0 0 0 1px rgba(239,68,68,0.35), 0 0 20px -4px rgba(239,68,68,0.35)',
      },
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0', transform: 'translateY(4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-in-right': {
          '0%': { opacity: '0', transform: 'translateX(16px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        'pulse-soft': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.4' },
        },
        'shimmer': {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
      },
      animation: {
        'fade-in': 'fade-in 0.25s ease-out',
        'slide-in-right': 'slide-in-right 0.3s ease-out',
        'pulse-soft': 'pulse-soft 1.6s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
      },
    },
  },
  plugins: [],
};
