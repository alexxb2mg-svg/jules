// Clair / sombre : suit le réglage du téléphone (prefers-color-scheme) tant que l'élève n'a rien choisi ;
// le bouton du tiroir force un thème et le mémorise (localStorage). Le thème = la classe .dark sur <html>.
import { useEffect, useState } from "react"

export type Theme = "clair" | "sombre"
const CLE = "jules-theme"
const SOMBRE = "(prefers-color-scheme: dark)"

const systeme = (): Theme => (window.matchMedia(SOMBRE).matches ? "sombre" : "clair")
function memorise(): Theme | null {
  try { const v = localStorage.getItem(CLE); return v === "clair" || v === "sombre" ? v : null } catch { return null }
}

export function appliquerTheme(theme: Theme = memorise() ?? systeme()) {
  document.documentElement.classList.toggle("dark", theme === "sombre")
}

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => memorise() ?? systeme())
  useEffect(() => { appliquerTheme(theme) }, [theme])
  useEffect(() => {
    const mq = window.matchMedia(SOMBRE)
    const suivre = () => { if (!memorise()) setTheme(systeme()) }
    mq.addEventListener("change", suivre)
    return () => mq.removeEventListener("change", suivre)
  }, [])
  const basculer = () => {
    const suivant: Theme = theme === "sombre" ? "clair" : "sombre"
    try { localStorage.setItem(CLE, suivant) } catch { /* navigation privée : le choix vaut pour la session */ }
    setTheme(suivant)
  }
  return { theme, basculer }
}
