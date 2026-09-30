"use client"

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn, fusion } from "@/lib/utils"
import { Progress as ProgressPrimitive } from "radix-ui"

// « matiere » : la progression prend l'accent de la matière posée sur la page (--m-accent).
const indicateurVariants = fusion(cva("h-full w-full flex-1 rounded-full transition-all", {
  variants: { ton: { jules: "bg-primary", matiere: "bg-(--m-accent,var(--j-bleu))" } },
  defaultVariants: { ton: "jules" },
}))

function Progress({
  className,
  value,
  ton,
  ...props
}: React.ComponentProps<typeof ProgressPrimitive.Root> & VariantProps<typeof indicateurVariants>) {
  return (
    <ProgressPrimitive.Root
      data-slot="progress"
      className={cn(
        "relative h-2 w-full overflow-hidden rounded-full bg-bord",
        className
      )}
      {...props}
    >
      <ProgressPrimitive.Indicator
        data-slot="progress-indicator"
        className={indicateurVariants({ ton })}
        style={{ transform: `translateX(-${100 - (value || 0)}%)` }}
      />
    </ProgressPrimitive.Root>
  )
}

export { Progress }
