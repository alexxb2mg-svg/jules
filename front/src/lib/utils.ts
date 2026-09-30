import { clsx, type ClassValue } from "clsx"
import { extendTailwindMerge } from "tailwind-merge"

// Tokens du thème (index.css) que tailwind-merge doit reconnaître : sans ça, « text-lecture » passerait pour une
// couleur et serait effacé par « text-encre », « rounded-surface » ne remplacerait pas « rounded-md ».
const twMerge = extendTailwindMerge({
  extend: {
    theme: {
      text: ["ecran", "matiere", "bloc", "lecture", "courant", "petit"],
      radius: ["surface"],
      shadow: ["relief", "relief-haut", "souleve"],
    },
  },
})

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** Enveloppe un `cva` : la `className` passée en option remplace proprement les classes du variant qu'elle contredit. */
// eslint-disable-next-line @typescript-eslint/no-explicit-any -- signature générique de cva
export const fusion = <F extends (...args: any[]) => string>(variants: F): F => ((...args: Parameters<F>) => cn(variants(...args))) as F
