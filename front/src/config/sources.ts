// Sources personnelles : tous les textes et réglages d'affichage (docs/SOURCES-CONTRAT.md §7-§8).
// Les composants n'écrivent aucun libellé métier : ils lisent ce fichier.
import type { LucideIcon } from "lucide-react"
import { Camera, FileText, Type } from "lucide-react"

export type Filtre = "toutes" | "natives" | "perso"

/** Filtre natif / personnel, partagé par la bibliothèque et la barre latérale (mémorisé). */
export const FILTRES: { id: Filtre; nom: string }[] = [
  { id: "toutes", nom: "Toutes" },
  { id: "natives", nom: "Fiches Jules" },
  { id: "perso", nom: "Mes fiches" },
]

export const PASTILLE_PERSO = "perso"

/** Style d'une fiche personnelle : l'accent de Jules (variables --j-perso du thème, index.css). */
export const stylePerso = {
  "--m-fond": "var(--j-perso-clair)",
  "--m-texte": "var(--j-perso)",
  "--m-accent": "var(--j-perso)",
} as React.CSSProperties

export type FormeSource = "photos" | "pdf" | "texte"
export const FORMES: { id: FormeSource; nom: string; aide: string; Icone: LucideIcon }[] = [
  { id: "photos", nom: "Photos", aide: "1 à 5 photos de ton cours, de ton exercice ou de ton chapitre.", Icone: Camera },
  { id: "pdf", nom: "PDF", aide: "Un PDF de 20 pages au plus (10 Mo).", Icone: FileText },
  { id: "texte", nom: "Texte", aide: "Colle le texte de ton cours.", Icone: Type },
]
export const LIMITES = { photos: 5, photoMo: 8, pdfMo: 10, texte: 30000, texteMin: 120 }

export const TEXTES = {
  ajouter: "Ajouter mon cours",
  titreAjout: "Ajouter mon cours",
  sousTitreAjout: "Jules en fait une fiche, au même format que ses fiches. Elle rejoint ta bibliothèque si tu la gardes.",
  carteNatif: { titre: "Mes cours Jules", texte: "Les fiches de Jules, rangées par matière et chapitre." },
  carteDocument: { titre: "Mon document", texte: "Une photo, un PDF ou un texte : Jules en fait ta fiche." },
  matiere: "Matière (si tu la connais)",
  matiereInconnue: "Je ne sais pas",
  generer: "Faire ma fiche",
  quota: (reste: number, total: number) => `${reste} fiche${reste > 1 ? "s" : ""} possible${reste > 1 ? "s" : ""} aujourd'hui sur ${total}.`,
  placeholderTexte: "Colle ici le texte de ton cours…",
  deposerPhotos: "Choisis ou dépose tes photos",
  deposerPdf: "Choisis ou dépose ton PDF",
  retirer: "Retirer",
  recommencer: "Recommencer",
  // question de rangement (contrat §7)
  questionGarder: "On garde cette fiche ?",
  expliqueGarder: "Si tu la gardes, elle rejoint ta bibliothèque.",
  garderNotion: (titre: string) => `Oui, dans « ${titre} »`,
  garderDossier: "Oui, dans un dossier…",
  garderNonClasse: "Oui, dans Non classé",
  pasGarder: "Non, ne pas garder",
  nouveauDossier: "Nouveau dossier",
  nomDossier: "Nom du dossier",
  creer: "Créer",
  annuler: "Rester sur la fiche",
  aucuneNotion: "Jules n'a trouvé aucune notion du programme pour ce document.",
  // bibliothèque et barre latérale
  mesDossiers: "Mes dossiers",
  nonClasse: "Non classé",
  aRanger: "À ranger",
  recentes: "Ouvertes récemment",
  mesFichesSurNotion: "Mes fiches sur cette notion",
  aucunePerso: "Tu n'as pas encore de fiche perso. Ajoute ton cours : Jules en fait une fiche.",
  videDossier: "Ce dossier est vide.",
  supprimerDossier: "Supprimer le dossier",
  confirmerSupprimerDossier: "Supprimer ce dossier ? Ses fiches restent dans leur notion, ou dans Non classé.",
  // fiche personnelle
  enteteFichePerso: "Ma fiche perso",
  refaire: "Refaire la fiche",
  supprimer: "Supprimer",
  confirmerSupprimer: "Supprimer cette fiche et ton document ? C'est définitif.",
  voirDocument: "Voir mon document",
  mentionSource: (titre: string) => `Source : ${titre} — fiche personnelle, visible seulement par toi et ton parent.`,
  accueilJulesPerso: "J'ai fait cette fiche à partir de ton document. Clique sur un bloc : je t'explique ce qu'il faut en retenir.",
  aRangerAuDemarrage: (n: number) => (n > 1 ? `${n} fiches t'attendent : on les garde ?` : "Une fiche t'attend : on la garde ?"),
  voir: "Voir",
}

/** Étapes réelles de la génération, dans l'ordre où le serveur les envoie (jules/sources.py `parcours`). */
export const ETAPES: { id: "lecture" | "notion" | "ecriture" | "verification"; nom: string }[] = [
  { id: "lecture", nom: "Je lis ton document" },
  { id: "notion", nom: "Je cherche la notion du programme" },
  { id: "ecriture", nom: "J'écris ta fiche" },
  { id: "verification", nom: "Je vérifie la fiche" },
]
