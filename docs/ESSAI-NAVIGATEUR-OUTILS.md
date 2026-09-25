# Essai réel d'isolement dans le navigateur — étape 3 (outils)

Fait le 24/09/2026, session navigateur `jules-s2`, serveur jetable sur le port 8798 (hors dépôt,
dans le dossier scratch de travail), avec les 3 outils de référence chargés dans des
`<iframe sandbox="allow-scripts">` (sans `allow-same-origin`), servis par
`/api/eleve/outils/<id>/`.

## Ce qui a été vérifié réellement (pas en théorie)

1. **Les 3 outils s'affichent et fonctionnent dans leur iframe** : frise (reçoit sa liste
   d'événements par `postMessage` et les affiche dans l'ordre), calculatrice (pavé numérique,
   calcule), lexique (reçoit ses termes, la recherche filtre, un clic sur un terme envoie
   `terme_consulte`).

2. **Le parent ne peut pas lire le contenu de l'iframe** : `document.getElementById(iframe)
   .contentDocument` renvoie `null` (sandbox sans `allow-same-origin`).

3. **Un outil malveillant ne peut PAS lire le cookie de session**, même en l'essayant : servi
   avec les mêmes en-têtes qu'un vrai outil (`ENTETES_OUTIL`) dans une iframe identique, son
   `document.cookie` lève `Failed to read the 'cookie' property from 'Document': The document is
   sandboxed and lacks the 'allow-same-origin' flag.` (résultat exact obtenu dans le navigateur).

4. **Un outil malveillant ne peut PAS appeler l'API** (`/api/infos`, `/api/session`), même en
   l'essayant : `fetch()` échoue avec `Failed to fetch`, `XMLHttpRequest` avec une erreur réseau
   — la CSP `connect-src 'none'` de `ENTETES_OUTIL` bloque toute requête sortante, y compris vers
   la même origine.

5. **Résultat complet transmis par `postMessage` et journalisé côté page hôte** (origine rendue
   `"null"`, cohérent avec une iframe sandboxée sans `allow-same-origin`) :
   ```json
   {
     "cookie": "ERREUR: Failed to read the 'cookie' property from 'Document': The document is sandboxed and lacks the 'allow-same-origin' flag.",
     "fetch_api_infos": "BLOQUE: Failed to fetch",
     "fetch_api_session": "BLOQUE: Failed to fetch",
     "xhr": "BLOQUE: erreur reseau"
   }
   ```

6. **Un message malformé (chaîne au lieu d'un objet, action inconnue) envoyé à la calculatrice
   est ignoré silencieusement** : aucune erreur JS, l'outil reste utilisable ensuite (un nouveau
   `postMessage` valide `{type:"action", action:"afficher"}` réinitialise correctement l'écran à
   `0`).

7. **La CSP `script-src 'self'` du site (page `/demo` et outils) bloque tout `<script>` inline**
   (constaté en pratique en écrivant d'abord la page de démo avec un script inline : le
   navigateur l'a ignoré sans même une erreur visible facilement — il a fallu l'externaliser en
   `.js` pour que ça s'exécute). C'est une preuve supplémentaire, non cherchée au départ, que la
   CSP posée par `ENTETES_OUTIL` (et par `jules/web/app.py` pour le reste du site) fait son
   travail.

## Ce qui n'a pas été testé ici (hors périmètre de l'étape 3)

- L'intégration réelle dans la page de cours (bloc `type: outil` d'une leçon) : décrite dans la
  description de la pull request pour l'intégration à l'étape suivante.
- Les permissions déclarées (`permissions:` dans `outil.yaml`) : aucun des 3 outils de référence
  n'en demande ; le chargeur refuse toute permission hors de la liste validée (testé par
  `tests/test_outils.py::test_permission_non_validee_refusee`), mais l'octroi réel d'une
  permission (ex. `micro`) n'a pas de mécanisme d'octroi à tester tant qu'aucun outil n'en a
  besoin.
