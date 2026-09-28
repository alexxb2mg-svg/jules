// Écran de discussion (#/discuter) — migré fidèlement de eleve.js vers React.
// Sidebar interne (historique), zone de chat avec bulles, saisie avec photos et auto-resize.
// L'envoi n'est PAS streaming : POST → JSON {reponse}. Bulle d'attente pendant le fetch.
import { useCallback, useEffect, useRef, useState } from "react"
import { Menu, Plus, Send, Camera, X } from "lucide-react"
import {
  conversations, infosChat, epreuve as apiEpreuve,
  type Conversation, type ConversationResume, type InfosChat, type MessageJules,
} from "@/api/jules"
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
  return mode ? `${mode.icone} ${mode.nom}` : id
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

  const filRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fichierRef = useRef<HTMLInputElement>(null)

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
    if (filRef.current) filRef.current.scrollTop = filRef.current.scrollHeight
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

  const envoyer = useCallback(async () => {
    if (occupe || !conv) return
    const contenu = texte.trim()
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

  const ajouterPhotos = useCallback(async (fichiers: FileList) => {
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
    <div className="flex h-full">
      {/* Sidebar historique */}
      <aside className={`
        absolute inset-y-0 left-0 z-30 flex w-72 flex-col border-r border-bord bg-nav transition-transform
        md:relative md:translate-x-0
        ${sidebarOuverte ? "translate-x-0" : "-translate-x-full"}
      `}>
        <div className="flex items-center justify-between border-b border-bord px-4 py-3">
          <h2 className="text-sm font-semibold">Historique</h2>
          <button onClick={ecranAccueil} title="Nouvelle discussion"
            className="rounded-lg p-1.5 transition hover:bg-bleu-clair/40">
            <Plus className="size-4" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto">
          {historique.map((c) => (
            <button key={c.id} onClick={() => ouvrirConversation(c.id)}
              className={`block w-full px-4 py-2.5 text-left text-[13px] transition hover:bg-bleu-clair/30 ${
                conv?.id === c.id ? "bg-bleu-clair/40 font-medium" : ""
              }`}>
              <span className="line-clamp-1">{c.titre || nomMode(c.mode, infos)}</span>
              <small className="text-[11px] text-gris">{heure(c.dernier || c.debut)}</small>
            </button>
          ))}
        </div>
      </aside>
      {/* Overlay mobile */}
      {sidebarOuverte && (
        <div className="absolute inset-0 z-20 bg-black/20 md:hidden" onClick={() => setSidebarOuverte(false)} />
      )}

      {/* Zone principale */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* En-tête */}
        <header className="flex items-center gap-3 border-b border-bord px-4 py-3">
          <button onClick={() => setSidebarOuverte(!sidebarOuverte)}
            className="rounded-lg p-1.5 transition hover:bg-bleu-clair/40 md:hidden">
            <Menu className="size-5" />
          </button>
          <h1 className="flex-1 truncate text-[15px] font-semibold">{titre}</h1>
        </header>

        {/* Fil de messages ou accueil */}
        <div ref={filRef} className="flex-1 overflow-y-auto">
          {conv === null && infos ? (
            <Accueil infos={infos} onDemarrer={demarrer} onEpreuve={commencerEpreuve} onExercice={commencerExercice} />
          ) : (
            <div className="flex flex-col gap-3 px-4 py-4">
              {messages.map((m, i) => <Bulle key={i} message={m} />)}
              {occupe && <BulleAttente />}
            </div>
          )}
        </div>

        {/* Aperçus photos */}
        {photos.length > 0 && (
          <div className="flex gap-2 border-t border-bord px-4 py-2">
            {photos.map((p, i) => (
              <div key={p.url} className="relative">
                <img src={p.url} alt="aperçu" className="size-16 rounded-lg object-cover" />
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
          <div className="border-t border-bord px-3 py-2">
            <div className="flex items-end gap-2 rounded-2xl border-2 border-bord bg-white p-2 focus-within:border-bleu">
              <button onClick={() => fichierRef.current?.click()}
                className="shrink-0 rounded-xl p-2 text-gris transition hover:bg-bleu-clair/40 hover:text-bleu"
                title="Ajouter une photo">
                <Camera className="size-5" />
              </button>
              <textarea ref={textareaRef} value={texte}
                onChange={(e) => setTexte(e.target.value)}
                onKeyDown={onKeyDown}
                rows={1} placeholder="Écris ton message…"
                className="max-h-40 flex-1 resize-none bg-transparent px-1 py-1.5 text-[16px] outline-none placeholder:text-gris" />
              <button onClick={envoyer} disabled={occupe || (!texte.trim() && photos.length === 0)}
                className="grid size-9 shrink-0 place-items-center rounded-xl bg-bleu text-white transition-opacity disabled:opacity-40"
                aria-label="Envoyer">
                <Send className="size-4" />
              </button>
            </div>
            <input ref={fichierRef} type="file" accept="image/*" multiple className="hidden"
              onChange={async (e) => {
                if (e.target.files) await ajouterPhotos(e.target.files)
                e.target.value = ""
              }} />
          </div>
        )}
      </div>
    </div>
  )
}
