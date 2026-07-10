import { z } from "zod"

import { THEME_VALUES } from "./constants"

const themeSchema = z.enum(THEME_VALUES)

type Theme = z.infer<typeof themeSchema>

export { themeSchema }
export type { Theme }
