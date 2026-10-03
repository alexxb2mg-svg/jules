import * as React from "react"
import type { VariantProps } from "class-variance-authority"
import { pastilleVariants } from "./variantes"

/** Étiquette ou puce ronde (voir pastilleVariants). */
export function Pastille({ className, ton, taille, ...props }: React.ComponentProps<"span"> & VariantProps<typeof pastilleVariants>) {
  return <span data-slot="pastille" className={pastilleVariants({ ton, taille, className })} {...props} />
}
