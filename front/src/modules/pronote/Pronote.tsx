// Écran Pronote — flux RSS maison : EDT, devoirs, contenu de cours, notes.
// Aucune donnée personnelle dans ce fichier (publiable sur GitHub).
import { useEffect, useState } from "react"
import { BookOpen, Calendar, CheckCircle2, Clock, GraduationCap, AlertCircle, RefreshCw, Circle } from "lucide-react"
import { feed as fetchFeed, type Feed, type Lesson, type Homework, type Grade } from "./api"

// -- helpers ----------------------------------------------------------------

const jour = (iso: string | null) => {
  if (!iso) return ""
  const d = new Date(iso)
  return d.toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" })
}
const heure = (iso: string | null) => {
  if (!iso) return ""
  return new Date(iso).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })
}

/** Regroupe les cours par jour. */
function parJour(lessons: Lesson[]): Map<string, Lesson[]> {
  const m = new Map<string, Lesson[]>()
  for (const l of lessons) {
    const k = l.start ? l.start.slice(0, 10) : "?"
    if (!m.has(k)) m.set(k, [])
    m.get(k)!.push(l)
  }
  // Trier chaque journée par heure de début
  for (const [, cours] of m) cours.sort((a, b) => (a.start || "").localeCompare(b.start || ""))
  return m
}

// -- sous-composants --------------------------------------------------------

function CarteEdt({ lessons }: { lessons: Lesson[] }) {
  const jours = parJour(lessons)
  if (jours.size === 0) return <p className="text-gris italic">Aucun cours cette semaine.</p>
  return (
    <div className="flex flex-col gap-4">
      {[...jours.entries()].map(([date, cours]) => (
        <div key={date}>
          <h3 className="mb-2 text-sm font-semibold capitalize text-bleu">{jour(cours[0].start)}</h3>
          <div className="flex flex-col gap-1.5">
            {cours.map((c, i) => (
              <div key={i} className={`flex items-center gap-3 rounded-xl px-3 py-2 text-sm ${c.canceled ? "bg-rouge/10 line-through opacity-60" : "bg-bleu-clair/40"}`}>
                <Clock className="size-4 shrink-0 text-bleu" />
                <span className="w-24 shrink-0 font-mono text-xs text-gris">{heure(c.start)} – {heure(c.end)}</span>
                <span className="font-medium">{c.subject || "—"}</span>
                {c.room && <span className="text-gris">({c.room})</span>}
                {c.teacher && <span className="hidden text-gris sm:inline">· {c.teacher}</span>}
                {c.canceled && <span className="ml-auto text-xs font-semibold text-rouge">Annulé</span>}
                {c.status && !c.canceled && <span className="ml-auto text-xs text-gris">{c.status}</span>}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

function CarteDevoirs({ devoirs }: { devoirs: Homework[] }) {
  if (devoirs.length === 0) return <p className="text-gris italic">Rien à faire pour le moment 🎉</p>
  return (
    <div className="flex flex-col gap-2">
      {devoirs.map((d, i) => (
        <div key={i} className={`flex items-start gap-3 rounded-xl px-3 py-2 text-sm ${d.done ? "bg-vert/10 opacity-60" : "bg-orange-50"}`}>
          {d.done ? <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-vert" /> : <Circle className="mt-0.5 size-4 shrink-0 text-orange-400" />}
          <div className="min-w-0 flex-1">
            <div className="flex items-baseline gap-2">
              <span className="font-medium">{d.subject || "—"}</span>
              {d.date && <span className="text-xs text-gris">pour le {jour(d.date)}</span>}
            </div>
            {d.description && <p className="mt-0.5 text-xs text-gris-fonce whitespace-pre-line">{d.description}</p>}
          </div>
        </div>
      ))}
    </div>
  )
}

function CarteNotes({ notes }: { notes: Grade[] }) {
  if (notes.length === 0) return <p className="text-gris italic">Aucune note pour cette période.</p>
  return (
    <div className="flex flex-col gap-1.5">
      {notes.map((n, i) => (
        <div key={i} className="flex items-center gap-3 rounded-xl bg-violet/5 px-3 py-2 text-sm">
          <GraduationCap className="size-4 shrink-0 text-violet" />
          <span className="font-medium">{n.subject || "—"}</span>
          <span className="ml-auto font-mono font-semibold">{n.grade}<span className="text-gris">/{n.out_of}</span></span>
          {n.average && <span className="text-xs text-gris">(moy. {n.average})</span>}
          {n.date && <span className="hidden text-xs text-gris sm:inline">· {jour(n.date)}</span>}
        </div>
      ))}
    </div>
  )
}

// -- écran principal --------------------------------------------------------

export function Pronote() {
  const [data, setData] = useState<Feed | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const charger = () => {
    setLoading(true)
    setErr(null)
    fetchFeed(1)
      .then(setData)
      .catch((e) => setErr(e.message || "Erreur de connexion"))
      .finally(() => setLoading(false))
  }

  useEffect(charger, [])

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
        {/* En-tête */}
        <div className="mb-6 flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-xl bg-bleu text-white">
            <BookOpen className="size-5" />
          </div>
          <div className="flex-1">
            <h1 className="text-xl font-bold text-bleu">Pronote</h1>
            {data?.info.name && <p className="text-sm text-gris">{data.info.name}{data.info.class ? ` · ${data.info.class}` : ""}</p>}
          </div>
          <button onClick={charger} disabled={loading}
            className="flex items-center gap-1.5 rounded-lg bg-bleu-clair px-3 py-1.5 text-sm font-medium text-bleu transition hover:bg-bleu/10 disabled:opacity-50">
            <RefreshCw className={`size-4 ${loading ? "animate-spin" : ""}`} />
            Actualiser
          </button>
        </div>

        {err && (
          <div className="mb-4 flex items-center gap-2 rounded-xl bg-rouge/10 px-4 py-3 text-sm text-rouge">
            <AlertCircle className="size-4 shrink-0" />
            {err}
          </div>
        )}

        {loading && !data && (
          <div className="flex items-center justify-center py-20">
            <RefreshCw className="size-6 animate-spin text-bleu" />
            <span className="ml-2 text-gris">Connexion à Pronote…</span>
          </div>
        )}

        {data && (
          <div className="flex flex-col gap-6">
            {/* EDT */}
            <section className="rounded-2xl border border-bord bg-white p-5 shadow-relief">
              <div className="mb-3 flex items-center gap-2">
                <Calendar className="size-5 text-bleu" />
                <h2 className="text-base font-semibold">Emploi du temps</h2>
              </div>
              <CarteEdt lessons={data.timetable} />
            </section>

            {/* Devoirs */}
            <section className="rounded-2xl border border-bord bg-white p-5 shadow-relief">
              <div className="mb-3 flex items-center gap-2">
                <BookOpen className="size-5 text-orange-500" />
                <h2 className="text-base font-semibold">Travail à faire</h2>
              </div>
              <CarteDevoirs devoirs={data.homework} />
            </section>

            {/* Notes */}
            <section className="rounded-2xl border border-bord bg-white p-5 shadow-relief">
              <div className="mb-3 flex items-center gap-2">
                <GraduationCap className="size-5 text-violet" />
                <h2 className="text-base font-semibold">Notes</h2>
              </div>
              <CarteNotes notes={data.grades} />
            </section>
          </div>
        )}
      </div>
    </div>
  )
}
