/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#111827",
        mist: "#eef2ff",
        sand: "#f7f4ec",
        line: "#d6d3d1",
        moss: "#12372a",
        accent: "#d97706",
      },
      boxShadow: {
        panel: "0 18px 60px rgba(17, 24, 39, 0.08)",
        soft: "0 10px 30px rgba(17, 24, 39, 0.06)",
      },
      borderRadius: {
        "4xl": "2rem",
      },
      fontFamily: {
        sans: ["Manrope", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      animation: {
        shimmer: "shimmer 1.8s linear infinite",
        floaty: "floaty 6s ease-in-out infinite",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        floaty: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-8px)" },
        },
      },
    },
  },
  plugins: [],
};
