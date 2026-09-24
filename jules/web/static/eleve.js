// Page eleve : choix du mode, conversation, photos.
"use strict";

(() => {
  const $ = (id) => document.getElementById(id);
  const etat = { infos: null, conv: null, photos: [], occupe: false };

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

  function ecranAccueil() {
    etat.conv = null;
    $("titre").textContent = "Nouvelle discussion";
    $("pastille-mode").classList.add("cache");
    $("saisie").classList.add("cache");
    const fil = $("fil");
    fil.innerHTML = "";
    const accueil = document.createElement("div");
    accueil.className = "accueil";
    accueil.innerHTML = `<img src="/api/persona/avatar" alt=""><p>${MS.echapper(etat.infos.persona.accueil)}</p>`;
    fil.appendChild(accueil);
    const grille = document.createElement("div");
    grille.className = "modes";
    for (const mode of etat.infos.modes || []) {
      const b = document.createElement("button");
      b.innerHTML = `<span class="icone">${MS.echapper(mode.icone)}</span><strong>${MS.echapper(mode.nom)}</strong><small>${MS.echapper(mode.description)}</small>`;
      b.addEventListener("click", () => demarrer(mode.id));
      grille.appendChild(b);
    }
    fil.appendChild(grille);
    marquerActif(null);
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
    marquerActif(id);
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
      chargerHistorique();
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
    ecranAccueil();
    chargerHistorique();
  }

  demarrage().catch((err) => { document.body.innerHTML = `<p class="erreur-page">Erreur : ${MS.echapper(err.message)}</p>`; });
})();
