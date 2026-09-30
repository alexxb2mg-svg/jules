// Barre latérale : shadcn/ui Sidebar (repliable en icônes, tiroir sur mobile, raccourci Ctrl+B),
// entièrement pilotée par config/navigation.ts (rubriques de tests/navigation-reference.json).
// Sous « Mes fiches » : filtre natif/perso, fiches ouvertes récemment (couleur perso pour les fiches perso),
// dossiers et « Ajouter mon cours » (docs/SOURCES-CONTRAT.md §8). Les rubriques de référence ne changent pas.
import { ExternalLink, Folder, Inbox, Moon, Plus, Sparkles, Sun } from "lucide-react"
import {
  Sidebar, SidebarContent, SidebarFooter, SidebarGroup, SidebarGroupContent, SidebarGroupLabel, SidebarHeader,
  SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarMenuSub, SidebarMenuSubButton, SidebarMenuSubItem, SidebarRail, useSidebar,
} from "@/components/ui/sidebar"
import { cn } from "@/lib/utils"
import { useTheme } from "@/lib/theme"
import { AvatarJules } from "@/components/ui/avatar"
import { buttonVariants } from "@/components/ui/button"
import { RUBRIQUES, MARQUE, NAV_ARIA, type EntreeNav, type SectionId } from "@/config/navigation"
import { iconeMatiere } from "@/config/matieres"
import { TEXTES } from "@/config/sources"
import { NON_CLASSE, useBibliothequePerso, useFiltre, useRecentes } from "@/modules/sources/etat"
import { FiltreFiches, voitNatives, voitPerso } from "@/modules/sources/pieces"
import { estNouveau, LIBELLE_NOUVEAU } from "@/config/veille"
import { SelecteurMatiere } from "@/modules/accueil/SelecteurMatiere"
import type { Route } from "@/routes"

