import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#fbf7f1",
          100: "#f3e9d9",
          200: "#e6cfae",
          300: "#d7ae7c",
          400: "#c78a52",
          500: "#b06a34",
          600: "#8f4f2a",
          700: "#723d24",
          800: "#5c3122",
          900: "#4c291f",
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
        display: ["var(--font-display)", "serif"],
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
