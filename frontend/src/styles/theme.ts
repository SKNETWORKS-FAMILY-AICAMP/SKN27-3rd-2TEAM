export const THEME = {
  color: {
    background: "#0E1018",
    surface: "rgba(255,255,255,0.06)",
    surface_strong: "rgba(255,255,255,0.10)",
    text_primary: "#F4F0FF",
    text_secondary: "#B9B3C9",
    accent_mint: "#8EF6D4",
    accent_lavender: "#BFA7FF",
    accent_blue: "#8EC5FF",
  },
  radius: {
    card: "24px",
    button: "999px",
    panel: "32px",
  },
  shadow: {
    soft: "0 20px 60px rgba(0,0,0,0.28)",
    glow: "0 0 40px rgba(191,167,255,0.22)",
  },
  blur: {
    glass: "blur(18px)",
  },
} as const;

export type ThemeColor = keyof typeof THEME.color;
