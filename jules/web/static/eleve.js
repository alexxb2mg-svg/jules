// Page eleve : choix du mode, conversation, photos.
"use strict";

(() => {
  const $ = (id) => document.getElementById(id);
  const etat = { infos: null, conv: null, photos: [], occupe: false, notion: null };

  // Reduit une photo de telephone (souvent 4000 px) a 1600 px max en JPEG : envoi plus rapide.
  function reduire(fichier) {
    return new Promise((resoudre) => {
      const img = new Image();
      img.onload = () => {
        const echelle = Math.min(1, 1600 / Math.max(img.width, img.height));
        const toile = document.createElement("canvas");
        toile.width = Math.round(img.width * echelle);
        toile.height = Math.round(img.height * echelle);
        toile.getContext("2d").drawImage(img, 0, 0, toile.width, toile.height);
        toile.toBlob((blob) => resoudre(blob || fichier), "image/jpeg", 0.85);
        URL.revokeObjectURL(img.src);
      };
      img.onerror = () => resoudre(fichier);
      img.src = URL.createObjectURL(fichier);
    });
  }

  function ajouterBulle(role, texte, images = [], classe = "") {
    const ligne = document.createElement("div");
    ligne.className = `ligne ${role === "eleve" ? "eleve" : "bot"} ${classe}`;
    const bulle = document.createElement("div");
    bulle.className = "bulle";
    let html = images.map((src) => `<img class="photo" src="${MS.echapper(src)}" alt="photo">`).join("");
    html += role === "eleve" ? `<p>${MS.echapper(texte).replace(/\n/g, "<br>")}</p>` : MS.markdown(texte);
    bulle.innerHTML = html;
    if (role !== "eleve") {
      const av = document.createElement("img");
      av.className = "av"; av.src = "/api/persona/avatar"; av.alt = "";
      ligne.appendChild(av);
    }
    ligne.appendChild(bulle);
    $("fil").appendChild(ligne);
    $("fil").scrollTop = $("fil").scrollHeight;
    return ligne;
  }

  // --- notion travaillee (module "notions", facultatif) ---------------------
  const catalogueNotions = () => (etat.infos && etat.infos.notions) || null;

  function afficherNotion(notion) {
    etat.notion = notion;
    const b = $("pastille-notion");
    if (!catalogueNotions() || !etat.conv || etat.conv.mode === "epreuve" || etat.conv.mode === "exercice") { b.classList.add("cache"); return; }
    b.classList.remove("cache");
    b.classList.toggle("choisie", Boolean(notion));
    b.textContent = notion ? `📚 ${notion.titre}` : "📚 Choisir une notion";
    b.title = notion
      ? `${notion.matiere} : ${notion.titre}${notion.origine === "auto" ? " (reconnue par Jules, touche pour changer)" : ""}`
      : "Choisir la notion travaillée";
  }

  async function chargerNotion() {
    if (!catalogueNotions() || !etat.conv) { afficherNotion(null); return; }
    try {
      const r = await MS.api(`/api/eleve/notions/conversations/${encodeURIComponent(etat.conv.id)}`);
      afficherNotion(r.notion);
    } catch (_) { afficherNotion(null); }
  }

  function remplirChoix(filtre = "") {
    const cat = catalogueNotions();
    const zone = $("choix-liste");
    zone.innerHTML = "";
    const cherche = MS.sansAccents(filtre.trim());
    for (const matiere of cat.matieres) {
      const notions = matiere.notions.filter((n) => !cherche || MS.sansAccents(`${n.titre} ${n.chapitre} ${matiere.nom}`).includes(cherche));
      if (!notions.length) continue;
      const bloc = document.createElement("details");
      bloc.open = Boolean(cherche);
      bloc.innerHTML = `<summary>${MS.echapper(matiere.nom)}</summary>`;
      for (const n of notions) {
        const b = document.createElement("button");
        b.type = "button";
        b.innerHTML = `${MS.echapper(n.titre)}${n.fiche ? '<span class="marque-fiche">fiche</span>' : ""}<small>${MS.echapper(n.chapitre)}</small>`;
        b.addEventListener("click", () => choisirNotion(n.id));
        bloc.appendChild(b);
      }
      zone.appendChild(bloc);
    }
    if (!zone.children.length) zone.innerHTML = '<p class="avertissement">Aucune notion trouvée.</p>';
  }

  function ouvrirChoix() {
    const cat = catalogueNotions();
    if (!cat || !etat.conv) return;
    const avertissements = cat.bibliotheques.filter((b) => b.avertissement).map((b) => `${b.titre} : ${b.avertissement}`);
    $("choix-avertissement").textContent = avertissements.join(" ");
    $("choix-recherche").value = "";
    remplirChoix();
    $("choix-retirer").classList.toggle("cache", !etat.notion);
    $("choix-notion").classList.remove("cache");
    $("choix-recherche").focus();
  }

  const fermerChoix = () => $("choix-notion").classList.add("cache");

  async function choisirNotion(id) {
    const r = await MS.api(`/api/eleve/notions/conversations/${encodeURIComponent(etat.conv.id)}`, MS.json({ notion: id }, "PUT"));
    afficherNotion(r.notion);
    fermerChoix();
  }

  async function retirerNotion() {
    await MS.api(`/api/eleve/notions/conversations/${encodeURIComponent(etat.conv.id)}`, { method: "DELETE" });
    afficherNotion(null);
    fermerChoix();
  }

  function ecranAccueil() {
    etat.conv = null;
    $("titre").textContent = "Nouvelle discussion";
    $("pastille-mode").classList.add("cache");
    $("saisie").classList.add("cache");
    afficherNotion(null);
    const fil = $("fil");
    fil.innerHTML = "";
    const accueil = document.createElement("div");
    accueil.className = "accueil";
    accueil.innerHTML = `<img src="/api/persona/avatar" alt=""><p>${MS.echapper(etat.infos.persona.accueil)}</p>`;
    fil.appendChild(accueil);
    const grille = document.createElement("div");
    grille.className = "modes";
    for (const mode of (etat.infos.modes || []).filter((m) => !m.cache)) {
      const b = document.createElement("button");
      b.innerHTML = `<span class="icone">${MS.echapper(mode.icone)}</span><strong>${MS.echapper(mode.nom)}</strong><small>${MS.echapper(mode.description)}</small>`;
      b.addEventListener("click", () => demarrer(mode.id));
      grille.appendChild(b);
    }
    fil.appendChild(grille);
    if (etat.infos.cours) {
      const lienCours = document.createElement("a");
      lienCours.className = "bouton secondaire espace-haut";
      lienCours.href = "/cours";
      lienCours.textContent = "📘 Suivre un cours";
      fil.appendChild(lienCours);
    }
    if (etat.infos.studio) {
      const lienStudio = document.createElement("a");
      lienStudio.className = "bouton secondaire espace-haut";
      lienStudio.href = "/studio";
      lienStudio.textContent = "🛠️ Mon studio";
      fil.appendChild(lienStudio);
    }
    proposerEpreuve(fil);
    proposerExercices(fil);
    marquerActif(null);
  }

  // --- epreuve sans aide (module "epreuve", facultatif) ---------------------
  async function proposerEpreuve(fil) {
    if (!etat.infos.epreuve) return;
    let notions = [];
    try { notions = (await MS.api("/api/eleve/epreuve/proposition")).notions; } catch (_) { return; }
    if (!notions.length || etat.conv) return;
    const encart = document.createElement("div");
    encart.className = "encart-epreuve";
    const liste = notions.map((n) => MS.echapper(n.notion)).join(", ");
    encart.innerHTML = `<p><strong>🧭 Épreuve sans aide</strong> : il y a quelques jours, tu avais compris ${liste}. Est-ce que ça a tenu ?</p>`;
    const b = document.createElement("button");
    b.className = "bouton";
    b.textContent = "Faire l'épreuve";
    b.addEventListener("click", commencerEpreuve);
    encart.appendChild(b);
    fil.appendChild(encart);
  }

  async function commencerEpreuve() {
    const conv = await MS.api("/api/eleve/epreuve/commencer", { method: "POST" });
    etat.conv = { id: conv.id, mode: conv.mode, titre: conv.titre };
    $("fil").innerHTML = "";
    $("titre").textContent = conv.titre;
    $("pastille-mode").textContent = nomMode(conv.mode);
    $("pastille-mode").classList.remove("cache");
    $("saisie").classList.remove("cache");
    afficherNotion(null);
    ajouterBulle("bot", conv.presentation);
    $("texte").focus();
    fermerCote();
  }

  const epreuveFinie = (texte) => /preuve terminée/i.test(texte || "");
  function fermerSiEpreuveFinie(texte) {
    if (etat.conv && etat.conv.mode === "epreuve" && epreuveFinie(texte)) $("saisie").classList.add("cache");
  }

  // --- exercices sans IA (module "exercices", facultatif) --------------------
  function proposerExercices(fil) {
    const notions = (etat.infos.exercices || []);
    if (!notions.length || etat.conv) return;
    const encart = document.createElement("div");
    encart.className = "encart-epreuve";
    encart.innerHTML = `<p><strong>📝 S'entraîner sans IA</strong> : des exercices corrigés tout de suite, avec un indice si tu bloques.</p>`;
    for (const n of notions) {
      const b = document.createElement("button");
      b.className = "bouton secondaire";
      b.textContent = `${n.titre} (${n.nb})`;
      b.addEventListener("click", () => commencerExercice(n.id));
      encart.appendChild(b);
    }
    fil.appendChild(encart);
  }

  async function commencerExercice(notionId) {
    const r = await MS.api(`/api/eleve/exercices/${encodeURIComponent(notionId)}/commencer`, { method: "POST" });
    await ouvrir(r.conversation);
  }

  function nomMode(id) {
    const mode = (etat.infos.modes || []).find((m) => m.id === id);
    return mode ? `${mode.icone} ${mode.nom}` : id;
  }

  async function demarrer(mode) {
    const conv = await MS.api("/api/conversations", MS.json({ mode }));
    etat.conv = { id: conv.id, mode: conv.mode, titre: "" };
    $("fil").innerHTML = "";
    $("titre").textContent = nomMode(conv.mode);
    $("pastille-mode").textContent = nomMode(conv.mode);
    $("pastille-mode").classList.remove("cache");
    $("saisie").classList.remove("cache");
    afficherNotion(null);
    ajouterBulle("bot", `C'est parti, ${etat.infos.prenom} ! Envoie-moi ton message ou une photo de ton exercice.`);
    $("texte").focus();
    fermerCote();
  }

  async function ouvrir(id) {
    const conv = await MS.api(`/api/conversations/${encodeURIComponent(id)}`);
    etat.conv = conv;
    $("fil").innerHTML = "";
    $("titre").textContent = conv.titre || nomMode(conv.mode);
    $("pastille-mode").textContent = nomMode(conv.mode);
    $("pastille-mode").classList.remove("cache");
    $("saisie").classList.remove("cache");
    for (const m of conv.messages) {
      ajouterBulle(m.role, m.texte, m.images.map((n) => `/api/images/${encodeURIComponent(n)}`));
    }
    const dernier = conv.messages[conv.messages.length - 1];
    if (dernier && dernier.role !== "eleve") fermerSiEpreuveFinie(dernier.texte);
    marquerActif(id);
    chargerNotion();
    fermerCote();
  }

  function marquerActif(id) {
    for (const b of $("historique").querySelectorAll("button")) b.classList.toggle("actif", b.dataset.id === id);
  }

  async function chargerHistorique() {
    const liste = await MS.api("/api/conversations");
    const zone = $("historique");
    zone.innerHTML = "";
    for (const c of liste.filter((c) => c.nb > 0)) {
      const b = document.createElement("button");
      b.dataset.id = c.id;
      b.innerHTML = `${MS.echapper(c.titre || nomMode(c.mode))}<small>${MS.echapper(MS.heure(c.dernier || c.debut))}</small>`;
      b.addEventListener("click", () => ouvrir(c.id));
      zone.appendChild(b);
    }
    if (etat.conv) marquerActif(etat.conv.id);
  }

  function afficherApercus() {
    const zone = $("apercus");
    zone.innerHTML = "";
    etat.photos.forEach((p, i) => {
      const img = document.createElement("img");
      img.src = p.url; img.title = "Retirer";
      img.addEventListener("click", () => { URL.revokeObjectURL(p.url); etat.photos.splice(i, 1); afficherApercus(); });
      zone.appendChild(img);
    });
  }

  async function envoyer(ev) {
    ev.preventDefault();
    if (etat.occupe || !etat.conv) return;
    const texte = $("texte").value.trim();
    if (!texte && !etat.photos.length) return;
    etat.occupe = true;
    $("bouton-envoyer").disabled = true;
    const donnees = new FormData();
    donnees.append("texte", texte);
    etat.photos.forEach((p, i) => donnees.append("photos", p.blob, `photo${i}.jpg`));
    ajouterBulle("eleve", texte, etat.photos.map((p) => p.url));
    $("texte").value = ""; ajusterHauteur();
    etat.photos = []; afficherApercus();
    const attente = ajouterBulle("bot", "Jules réfléchit…", [], "attente");
    try {
      const r = await MS.api(`/api/conversations/${encodeURIComponent(etat.conv.id)}/messages`, { method: "POST", body: donnees });
      attente.remove();
      ajouterBulle("bot", r.reponse);
      fermerSiEpreuveFinie(r.reponse);
      chargerHistorique();
      if (!etat.notion) chargerNotion();
    } catch (err) {
      attente.remove();
      if (err.code === 401) { location.reload(); return; }
      ajouterBulle("bot", `Petit souci : ${err.message}. Réessaie.`);
    } finally {
      etat.occupe = false;
      $("bouton-envoyer").disabled = false;
      $("texte").focus();
    }
  }

  function ajusterHauteur() {
    const t = $("texte");
    t.style.height = "auto";
    t.style.height = Math.min(t.scrollHeight, 160) + "px";
  }
  const fermerCote = () => $("cote").classList.remove("ouvert");

  async function demarrage() {
    await MS.porte("eleve", { porte: $("porte"), contenu: $("contenu"), formulaire: $("porte-form"), champ: $("porte-code"), erreur: $("porte-erreur") });
    MS.signalerFinDeSeance();
    etat.infos = await MS.api("/api/infos");
    MS.appliquerCouleurs(etat.infos.persona.couleurs);
    document.title = etat.infos.persona.nom;
    $("nom-persona").textContent = etat.infos.persona.nom;
    $("nouvelle").addEventListener("click", ecranAccueil);
    $("menu-cote").addEventListener("click", () => $("cote").classList.toggle("ouvert"));
    $("formulaire").addEventListener("submit", envoyer);
    $("texte").addEventListener("input", ajusterHauteur);
    $("texte").addEventListener("keydown", (ev) => {
      if (ev.key === "Enter" && !ev.shiftKey && window.matchMedia("(pointer: fine)").matches) envoyer(ev);
    });
    $("bouton-photo").addEventListener("click", () => $("fichier").click());
    $("fichier").addEventListener("change", async () => {
      for (const f of Array.from($("fichier").files).slice(0, 3 - etat.photos.length)) {
        const blob = await reduire(f);
        etat.photos.push({ blob, url: URL.createObjectURL(blob) });
      }
      $("fichier").value = "";
      afficherApercus();
    });
    $("pastille-notion").addEventListener("click", ouvrirChoix);
    $("choix-fermer").addEventListener("click", fermerChoix);
    $("choix-retirer").addEventListener("click", retirerNotion);
    $("choix-recherche").addEventListener("input", (ev) => remplirChoix(ev.target.value));
    $("choix-notion").addEventListener("click", (ev) => { if (ev.target === $("choix-notion")) fermerChoix(); });
    document.addEventListener("keydown", (ev) => { if (ev.key === "Escape") fermerChoix(); });
    ecranAccueil();
    chargerHistorique();
    // Arrivee depuis « Mes fiches » avec ?notion=... : ouvre une discussion deja rattachee a la notion.
    const notionDemandee = new URLSearchParams(location.search).get("notion");
    if (notionDemandee) {
      await demarrer("aide-devoirs");
      try { await choisirNotion(notionDemandee); } catch (_) { /* notion inconnue : on continue sans */ }
    }
  }

  demarrage().catch((err) => { document.body.innerHTML = `<p class="erreur-page">Erreur : ${MS.echapper(err.message)}</p>`; });
})();
