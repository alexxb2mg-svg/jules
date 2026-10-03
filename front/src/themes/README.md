# Thèmes de Jules

Un thème = un fichier CSS qui définit **toutes** les variables `--j-*` (clair dans `:root`, sombre dans `:root.dark`).
`index.css` en importe un seul (`@import "./themes/cahier.css";`) et branche ces variables sur les tokens Tailwind/shadcn (`@theme inline`).
Changer de thème = changer cette ligne d'import ; `base.css` garde le jeu d'avant le relifting (clair seulement).
Un nouveau thème copie `cahier.css` et en change les valeurs, jamais les noms (les écrans n'emploient que les tokens).
`white` (Tailwind) vaut `--j-sur-plein` : le texte posé sur un aplat coloré, blanc en clair, encre sombre en sombre.
