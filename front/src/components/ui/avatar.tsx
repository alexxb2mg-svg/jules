import type { VariantProps } from "class-variance-authority"
import { Avatar as AvatarPrimitive } from "radix-ui"
import { avatarVariants } from "./variantes"

/** Jules en personnage : son portrait (persona/jules/avatar.png, servi par /api/persona/avatar), initiale si absent. */
export function AvatarJules({ className, taille, alt = "" }: { className?: string; alt?: string } & VariantProps<typeof avatarVariants>) {
  return (
    <AvatarPrimitive.Root data-slot="avatar-jules" className={avatarVariants({ taille, className })}>
      <AvatarPrimitive.Image src="/api/persona/avatar" alt={alt} className="size-full object-cover" />
      <AvatarPrimitive.Fallback delayMs={600} className="grid size-full place-items-center font-titre font-bold text-bleu">J</AvatarPrimitive.Fallback>
    </AvatarPrimitive.Root>
  )
}
