/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      animation: {
        pulse: "pulse 0.6s ease-in-out",
      },
    },
  },
  plugins: [],
};
