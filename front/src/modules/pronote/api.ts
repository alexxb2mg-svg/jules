// API Pronote — appels vers /api/pronote/*
// Aucune donnée personnelle dans ce fichier (publiable sur GitHub).

export type PronoteInfo = {
  connected: boolean
  name?: string | null
  school?: string | null
  class?: string | null
  error?: string
}

export type Lesson = {
  id: string | null
  subject: string | null
  teacher: string | null
  room: string | null
  start: string | null
  end: string | null
  canceled: boolean
  status: string | null
  memo: string | null
}

export type Homework = {
  id: string | null
  subject: string | null
  description: string | null
  done: boolean
  date: string | null
}

export type Grade = {
  subject: string | null
  grade: string | null
  out_of: string | null
  average: string | null
  date: string | null
  comment: string | null
}

export type Feed = {
  date: string
  timetable: Lesson[]
  homework: Homework[]
  grades: Grade[]
  info: PronoteInfo
}

const BASE = "/api/pronote"

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`, { credentials: "include" })
  if (!r.ok) throw new Error(`Pronote API ${r.status}`)
  return r.json()
}

export const status = () => get<PronoteInfo>("/status")
export const timetable = (date?: string, weeks = 1) =>
  get<Lesson[]>(`/timetable?weeks=${weeks}${date ? `&date=${date}` : ""}`)
export const homework = (dateFrom?: string) =>
  get<Homework[]>(`/homework${dateFrom ? `?date_from=${dateFrom}` : ""}`)
export const grades = (period?: string) =>
  get<Grade[]>(`/grades${period ? `?period=${encodeURIComponent(period)}` : ""}`)
export const feed = (weeks = 1) => get<Feed>(`/feed?weeks=${weeks}`)
