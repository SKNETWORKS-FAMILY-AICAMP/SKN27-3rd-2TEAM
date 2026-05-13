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
    dreamNavy: "#131528",
    dreamDeep: "#1A1431",
    dreamPurple: "#8B6DFF",
    dreamPink: "#FF9AC8",
    dreamLavender: "#D9CCFF",
    dreamPeach: "#FFD4B8",
    dreamText: "#FAF7FF",
    dreamMuted: "#C9C0DD",
  },
  radius: {
    card: "24px",
    button: "999px",
    panel: "32px",
    pill: "999px",
  },
  shadow: {
    soft: "0 20px 60px rgba(0,0,0,0.28)",
    glow: "0 0 40px rgba(191,167,255,0.22)",
    glowSoft: "0 0 34px rgba(217,204,255,0.20)",
    card: "0 18px 42px rgba(10,8,24,0.26)",
  },
  blur: {
    glass: "blur(18px)",
    glassBase: "blur(12px)",
    glassStrong: "blur(18px)",
  },
} as const;

export type ThemeColor = keyof typeof THEME.color;
