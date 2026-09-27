// Barre latérale : shadcn/ui Sidebar (repliable en icônes, tiroir sur mobile, raccourci Ctrl+B),
// entièrement pilotée par config/navigation.ts.
import {
  Sidebar, SidebarContent, SidebarFooter, SidebarGroup, SidebarGroupContent, SidebarHeader,
  SidebarMenu, SidebarMenuBadge, SidebarMenuButton, SidebarMenuItem, SidebarSeparator, SidebarRail,
} from "@/components/ui/sidebar"
import { NAV, MARQUE, type EntreeNav, type SectionId } from "@/config/navigation"

export function Nav({ actif, onChange, eleve }: {
  actif: SectionId; onChange: (s: SectionId) => void; eleve: { prenom: string; classe: string }
}) {
  const haut = NAV.filter((e) => e.groupe !== "bas")
  const bas = NAV.filter((e) => e.groupe === "bas")

  const entree = ({ id, nom, Icone, bientot }: EntreeNav) => (
    <SidebarMenuItem key={id}>
      <SidebarMenuButton
        size="lg" tooltip={nom} isActive={actif === id} aria-disabled={bientot}
        onClick={() => !bientot && onChange(id)}
        className="h-11 rounded-xl text-[16px] font-medium [&>svg]:size-5 data-[active=true]:bg-bleu data-[active=true]:text-white data-[active=true]:shadow-relief aria-disabled:opacity-55"
      >
        <Icone />
        <span>{nom}</span>
      </SidebarMenuButton>
      {bientot && <SidebarMenuBadge className="rounded-md bg-survol text-[11px] text-gris">bientôt</SidebarMenuBadge>}
    </SidebarMenuItem>
  )

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="px-4 pt-5 pb-3 group-data-[collapsible=icon]:px-2">
        <span className="font-titre text-[26px] leading-none font-bold text-bleu group-data-[collapsible=icon]:text-center group-data-[collapsible=icon]:text-xl">
          <span className="group-data-[collapsible=icon]:hidden">{MARQUE.nom}</span>
          <span className="hidden group-data-[collapsible=icon]:inline">{MARQUE.nom[0]}</span>
          <span className="text-rouge">{MARQUE.point}</span>
        </span>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent><SidebarMenu className="gap-1">{haut.map(entree)}</SidebarMenu></SidebarGroupContent>
        </SidebarGroup>
        {bas.length > 0 && (
          <>
            <SidebarSeparator />
            <SidebarGroup>
              <SidebarGroupContent><SidebarMenu className="gap-1">{bas.map(entree)}</SidebarMenu></SidebarGroupContent>
            </SidebarGroup>
          </>
        )}
      </SidebarContent>

      <SidebarFooter className="p-3">
        <div className="flex items-center gap-3 text-[15px] text-gris group-data-[collapsible=icon]:justify-center">
          <span className="grid size-8 shrink-0 place-items-center rounded-full bg-bleu font-titre font-bold text-white">{eleve.prenom[0]}</span>
          <span className="group-data-[collapsible=icon]:hidden"><b className="block text-encre">{eleve.prenom}</b>{eleve.classe}</span>
        </div>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
