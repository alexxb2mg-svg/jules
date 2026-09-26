// Jules - page studio (lot C) : mes supports a gauche, la trame au centre, les retours de Jules a droite.
// Contrat : docs/STUDIO-CONTRAT.md paragraphe 3 (API) et paragraphe 6 (perimetre de cette page).
// Le module serveur (lot B, jules/modules/studio.py) n'existe pas encore dans ce worktree : les
// chemins d'API ci-dessous suivent EXACTEMENT le tableau du contrat, rien n'est invente. La facon
// dont "ecrire" fait grandir un tableau vide (noeuds/sections/questions/cartes) quand on ecrit a un
// index au-dela de sa longueur actuelle est une consequence directe de "l'eleve ajoute ses branches
// une par une" (contrat paragraphe 1) : a verifier avec le lot B a l'integration.
"use strict";

(() => {
  const $ = (id) => document.getElementById(id);

  const TYPES_SUPPORT = ["carte_mentale", "fiche", "quiz", "cartes_memoire"];
  const LIBELLES_TYPE_SUPPORT = {
    carte_mentale: "🧠 Carte mentale", fiche: "📋 Fiche", quiz: "❓ Quiz", cartes_memoire: "🗂️ Cartes mémoire",
  };
  const LIBELLES_STATUT_SUPPORT = { brouillon: "brouillon", relu: "relu", valide: "validé" };
  const LIBELLES_ETAT = {
    a_venir: "à venir", en_cours: "en cours", bloque: "bloqué", compris: "compris", acquis: "acquis",
  };
  const LIBELLES_ETAT_CARTE = { nouvelle: "nouvelle", apprentissage: "en apprentissage", acquise: "acquise" };
  const LIBELLES_CHEMIN = { titre: "Titre", noeuds: "Branche", sections: "Section", questions: "Question", cartes: "Carte" };

  const etat = {
    infos: null,
    matieres: [],
    matiereChoisie: null,
    support: null,           // support ouvert (Support.public())
    revisionsDisponibles: [],
    revision: null,          // { cartes, index }
  };

  // --- utilitaires -----------------------------------------------------------
  function creer(balise, classe, html) {
    const el = document.createElement(balise);
    if (classe) el.className = classe;
    if (html !== undefined) el.innerHTML = html;
    return el;
  }

  function estVerrouille() {
    return Boolean(etat.support && etat.support.statut === "valide");
  }

  function afficherErreurSupport(msg) {
    $("support-erreur").textContent = msg;
    $("support-erreur").classList.remove("cache");
  }

  // --- panneaux repliables (tablette) ------------------------------------------
  function ouvrirPanneau(nom) {
    const id = nom === "jules" ? "panneau-jules" : "notions";
    $(id).classList.add("ouvert");
    $(`menu-${nom}`).setAttribute("aria-expanded", "true");
  }
  function fermerPanneau(nom) {
    const id = nom === "jules" ? "panneau-jules" : "notions";
    $(id).classList.remove("ouvert");
    $(`menu-${nom}`).setAttribute("aria-expanded", "false");
  }

  // --- mes supports (gauche) --------------------------------------------------
  async function chargerNotions(matiere) {
    $("notions-attente").classList.remove("cache");
    try {
      const chemin = "/api/eleve/studio/notions" + (matiere ? `?matiere=${encodeURIComponent(matiere)}` : "");
      const r = await MS.api(chemin);
      etat.matieres = r.matieres || [];
      etat.matiereChoisie = r.matiere;
      remplirSelectMatieres();
      afficherNotions(r.notions || []);
    } catch (err) {
      $("notions-liste").innerHTML = "";
      $("notions-liste").appendChild(creer("p", "studio-erreur-ligne", MS.echapper(`Impossible de charger tes notions : ${err.message}`)));
    } finally {
      $("notions-attente").classList.add("cache");
    }
  }

  function remplirSelectMatieres() {
    const select = $("select-matiere");
    select.innerHTML = "";
    for (const m of etat.matieres) {
      const opt = document.createElement("option");
      opt.value = m.id;
      opt.textContent = m.nom;
      opt.selected = m.id === etat.matiereChoisie;
      select.appendChild(opt);
    }
  }

  function afficherNotions(toutes) {
    // le studio ne sert qu'aux notions qui ont une lecon : les autres encombreraient la liste
    const notions = toutes.filter((n) => n.lecon);
    const sansLecon = toutes.length - notions.length;
    const zone = $("notions-liste");
    zone.innerHTML = "";
    const chapitres = [];
    const parChapitre = new Map();
    for (const n of notions) {
      const cle = n.chapitre || "";
      if (!parChapitre.has(cle)) { parChapitre.set(cle, []); chapitres.push(cle); }
      parChapitre.get(cle).push(n);
    }
    if (!chapitres.length) {
      zone.appendChild(creer("p", "avertissement", "Pas encore de leçon dans cette matière : le studio n'y est pas encore utilisable."));
      return;
    }
    if (sansLecon) {
      zone.appendChild(creer("p", "sans-support", `Les ${sansLecon} autres notions de la matière n'ont pas encore de leçon.`));
    }
    for (const chap of chapitres) {
      if (chap) zone.appendChild(creer("div", "notion-bloc-titre", MS.echapper(chap)));
      for (const n of parChapitre.get(chap)) zone.appendChild(construireNotionBloc(n));
    }
    marquerSupportActif();
  }

  function construireNotionBloc(n) {
    const bloc = creer("div", "notion-bloc");
    const pastille = `<span class="pastille-etat ${MS.echapper(n.etat)}">${MS.echapper(LIBELLES_ETAT[n.etat] || n.etat)}</span>`;
    bloc.appendChild(creer("div", "notion-ligne-titre", `<span class="nom">${MS.echapper(n.titre)}</span>${pastille}`));
    if (!n.lecon) {
      bloc.appendChild(creer("p", "sans-support", "Pas encore de leçon : le studio n'est pas encore utilisable ici."));
      return bloc;
    }
    const supports = creer("div", "notion-supports");
    for (const s of n.supports || []) {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "support-ligne";
      b.dataset.id = s.id;
      const pastilleStatut = `<span class="pastille-statut ${MS.echapper(s.statut)}">${MS.echapper(LIBELLES_STATUT_SUPPORT[s.statut] || s.statut)}</span>`;
      b.innerHTML = `<span class="nom">${MS.echapper(LIBELLES_TYPE_SUPPORT[s.type] || s.type)} — ${MS.echapper(s.titre || "sans titre")}</span>${pastilleStatut}`;
      b.addEventListener("click", () => ouvrirSupport(s.id));
      supports.appendChild(b);
    }
    bloc.appendChild(supports);
    const nouveau = creer("button", "bouton-nouveau-support", "+ nouveau support");
    nouveau.type = "button";
    nouveau.addEventListener("click", () => ouvrirChoixType(n.id));
    bloc.appendChild(nouveau);
    return bloc;
  }

  function marquerSupportActif() {
    const id = etat.support && etat.support.id;
    for (const b of document.querySelectorAll(".support-ligne")) {
      b.classList.toggle("active", Boolean(id) && b.dataset.id === id);
    }
  }

  // --- choix du type a la creation ---------------------------------------------
  function ouvrirChoixType(notionId) {
    const zone = $("choix-type-liste");
    zone.innerHTML = "";
    for (const type of TYPES_SUPPORT) {
      const b = document.createElement("button");
      b.type = "button";
      b.textContent = LIBELLES_TYPE_SUPPORT[type] || type;
      b.addEventListener("click", () => { fermerChoixType(); creerSupport(notionId, type); });
      zone.appendChild(b);
    }
    $("choix-type").classList.remove("cache");
  }
  const fermerChoixType = () => $("choix-type").classList.add("cache");

  async function creerSupport(notionId, type) {
    try {
      const r = await MS.api(`/api/eleve/studio/notions/${encodeURIComponent(notionId)}/creer`, MS.json({ type }));
      etat.support = r.support;
      $("retours-fil").innerHTML = "";
      afficherSupport();
      chargerNotions(etat.matiereChoisie);
      fermerPanneau("notions");
    } catch (err) {
      afficherErreurSupport(`Impossible de créer ce support : ${err.message}`);
    }
  }

  async function ouvrirSupport(id) {
    try {
      const r = await MS.api(`/api/eleve/studio/supports/${encodeURIComponent(id)}`);
      etat.support = r.support;
      $("retours-fil").innerHTML = "";
      afficherSupport();
      fermerPanneau("notions");
    } catch (err) {
      afficherErreurSupport(`Impossible d'ouvrir ce support : ${err.message}`);
    }
  }

  // --- affichage du support (centre) --------------------------------------------
  function motifBlocageValidation(support) {
    const c = support.contenu || {};
    switch (support.type) {
      case "carte_mentale": {
        const n = (c.noeuds || []).length;
        return n >= 3 ? null : "Ajoute au moins 3 branches pour pouvoir valider cette carte mentale.";
      }
      case "fiche": {
        const n = (c.sections || []).filter((s) => (s.contenu || "").trim()).length;
        return n >= 2 ? null : "Ajoute au moins 2 sections avec du contenu pour pouvoir valider cette fiche.";
      }
      case "quiz": {
        const n = (c.questions || []).filter((q) => (q.question || "").trim() && (q.reponse || "").trim()).length;
        return n >= 3 ? null : "Écris au moins 3 questions avec leur réponse pour pouvoir valider ce quiz.";
      }
      case "cartes_memoire": {
        const n = (c.cartes || []).filter((cc) => (cc.recto || "").trim() && (cc.verso || "").trim()).length;
        return n >= 4 ? null : "Ajoute au moins 4 cartes (recto et verso remplis) pour pouvoir valider ces cartes mémoire.";
      }
      default:
        return null;
    }
  }

  function afficherSupport() {
    // Rappel au survol du sens des lettres de la notion du support (symboles.js).
    if (typeof Symboles !== "undefined") Symboles.notion(document.body, etat.support && etat.support.notion);
    const support = etat.support;
    $("accueil-studio").classList.add("cache");
    $("support").classList.remove("cache");
    $("support-erreur").classList.add("cache");
    const verrouille = estVerrouille();
    $("support").classList.toggle("verrouille", verrouille);
    $("support-titre").textContent = support.titre || LIBELLES_TYPE_SUPPORT[support.type] || support.type;
    $("support-meta").textContent = `${LIBELLES_TYPE_SUPPORT[support.type] || support.type} · ${LIBELLES_STATUT_SUPPORT[support.statut] || support.statut}`;

    const avert = $("support-avertissement");
    if (verrouille) {
      avert.textContent = "🔒 Ce support est validé : il est en lecture seule et entre dans tes révisions.";
      avert.classList.remove("cache");
    } else {
      avert.classList.add("cache");
    }

    const zone = $("trame");
    zone.innerHTML = "";
    zone.appendChild(champEditable(support.titre, ["titre"], { placeholder: "Titre du support…", labelTexte: "Titre du support" }));
    switch (support.type) {
      case "carte_mentale": zone.appendChild(construireCarteMentale(support)); break;
      case "fiche": zone.appendChild(construireFiche(support)); break;
      case "quiz": zone.appendChild(construireQuiz(support)); break;
      case "cartes_memoire": zone.appendChild(construireCartesMemoire(support)); break;
      default: zone.appendChild(creer("p", "avertissement", "Type de support non reconnu."));
    }

    const motif = verrouille ? null : motifBlocageValidation(support);
    const aide = $("support-aide-validation");
    if (!verrouille && motif) { aide.textContent = motif; aide.classList.remove("cache"); } else { aide.classList.add("cache"); }

    $("bouton-valider").disabled = verrouille || Boolean(motif);
    $("bouton-relire").disabled = false;
    $("bouton-devalider").classList.toggle("cache", !verrouille);
    $("bouton-supprimer").classList.toggle("cache", verrouille);
    marquerSupportActif();
  }

  // --- champ editable generique (titre, branche, section, question, carte) -------
  function champEditable(valeur, chemin, { zone = false, placeholder = "", labelTexte = "" } = {}) {
    const id = `champ-${chemin.join("-")}`;
    const wrap = creer("div", "champ-bloc");
    if (labelTexte) {
      const lab = creer("label", "cache-visuel", MS.echapper(labelTexte));
      lab.htmlFor = id;
      wrap.appendChild(lab);
    }
    const el = document.createElement(zone ? "textarea" : "input");
    if (!zone) el.type = "text";
    el.id = id;
    el.className = zone ? "champ-zone" : "champ-texte";
    el.maxLength = 200;
    el.placeholder = placeholder;
    el.value = valeur || "";
    el.disabled = estVerrouille();
    const compteur = creer("p", "compteur-champ", `${el.value.length} / 200`);
    el.addEventListener("input", () => { compteur.textContent = `${el.value.length} / 200`; });
    let envoye = valeur || "";
    el.addEventListener("blur", async () => {
      const v = el.value.trim();
      if (v === envoye) return;
      try {
        await ecrireChamp(chemin, v);
        envoye = v;
      } catch (err) {
        afficherErreurSupport(`Impossible d'enregistrer : ${err.message}`);
      }
    });
    wrap.appendChild(el);
    wrap.appendChild(compteur);
    return wrap;
  }

  async function ecrireChampBrut(chemin, valeur) {
    const r = await MS.api(`/api/eleve/studio/supports/${encodeURIComponent(etat.support.id)}/ecrire`, MS.json({ chemin, valeur }));
    etat.support = r.support;
    return r.support;
  }

  async function ecrireChamp(chemin, valeur) {
    await ecrireChampBrut(chemin, valeur);
    afficherSupport();
  }

  async function rechargerSupport() {
    const r = await MS.api(`/api/eleve/studio/supports/${encodeURIComponent(etat.support.id)}`);
    etat.support = r.support;
    afficherSupport();
  }

  async function ajouterElement(cle, champPrincipal, valeurDefaut) {
    const index = ((etat.support.contenu || {})[cle] || []).length;
    try {
      await ecrireChampBrut([cle, index, champPrincipal], valeurDefaut);
      await rechargerSupport();
    } catch (err) {
      afficherErreurSupport(`Impossible d'ajouter : ${err.message}`);
    }
  }

  async function ajouterNoeud(parentId) {
    const index = ((etat.support.contenu || {}).noeuds || []).length;
    try {
      await ecrireChampBrut(["noeuds", index, "texte"], "");
      await ecrireChampBrut(["noeuds", index, "parent"], parentId);
      await rechargerSupport();
    } catch (err) {
      afficherErreurSupport(`Impossible d'ajouter : ${err.message}`);
    }
  }

  // --- carte mentale -----------------------------------------------------------
  function construireCarteMentale(support) {
    const dom = creer("div", "arbre-mental");
    const noeuds = support.contenu.noeuds || [];
    const enfantsDe = (parentId) => noeuds.filter((n) => (n.parent || null) === parentId);
    const construireNoeud = (noeud, estRacine) => {
      const index = noeuds.indexOf(noeud);
      const bloc = creer("div", `noeud-mental${estRacine ? " racine" : ""}`);
      const entete = creer("div", "noeud-entete");
      entete.appendChild(champEditable(noeud.texte, ["noeuds", index, "texte"], { placeholder: "Idée…", labelTexte: `Branche ${index + 1}` }));
      bloc.appendChild(entete);
      const zoneEnfants = creer("div", "enfants");
      for (const enfant of enfantsDe(noeud.id)) zoneEnfants.appendChild(construireNoeud(enfant, false));
      if (!estVerrouille()) {
        const ajouter = creer("button", "bouton-ajouter-branche", "+ sous-branche");
        ajouter.type = "button";
        ajouter.addEventListener("click", () => ajouterNoeud(noeud.id));
        zoneEnfants.appendChild(ajouter);
      }
      bloc.appendChild(zoneEnfants);
      return bloc;
    };
    for (const racine of enfantsDe(null)) dom.appendChild(construireNoeud(racine, true));
    if (!estVerrouille()) {
      const ajouter = creer("button", "bouton-ajouter", "+ Ajouter une idée");
      ajouter.type = "button";
      ajouter.addEventListener("click", () => ajouterNoeud(null));
      dom.appendChild(ajouter);
    }
    if (!noeuds.length) dom.appendChild(creer("p", "avertissement", "Une carte mentale vide : commence par ajouter une idée."));
    return dom;
  }

  // --- fiche ---------------------------------------------------------------------
  function construireFiche(support) {
    const dom = creer("div", "fiche-sections");
    const sections = support.contenu.sections || [];
    sections.forEach((s, i) => {
      const bloc = creer("div", "fiche-section");
      const entete = creer("div", "fiche-section-entete");
      entete.appendChild(champEditable(s.titre, ["sections", i, "titre"], { placeholder: "Titre de la section", labelTexte: `Titre section ${i + 1}` }));
      bloc.appendChild(entete);
      bloc.appendChild(champEditable(s.contenu, ["sections", i, "contenu"], { zone: true, placeholder: "Contenu…", labelTexte: `Contenu section ${i + 1}` }));
      dom.appendChild(bloc);
    });
    if (!estVerrouille()) {
      const ajouter = creer("button", "bouton-ajouter", "+ Ajouter une section");
      ajouter.type = "button";
      ajouter.addEventListener("click", () => ajouterElement("sections", "titre", "Nouvelle section"));
      dom.appendChild(ajouter);
    }
    if (!sections.length) dom.appendChild(creer("p", "avertissement", "Une fiche vide : commence par ajouter une section."));
    return dom;
  }

  // --- quiz --------------------------------------------------------------------
  function construireQuiz(support) {
    const dom = creer("div", "quiz-questions");
    const questions = support.contenu.questions || [];
    questions.forEach((q, i) => {
      const bloc = creer("div", "quiz-question");
      const entete = creer("div", "quiz-question-entete");
      entete.appendChild(champEditable(q.question, ["questions", i, "question"], { placeholder: "Ta question…", labelTexte: `Question ${i + 1}` }));
      bloc.appendChild(entete);
      bloc.appendChild(champEditable(q.reponse, ["questions", i, "reponse"], { zone: true, placeholder: "Ta réponse…", labelTexte: `Réponse ${i + 1}` }));
      dom.appendChild(bloc);
    });
    if (!estVerrouille()) {
      const ajouter = creer("button", "bouton-ajouter", "+ Ajouter une question");
      ajouter.type = "button";
      ajouter.addEventListener("click", () => ajouterElement("questions", "question", "Nouvelle question"));
      dom.appendChild(ajouter);
    }
    if (!questions.length) dom.appendChild(creer("p", "avertissement", "Un quiz vide : commence par ajouter une question. C'est toi qui écris tes questions, Jules ne les corrige pas automatiquement."));
    return dom;
  }

  // --- cartes memoire ------------------------------------------------------------
  function construireCartesMemoire(support) {
    const dom = creer("div", "cartes-pile");
    const cartes = support.contenu.cartes || [];
    cartes.forEach((c, i) => {
      const bloc = creer("div", "carte-memoire");
      const entete = creer("div", "carte-memoire-entete");
      entete.appendChild(creer("strong", "", MS.echapper(`Carte ${i + 1}`)));
      entete.appendChild(creer("span", `pastille-statut ${MS.echapper(c.etat || "nouvelle")}`, MS.echapper(LIBELLES_ETAT_CARTE[c.etat] || c.etat || "nouvelle")));
      bloc.appendChild(entete);
      const champs = creer("div", "carte-memoire-champs");
      champs.appendChild(champEditable(c.recto, ["cartes", i, "recto"], { zone: true, placeholder: "Recto…", labelTexte: `Recto carte ${i + 1}` }));
      champs.appendChild(champEditable(c.verso, ["cartes", i, "verso"], { zone: true, placeholder: "Verso…", labelTexte: `Verso carte ${i + 1}` }));
      bloc.appendChild(champs);
      dom.appendChild(bloc);
    });
    if (!estVerrouille()) {
      const ajouter = creer("button", "bouton-ajouter", "+ Ajouter une carte");
      ajouter.type = "button";
      ajouter.addEventListener("click", () => ajouterElement("cartes", "recto", ""));
      dom.appendChild(ajouter);
    }
    if (!cartes.length) dom.appendChild(creer("p", "avertissement", "Des cartes mémoire vides : commence par ajouter une carte."));
    return dom;
  }

  // --- retours de Jules (droite) --------------------------------------------------
  function libelleChemin(chemin) {
    if (!Array.isArray(chemin) || !chemin.length) return "";
    const [cle, index] = chemin;
    if (cle === "titre") return "Titre";
    const base = LIBELLES_CHEMIN[cle] || cle;
    return typeof index === "number" ? `${base} ${index + 1}` : base;
  }

  function ajouterRetourJules(chemin, message) {
    const ligne = creer("div", "retour-jules");
    const lbl = libelleChemin(chemin);
    ligne.innerHTML = (lbl ? `<span class="retour-chemin">${MS.echapper(lbl)}</span>` : "") + MS.markdown(message);
    $("retours-fil").appendChild(ligne);
    $("retours-fil").scrollTop = $("retours-fil").scrollHeight;
  }

  async function relire() {
    if (!etat.support) return;
    $("bouton-relire").disabled = true;
    const attente = creer("div", "attente-ligne", "Jules relit…");
    $("retours-fil").appendChild(attente);
    try {
      const r = await MS.api(`/api/eleve/studio/supports/${encodeURIComponent(etat.support.id)}/relire`, { method: "POST" });
      attente.remove();
      etat.support = r.support;
      const retours = r.retours || [];
      if (retours.length) for (const retour of retours) ajouterRetourJules(retour.chemin, retour.message);
      else ajouterRetourJules([], "Jules n'a pas de remarque pour l'instant, continue !");
      afficherSupport();
    } catch (err) {
      attente.remove();
      ajouterRetourJules([], `Petit souci : ${err.message}. Réessaie.`);
      $("bouton-relire").disabled = false;
    }
  }

  // --- valider / devalider / supprimer ---------------------------------------------
  async function valider() {
    $("bouton-valider").disabled = true;
    try {
      const r = await MS.api(`/api/eleve/studio/supports/${encodeURIComponent(etat.support.id)}/valider`, { method: "POST" });
      etat.support = r.support;
      afficherSupport();
      chargerNotions(etat.matiereChoisie);
      chargerRevisionsDisponibles();
    } catch (err) {
      afficherErreurSupport(`Impossible de valider : ${err.message}`);
      $("bouton-valider").disabled = false;
    }
  }

  async function devalider() {
    $("bouton-devalider").disabled = true;
    try {
      const r = await MS.api(`/api/eleve/studio/supports/${encodeURIComponent(etat.support.id)}/devalider`, { method: "POST" });
      etat.support = r.support;
      afficherSupport();
      chargerNotions(etat.matiereChoisie);
      chargerRevisionsDisponibles();
    } catch (err) {
      afficherErreurSupport(`Impossible de dévalider : ${err.message}`);
    } finally {
      $("bouton-devalider").disabled = false;
    }
  }

  function surClicDevalider() {
    if (!etat.support) return;
    if (etat.support.type === "cartes_memoire") {
      $("confirmation-devalidation").classList.remove("cache");
    } else {
      devalider();
    }
  }
  const fermerConfirmation = () => $("confirmation-devalidation").classList.add("cache");

  async function supprimer() {
    if (!etat.support) return;
    if (!confirm("Supprimer ce brouillon ? Cette action est définitive.")) return; // eslint-disable-line no-alert
    try {
      await MS.api(`/api/eleve/studio/supports/${encodeURIComponent(etat.support.id)}`, { method: "DELETE" });
      etat.support = null;
      $("support").classList.add("cache");
      $("accueil-studio").classList.remove("cache");
      chargerNotions(etat.matiereChoisie);
    } catch (err) {
      afficherErreurSupport(`Impossible de supprimer : ${err.message}`);
    }
  }

  // --- ecran de revision (cartes memoire) -------------------------------------------
  async function chargerRevisionsDisponibles() {
    try {
      const r = await MS.api("/api/eleve/studio/revisions");
      etat.revisionsDisponibles = r.cartes || [];
      $("bouton-revision").classList.toggle("cache", !etat.revisionsDisponibles.length);
    } catch (_) {
      $("bouton-revision").classList.add("cache");
    }
  }

  function afficherErreurRevision(msg) {
    $("revision-compteur").textContent = msg;
  }

  function afficherCarteRevision() {
    const rev = etat.revision;
    const zone = $("revision-carte");
    const reponses = $("revision-reponses");
    const retourner = $("revision-retourner");
    zone.innerHTML = "";
    if (!rev || rev.index >= rev.cartes.length) {
      reponses.classList.add("cache");
      retourner.classList.add("cache");
      $("revision-fin").classList.remove("cache");
      $("revision-compteur").textContent = "";
      return;
    }
    $("revision-fin").classList.add("cache");
    retourner.classList.remove("cache");
    reponses.classList.add("cache");
    const carte = rev.cartes[rev.index];
    $("revision-compteur").textContent = `Carte ${rev.index + 1} / ${rev.cartes.length} · ${carte.notion}`;
    zone.appendChild(creer("p", "", MS.echapper(carte.recto)));
  }

  function ouvrirRevision() {
    if (!etat.revisionsDisponibles.length) return;
    etat.revision = { cartes: etat.revisionsDisponibles.slice(), index: 0 };
    $("ecran-revision").classList.remove("cache");
    afficherCarteRevision();
  }

  function fermerRevision() {
    $("ecran-revision").classList.add("cache");
    etat.revision = null;
    chargerRevisionsDisponibles();
  }

  async function retournerCarte() {
    const rev = etat.revision;
    if (!rev || rev.index >= rev.cartes.length) return;
    const carte = rev.cartes[rev.index];
    try {
      const r = await MS.api(`/api/eleve/studio/supports/${encodeURIComponent(carte.support)}`);
      const trouvee = (r.support.contenu.cartes || []).find((c) => c.id === carte.carte_id);
      const zone = $("revision-carte");
      zone.innerHTML = "";
      zone.appendChild(creer("p", "", MS.echapper(carte.recto)));
      zone.appendChild(creer("p", "verso", trouvee ? MS.echapper(trouvee.verso) : "…"));
      $("revision-retourner").classList.add("cache");
      $("revision-reponses").classList.remove("cache");
    } catch (err) {
      afficherErreurRevision(`Impossible d'afficher le verso : ${err.message}`);
    }
  }

  async function repondreCarte(reponse) {
    const rev = etat.revision;
    if (!rev || rev.index >= rev.cartes.length) return;
    const carte = rev.cartes[rev.index];
    const boutons = ["revision-facile", "revision-difficile", "revision-rate"];
    boutons.forEach((id) => { $(id).disabled = true; });
    try {
      await MS.api(
        `/api/eleve/studio/revisions/${encodeURIComponent(carte.support)}/${encodeURIComponent(carte.carte_id)}/reponse`,
        MS.json({ reponse })
      );
      rev.index += 1;
      afficherCarteRevision();
    } catch (err) {
      afficherErreurRevision(`Petit souci : ${err.message}. Réessaie.`);
    } finally {
      boutons.forEach((id) => { $(id).disabled = false; });
    }
  }

  // --- demarrage -----------------------------------------------------------
  async function demarrage() {
    await MS.porte("eleve", { porte: $("porte"), contenu: $("contenu"), formulaire: $("porte-form"), champ: $("porte-code"), erreur: $("porte-erreur") });
    etat.infos = await MS.api("/api/infos");
    MS.appliquerCouleurs(etat.infos.persona.couleurs);
    document.title = `${etat.infos.persona.nom} - studio`;
    $("nom-persona").textContent = etat.infos.persona.nom;
    $("jules-nom").textContent = etat.infos.persona.nom;

    $("select-matiere").addEventListener("change", (ev) => chargerNotions(ev.target.value));
    $("menu-notions").addEventListener("click", () => {
      const ouvert = $("notions").classList.contains("ouvert");
      if (ouvert) fermerPanneau("notions"); else ouvrirPanneau("notions");
    });
    $("menu-jules").addEventListener("click", () => {
      const ouvert = $("panneau-jules").classList.contains("ouvert");
      if (ouvert) fermerPanneau("jules"); else ouvrirPanneau("jules");
    });
    $("notions-fermer").addEventListener("click", () => fermerPanneau("notions"));
    $("jules-fermer").addEventListener("click", () => fermerPanneau("jules"));

    $("choix-type-fermer").addEventListener("click", fermerChoixType);
    $("choix-type").addEventListener("click", (ev) => { if (ev.target === $("choix-type")) fermerChoixType(); });

    $("bouton-relire").addEventListener("click", relire);
    $("bouton-valider").addEventListener("click", valider);
    $("bouton-devalider").addEventListener("click", surClicDevalider);
    $("bouton-supprimer").addEventListener("click", supprimer);

    $("confirmation-fermer").addEventListener("click", fermerConfirmation);
    $("confirmation-annuler").addEventListener("click", fermerConfirmation);
    $("confirmation-confirmer").addEventListener("click", async () => { fermerConfirmation(); await devalider(); });
    $("confirmation-devalidation").addEventListener("click", (ev) => { if (ev.target === $("confirmation-devalidation")) fermerConfirmation(); });

    $("bouton-revision").addEventListener("click", ouvrirRevision);
    $("revision-fermer").addEventListener("click", fermerRevision);
    $("revision-retourner").addEventListener("click", retournerCarte);
    $("revision-facile").addEventListener("click", () => repondreCarte("facile"));
    $("revision-difficile").addEventListener("click", () => repondreCarte("difficile"));
    $("revision-rate").addEventListener("click", () => repondreCarte("rate"));
    $("ecran-revision").addEventListener("click", (ev) => { if (ev.target === $("ecran-revision")) fermerRevision(); });
    document.addEventListener("keydown", (ev) => { if (ev.key === "Escape") { fermerChoixType(); fermerConfirmation(); } });

    await chargerNotions(null);
    await chargerRevisionsDisponibles();
  }

  demarrage().catch((err) => { document.body.innerHTML = `<p class="erreur-page">Erreur : ${MS.echapper(err.message)}</p>`; });
})();
