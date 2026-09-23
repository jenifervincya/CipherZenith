/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        console: {
          bg: "#05070a",
          panel: "#0b0f14",
        },
      },
    },
  },
  plugins: [],
};