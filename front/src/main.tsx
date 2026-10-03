import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { Porte } from './composants/Porte'
import { appliquerTheme } from './lib/theme'

appliquerTheme()  // avant le premier rendu : pas d'éclair blanc en thème sombre

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Porte><App /></Porte>
  </StrictMode>,
)
