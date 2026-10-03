// Barre de recherche des notions, en tête de la barre latérale (sous le sélecteur de matière).
// Recherche locale instantanée sur l'index du serveur (GET /api/eleve/notions/index, sans IA) : titre, chapitre,
// matière et mots-clés, sans accents ni casse. Combobox accessible (flèches, Entrée, Échap), raccourci / ou Ctrl+K.
import { createElement, useEffect, useId, useMemo, useRef, useState } from "react"
import { Search, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { useSidebar } from "@/components/ui/sidebar"
import { Pastille } from "@/components/ui/pastille"
import { rechercheNotions, type NotionRecherche } from "@/api/jules"
import { iconeMatiere } from "@/config/matieres"
import { styleMatiere } from "@/modules/fiches/FicheVisuelle"
import type { Route } from "@/routes"
import { chercher, demanderFocus, nomCourt, prendreDemande, routeDe, surDemande, TEXTES_RECHERCHE as T } from "./etat"

export function RechercheNotions({ onAller }: { onAller: (r: Route) => void }) {
  const { setOpen } = useSidebar()
  const [notions, setNotions] = useState<NotionRecherche[] | null>(null)
  const [erreur, setErreur] = useState(false)
  const [requete, setRequete] = useState("")
  const [ouvert, setOuvert] = useState(false)
  const [actif, setActif] = useState(0)
  const champ = useRef<HTMLInputElement>(null)
  const id = useId()
  const idListe = `${id}-liste`
  const idOption = (i: number) => `${id}-option-${i}`

  useEffect(() => { rechercheNotions.index().then(setNotions).catch(() => setErreur(true)) }, [])

  // Focus demandé (raccourci, loupe) : le champ peut encore être caché (barre repliée qui s'ouvre, tiroir qui glisse).
  useEffect(() => {
    let minuterie: number | undefined
    const focaliser = () => {
      prendreDemande()
      let essais = 0
      const essayer = () => {
        const c = champ.current
        if (c && !c.disabled && c.getClientRects().length > 0) { c.focus(); c.select(); return }
        if (essais++ < 25) minuterie = window.setTimeout(essayer, 30)
      }
      essayer()
    }
    if (prendreDemande()) focaliser()
    const retirer = surDemande(focaliser)
    return () => { retirer(); window.clearTimeout(minuterie) }
  }, [])

  const resultats = useMemo(() => (notions ? chercher(notions, requete) : []), [notions, requete])
  const visible = ouvert && requete.trim().length > 0
  const courant = Math.min(actif, Math.max(resultats.length - 1, 0))

  const vider = () => { setRequete(""); setOuvert(false); setActif(0) }
  const ouvrir = (n: NotionRecherche) => { vider(); champ.current?.blur(); onAller(routeDe(n)) }

  const clavier = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault()
      if (!visible) { setOuvert(true); return }
      if (!resultats.length) return
      const pas = e.key === "ArrowDown" ? 1 : -1
      setActif((courant + pas + resultats.length) % resultats.length)
    } else if (e.key === "Enter") {
      if (visible && resultats[courant]) { e.preventDefault(); ouvrir(resultats[courant]) }
    } else if (e.key === "Escape") {
      e.preventDefault()
      if (!requete && !visible) champ.current?.blur()
      vider()
    }
  }

  const indication = erreur ? T.indisponible : T.indication

  return (
    <>
      {/* Barre dépliée (et tiroir du téléphone) : le champ, la liste s'ouvre par-dessus le menu */}
      <div className="relative group-data-[collapsible=icon]:hidden">
        <label className="relative flex items-center">
          <Search size={16} aria-hidden className="pointer-events-none absolute left-3.5 text-gris" />
          <input
            ref={champ} type="text" value={requete} placeholder={indication} autoComplete="off" spellCheck={false}
            role="combobox" aria-label={T.libelle} aria-expanded={visible} aria-controls={idListe} aria-autocomplete="list"
            aria-activedescendant={visible && resultats.length ? idOption(courant) : undefined}
            aria-describedby={erreur ? `${id}-etat` : undefined} aria-keyshortcuts="/ Control+K"
            title={erreur ? T.indisponible : T.raccourci}
            onChange={(e) => { setRequete(e.target.value); setOuvert(true); setActif(0) }}
            onFocus={() => setOuvert(true)} onBlur={() => setOuvert(false)} onKeyDown={clavier}
            className={cn("h-10 w-full rounded-full bg-surface-2 pr-9 pl-10 text-petit text-encre outline-none transition-shadow",
              "placeholder:text-gris focus:ring-2 focus:ring-bleu/40", erreur && "placeholder:italic")}
          />
          {requete && (
            <button type="button" onMouseDown={(e) => e.preventDefault()} onClick={() => { vider(); champ.current?.focus() }}
              aria-label="Effacer la recherche" className="absolute right-2 rounded-full p-1 text-gris hover:bg-survol">
              <X size={14} />
            </button>
          )}
        </label>
        {erreur && <span id={`${id}-etat`} className="sr-only">{T.indisponible}</span>}
        <ul id={idListe} role="listbox" aria-label={T.libelle} hidden={!visible}
          className="absolute top-full right-0 left-0 z-50 mt-1.5 max-h-[60vh] list-none overflow-y-auto rounded-surface bg-popover p-1.5 shadow-souleve">
          {visible && (
            !notions ? (
              <li role="presentation" className="px-3 py-2 text-petit text-gris">{erreur ? T.indisponible : T.chargement}</li>
            ) : resultats.length === 0 ? (
              <li role="presentation" className="px-3 py-2 text-petit text-gris">{T.aucune}</li>
            ) : resultats.map((n, i) => (
              <li key={n.id} id={idOption(i)} role="option" aria-selected={i === courant} style={styleMatiere(n.matiere)}
                onMouseDown={(e) => e.preventDefault()} onClick={() => ouvrir(n)} onMouseMove={() => i !== courant && setActif(i)}
                className={cn("flex cursor-pointer items-start gap-2.5 rounded-2xl px-2.5 py-2 transition-colors",
                  i === courant ? "bg-(--m-fond,var(--j-nav))" : "hover:bg-survol")}>
                <Pastille ton="matiere-accent" taille="puce" className="mt-0.5 size-7 rounded-xl">
                  {createElement(iconeMatiere(n.matiere), { size: 15, "aria-hidden": true })}
                </Pastille>
                <span className="min-w-0 flex-1">
                  <b className="block text-petit leading-snug font-semibold text-encre">{n.titre}</b>
                  <span className="block truncate text-petit text-(--m-texte,var(--j-gris))">
                    {nomCourt(n.nom_matiere)}{n.chapitre ? ` · ${n.chapitre}` : ""}
                  </span>
                  {(n.fiche || n.lecon) && (
                    <span className="mt-1 flex gap-1">
                      {n.lecon && <Pastille ton="matiere" className="px-2 py-px text-[0.75rem]">{T.lecon}</Pastille>}
                      {n.fiche && <Pastille ton="neutre" className="px-2 py-px text-[0.75rem]">{T.fiche}</Pastille>}
                    </span>
                  )}
                </span>
              </li>
            ))
          )}
        </ul>
      </div>
      {/* Barre repliée en icônes (bureau) : une loupe qui déplie la barre et met le focus dans le champ */}
      <button type="button" onClick={() => { setOpen(true); demanderFocus() }} aria-label={T.libelle} title={`${T.libelle} (/)`}
        className="hidden size-11 items-center justify-center self-center rounded-full bg-surface-2 text-encre transition-colors hover:bg-survol group-data-[collapsible=icon]:flex">
        <Search size={17} />
      </button>
    </>
  )
}
