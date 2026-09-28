// Porte d'entrée de l'espace parent : formulaire de code (POST /api/session).
// Reproduit MS.porte de commun.js en React.
import { useState } from "react"
import { Lock, ArrowRight, AlertCircle } from "lucide-react"
import { sessionParent } from "./api"

export function Porte({ onAcces }: { onAcces: () => void }) {
  const [code, setCode] = useState("")
  const [erreur, setErreur] = useState<string | null>(null)
  const [envoi, setEnvoi] = useState(false)

  const soumettre = async (ev: React.FormEvent) => {
    ev.preventDefault()
    if (!code.trim() || envoi) return
    setErreur(null)
    setEnvoi(true)
    try {
      await sessionParent.ouvrir(code)
      const etat = await sessionParent.etat()
      if (!etat.parent) { setErreur("Ce code n'ouvre pas cette page."); setEnvoi(false); return }
      onAcces()
    } catch (err) {
      setErreur(err instanceof Error && err.message === "code requis" ? "Code incorrect" : (err instanceof Error ? err.message : "Erreur"))
      setEnvoi(false)
    }
  }

  return (
    <div className="flex h-full items-center justify-center">
      <div className="mx-auto w-full max-w-sm rounded-2xl border border-bord bg-white p-8 shadow-relief text-center">
        <div className="mx-auto mb-4 flex size-14 items-center justify-center rounded-full bg-bleu/10">
          <Lock className="size-7 text-bleu" />
        </div>
        <h1 className="mb-1 text-xl font-bold text-encre">Espace parent</h1>
        <p className="mb-6 text-sm text-gris">Entrez le code parent pour accéder à cet espace.</p>
        <form onSubmit={soumettre} className="flex flex-col gap-3">
          <input type="password" autoComplete="current-password" aria-label="Code parent"
            value={code} onChange={(e) => setCode(e.target.value)} autoFocus
            className="rounded-xl border border-bord px-4 py-2.5 text-center text-lg tracking-widest focus:border-bleu focus:ring-1 focus:ring-bleu focus:outline-none" />
          <button type="submit" disabled={envoi || !code.trim()}
            className="flex items-center justify-center gap-2 rounded-xl bg-bleu px-4 py-2.5 font-medium text-white transition hover:bg-bleu/90 disabled:opacity-50">
            <span>Entrer</span><ArrowRight className="size-4" />
          </button>
        </form>
        {erreur && (
          <div className="mt-4 flex items-center gap-2 rounded-xl bg-rouge/10 px-4 py-2 text-sm text-rouge">
            <AlertCircle className="size-4 shrink-0" />{erreur}
          </div>
        )}
      </div>
    </div>
  )
}
