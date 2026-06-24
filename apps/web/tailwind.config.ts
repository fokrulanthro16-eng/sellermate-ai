import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    container: { center: true, padding: "2rem", screens: { "2xl": "1400px" } },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: { DEFAULT: "hsl(var(--primary))", foreground: "hsl(var(--primary-foreground))" },
        secondary: { DEFAULT: "hsl(var(--secondary))", foreground: "hsl(var(--secondary-foreground))" },
        destructive: { DEFAULT: "hsl(var(--destructive))", foreground: "hsl(var(--destructive-foreground))" },
        muted: { DEFAULT: "hsl(var(--muted))", foreground: "hsl(var(--muted-foreground))" },
        accent: { DEFAULT: "hsl(var(--accent))", foreground: "hsl(var(--accent-foreground))" },
        popover: { DEFAULT: "hsl(var(--popover))", foreground: "hsl(var(--popover-foreground))" },
        card: { DEFAULT: "hsl(var(--card))", foreground: "hsl(var(--card-foreground))" },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        "2xl": "1rem",
        "3xl": "1.25rem",
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "system-ui", "-apple-system", "sans-serif"],
      },
      animation: {
        "slide-up":   "slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) both",
        "slide-down": "slideDown 0.3s cubic-bezier(0.16, 1, 0.3, 1) both",
        "fade-in":    "fadeIn 0.3s ease both",
        "scale-in":   "scaleIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) both",
        "float":      "float 3.5s ease-in-out infinite",
        "pulse-glow": "pulseGlow 2.5s ease-in-out infinite",
        "spin-slow":  "spin 8s linear infinite",
        "shimmer":    "shimmer 2s linear infinite",
      },
      keyframes: {
        slideUp: {
          from: { opacity: "0", transform: "translateY(14px)" },
          to:   { opacity: "1", transform: "translateY(0)" },
        },
        slideDown: {
          from: { opacity: "0", transform: "translateY(-8px)" },
          to:   { opacity: "1", transform: "translateY(0)" },
        },
        fadeIn: {
          from: { opacity: "0" },
          to:   { opacity: "1" },
        },
        scaleIn: {
          from: { opacity: "0", transform: "scale(0.95)" },
          to:   { opacity: "1", transform: "scale(1)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%":      { transform: "translateY(-5px)" },
        },
        pulseGlow: {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(99, 102, 241, 0)" },
          "50%":      { boxShadow: "0 0 20px 4px rgba(99, 102, 241, 0.15)" },
        },
        shimmer: {
          from: { backgroundPosition: "-400% 0" },
          to:   { backgroundPosition: "400% 0" },
        },
      },
      backgroundSize: {
        "400%": "400%",
      },
      boxShadow: {
        "glass": "0 8px 32px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
        "glass-dark": "0 8px 32px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.2)",
        "glow-blue": "0 0 24px rgba(59,130,246,0.3)",
        "glow-violet": "0 0 24px rgba(124,58,237,0.3)",
        "glow-primary": "0 0 20px rgba(79,110,247,0.25)",
        "premium": "0 4px 24px rgba(0,0,0,0.06), 0 1px 4px rgba(0,0,0,0.04)",
        "premium-hover": "0 8px 40px rgba(0,0,0,0.1), 0 2px 8px rgba(0,0,0,0.06)",
      },
    },
  },
  plugins: [],
};

export default config;
