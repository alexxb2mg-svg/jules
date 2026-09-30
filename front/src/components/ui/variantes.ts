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
      // carte de liste : la couleur de la matière se fond dans la surface (coin haut gauche → bas droite)
      degrade: "bg-[linear-gradient(135deg,var(--m-fond,var(--j-surface-2))_25%,var(--j-surface))] text-encre",
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
      // pleines : l'accent de la matière (en-tête de liste), la couleur du type de bloc (voir blocVariants)
      "matiere-accent": "bg-(--m-accent,var(--j-bleu)) text-white",
      bloc: "bg-(--b-plein) text-white",
    },
    taille: {
      puce: "size-8 justify-center text-petit",
      icone: "size-10 justify-center rounded-2xl",
      bloc: "size-9 justify-center",
      entete: "size-14 justify-center rounded-2xl",
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
      matiere: "text-matiere font-extrabold text-balance",
      bloc: "text-bloc font-bold",
      surtitre: "text-petit font-semibold text-(--m-texte,var(--j-gris))",
      etiquette: "text-petit font-semibold tracking-wide uppercase",
    },
  },
  defaultVariants: { niveau: "bloc" },
}))

// Type d'un bloc de leçon ou de fiche : reconnaissable d'un coup d'œil par sa teinte de fond. Pose --b-plein
// (pastille d'icône, étiquette) et --b-fond (le bloc) ; « retenir » et « matiere » prennent la couleur de la matière.
export const blocVariants = fusion(cva("rounded-surface bg-(--b-fond) text-encre transition-colors", {
  variants: {
    type: {
      retenir: "[--b-plein:var(--m-texte,var(--j-bleu))] [--b-fond:color-mix(in_oklab,var(--m-accent,var(--j-bleu))_9%,var(--j-surface))]",
      matiere: "[--b-plein:var(--m-texte,var(--j-bleu))] [--b-fond:var(--j-surface)]",
      objectifs: "[--b-plein:var(--j-bloc-objectifs)] [--b-fond:var(--j-bloc-objectifs-fond)]",
      exemple: "[--b-plein:var(--j-bloc-exemple)] [--b-fond:var(--j-bloc-exemple-fond)]",
      exercice: "[--b-plein:var(--j-bloc-exercice)] [--b-fond:var(--j-bloc-exercice-fond)]",
      ouverte: "[--b-plein:var(--j-bloc-ouverte)] [--b-fond:var(--j-bloc-ouverte-fond)]",
      piege: "[--b-plein:var(--j-erreur)] [--b-fond:var(--j-erreur-fond)]",
    },
    // bloc corrigé : un filet de l'état sur le bord gauche, par-dessus la teinte du type
    lisere: {
      succes: "shadow-[inset_4px_0_0_0_var(--j-succes)]",
      alerte: "shadow-[inset_4px_0_0_0_var(--j-orange)]",
      aucun: "",
    },
    espace: { normal: "p-5", large: "p-5 md:p-7" },
  },
  defaultVariants: { type: "matiere", lisere: "aucun", espace: "large" },
}))

// Formule d'un contenu : seule sur sa ligne, centrée, sur une bande claire.
export const formuleVariants = fusion(cva("my-1 rounded-2xl bg-card px-4 py-3 text-center font-titre text-bloc font-semibold tracking-wide text-encre [overflow-wrap:anywhere]"))

// Choix en pastille : matière (bandeau des listes, tiroir) ou suggestion à toucher. Actif = accent plein de la matière.
export const choixVariants = fusion(cva("inline-flex shrink-0 items-center justify-center gap-2 rounded-full font-semibold transition-colors", {
  variants: {
    actif: {
      true: "bg-(--m-accent,var(--j-bleu)) text-white",
      false: "bg-(--m-fond,var(--j-bleu-clair)) text-(--m-texte,var(--j-bleu)) hover:brightness-95",
    },
    forme: {
      pastille: "min-h-11 px-4 py-2 text-courant",
      suggestion: "min-h-10 max-w-full shrink px-4 py-2 text-left text-courant whitespace-normal",
      icone: "size-11",
    },
  },
  defaultVariants: { actif: false, forme: "pastille" },
}))

// Point d'état d'une notion (liste des leçons). « a_faire » prend la matière : rien de gris.
export const etatVariants = fusion(cva("inline-block size-2.5 shrink-0 rounded-full", {
  variants: {
    etat: {
      a_faire: "bg-(--m-accent,var(--j-bleu))",
      en_cours: "bg-orange",
      bloque: "bg-erreur",
      compris: "bg-bleu",
      acquis: "bg-succes",
    },
  },
  defaultVariants: { etat: "a_faire" },
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
