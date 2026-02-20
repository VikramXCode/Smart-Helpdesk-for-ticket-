/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    darkMode: "class",
    theme: {
        extend: {
            colors: {
                primary: { DEFAULT: "#0f1729", hover: "#1e293b" },
                accent: { DEFAULT: "#3b82f6", blue: "#3b82f6", red: "#ef4444", green: "#22c55e" },
                "background-light": "#f1f5f9",
                "background-dark": "#0f1729",
                "card-light": "#ffffff",
                "card-dark": "#1e293b",
                "border-light": "#e2e8f0",
                "border-dark": "#334155",
                "text-light": "#0f172a",
                "text-dark": "#f8fafc",
                "subtext-light": "#64748b",
                "subtext-dark": "#94a3b8",
            },
            fontFamily: {
                display: ["Inter", "sans-serif"],
            },
            borderRadius: {
                DEFAULT: "0.5rem",
                lg: "0.75rem",
                xl: "1rem",
                full: "9999px",
            },
            boxShadow: {
                'soft': '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)',
                'hover': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
            }
        },
    },
    plugins: [
        require('@tailwindcss/forms'),
        require('@tailwindcss/container-queries'),
    ],
}
