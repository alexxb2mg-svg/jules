// Jules - page de cours (lot D) : parcours a gauche, lecon au centre, Jules a droite.
// Contrat : docs/COURS-CONTRAT.md paragraphe 3 (API) et 4 (perimetre de cette page).
"use strict";

(() => {
  const $ = (id) => document.getElementById(id);

  const LIBELLES_ETAT = {
    a_venir: "à venir", en_cours: "en cours", bloque: "bloqué", compris: "compris", acquis: "acquis",
  };
  const LIBELLES_BLOC_ETAT = {
    a_faire: "à faire", en_cours: "en cours", reussi: "réussi", a_revoir: "à revoir", fait: "fait",
  };

  const etat = {
    infos: null,
    matieres: [],
    matiereChoisie: null,
    session: null,       // id de session de la lecon en cours
    conversation: null,  // id de conversation associee
    lecon: null,
    progression: null,
    blocEls: [],          // index -> { conteneur, maj(progressionBloc) }
    occupeParcours: false,
    julesOccupe: false,
  };

  // --- utilitaires ---------------------------------------------------------
  function creer(balise, classe, html) {
    const el = document.createElement(balise);
    if (classe) el.className = classe;
    if (html !== undefined) el.innerHTML = html;
    return el;
  }

  function formatNombre(n) {
    return String(n).replace(".", ",");
  }

  // --- parcours (gauche) ----------------------------------------------------
  async function chargerParcours(matiere) {
    etat.occupeParcours = true;
    $("parcours-attente").classList.remove("cache");
    try {
      const chemin = "/api/eleve/cours/parcours" + (matiere ? `?matiere=${encodeURIComponent(matiere)}` : "");
      const r = await MS.api(chemin);
      etat.matieres = r.matieres || [];
      etat.matiereChoisie = r.matiere;
      remplirSelectMatieres();
      $("parcours-estimation").textContent = r.estimation || "";
      afficherNotions(r.notions || []);
    } catch (err) {
      $("parcours-liste").innerHTML = "";
      $("parcours-liste").appendChild(creer("p", "cours-erreur-ligne", MS.echapper(`Impossible de charger ton parcours : ${err.message}`)));
    } finally {
      etat.occupeParcours = false;
      $("parcours-attente").classList.add("cache");
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

  function afficherNotions(notions) {
    const zone = $("parcours-liste");
    zone.innerHTML = "";
    const chapitres = [];
    const parChapitre = new Map();
    for (const n of notions) {
      if (!parChapitre.has(n.chapitre)) { parChapitre.set(n.chapitre, []); chapitres.push(n.chapitre); }
      parChapitre.get(n.chapitre).push(n);
    }
    if (!chapitres.length) {
      zone.appendChild(creer("p", "avertissement", "Aucune notion pour cette matière pour le moment."));
      return;
    }
    for (const chap of chapitres) {
      zone.appendChild(creer("div", "chapitre-titre", MS.echapper(chap)));
      for (const n of parChapitre.get(chap)) {
        const bouton = document.createElement("button");
        bouton.type = "button";
        bouton.className = "notion-ligne";
        bouton.dataset.id = n.id;
        const pastille = `<span class="pastille-etat ${MS.echapper(n.etat)}">${MS.echapper(LIBELLES_ETAT[n.etat] || n.etat)}</span>`;
        if (n.lecon) {
          bouton.innerHTML = `<span class="nom">${MS.echapper(n.titre)}</span>${pastille}`;
          bouton.addEventListener("click", () => ouvrirLecon(n.id, bouton));
        } else {
          bouton.disabled = true;
          bouton.innerHTML = `<span class="nom">${MS.echapper(n.titre)}<span class="sans-lecon">pas encore de leçon</span></span>${pastille}`;
        }
        zone.appendChild(bouton);
      }
    }
    marquerNotionActive();
  }

  function marquerNotionActive() {
    const notionId = etat.lecon && etat.lecon.notion;
    for (const b of $("parcours-liste").querySelectorAll(".notion-ligne")) {
      b.classList.toggle("active", Boolean(notionId) && b.dataset.id === notionId);
    }
  }

  // --- ouverture d'une lecon --------------------------------------------------
  async function ouvrirLecon(notionId) {
    if (etat.occupeParcours) return;
    $("lecon-erreur").classList.add("cache");
    try {
      const r = await MS.api(`/api/eleve/cours/lecons/${encodeURIComponent(notionId)}/ouvrir`, { method: "POST" });
      etat.session = r.session;
      etat.conversation = r.conversation;
      etat.lecon = r.lecon;
      // Rappel au survol du sens des lettres de la notion de la lecon (symboles.js).
      if (typeof Symboles !== "undefined") Symboles.notion(document.body, notionId);
      etat.progression = r.progression;
      $("lecon-vide").classList.add("cache");
      $("lecon").classList.remove("cache");
      afficherLecon();
      marquerNotionActive();
      await chargerConversation();
      fermerPanneau("parcours");
    } catch (err) {
      $("lecon-vide").classList.add("cache");
      $("lecon").classList.add("cache");
      $("lecon-erreur").textContent = `Impossible d'ouvrir cette leçon : ${err.message}`;
      $("lecon-erreur").classList.remove("cache");
    }
  }

  function afficherLecon() {
    const lecon = etat.lecon;
    $("lecon-titre").textContent = lecon.titre;
    const meta = [lecon.matiere, lecon.niveau, lecon.duree_minutes ? `${lecon.duree_minutes} min` : null].filter(Boolean);
    $("lecon-meta").textContent = meta.join(" · ");
    const avert = $("lecon-avertissement");
    if (lecon.avertissement) {
      avert.textContent = `⚠️ ${lecon.avertissement}`;
      avert.classList.remove("cache");
    } else {
      avert.classList.add("cache");
    }
    $("lecon-fin").classList.add("cache");
    const zone = $("blocs");
    zone.innerHTML = "";
    etat.blocEls = [];
    for (const bloc of lecon.blocs) {
      const construction = construireBloc(bloc);
      etat.blocEls[bloc.index] = construction;
      zone.appendChild(construction.conteneur);
    }
    actualiserProgression(etat.progression, true);
  }

  function actualiserProgression(progression, initial = false) {
    etat.progression = progression;
    const total = progression.blocs.length || 1;
    const faits = progression.blocs.filter((b) => b.etat !== "a_faire").length;
    $("progression-remplie").style.width = `${Math.round((faits / total) * 100)}%`;
    $("progression-texte").textContent = `${faits} / ${total} bloc${total > 1 ? "s" : ""}`;
    for (const b of progression.blocs) {
      const construction = etat.blocEls[b.index];
      if (construction) construction.maj(b, b.index === progression.bloc_courant);
    }
    if (progression.termine) {
      $("lecon-fin").classList.remove("cache");
    }
    if (initial) {
      const courant = etat.blocEls[progression.bloc_courant];
      if (courant) courant.conteneur.scrollIntoView({ block: "center" });
    }
  }

  // --- construction d'un bloc --------------------------------------------------
  function construireBloc(bloc) {
    const conteneur = creer("section", "bloc");
    conteneur.dataset.index = String(bloc.index);
    const entete = creer("div", "bloc-entete");
    const titreTxt = MS.echapper(titreBloc(bloc));
    entete.innerHTML = `<strong>${titreTxt}</strong>`;
    const etatSpan = creer("span", "bloc-etat", "");
    entete.appendChild(etatSpan);
    conteneur.appendChild(entete);

    const corps = creer("div", "bloc-corps");
    conteneur.appendChild(corps);

    const majEtatSpan = (etatBloc) => {
      etatSpan.textContent = LIBELLES_BLOC_ETAT[etatBloc] || etatBloc;
      etatSpan.className = `bloc-etat ${etatBloc}`;
    };

    let majSpecifique = () => {};
    let ajouterTentative = () => {};
    let ajouterIndice = () => {};
    let ajouterFait = () => {};

    switch (bloc.type) {
      case "objectifs": {
        const liste = creer("ul");
        for (const it of bloc.items || []) liste.appendChild(creer("li", "", MS.echapper(it)));
        corps.appendChild(liste);
        const actions = creer("div", "bloc-actions");
        const boutonLu = creer("button", "bouton secondaire", "J'ai lu");
        boutonLu.type = "button";
        boutonLu.addEventListener("click", () => faireBloc(bloc.index, boutonLu));
        actions.appendChild(boutonLu);
        corps.appendChild(actions);
        majSpecifique = (etatBloc) => { boutonLu.disabled = etatBloc !== "a_faire" && etatBloc !== "en_cours"; if (etatBloc === "fait") boutonLu.textContent = "✓ Lu"; };
        break;
      }
      case "texte": {
        corps.appendChild(creer("div", "bloc-markdown", MS.markdown(bloc.contenu || "")));
        const actions = creer("div", "bloc-actions");
        const boutonLu = creer("button", "bouton secondaire", "J'ai lu");
        boutonLu.type = "button";
        boutonLu.addEventListener("click", () => faireBloc(bloc.index, boutonLu));
        actions.appendChild(boutonLu);
        corps.appendChild(actions);
        majSpecifique = (etatBloc) => { boutonLu.disabled = etatBloc !== "a_faire" && etatBloc !== "en_cours"; if (etatBloc === "fait") boutonLu.textContent = "✓ Lu"; };
        break;
      }
      case "exemple": {
        corps.appendChild(creer("p", "bloc-enonce", MS.markdown(bloc.enonce || "")));
        const ol = creer("ol", "etapes");
        for (const e of bloc.etapes || []) ol.appendChild(creer("li", "", MS.markdown(e)));
        corps.appendChild(ol);
        const actions = creer("div", "bloc-actions");
        const boutonLu = creer("button", "bouton secondaire", "J'ai lu");
        boutonLu.type = "button";
        boutonLu.addEventListener("click", () => faireBloc(bloc.index, boutonLu));
        actions.appendChild(boutonLu);
        corps.appendChild(actions);
        majSpecifique = (etatBloc) => { boutonLu.disabled = etatBloc !== "a_faire" && etatBloc !== "en_cours"; if (etatBloc === "fait") boutonLu.textContent = "✓ Lu"; };
        break;
      }
      case "outil": {
        corps.appendChild(creer("p", "outil-a-venir", "🛠️ Cet outil arrivera bientôt dans Jules."));
        const actions = creer("div", "bloc-actions");
        const boutonLu = creer("button", "bouton secondaire", "J'ai lu");
        boutonLu.type = "button";
        boutonLu.addEventListener("click", () => faireBloc(bloc.index, boutonLu));
        actions.appendChild(boutonLu);
        corps.appendChild(actions);
        majSpecifique = (etatBloc) => { boutonLu.disabled = etatBloc !== "a_faire" && etatBloc !== "en_cours"; if (etatBloc === "fait") boutonLu.textContent = "✓ Lu"; };
        break;
      }
      case "exercice": {
        const r = construireExercice(bloc);
        corps.appendChild(r.dom);
        majSpecifique = r.maj;
        break;
      }
      case "question_ouverte":
      case "synthese": {
        const r = construireLibre(bloc);
        corps.appendChild(r.dom);
        majSpecifique = r.maj;
        break;
      }
      default: {
        corps.appendChild(creer("p", "avertissement", "Type de bloc non reconnu."));
      }
    }

    const maj = (progressionBloc, estCourant) => {
      majEtatSpan(progressionBloc.etat);
      conteneur.classList.toggle("courant", estCourant);
      conteneur.classList.toggle("reussi", progressionBloc.etat === "reussi" || progressionBloc.etat === "fait");
      conteneur.classList.toggle("a_revoir", progressionBloc.etat === "a_revoir");
      majSpecifique(progressionBloc.etat, progressionBloc);
    };
    return { conteneur, maj };
  }

  function titreBloc(bloc) {
    return {
      objectifs: "🎯 Ce que tu vas savoir faire",
      texte: bloc.titre || "📖 Le cours",
      exemple: "💡 Un exemple",
      exercice: "✏️ À toi de jouer",
      question_ouverte: "🤔 À toi de réfléchir",
      synthese: "📝 Ce que tu retiens",
      outil: "🛠️ Outil",
    }[bloc.type] || bloc.type;
  }

  // --- bloc exercice --------------------------------------------------------
  function construireExercice(bloc) {
    const dom = creer("div");
    dom.appendChild(creer("p", "bloc-enonce", MS.echapper(bloc.enonce || "")));

    const champZone = creer("div", "reponse-champ");
    let lireReponse = () => "";
    let champPrincipal = null;
    const forme = bloc.forme;
    if (forme === "qcm") {
      const liste = creer("div", "qcm-liste");
      (bloc.choix || []).forEach((choix, i) => {
        const label = creer("label", "qcm-option");
        const input = document.createElement("input");
        input.type = "radio"; input.name = `qcm-${bloc.index}`; input.value = String(i);
        label.appendChild(input);
        label.appendChild(document.createTextNode(choix));
        liste.appendChild(label);
      });
      champZone.appendChild(liste);
      lireReponse = () => {
        const coche = liste.querySelector("input:checked");
        return coche ? Number(coche.value) : null;
      };
      champPrincipal = liste;
    } else {
      const input = document.createElement("input");
      input.type = "text";
      input.inputMode = forme === "nombre" ? "decimal" : "text";
      input.id = `reponse-${bloc.index}`;
      const label = creer("label", "cache-visuel", MS.echapper(bloc.enonce || "Ta réponse"));
      label.htmlFor = input.id;
      champZone.appendChild(label);
      champZone.appendChild(input);
      if (forme === "nombre" && bloc.unite) champZone.appendChild(creer("span", "reponse-unite", MS.echapper(bloc.unite)));
      lireReponse = () => input.value.trim();
      champPrincipal = input;
      input.addEventListener("keydown", (ev) => { if (ev.key === "Enter") { ev.preventDefault(); valider(); } });
    }
    dom.appendChild(champZone);

    const indicesVusZone = creer("ul", "indices-vus");
    dom.appendChild(indicesVusZone);
    const totalIndices = (bloc.indices || []).length;

    const actions = creer("div", "bloc-actions");
    const boutonValider = creer("button", "bouton", "Valider");
    boutonValider.type = "button";
    const boutonIndice = creer("button", "bouton secondaire", "Un indice");
    boutonIndice.type = "button";
    actions.appendChild(boutonValider);
    if (totalIndices) actions.appendChild(boutonIndice);
    dom.appendChild(actions);

    const retour = creer("div", "retour-tentative cache");
    retour.setAttribute("aria-live", "polite");
    dom.appendChild(retour);
    const explication = creer("div", "explication cache");
    dom.appendChild(explication);

    let indicesAffiches = 0;
    function afficherIndicesJusqua(n) {
      const liste = bloc.indices || [];
      while (indicesAffiches < n && indicesAffiches < liste.length) {
        indicesVusZone.appendChild(creer("li", "", MS.echapper(liste[indicesAffiches])));
        indicesAffiches += 1;
      }
    }

    async function valider() {
      const reponse = lireReponse();
      if (reponse === null || reponse === "") return;
      boutonValider.disabled = true; boutonIndice.disabled = true;
      try {
        const r = await MS.api(`/api/eleve/cours/sessions/${encodeURIComponent(etat.session)}/blocs/${bloc.index}/tentative`, MS.json({ reponse }));
        retour.classList.remove("cache");
        retour.classList.toggle("juste", r.juste === true);
        retour.classList.toggle("faux", r.juste === false);
        retour.textContent = r.juste === true ? "✅ Bonne réponse !" : r.juste === false ? "❌ Ce n'est pas ça, réessaie." : "";
        if (r.explication) { explication.innerHTML = MS.markdown(r.explication); explication.classList.remove("cache"); }
        if (r.jules) ajouterMessageJules(r.jules);
        actualiserProgression(r.progression);
      } catch (err) {
        retour.classList.remove("cache"); retour.classList.add("faux");
        retour.textContent = `Petit souci : ${err.message}. Réessaie.`;
      } finally {
        const verrouille = etat.progression.blocs[bloc.index].etat !== "a_faire" && etat.progression.blocs[bloc.index].etat !== "en_cours";
        boutonValider.disabled = verrouille;
        boutonIndice.disabled = verrouille || indicesAffiches >= totalIndices;
        if (!verrouille) { boutonValider.disabled = false; if (champPrincipal && champPrincipal.focus) champPrincipal.focus(); }
      }
    }

    async function demanderIndice() {
      boutonIndice.disabled = true;
      try {
        const r = await MS.api(`/api/eleve/cours/sessions/${encodeURIComponent(etat.session)}/blocs/${bloc.index}/indice`, { method: "POST" });
        if (r.indice) { indicesVusZone.appendChild(creer("li", "", MS.echapper(r.indice))); indicesAffiches += 1; }
        boutonIndice.textContent = r.restants > 0 ? `Un indice (${r.restants} restant${r.restants > 1 ? "s" : ""})` : "Plus d'indice";
        boutonIndice.disabled = r.restants <= 0;
        actualiserProgression(r.progression);
      } catch (err) {
        indicesVusZone.appendChild(creer("li", "cours-erreur-ligne", MS.echapper(`Impossible d'avoir un indice : ${err.message}`)));
        boutonIndice.disabled = false;
      }
    }

    boutonValider.addEventListener("click", valider);
    boutonIndice.addEventListener("click", demanderIndice);

    const maj = (etatBloc, progressionBloc) => {
      afficherIndicesJusqua(progressionBloc.indices_vus || 0);
      const restants = totalIndices - (progressionBloc.indices_vus || 0);
      if (totalIndices) boutonIndice.textContent = restants > 0 ? `Un indice (${restants} restant${restants > 1 ? "s" : ""})` : "Plus d'indice";
      const verrouille = etatBloc === "reussi" || etatBloc === "a_revoir";
      boutonValider.disabled = verrouille;
      boutonIndice.disabled = verrouille || restants <= 0;
      if (champPrincipal) {
        if (champPrincipal.querySelectorAll) champPrincipal.querySelectorAll("input").forEach((i) => { i.disabled = verrouille; });
        else champPrincipal.disabled = verrouille;
      }
    };
    return { dom, maj };
  }

  // --- bloc question_ouverte / synthese --------------------------------------
  function construireLibre(bloc) {
    const dom = creer("div");
    const consigne = bloc.type === "synthese" ? bloc.consigne : bloc.question;
    dom.appendChild(creer("p", "bloc-enonce", MS.echapper(consigne || "")));

    const labelId = `libre-${bloc.index}`;
    const label = creer("label", "cache-visuel", "Ta réponse");
    label.htmlFor = labelId;
    dom.appendChild(label);
    const zone = document.createElement("textarea");
    zone.className = "zone-libre";
    zone.id = labelId;
    zone.placeholder = "Écris ton idée, même incomplète.";
    dom.appendChild(zone);

    const indicesVusZone = creer("ul", "indices-vus");
    dom.appendChild(indicesVusZone);
    const totalIndices = (bloc.indices || []).length;

    const actions = creer("div", "bloc-actions");
    const boutonEnvoyer = creer("button", "bouton", "Envoyer à Jules");
    boutonEnvoyer.type = "button";
    const boutonIndice = creer("button", "bouton secondaire", "Un indice");
    boutonIndice.type = "button";
    actions.appendChild(boutonEnvoyer);
    if (totalIndices) actions.appendChild(boutonIndice);
    dom.appendChild(actions);

    const retour = creer("div", "retour-tentative cache");
    retour.setAttribute("aria-live", "polite");
    dom.appendChild(retour);

    let indicesAffiches = 0;
    function afficherIndicesJusqua(n) {
      const liste = bloc.indices || [];
      while (indicesAffiches < n && indicesAffiches < liste.length) {
        indicesVusZone.appendChild(creer("li", "", MS.echapper(liste[indicesAffiches])));
        indicesAffiches += 1;
      }
    }

    async function envoyer() {
      const reponse = zone.value.trim();
      if (!reponse) return;
      boutonEnvoyer.disabled = true;
      retour.classList.remove("cache", "juste", "faux");
      retour.textContent = "Jules relit ta réponse…";
      try {
        const r = await MS.api(`/api/eleve/cours/sessions/${encodeURIComponent(etat.session)}/blocs/${bloc.index}/tentative`, MS.json({ reponse }));
        retour.textContent = "Envoyé : regarde la réponse de Jules à droite →";
        if (r.jules) ajouterMessageJules(r.jules);
        actualiserProgression(r.progression);
      } catch (err) {
        retour.classList.add("faux");
        retour.textContent = `Petit souci : ${err.message}. Réessaie.`;
        boutonEnvoyer.disabled = false;
      }
    }

    async function demanderIndice() {
      boutonIndice.disabled = true;
      try {
        const r = await MS.api(`/api/eleve/cours/sessions/${encodeURIComponent(etat.session)}/blocs/${bloc.index}/indice`, { method: "POST" });
        if (r.indice) { indicesVusZone.appendChild(creer("li", "", MS.echapper(r.indice))); indicesAffiches += 1; }
        boutonIndice.textContent = r.restants > 0 ? `Un indice (${r.restants} restant${r.restants > 1 ? "s" : ""})` : "Plus d'indice";
        boutonIndice.disabled = r.restants <= 0;
        actualiserProgression(r.progression);
      } catch (err) {
        indicesVusZone.appendChild(creer("li", "cours-erreur-ligne", MS.echapper(`Impossible d'avoir un indice : ${err.message}`)));
        boutonIndice.disabled = false;
      }
    }

    boutonEnvoyer.addEventListener("click", envoyer);
    boutonIndice.addEventListener("click", demanderIndice);
    zone.addEventListener("keydown", (ev) => { if (ev.key === "Enter" && (ev.ctrlKey || ev.metaKey)) { ev.preventDefault(); envoyer(); } });

    const maj = (etatBloc, progressionBloc) => {
      afficherIndicesJusqua(progressionBloc.indices_vus || 0);
      const restants = totalIndices - (progressionBloc.indices_vus || 0);
      if (totalIndices) boutonIndice.textContent = restants > 0 ? `Un indice (${restants} restant${restants > 1 ? "s" : ""})` : "Plus d'indice";
      const verrouille = etatBloc === "fait";
      boutonEnvoyer.disabled = verrouille;
      boutonIndice.disabled = verrouille || restants <= 0;
      zone.disabled = verrouille;
      if (verrouille) retour.classList.remove("cache");
    };
    return { dom, maj };
  }

  // --- blocs sans tentative : "J'ai lu" ---------------------------------------
  async function faireBloc(index, bouton) {
    bouton.disabled = true;
    try {
      const r = await MS.api(`/api/eleve/cours/sessions/${encodeURIComponent(etat.session)}/blocs/${index}/fait`, { method: "POST" });
      actualiserProgression(r.progression);
    } catch (err) {
      bouton.disabled = false;
      alert(`Petit souci : ${err.message}. Réessaie.`); // eslint-disable-line no-alert
    }
  }

  // --- panneau Jules -----------------------------------------------------------
  function ajouterBulleJules(role, texte, classe = "") {
    const ligne = creer("div", `ligne ${role === "eleve" ? "eleve" : "bot"} ${classe}`);
    const bulle = creer("div", "bulle");
    bulle.innerHTML = role === "eleve" ? `<p>${MS.echapper(texte).replace(/\n/g, "<br>")}</p>` : MS.markdown(texte);
    if (role !== "eleve") {
      const av = document.createElement("img");
      av.className = "av"; av.src = "/api/persona/avatar"; av.alt = "";
      ligne.appendChild(av);
    }
    ligne.appendChild(bulle);
    $("jules-fil").appendChild(ligne);
    $("jules-fil").scrollTop = $("jules-fil").scrollHeight;
    return ligne;
  }

  function ajouterMessageJules(texte) {
    ajouterBulleJules("bot", texte);
  }

  async function chargerConversation() {
    $("jules-fil").innerHTML = "";
    $("jules-texte").disabled = false;
    $("jules-envoyer").disabled = false;
    if (!etat.conversation) return;
    try {
      const conv = await MS.api(`/api/conversations/${encodeURIComponent(etat.conversation)}`);
      for (const m of conv.messages) ajouterBulleJules(m.role, m.texte);
    } catch (err) {
      ajouterBulleJules("bot", `Impossible de charger la conversation : ${err.message}`);
    }
  }

  async function envoyerAJules(ev) {
    ev.preventDefault();
    if (etat.julesOccupe || !etat.conversation) return;
    const texte = $("jules-texte").value.trim();
    if (!texte) return;
    etat.julesOccupe = true;
    $("jules-envoyer").disabled = true;
    $("jules-texte").disabled = true;
    ajouterBulleJules("eleve", texte);
    $("jules-texte").value = "";
    const attente = ajouterBulleJules("bot", "Jules réfléchit…", "attente");
    const donnees = new FormData();
    donnees.append("texte", texte);
    try {
      const r = await MS.api(`/api/conversations/${encodeURIComponent(etat.conversation)}/messages`, { method: "POST", body: donnees });
      attente.remove();
      ajouterBulleJules("bot", r.reponse);
    } catch (err) {
      attente.remove();
      ajouterBulleJules("bot", `Petit souci : ${err.message}. Réessaie.`);
    } finally {
      etat.julesOccupe = false;
      $("jules-envoyer").disabled = false;
      $("jules-texte").disabled = false;
      $("jules-texte").focus();
    }
  }

  // --- panneaux repliables (tablette) ------------------------------------------
  function ouvrirPanneau(nom) {
    $(nom).classList.add("ouvert");
    $(`menu-${nom === "panneau-jules" ? "jules" : "parcours"}`).setAttribute("aria-expanded", "true");
  }
  function fermerPanneau(nom) {
    const id = nom === "jules" ? "panneau-jules" : "parcours";
    $(id).classList.remove("ouvert");
    $(`menu-${nom}`).setAttribute("aria-expanded", "false");
  }

  // --- retour au parcours -------------------------------------------------------
  function retourAuParcours() {
    etat.session = null; etat.conversation = null; etat.lecon = null; etat.progression = null;
    $("lecon").classList.add("cache");
    $("lecon-vide").classList.remove("cache");
    $("jules-fil").innerHTML = "";
    $("jules-texte").disabled = true;
    $("jules-envoyer").disabled = true;
    marquerNotionActive();
    chargerParcours(etat.matiereChoisie);
  }

  // --- demarrage -----------------------------------------------------------
  async function demarrage() {
    await MS.porte("eleve", { porte: $("porte"), contenu: $("contenu"), formulaire: $("porte-form"), champ: $("porte-code"), erreur: $("porte-erreur") });
    etat.infos = await MS.api("/api/infos");
    MS.appliquerCouleurs(etat.infos.persona.couleurs);
    document.title = `${etat.infos.persona.nom} - cours`;
    $("nom-persona").textContent = etat.infos.persona.nom;
    $("jules-nom").textContent = etat.infos.persona.nom;

    $("select-matiere").addEventListener("change", (ev) => chargerParcours(ev.target.value));
    $("menu-parcours").addEventListener("click", () => {
      const ouvert = $("parcours").classList.contains("ouvert");
      if (ouvert) fermerPanneau("parcours"); else ouvrirPanneau("parcours");
    });
    $("menu-jules").addEventListener("click", () => {
      const ouvert = $("panneau-jules").classList.contains("ouvert");
      if (ouvert) fermerPanneau("jules"); else ouvrirPanneau("panneau-jules");
    });
    $("parcours-fermer").addEventListener("click", () => fermerPanneau("parcours"));
    $("jules-fermer").addEventListener("click", () => fermerPanneau("jules"));
    $("retour-parcours").addEventListener("click", retourAuParcours);

    $("jules-formulaire").addEventListener("submit", envoyerAJules);
    $("jules-texte").addEventListener("input", () => {
      const t = $("jules-texte");
      t.style.height = "auto";
      t.style.height = Math.min(t.scrollHeight, 140) + "px";
    });
    $("jules-texte").addEventListener("keydown", (ev) => {
      if (ev.key === "Enter" && !ev.shiftKey && window.matchMedia("(pointer: fine)").matches) envoyerAJules(ev);
    });

    await chargerParcours(null);
  }

  demarrage().catch((err) => { document.body.innerHTML = `<p class="erreur-page">Erreur : ${MS.echapper(err.message)}</p>`; });
})();
