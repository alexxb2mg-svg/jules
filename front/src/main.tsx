import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { Porte } from './composants/Porte'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Porte><App /></Porte>
  </StrictMode>,
)
