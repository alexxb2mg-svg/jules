// Écran de discussion (#/discuter) — migré fidèlement de eleve.js vers React.
// Sidebar interne (historique), zone de chat avec bulles, saisie avec photos et auto-resize.
// L'envoi n'est PAS streaming : POST → JSON {reponse}. Bulle d'attente pendant le fetch.
import { useCallback, useEffect, useRef, useState } from "react"
import { motion } from "framer-motion"
import { History, Plus, Send, Camera, X } from "lucide-react"
import {
  conversations, infosChat, epreuve as apiEpreuve,
  type Conversation, type ConversationResume, type InfosChat, type MessageJules,
} from "@/api/jules"
import { PriseDePhoto } from "@/composants/PriseDePhoto"
import { buttonVariants } from "@/components/ui/button"
import { AvatarJules } from "@/components/ui/avatar"
import { choixVariants, surfaceVariants, titreVariants } from "@/components/ui/variantes"
import { exemplesMode } from "@/config/modes"
import { useMatiere } from "@/modules/accueil/etat"
import { styleMatiere } from "@/modules/fiches/FicheVisuelle"
import { useMotion } from "@/lib/motion"
import { cn } from "@/lib/utils"
import { Bulle, BulleAttente } from "./Bulle"
import { Accueil } from "./Accueil"

// -- Resize de photo (identique à eleve.js) -----------------------------------

function reduirePhoto(fichier: File): Promise<Blob> {
  return new Promise((resoudre) => {
    const img = new Image()
    img.onload = () => {
      const echelle = Math.min(1, 1600 / Math.max(img.width, img.height))
      const toile = document.createElement("canvas")
      toile.width = Math.round(img.width * echelle)
      toile.height = Math.round(img.height * echelle)
      toile.getContext("2d")!.drawImage(img, 0, 0, toile.width, toile.height)
      toile.toBlob((blob) => resoudre(blob || fichier), "image/jpeg", 0.85)
      URL.revokeObjectURL(img.src)
    }
    img.onerror = () => resoudre(fichier)
    img.src = URL.createObjectURL(fichier)
  })
}

// -- Helpers ------------------------------------------------------------------

const heure = (iso: string) => {
  if (!iso) return ""
  return new Date(iso).toLocaleString("fr-FR", {
    weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
  })
}

const nomMode = (id: string, infos: InfosChat | null) => {
  const mode = (infos?.modes ?? []).find((m) => m.id === id)
  return mode ? mode.nom : id
}

// -- État de la conversation active -------------------------------------------

type ConvActive = { id: string; mode: string; titre?: string } | null
type PhotoApercu = { blob: Blob; url: string }

// -- Composant principal ------------------------------------------------------

