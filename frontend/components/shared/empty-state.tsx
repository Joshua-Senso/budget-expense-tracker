import { cn } from "@/lib/utils"

function EmptyState({
  message,
  className,
}: {
  message: string
  className?: string
}) {
  return (
    <p className={cn("text-sm text-muted-foreground", className)} role="status">
      {message}
    </p>
  )
}

export { EmptyState }