export function Nav({ admin = true, actif, onChange, onMatiere, prenom, route, aller }: {
  /** Faux à distance : l'espace parent (administration) n'y est pas proposé. */
  admin?: boolean
  actif: SectionId; onChange: (s: SectionId) => void; onMatiere: (m: string | null) => void; prenom: string; route: Route; aller: (r: Route) => void
}) {
  // Sur téléphone la barre est un tiroir : tout choix le referme après la navigation (sur bureau, rien ne change).
  const { isMobile, setOpenMobile } = useSidebar()
  const fermer = () => { if (isMobile) setOpenMobile(false) }
  const { theme, basculer } = useTheme()
  const entree = ({ id, nom, Icone, pageExistante }: EntreeNav) => (
    <SidebarMenuItem key={id}>
      <SidebarMenuButton
        size="lg" tooltip={nom} isActive={actif === id} asChild={Boolean(pageExistante)}
        onClick={pageExistante ? undefined : () => { onChange(id); fermer() }}
        className="h-12 rounded-full px-4 text-courant font-medium transition-all group-data-[collapsible=icon]:!rounded-xl [&>svg]:size-5 data-[active=true]:bg-bleu data-[active=true]:font-semibold data-[active=true]:text-white"
      >
        {pageExistante ? (
          <a href={pageExistante} onClick={fermer}><Icone /><span className="flex-1">{nom}</span><ExternalLink className="!size-3.5 opacity-40" /></a>
        ) : (
          <><Icone /><span>{nom}</span></>
        )}
      </SidebarMenuButton>
      {id === "fiches" && actif === "fiches" && <SousFiches route={route} aller={(r) => { aller(r); fermer() }} />}
    </SidebarMenuItem>
  )

  return (
    <Sidebar collapsible="icon" aria-label={NAV_ARIA}>
      <SidebarHeader className="px-4 pt-5 pb-2 group-data-[collapsible=icon]:px-2">
        <span className="font-titre text-ecran leading-none font-extrabold text-bleu group-data-[collapsible=icon]:text-center group-data-[collapsible=icon]:text-xl">
          <span className="group-data-[collapsible=icon]:hidden">{MARQUE.nom}</span>
          <span className="hidden group-data-[collapsible=icon]:inline">{MARQUE.nom[0]}</span>
          <span className="text-rouge">{MARQUE.point}</span>
        </span>
        <div className="mt-3"><SelecteurMatiere onChoix={(m) => { onMatiere(m); fermer() }} /></div>
      </SidebarHeader>

      <SidebarContent>
        {RUBRIQUES.map((r) => ({ ...r, entrees: r.entrees.filter((e) => admin || e.id !== "parent") })).filter((r) => r.entrees.length > 0).map((r) => (
          <SidebarGroup key={r.titre} className="py-1">
            <SidebarGroupLabel className="px-4 text-petit font-semibold tracking-wide text-gris uppercase">{r.titre}</SidebarGroupLabel>
            <SidebarGroupContent><SidebarMenu className="gap-1">{r.entrees.map(entree)}</SidebarMenu></SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>

      <SidebarFooter className="p-3">
        <div className="flex items-center gap-3 rounded-surface bg-surface-2 p-2 text-courant text-gris group-data-[collapsible=icon]:flex-col group-data-[collapsible=icon]:bg-transparent group-data-[collapsible=icon]:p-0">
          <AvatarJules taille="md" />
          <span className="min-w-0 flex-1 leading-tight group-data-[collapsible=icon]:hidden"><b className="block truncate text-encre">{prenom}</b>avec Jules</span>
          <button type="button" onClick={basculer} aria-pressed={theme === "sombre"}
            aria-label={theme === "sombre" ? "Passer en thème clair" : "Passer en thème sombre"} title={theme === "sombre" ? "Thème clair" : "Thème sombre"}
            className={buttonVariants({ variant: "sombre", size: "rond", className: "text-encre" })}>
            {theme === "sombre" ? <Sun /> : <Moon />}
          </button>
        </div>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}

/** Sous « Mes fiches » : filtre, récentes (perso en violet), dossiers, ajouter. Caché quand la barre est repliée. */
function SousFiches({ route, aller }: { route: Route; aller: (r: Route) => void }) {
  const [filtre] = useFiltre()
  const recentes = useRecentes().filter((r) => (r.genre === "perso" ? voitPerso(filtre) : voitNatives(filtre)))
  const biblio = useBibliothequePerso()
  const nonClasses = (biblio?.fiches ?? []).some((f) => f.etat === "rangee" && !f.notion && !f.dossier)
  const aRanger = (biblio?.fiches ?? []).filter((f) => f.etat === "a_ranger").length
  const lien = "h-9 gap-2 rounded-full text-petit whitespace-nowrap"
  return (
    <div className="mt-2 flex flex-col gap-1.5 group-data-[collapsible=icon]:hidden">
      <div className="pr-1 pl-3"><FiltreFiches compact /></div>
      {recentes.length > 0 && (
        <SidebarMenuSub aria-label={TEXTES.recentes}>
          {recentes.slice(0, 5).map((r) => {
            const perso = r.genre === "perso"
            const on = perso ? route.ecran === "perso" && route.id === r.id : route.ecran === "fiche" && route.notion === r.id
            const Icone = perso ? Sparkles : iconeMatiere(r.matiere)
            return (
              <SidebarMenuSubItem key={`${r.genre}-${r.id}`}>
                <SidebarMenuSubButton isActive={on} onClick={() => aller(perso ? { ecran: "perso", id: r.id } : { ecran: "fiche", notion: r.id })}
                  className={cn(lien, "cursor-pointer", perso && "text-perso data-[active=true]:bg-perso-clair data-[active=true]:text-perso [&>svg]:text-perso")}>
                  <Icone /><span className="truncate">{r.titre}</span>
                  {perso && <span aria-hidden className="ml-auto size-2 shrink-0 rounded-full bg-perso" />}
                </SidebarMenuSubButton>
              </SidebarMenuSubItem>
            )
          })}
        </SidebarMenuSub>
      )}
      {voitPerso(filtre) && (
        <SidebarMenuSub aria-label={TEXTES.mesDossiers}>
          {(biblio?.dossiers ?? []).map((d) => (
            <SidebarMenuSubItem key={d.id}>
              <SidebarMenuSubButton isActive={route.ecran === "dossier" && route.id === d.id} onClick={() => aller({ ecran: "dossier", id: d.id })}
                className={cn(lien, "cursor-pointer text-perso [&>svg]:text-perso data-[active=true]:bg-perso-clair")}>
                <Folder /><span className="truncate">{d.nom}</span>
              </SidebarMenuSubButton>
            </SidebarMenuSubItem>
          ))}
          {nonClasses && (
            <SidebarMenuSubItem>
              <SidebarMenuSubButton isActive={route.ecran === "dossier" && route.id === NON_CLASSE} onClick={() => aller({ ecran: "dossier", id: NON_CLASSE })}
                className={cn(lien, "cursor-pointer text-perso [&>svg]:text-perso data-[active=true]:bg-perso-clair")}>
                <Inbox /><span>{TEXTES.nonClasse}</span>
              </SidebarMenuSubButton>
            </SidebarMenuSubItem>
          )}
          <SidebarMenuSubItem>
            <SidebarMenuSubButton isActive={route.ecran === "ajouter"} onClick={() => aller({ ecran: "ajouter" })}
              className={cn(lien, "cursor-pointer font-semibold text-perso [&>svg]:text-perso data-[active=true]:bg-perso-clair")}>
              <Plus /><span>{TEXTES.ajouter}</span>
              {estNouveau("fiches:ajouter") && aRanger === 0 && <span title={LIBELLE_NOUVEAU} aria-label={LIBELLE_NOUVEAU} className="ml-auto size-2 shrink-0 rounded-full bg-perso ring-2 ring-perso-clair" />}
              {aRanger > 0 && <span className="ml-auto rounded-full bg-perso px-2 text-petit font-bold text-white" title={TEXTES.aRanger}>{aRanger}</span>}
            </SidebarMenuSubButton>
          </SidebarMenuSubItem>
        </SidebarMenuSub>
      )}
    </div>
  )
}
