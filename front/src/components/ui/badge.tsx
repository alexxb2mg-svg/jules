import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn, fusion } from "@/lib/utils"
import { Slot } from "radix-ui"

const badgeVariants = fusion(cva(
  "inline-flex w-fit shrink-0 items-center justify-center gap-1 overflow-hidden rounded-full border border-transparent px-2 py-0.5 text-xs font-medium whitespace-nowrap transition-[color,box-shadow] focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 aria-invalid:border-destructive aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 [&>svg]:pointer-events-none [&>svg]:size-3",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground [a&]:hover:bg-primary/90",
        secondary:
          "bg-secondary text-secondary-foreground [a&]:hover:bg-secondary/90",
        destructive:
          "bg-destructive text-white focus-visible:ring-destructive/20 dark:bg-destructive/60 dark:focus-visible:ring-destructive/40 [a&]:hover:bg-destructive/90",
        outline:
          "border-border text-foreground [a&]:hover:bg-accent [a&]:hover:text-accent-foreground",
        ghost: "[a&]:hover:bg-accent [a&]:hover:text-accent-foreground",
        link: "text-primary underline-offset-4 [a&]:hover:underline",
        // états d'une notion (leçons, bilan) : teinte douce, texte contrasté dans les deux thèmes
        succes: "bg-succes-fond px-2.5 py-1 text-petit font-semibold text-succes [&>svg]:size-3.5",
        alerte: "bg-alerte-fond px-2.5 py-1 text-petit font-semibold text-alerte [&>svg]:size-3.5",
        info: "bg-bleu-clair px-2.5 py-1 text-petit font-semibold text-bleu [&>svg]:size-3.5",
        neutre: "bg-surface-2 px-2.5 py-1 text-petit font-semibold text-gris [&>svg]:size-3.5",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
))

function Badge({
  className,
  variant = "default",
  asChild = false,
  ...props
}: React.ComponentProps<"span"> &
  VariantProps<typeof badgeVariants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot.Root : "span"

  return (
    <Comp
      data-slot="badge"
      data-variant={variant}
      className={cn(badgeVariants({ variant }), className)}
      {...props}
    />
  )
}

export { Badge, badgeVariants }
