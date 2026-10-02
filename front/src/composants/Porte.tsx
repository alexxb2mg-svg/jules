// Porte d'entrée de la nouvelle interface : si le serveur demande un code (accès à distance, ou code élève
// défini), on le demande avant d'afficher quoi que ce soit. Le code n'est jamais gardé côté navigateur : le
// serveur pose un cookie de session signé (httponly), comme pour les anciennes pages (MS.porte).
import { useEffect, useRef, useState } from "react"
import { motion } from "framer-motion"
import { ArrowRight, LockKeyhole } from "lucide-react"
import { session } from "@/api/jules"

export const TEXTES_PORTE = {
  titre: "Bienvenue sur Jules",
  aide: "Tape le code qu'on t'a donné.",
  champ: "Code",
  entrer: "Entrer",
  incorrect: "Code incorrect.",
}

export function Porte({ children }: { children: React.ReactNode }) {
  const [etat, setEtat] = useState<"verif" | "ouvert" | "ferme">("verif")
  const [code, setCode] = useState("")
  const [erreur, setErreur] = useState<string | null>(null)
  const [envoi, setEnvoi] = useState(false)
  const champ = useRef<HTMLInputElement>(null)

  useEffect(() => {
    session.etat().then((s) => setEtat(s.eleve ? "ouvert" : "ferme")).catch(() => setEtat("ferme"))
  }, [])
  useEffect(() => { if (etat === "ferme") champ.current?.focus() }, [etat])

  const entrer = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!code.trim() || envoi) return
    setEnvoi(true); setErreur(null)
    try {
      await session.ouvrir(code.trim())
      const s = await session.etat()
      if (s.eleve) { setEtat("ouvert"); return }
      setErreur(TEXTES_PORTE.incorrect)
    } catch (err) {
      const m = (err as Error).message
      setErreur(m === "Code incorrect" ? TEXTES_PORTE.incorrect : m)
    } finally { setEnvoi(false); setCode("") }
  }

  if (etat === "ouvert") return <>{children}</>
  if (etat === "verif") return <div className="h-full" />
  return (
    <div className="grid h-full place-items-center bg-[radial-gradient(ellipse_at_top,var(--j-bleu-clair),transparent_60%)] p-5">
      <motion.form onSubmit={entrer} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
        className="flex w-full max-w-[400px] flex-col gap-4 rounded-3xl bg-white p-7 shadow-relief-haut">
        <span className="grid size-12 place-items-center rounded-2xl bg-bleu-clair text-bleu"><LockKeyhole size={22} /></span>
        <div>
          <h1 className="m-0 font-titre text-[1.6rem] font-bold text-encre">{TEXTES_PORTE.titre}</h1>
          <p className="mt-1 mb-0 text-gris">{TEXTES_PORTE.aide}</p>
        </div>
        <input ref={champ} type="password" autoComplete="current-password" value={code} onChange={(e) => setCode(e.target.value)}
          aria-label={TEXTES_PORTE.champ} placeholder={TEXTES_PORTE.champ}
          className="h-12 rounded-2xl border-2 border-bord px-4 text-[1.05rem] outline-none focus:border-bleu" />
        {erreur && <p role="alert" className="m-0 text-[0.92rem] text-rouge">{erreur}</p>}
        <motion.button whileTap={{ scale: 0.97 }} disabled={!code.trim() || envoi}
          className="inline-flex h-12 items-center justify-center gap-2 rounded-2xl bg-bleu font-semibold text-white shadow-relief disabled:opacity-40">
          {TEXTES_PORTE.entrer} <ArrowRight size={18} />
        </motion.button>
      </motion.form>
    </div>
  )
}
