import { cn } from "@/lib/utils"

interface CategoryColorProps {
  color: string
  className?: string
}

function CategoryColor({ color, className }: CategoryColorProps) {
  return (
    <span
      className={cn("inline-block size-4 shrink-0 rounded-full", className)}
      style={{ backgroundColor: color }}
      aria-hidden="true"
    />
  )
}

export { CategoryColor }
