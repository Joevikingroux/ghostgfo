import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          teal: "#2DD4BF",
          cyan: "#06B6D4",
        },
        surface: {
          DEFAULT: "#0d0d0d",
          card: "#141414",
          border: "#222222",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        heading: ["Space Grotesk", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      backgroundImage: {
        "brand-gradient":
          "linear-gradient(135deg, #2DD4BF 0%, #06B6D4 100%)",
      },
    },
  },
  plugins: [],
};

export default config;
