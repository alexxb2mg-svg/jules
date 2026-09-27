export type CarteFlash = {
  id: string
  recto: string
  verso: string
  indice?: string
}

export type PaquetFlash = {
  id: string
  titre: string
  matiere?: string
  cartes: CarteFlash[]
}

/** Résumé d'une session, transmis à `onFin`. */
export type BilanFlash = {
  total: number
  su: number
  aRevoir: number
}
