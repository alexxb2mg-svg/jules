// Variants (class-variance-authority) des surfaces de Jules, sans composant : les écrans les appliquent sur leurs
// propres éléments (motion.section, motion.button…). Toute valeur vient des tokens du thème (index.css).
import { cva } from "class-variance-authority"
import { fusion } from "@/lib/utils"

// Surfaces : séparées par la teinte et l'espace, pas par un cadre. Seul « souleve » porte une ombre
// (ce qui flotte réellement : tiroir, bulle, bouton). « lisere » : filet de la matière (ou d'un état) sur le bord gauche.
export const surfaceVariants = fusion(cva("rounded-surface transition-colors", {
  variants: {
    ton: {
      plat: "bg-card text-card-foreground",
      teinte: "bg-surface-2 text-encre",
      matiere: "bg-(--m-fond) text-encre",
      souleve: "bg-card text-card-foreground shadow-souleve",
    },
    lisere: {
      true: "shadow-[inset_3px_0_0_0_var(--m-accent,var(--j-bleu))]",
      succes: "shadow-[inset_3px_0_0_0_var(--j-succes)]",
      alerte: "shadow-[inset_3px_0_0_0_var(--j-orange)]",
      false: "",
    },
    espace: {
      aucun: "",
      compact: "px-4 py-3",
      normal: "p-5",
      large: "p-5 md:p-7",
    },
    cliquable: {
      true: "cursor-pointer text-left hover:bg-survol",
      false: "",
    },
  },
  defaultVariants: { ton: "plat", lisere: false, espace: "normal", cliquable: false },
}))

// Pastille : étiquette ou puce ronde (999 px), teintée par la matière ou par un état.
export const pastilleVariants = fusion(cva("inline-flex shrink-0 items-center gap-1.5 rounded-full font-semibold", {
  variants: {
    ton: {
      matiere: "bg-(--m-fond) text-(--m-texte)",
      "matiere-plein": "bg-(--m-texte) text-white",
      jules: "bg-bleu-clair text-bleu",
      neutre: "bg-surface-2 text-gris",
      succes: "bg-succes-fond text-succes",
      alerte: "bg-alerte-fond text-alerte",
    },
    taille: {
      puce: "size-8 justify-center text-petit",
      icone: "size-10 justify-center rounded-2xl",
      etiquette: "px-3 py-1 text-petit",
    },
  },
  defaultVariants: { ton: "matiere", taille: "etiquette" },
}))

// Typographie : la hiérarchie passe par la taille et la graisse, pas par des cadres.
export const titreVariants = fusion(cva("m-0 font-titre text-encre", {
  variants: {
    niveau: {
      ecran: "text-ecran font-extrabold text-balance",
      bloc: "text-bloc font-bold",
      surtitre: "text-petit font-semibold text-(--m-texte,var(--j-gris))",
      etiquette: "text-petit font-semibold tracking-wide uppercase",
    },
  },
  defaultVariants: { niveau: "bloc" },
}))

// Bulles de conversation. Jules : bleu clair, coin cassé du côté de son portrait (première bulle d'un groupe).
// Élève : aplat d'encre à droite. Même rendu dans la discussion et dans le panneau Jules d'une leçon.
export const bulleVariants = fusion(cva("px-4 py-3 text-lecture break-words", {
  variants: {
    auteur: {
      jules: "rounded-surface bg-bleu-clair text-encre",
      eleve: "rounded-surface rounded-br-md bg-eleve text-sur-eleve",
    },
    tete: { true: "", false: "" },
  },
  compoundVariants: [
    { auteur: "jules", tete: true, class: "rounded-tl-md" },
    { auteur: "jules", tete: false, class: "rounded-l-md" },
  ],
  defaultVariants: { auteur: "jules", tete: true },
}))

// Portrait de Jules.
export const avatarVariants = fusion(cva("relative flex shrink-0 overflow-hidden rounded-full bg-bleu-clair", {
  variants: {
    taille: { sm: "size-8", md: "size-10", lg: "size-12", xl: "size-20" },
  },
  defaultVariants: { taille: "md" },
}))
