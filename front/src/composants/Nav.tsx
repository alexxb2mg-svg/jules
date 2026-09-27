// Barre latérale : shadcn/ui Sidebar (repliable en icônes, tiroir sur mobile, raccourci Ctrl+B),
// entièrement pilotée par config/navigation.ts (rubriques de tests/navigation-reference.json).
import { ExternalLink } from "lucide-react"
import {
  Sidebar, SidebarContent, SidebarFooter, SidebarGroup, SidebarGroupContent, SidebarGroupLabel, SidebarHeader,
  SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarRail,
} from "@/components/ui/sidebar"
import { RUBRIQUES, MARQUE, NAV_ARIA, type EntreeNav, type SectionId } from "@/config/navigation"

export function Nav({ actif, onChange, prenom }: {
  actif: SectionId; onChange: (s: SectionId) => void; prenom: string
}) {
  const entree = ({ id, nom, Icone, pageExistante }: EntreeNav) => (
    <SidebarMenuItem key={id}>
      <SidebarMenuButton
        size="lg" tooltip={nom} isActive={actif === id} asChild={Boolean(pageExistante)}
        onClick={pageExistante ? undefined : () => onChange(id)}
        className="h-11 rounded-xl text-[16px] font-medium transition-all [&>svg]:size-5 data-[active=true]:bg-bleu data-[active=true]:text-white data-[active=true]:shadow-relief"
      >
        {pageExistante ? (
          <a href={pageExistante}><Icone /><span className="flex-1">{nom}</span><ExternalLink className="!size-3.5 opacity-40" /></a>
        ) : (
          <><Icone /><span>{nom}</span></>
        )}
      </SidebarMenuButton>
    </SidebarMenuItem>
  )

  return (
    <Sidebar collapsible="icon" aria-label={NAV_ARIA}>
      <SidebarHeader className="px-4 pt-5 pb-2 group-data-[collapsible=icon]:px-2">
        <span className="font-titre text-[26px] leading-none font-bold text-bleu group-data-[collapsible=icon]:text-center group-data-[collapsible=icon]:text-xl">
          <span className="group-data-[collapsible=icon]:hidden">{MARQUE.nom}</span>
          <span className="hidden group-data-[collapsible=icon]:inline">{MARQUE.nom[0]}</span>
          <span className="text-rouge">{MARQUE.point}</span>
        </span>
      </SidebarHeader>

      <SidebarContent>
        {RUBRIQUES.map((r) => (
          <SidebarGroup key={r.titre} className="py-1">
            <SidebarGroupLabel className="text-[12px] font-semibold tracking-wide text-gris uppercase">{r.titre}</SidebarGroupLabel>
            <SidebarGroupContent><SidebarMenu className="gap-1">{r.entrees.map(entree)}</SidebarMenu></SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>

      <SidebarFooter className="p-3">
        <div className="flex items-center gap-3 text-[15px] text-gris group-data-[collapsible=icon]:justify-center">
          <img src="/api/persona/avatar" alt="" className="size-8 shrink-0 rounded-full bg-bleu-clair object-cover" />
          <span className="group-data-[collapsible=icon]:hidden"><b className="block text-encre">{prenom}</b>avec Jules</span>
        </div>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
