import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "#050507",
        panel: "#0a0a0f",
        border: "rgba(255,255,255,0.08)",
        muted: "#8890ae",
        purple: "#8b5cf6",
        emerald: "#06d6a0",
        pink: "#ec4899",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["SF Mono", "Fira Code", "monospace"],
      },
      boxShadow: {
        glow: "0 0 40px rgba(139,92,246,0.15)",
      },
      animation: {
        "in": "in 0.4s ease-out",
      },
      keyframes: {
        in: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};
export default config;