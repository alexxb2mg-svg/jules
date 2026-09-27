# Sécurité

Jules est utilisé par des enfants. Nous traitons en priorité tout problème qui pourrait les exposer.

## Signaler une faille

**Ne publiez pas la faille dans un ticket public.** Utilisez le signalement privé de GitHub : onglet **Security**, puis **Report a vulnerability**. Seuls les mainteneurs le voient.

Décrivez si possible : ce qui est touché, comment le reproduire, et ce qu'un attaquant pourrait obtenir. Nous répondons sous 7 jours et vous tenons au courant jusqu'à la correction. Avec votre accord, nous vous remercierons nommément dans la note de version.

## Ce qui compte comme une faille

- accéder aux conversations, photos ou bilans sans le bon code ;
- contourner la vigilance ou les consignes de sécurité (par exemple, un message qui empêche l'alerte au parent) ;
- lire un fichier de l'ordinateur à travers Jules ;
- faire fuiter une clé API ou un code d'accès ;
- exécuter du code dans la page ou sur l'ordinateur.

## Ce qui n'en est pas

- faire donner une réponse à Jules en insistant : c'est important, mais c'est un défaut pédagogique. Ouvrez un ticket normal ;
- les problèmes d'un fournisseur d'IA (Anthropic, Mistral, OpenAI...) : signalez-les à ce fournisseur.

## Ce que Jules protège / ce qu'il ne protège pas

**Jules protège contre :**

- un curieux du réseau local qui n'a pas le code d'accès (aucune donnée de l'élève n'est servie sans lui) ;
- une injection de script dans un message ou une fiche (XSS : les pages échappent tout contenu affiché) ;
- un outil communautaire qui tenterait d'exfiltrer des données (iframe isolée, aucun accès réseau, voir `docs/OUTILS-CONTRAT.md`) ;
- une photo piégée (fichier vérifié avant d'être enregistré : vraie image, taille limitée) ;
- un brute-force naïf sur les codes d'accès (limitation du nombre d'essais).

**Jules ne protège pas contre :**

- quelqu'un qui a accès au disque de l'ordinateur familial : `jules.db`, `donnees/images/`, les exports `.zip` et les journaux techniques sont **en clair**, non chiffrés par Jules. Chiffrez le disque (BitLocker sous Windows, FileVault sous macOS) et excluez `donnees/` de toute sauvegarde envoyée vers un service en ligne ;
- quelqu'un à qui l'enfant a donné son code d'accès ;
- le fournisseur d'IA en ligne choisi à l'installation (Mistral, Anthropic, OpenAI...) : il reçoit les messages et les photos envoyés par l'enfant pendant la conversation. C'est un choix du parent, qui en reste responsable (voir « Choisir l'intelligence artificielle » dans le README) ;
- un modèle qui céderait et donnerait la réponse malgré les consignes.

La vigilance (détection d'un message inquiétant) est un meilleur effort : elle dépend du modèle configuré et s'appuie, en secours, sur un plancher de mots-clés (`consignes/vigilance_plancher.yaml`). Ce n'est pas une garantie.

Le journal technique (`donnees/jules.log`) peut contenir des extraits de messages échangés avec Jules ; il est écrit dans `donnees/`, au même titre que le reste du dossier de l'élève.

## Versions suivies

Seule la dernière version de la branche `main` reçoit des corrections.

## Bonnes pratiques pour les familles

- Définissez les deux codes d'accès avant d'ouvrir Jules à une tablette.
- N'exposez jamais Jules sur Internet (pas de redirection de port sur la box).
- Avec un service d'IA payant, fixez un plafond de dépense dans sa console.
