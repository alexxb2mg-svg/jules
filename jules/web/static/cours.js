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
    outils: [],           // outils montes dans la lecon (OutilsHote.monter), demontes a la sortie
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

  // Consigne d'un bloc (enonce, question) : bouton de lecture selon le levier, jamais lue sans clic
  // (EX-109).
  function enonce(html) {
    const p = creer("p", "bloc-enonce", html);
    LectureVocale.equiperConsigne(p);
    return p;
  }

  // --- parcours (zone centrale, tant qu'aucune lecon n'est ouverte) ------------------------------------
  // EX-209 : la matiere vient de l'adresse (?matiere=, lien de la barre), sinon de la memoire `jules.matiere`.
  // Un seul appel parcours ; la page affiche la matiere renvoyee par le serveur et n'ecrase pas la memoire.
  // Premiere visite (ni adresse ni memoire) : « Choisis une matière », sans les notions de la matiere par defaut.
  async function chargerParcours(matiere, notionDemandee) {
    etat.occupeParcours = true;
    $("parcours-attente").classList.remove("cache");
    try {
      const r = await MS.api(MS.cheminMatiere("/api/eleve/cours/parcours", matiere));
      etat.matieres = r.matieres || [];
      if (!matiere) {
        afficherChoixMatiere();
        return;
      }
      etat.matiereChoisie = r.matiere;
      $("choix-matiere").classList.add("cache");
      $("parcours").classList.remove("cache");
      const nom = (etat.matieres.find((m) => m.id === r.matiere) || { nom: r.matiere }).nom;
      $("catalogue-titre").textContent = `Mes leçons : ${nom}`;
      $("parcours-estimation").textContent = r.estimation || "";
      afficherNotions(r.notions || []);
      // Une notion demandee par l'adresse s'ouvre si elle est une lecon de la matiere ; sinon la liste reste.
      const n = notionDemandee && (r.notions || []).find((x) => x.id === notionDemandee && x.lecon);
      if (n) {
        etat.occupeParcours = false;
        await ouvrirLecon(n.id);
      }
    } catch (err) {
      $("parcours").classList.remove("cache");
      $("parcours-liste").innerHTML = "";
      $("parcours-liste").appendChild(creer("p", "cours-erreur-ligne", MS.echapper(`Impossible de charger ton parcours : ${err.message}`)));
    } finally {
      etat.occupeParcours = false;
      $("parcours-attente").classList.add("cache");
    }
  }

  // Premiere visite : la liste des matieres de la reponse, un bouton par matiere (meme action que l'etape 2 de la
  // barre : matiere retenue, puis ses notions).
  function afficherChoixMatiere() {
    $("parcours").classList.add("cache");
    $("catalogue-titre").textContent = "Mes leçons";
    const liste = $("choix-matiere-liste");
    liste.replaceChildren();
    for (const m of etat.matieres) {
      const li = document.createElement("li");
      const b = document.createElement("button");
      b.type = "button";
      b.className = "choix-matiere-bouton";
      b.dataset.matiere = m.id;
      b.textContent = m.nom;
      b.addEventListener("click", () => choisirMatiere(m.id));
      li.appendChild(b);
      liste.appendChild(li);
    }
    $("choix-matiere").classList.remove("cache");
  }

  async function choisirMatiere(id) {
    MS.retenirMatiere(id);
    Navigation.suivreMatiere(id);
    await chargerParcours(id, null);
    $("catalogue-titre").focus();
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
      $("catalogue").classList.add("cache");
      $("lecon").classList.remove("cache");
      afficherLecon();
      marquerNotionActive();
      await chargerConversation();
    } catch (err) {
      $("catalogue").classList.remove("cache");
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
    demonterOutils();
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
        corps.appendChild(enonce(MS.markdown(bloc.enonce || "")));
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
        corps.appendChild(construireOutil(bloc));
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

  // --- bloc outil (docs/OUTILS-CONTRAT.md) ------------------------------------
  // L'outil s'ouvre dans une iframe isolee creee par outils-hote.js, qui ne laisse passer que les
  // messages venant de CETTE iframe et declares dans la fiche de l'outil.
  function construireOutil(bloc) {
    const catalogue = (etat.infos && etat.infos.outils && etat.infos.outils.catalogue) || [];
    const outil = catalogue.find((o) => o.id === bloc.outil);
    if (!outil || typeof OutilsHote === "undefined") {
      return creer("p", "outil-a-venir", "🛠️ Cet outil arrivera bientôt dans Jules.");
    }
    const zone = creer("div", "outil-zone");
    etat.outils.push(OutilsHote.monter(zone, outil, { action: bloc.action, donnees: bloc.donnees, leviers: etat.leviers || {} }));
    return zone;
  }

  function demonterOutils() {
    for (const o of etat.outils) o.demonter();
    etat.outils = [];
  }

  // --- bloc exercice --------------------------------------------------------
  function construireExercice(bloc) {
    const dom = creer("div");
    dom.appendChild(enonce(MS.echapper(bloc.enonce || "")));

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
    dom.appendChild(enonce(MS.echapper(consigne || "")));

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
  function ajouterBulleJules(role, texte, classe = "", nouvelle = true) {
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
    // Bouton de lecture sur les bulles de Jules seulement ; lue en mode automatique si nouvelle (EX-109).
    if (role !== "eleve" && classe !== "attente") LectureVocale.equiperBulle(bulle, { nouvelle });
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
      for (const m of conv.messages) ajouterBulleJules(m.role, m.texte, "", false);
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

  // --- panneau de Jules repliable (tablette) -------------------------------------
  function ouvrirPanneau() {
    $("panneau-jules").classList.add("ouvert");
    $("menu-jules").setAttribute("aria-expanded", "true");
  }
  function fermerPanneau() {
    $("panneau-jules").classList.remove("ouvert");
    $("menu-jules").setAttribute("aria-expanded", "false");
  }

  // --- retour au parcours -------------------------------------------------------
  function retourAuParcours() {
    etat.session = null; etat.conversation = null; etat.lecon = null; etat.progression = null;
    demonterOutils();
    $("lecon").classList.add("cache");
    $("catalogue").classList.remove("cache");
    $("jules-fil").innerHTML = "";
    $("jules-texte").disabled = true;
    $("jules-envoyer").disabled = true;
    marquerNotionActive();
    chargerParcours(etat.matiereChoisie, null);
  }

  // --- demarrage -----------------------------------------------------------
  async function demarrage() {
    const session = await MS.porte("eleve", { porte: $("porte"), contenu: $("contenu"), formulaire: $("porte-form"), champ: $("porte-code"), erreur: $("porte-erreur") });
    etat.infos = await MS.api("/api/infos");
    Navigation.monter(session, etat.infos);  // barre commune ; elle fixe aussi le titre d'onglet (EX-211)
    MS.appliquerCouleurs(etat.infos.persona.couleurs);
    etat.leviers = MS.appliquerLeviers(etat.infos);
    $("nom-persona").textContent = etat.infos.persona.nom;
    $("jules-nom").textContent = etat.infos.persona.nom;
    LectureVocale.initialiser();
    LectureVocale.definirMode(LectureVocale.modeDepuis(etat.infos));
    LectureVocale.brancherSaisie(document); // chat et reponses aux exercices

    $("menu-jules").addEventListener("click", () => {
      if ($("panneau-jules").classList.contains("ouvert")) fermerPanneau(); else ouvrirPanneau();
    });
    $("jules-fermer").addEventListener("click", fermerPanneau);
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

    await chargerParcours(...matiereDeDepart());
  }

  // ?matiere=&notion= (lien de l'etape 4 de la barre), sinon la matiere retenue ; rien a la premiere visite.
  function matiereDeDepart() {
    const p = new URLSearchParams(location.search);
    const matiere = p.get("matiere");
    if (matiere) return [matiere, p.get("notion")];
    return [MS.matiereRetenue(), null];
  }

  demarrage().catch((err) => { document.body.innerHTML = `<p class="erreur-page">Erreur : ${MS.echapper(err.message)}</p>`; });
})();
