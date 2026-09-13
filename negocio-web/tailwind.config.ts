import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#fff5f1",
          100: "#ffe6db",
          200: "#ffc8b0",
          300: "#ffa47e",
          400: "#fb7a52",
          500: "#f2502e",
          600: "#d63c1e",
          700: "#ad2f18",
          800: "#86271a",
          900: "#6b2117",
        },
        ink: {
          50: "#f6f6f5",
          100: "#e7e6e3",
          200: "#cfcdc7",
          300: "#aeaba1",
          400: "#87837a",
          500: "#6b675f",
          600: "#54514b",
          700: "#44423d",
          800: "#2f2d2a",
          900: "#1c1b19",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "sans-serif"],
        sans: ["var(--font-sans)", "sans-serif"],
      },
      boxShadow: {
        card: "0 2px 10px rgba(28, 27, 25, 0.06)",
      },
    },
  },
  plugins: [],
};

export default config;
