const THEME_VALUES = ["dark", "light"] as const

type ThemeName = (typeof THEME_VALUES)[number]

const DEFAULT_THEME: ThemeName = "dark"

// Display labels only -- the stored/CSS-facing value stays "dark" (not
// "warm-dark") to match the existing DB default and the `.dark` selector in
// styles/themes/warm-dark.css.
const THEME_LABELS: Record<ThemeName, string> = {
  dark: "Warm Dark",
  light: "Light",
}

export { THEME_VALUES, DEFAULT_THEME, THEME_LABELS }
export type { ThemeName }