export function Chat() {
  const [infos, setInfos] = useState<InfosChat | null>(null)
  const [conv, setConv] = useState<ConvActive>(null)
  const [messages, setMessages] = useState<MessageJules[]>([])
  const [historique, setHistorique] = useState<ConversationResume[]>([])
  const [occupe, setOccupe] = useState(false)
  const [sidebarOuverte, setSidebarOuverte] = useState(false)
  const [photos, setPhotos] = useState<PhotoApercu[]>([])
  const [saisieCache, setSaisieCache] = useState(false)
  const [texte, setTexte] = useState("")

  const { tap } = useMotion()
  const matiere = useMatiere()  // les pastilles de suggestion prennent la matière choisie (bleu de Jules sinon)
  const filRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Charger les infos au montage
  useEffect(() => {
    infosChat().then(setInfos).catch(() => {})
  }, [])

  // Charger l'historique
  const chargerHistorique = useCallback(() => {
    conversations.lister()
      .then((liste) => setHistorique(liste.filter((c) => c.nb > 0)))
      .catch(() => {})
  }, [])

  useEffect(() => { chargerHistorique() }, [chargerHistorique])

  // Scroller en bas à chaque nouveau message
  useEffect(() => {
    requestAnimationFrame(() => {
      if (filRef.current) filRef.current.scrollTop = filRef.current.scrollHeight
    })
  }, [messages, occupe])

  // Auto-resize du textarea
  const ajusterHauteur = useCallback(() => {
    const t = textareaRef.current
    if (!t) return
    t.style.height = "auto"
    t.style.height = `${Math.min(t.scrollHeight, 160)}px`
  }, [])

  useEffect(() => { ajusterHauteur() }, [texte, ajusterHauteur])

  // -- Actions ----------------------------------------------------------------

  const ouvrirConversation = useCallback(async (id: string) => {
    try {
      const c: Conversation = await conversations.lire(id)
      setConv({ id: c.id, mode: c.mode, titre: c.titre })
      setMessages(c.messages)
      setSaisieCache(false)
      // Épreuve finie ?
      const dernier = c.messages[c.messages.length - 1]
      if (dernier && dernier.role !== "eleve" && c.mode === "epreuve" && /preuve terminée/i.test(dernier.texte)) {
        setSaisieCache(true)
      }
      setSidebarOuverte(false)
      textareaRef.current?.focus()
    } catch { /* ignoré */ }
  }, [])

  const demarrer = useCallback(async (mode: string) => {
    try {
      const c = await conversations.creer(mode)
      setConv({ id: c.id, mode: c.mode })
      setMessages([{
        role: "jules",
        texte: `C'est parti, ${infos?.prenom ?? ""} ! Envoie-moi ton message ou une photo de ton exercice.`,
      }])
      setSaisieCache(false)
      setSidebarOuverte(false)
      textareaRef.current?.focus()
    } catch { /* ignoré */ }
  }, [infos])

  const ecranAccueil = useCallback(() => {
    setConv(null)
    setMessages([])
    setPhotos([])
    setSaisieCache(false)
    setTexte("")
  }, [])

  const commencerEpreuve = useCallback(async () => {
    try {
      const r = await apiEpreuve.commencer()
      setConv({ id: r.id, mode: r.mode, titre: r.titre })
      setMessages([{ role: "jules", texte: r.presentation }])
      setSaisieCache(false)
      setSidebarOuverte(false)
      textareaRef.current?.focus()
    } catch { /* ignoré */ }
  }, [])

  const commencerExercice = useCallback(async (notionId: string, generee?: boolean) => {
    try {
      const action = generee ? "generer" : "commencer"
      const r = await fetch(`/api/eleve/exercices/${encodeURIComponent(notionId)}/${action}`, {
        method: "POST", credentials: "same-origin",
      })
      if (!r.ok) return
      const data = await r.json() as { conversation: string }
      await ouvrirConversation(data.conversation)
    } catch { /* ignoré */ }
  }, [ouvrirConversation])

  // -- Envoi de message -------------------------------------------------------

  // `impose` : une suggestion de départ touchée (envoyée telle quelle, sans passer par la saisie).
  const envoyer = useCallback(async (impose?: string) => {
    if (occupe || !conv) return
    const contenu = (impose ?? texte).trim()
    if (!contenu && photos.length === 0) return

    setOccupe(true)
    const photosAEnvoyer = photos.map((p) => p.blob)
    const imagesLocales = photos.map((p) => p.url)

    // Ajouter la bulle élève
    setMessages((m) => [...m, {
      role: "eleve",
      texte: contenu,
      images: imagesLocales,
    }])
    setTexte("")
    setPhotos([])

    try {
      const r = await conversations.envoyer(conv.id, contenu, photosAEnvoyer.length > 0 ? photosAEnvoyer : undefined)
      setMessages((m) => [...m, { role: "jules", texte: r.reponse, horodatage: r.horodatage }])
      // Épreuve finie ?
      if (conv.mode === "epreuve" && /preuve terminée/i.test(r.reponse)) {
        setSaisieCache(true)
      }
      chargerHistorique()
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Erreur inconnue"
      setMessages((m) => [...m, { role: "jules", texte: `Petit souci : ${msg}. Réessaie.` }])
    } finally {
      setOccupe(false)
      textareaRef.current?.focus()
    }
  }, [occupe, conv, texte, photos, chargerHistorique])

  // -- Photos -----------------------------------------------------------------

  const ajouterPhotos = useCallback(async (fichiers: ArrayLike<File>) => {
    const restant = 3 - photos.length
    const aTraiter = Array.from(fichiers).slice(0, restant)
    const nouvelles: PhotoApercu[] = []
    for (const f of aTraiter) {
      const blob = await reduirePhoto(f)
      nouvelles.push({ blob, url: URL.createObjectURL(blob) })
    }
    setPhotos((p) => [...p, ...nouvelles])
  }, [photos.length])

  const retirerPhoto = useCallback((index: number) => {
    setPhotos((p) => {
      const copie = [...p]
      URL.revokeObjectURL(copie[index].url)
      copie.splice(index, 1)
      return copie
    })
  }, [])

  // -- Clavier ----------------------------------------------------------------

  const onKeyDown = useCallback((ev: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (ev.key === "Enter" && !ev.shiftKey && window.matchMedia("(pointer: fine)").matches) {
      ev.preventDefault()
      envoyer()
    }
  }, [envoyer])

  // -- Rendu ------------------------------------------------------------------

  const titre = conv
    ? conv.titre || nomMode(conv.mode, infos)
    : "Nouvelle discussion"

  return (
    <div className="flex h-full" style={matiere ? styleMatiere(matiere) : undefined}>
      {/* Sidebar historique */}
      <aside className={cn("absolute inset-y-0 left-0 z-30 flex w-72 flex-col bg-card transition-transform md:relative md:translate-x-0",
        sidebarOuverte ? "translate-x-0 shadow-souleve md:shadow-none" : "-translate-x-full")}>
        <div className="flex min-h-[68px] items-center justify-between py-3 pr-3 pl-16 md:pl-5">
          <h2 className={titreVariants({ niveau: "etiquette", className: "text-gris" })}>Historique</h2>
          <button onClick={ecranAccueil} title="Nouvelle discussion" aria-label="Nouvelle discussion"
            className={buttonVariants({ variant: "doux", size: "rond" })}>
            <Plus />
          </button>
        </div>
        <div className="flex flex-1 flex-col gap-0.5 overflow-y-auto px-2 pb-3">
          {historique.map((c) => (
            <button key={c.id} onClick={() => ouvrirConversation(c.id)}
              className={cn("block w-full rounded-2xl px-3 py-2.5 text-left text-courant transition-colors hover:bg-survol",
                conv?.id === c.id && "bg-bleu-clair font-semibold")}>
              <span className="line-clamp-1">{c.titre || nomMode(c.mode, infos)}</span>
              <small className="text-petit text-gris">{heure(c.dernier || c.debut)}</small>
            </button>
          ))}
        </div>
      </aside>
      {/* Overlay mobile */}
      {sidebarOuverte && (
        <div className="absolute inset-0 z-20 bg-black/30 md:hidden" onClick={() => setSidebarOuverte(false)} />
      )}

      {/* Zone principale */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* En-tête */}
        {/* Téléphone : rangée des boutons (celui de la barre et la calculatrice flottent en haut), puis le titre en grand. */}
        <header className="flex flex-col px-4 pt-3 pb-2 md:flex-row md:items-center md:gap-3 md:py-4 md:pr-20 md:pl-6">
          <div className="flex h-11 items-center pl-12 md:hidden">
            <button onClick={() => setSidebarOuverte(!sidebarOuverte)} aria-label="Historique des discussions"
              className={buttonVariants({ variant: "ghost", size: "rond" })}>
              <History />
            </button>
          </div>
          <div className="mt-2 flex min-w-0 items-center gap-3 md:mt-0">
            <AvatarJules taille="sm" />
            <h1 className={titreVariants({ niveau: "ecran", className: "truncate" })}>{titre}</h1>
          </div>
        </header>

        {/* Fil de messages ou accueil */}
        <div ref={filRef} className="flex-1 overflow-y-auto">
          {conv === null && infos ? (
            <Accueil infos={infos} onDemarrer={demarrer} onEpreuve={commencerEpreuve} onExercice={commencerExercice} />
          ) : (
            <div className="mx-auto flex max-w-3xl flex-col gap-1.5 px-4 pt-3 pb-6 md:px-6">
              {messages.map((m, i) => {
                const nouveauGroupe = i > 0 && (messages[i - 1].role === "eleve") !== (m.role === "eleve")
                return <div key={i} className={nouveauGroupe ? "mt-4" : undefined}><Bulle message={m} tete={i === 0 || nouveauGroupe} /></div>
              })}
              {occupe && <div className="mt-4"><BulleAttente /></div>}
              {/* Suggestions de départ : tant que seul Jules a parlé, des pastilles à toucher pour lancer l'échange */}
              {conv && !occupe && messages.length === 1 && messages[0].role !== "eleve" && (
                <div className="mt-4 flex flex-wrap gap-2 pl-12.5" aria-label="Idées pour commencer">
                  {exemplesMode(conv.mode).map((e) => (
                    <motion.button key={e} {...tap} onClick={() => void envoyer(e)} className={choixVariants({ forme: "suggestion" })}>{e}</motion.button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Aperçus photos */}
        {photos.length > 0 && (
          <div className="flex gap-2 px-4 pt-2">
            {photos.map((p, i) => (
              <div key={p.url} className="relative">
                <img src={p.url} alt="aperçu" className="size-16 rounded-2xl object-cover" />
                <button onClick={() => retirerPhoto(i)} title="Retirer"
                  className="absolute -top-1.5 -right-1.5 flex size-5 items-center justify-center rounded-full bg-rouge text-white">
                  <X className="size-3" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Saisie */}
        {conv !== null && !saisieCache && (
          <div className="px-3 pt-1 pb-3 md:px-6">
            <div className={surfaceVariants({ ton: "souleve", espace: "aucun",
              className: "mx-auto flex max-w-3xl items-end gap-1 p-1.5 focus-within:ring-2 focus-within:ring-bleu/40" })}>
              <PriseDePhoto accept="image/*" multiple compact onFichiers={(f) => void ajouterPhotos(f)}>
                {(ouvrir) => (
                  <button onClick={ouvrir}
                    className={buttonVariants({ variant: "ghost", size: "rond", className: "text-gris hover:text-bleu" })}
                    title="Ajouter une photo" aria-label="Ajouter une photo">
                    <Camera />
                  </button>
                )}
              </PriseDePhoto>
              <textarea ref={textareaRef} value={texte}
                onChange={(e) => setTexte(e.target.value)}
                onKeyDown={onKeyDown}
                rows={1} placeholder="Écris ton message…"
                className="max-h-40 min-h-11 flex-1 resize-none bg-transparent px-1 py-2.5 text-courant outline-none placeholder:text-gris" />
              <motion.button {...tap} onClick={() => void envoyer()} disabled={occupe || (!texte.trim() && photos.length === 0)}
                className={buttonVariants({ variant: "jules", size: "rond", className: "shadow-none disabled:opacity-40" })}
                aria-label="Envoyer">
                <Send />
              </motion.button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
