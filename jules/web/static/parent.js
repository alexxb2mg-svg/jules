// Page parent : rapport, signaux, notes, lecture des conversations, lecture vocale, export et effacement
// du dossier.
"use strict";

(() => {
  const $ = (id) => document.getElementById(id);
  let modules = [];
  const actif = (id) => modules.some((m) => m.id === id);
  const aujourdhui = () => new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 10);

  async function chargerRapport() {
    if (!actif("rapport")) { $("carte-rapport").classList.add("cache"); return; }
    $("rapport").textContent = "Calcul en cours (quelques secondes)…";
    try {
      const r = await MS.api(`/api/modules/rapport/jour?date=${$("jour").value}`);
      $("rapport").textContent = r.texte;
      $("rapport").classList.remove("muet");
    } catch (err) { $("rapport").textContent = `Erreur : ${err.message}`; }
  }

  async function chargerAlertes() {
    if (!actif("vigilance")) { $("carte-alertes").classList.add("cache"); return; }
    const liste = await MS.api("/api/parent/evenements/vigilance");
    const zone = $("alertes");
    if (!liste.length) { zone.textContent = "Aucun signal."; return; }
    zone.classList.remove("muet");
    zone.innerHTML = liste.slice(0, 30).map((ev) =>
      `<div class="alerte"><b>${MS.echapper(ev.donnees.niveau)}</b> - ${MS.echapper(MS.heure(ev.horodatage))} : ${MS.echapper(ev.donnees.motif)}</div>`
    ).join("");
  }

  async function chargerNotes() {
    if (!actif("memoire")) { $("carte-notes").classList.add("cache"); return; }
    const notes = await MS.api("/api/modules/memoire/notes");
    const zone = $("notes");
    zone.innerHTML = "";
    for (const n of notes) {
      const li = document.createElement("li");
      const fin = n.jusqu_au ? ` <span class="muet">(jusqu'au ${MS.echapper(n.jusqu_au)})</span>` : "";
      li.innerHTML = `<span>${MS.echapper(n.texte)}${fin}</span>`;
      const b = document.createElement("button");
      b.textContent = "Supprimer";
      b.addEventListener("click", async () => { await MS.api(`/api/modules/memoire/notes/${n.id}`, { method: "DELETE" }); chargerNotes(); });
      li.appendChild(b);
      zone.appendChild(li);
    }
    if (!notes.length) zone.innerHTML = '<li class="muet">Aucune info pour le moment.</li>';
  }

  // Retours (module 'retours') : bug, dysfonctionnement, suggestion, amelioration, avec la page d'origine.
  const TYPES_RETOUR = { bug: "Bug", dysfonctionnement: "Ça marche mal", suggestion: "Suggestion", amelioration: "Amélioration" };
  async function chargerRetours() {
    if (!actif("retours")) return;
    $("carte-retours").classList.remove("cache");
    const tous = $("retours-traites").checked;
    const liste = await MS.api(`/api/modules/retours/liste${tous ? "" : "?traite=false"}`);
    const zone = $("retours");
    zone.innerHTML = "";
    for (const r of liste) {
      const li = document.createElement("li");
      const quand = MS.echapper(MS.heure(r.cree_le));
      const qui = r.auteur ? ` <span class="muet">— ${MS.echapper(r.auteur)}</span>` : "";
      li.innerHTML = `<span><b>${MS.echapper(TYPES_RETOUR[r.type] || r.type)}</b>${qui}${r.traite ? " <span class=\"muet\">(traité)</span>" : ""} : `
        + `${MS.echapper(r.texte).replace(/\n/g, "<br>")}<br><span class="muet">${quand} · `
        + `<a href="${MS.echapper(r.adresse)}" target="_blank" rel="noopener">${MS.echapper(r.adresse)}</a>`
        + `${r.ecran ? ` · écran ${MS.echapper(r.ecran)}` : ""}</span></span>`;
      const traite = document.createElement("button");
      traite.textContent = r.traite ? "Rouvrir" : "Traité";
      traite.addEventListener("click", async () => { await MS.api(`/api/modules/retours/${r.id}`, MS.json({ traite: !r.traite }, "PATCH")); chargerRetours(); });
      const suppr = document.createElement("button");
      suppr.textContent = "Supprimer";
      suppr.addEventListener("click", async () => { await MS.api(`/api/modules/retours/${r.id}`, { method: "DELETE" }); chargerRetours(); });
      li.append(traite, suppr);
      zone.appendChild(li);
    }
    if (!liste.length) zone.innerHTML = '<li class="muet">Aucun retour en attente.</li>';
  }

  async function chargerConversations() {
    const liste = await MS.api(`/api/conversations?jour=${$("jour").value}`);
    const zone = $("conversations");
    zone.innerHTML = "";
    const pleines = liste.filter((c) => c.nb > 0);
    if (!pleines.length) { zone.textContent = "Aucune conversation ce jour-là."; return; }
    zone.classList.remove("muet");
    for (const c of pleines) {
      const bloc = document.createElement("details");
      bloc.className = "conv-parent";
      bloc.innerHTML = `<summary>${MS.echapper(c.titre || c.mode)} - ${MS.echapper(MS.heure(c.debut))} (${c.nb} messages)</summary>`;
      bloc.addEventListener("toggle", async () => {
        if (!bloc.open || bloc.dataset.charge) return;
        bloc.dataset.charge = "1";
        const conv = await MS.api(`/api/conversations/${c.id}`);
        for (const m of conv.messages) {
          const div = document.createElement("div");
          div.className = "msg";
          const qui = m.role === "eleve" ? "Élève" : "Bot";
          const photos = m.images.length ? ` [${m.images.length} photo(s)]` : "";
          div.innerHTML = `<b>${qui}${photos} :</b> ${MS.echapper(m.texte).replace(/\n/g, "<br>")}`;
          bloc.appendChild(div);
        }
        const effacer = document.createElement("button");
        effacer.className = "effacer-conv";
        effacer.textContent = "Effacer cette conversation";
        effacer.addEventListener("click", async () => {
          const titre = c.titre || c.mode;
          if (!window.confirm(`Effacer définitivement « ${titre} » (messages, photos et analyses) ? Impossible de revenir en arrière.`)) return;
          try {
            await MS.api(`/api/parent/conversations/${c.id}`, { method: "DELETE" });
            chargerConversations(); chargerRapport();
          } catch (err) { window.alert(`Erreur : ${err.message}`); }
        });
        bloc.appendChild(effacer);
      });
      zone.appendChild(bloc);
    }
  }

  function preparerEffacement() {
    const mot = $("effacer-mot");
    const bouton = $("effacer-tout");
    mot.addEventListener("input", () => { bouton.disabled = mot.value.trim().toUpperCase() !== "EFFACER"; });
    $("form-effacer").addEventListener("submit", async (ev) => {
      ev.preventDefault();
      if (bouton.disabled) return;
      if (!window.confirm("Dernière vérification : tout le dossier de l'élève va être effacé, sans retour possible. Continuer ?")) return;
      bouton.disabled = true;
      $("etat-effacement").textContent = "Effacement…";
      try {
        const r = await MS.api("/api/parent/dossier/effacer", MS.json({ confirmation: mot.value }));
        const e = r.efface;
        $("etat-effacement").textContent = `Dossier effacé : ${e.conversations} conversation(s), ${e.evenements} analyse(s), ${e.bilans} fichier(s) de bilans.`;
        mot.value = "";
        await Promise.all([chargerAlertes(), chargerNotes(), chargerConversations()]);
        chargerRapport();
      } catch (err) {
        $("etat-effacement").textContent = `Erreur : ${err.message}`;
        bouton.disabled = false;
      }
    });
  }

  // Amenagements du PAP, preferences hors PAP et conflits (docs/spec/ADAPTATIONS-LOT2.md, EX-108).
  // Tout texte vient du serveur et passe par textContent. Les conflits sont montres, jamais tranches.
  const Adaptations = {
    lireChoix() {
      const coches = [...document.querySelectorAll("#form-adaptations input[data-amenagement]")]
        .filter((c) => c.checked).map((c) => c.dataset.amenagement);
      const preferences = { police: $("pref-police").value, fond: $("pref-fond").value };
      if ($("pref-lecture-automatique").checked) preferences["lecture-vocale"] = "automatique";
      return { amenagements: coches, preferences };
    },

    ligne(a) {
      const li = document.createElement("li");
      li.dataset.amenagement = a.id;
      const label = document.createElement("label");
      const case_ = document.createElement("input");
      case_.type = "checkbox";
      case_.dataset.amenagement = a.id;
      case_.checked = a.coche;
      case_.addEventListener("change", () => Adaptations.apercu());
      label.appendChild(case_);
      const texte = document.createElement("span");
      texte.className = "adaptation-libelle";
      if (a.rubrique_autres) {
        const ref = a.reference;
        texte.textContent = ref ? `${ref.texte} (libellé ${ref.nom_niveau}, p. ${ref.page})` : a.id;
        const mention = document.createElement("em");
        mention.className = "adaptation-mention";
        mention.textContent = ` : ${a.mention}`;
        texte.appendChild(mention);
      } else {
        texte.textContent = `${a.texte} (p. ${a.page})`;
      }
      label.appendChild(texte);
      li.appendChild(label);
      return li;
    },

    remplirSelect(select, pref) {
      select.textContent = "";
      for (const c of pref.choix) {
        const option = document.createElement("option");
        option.value = c.valeur;
        option.textContent = c.libelle;
        select.appendChild(option);
      }
      select.value = pref.valeur;
    },

    afficherConflits(conflits) {
      const zone = $("adaptations-conflits");
      zone.textContent = "";
      zone.dataset.nombre = String(conflits.length);
      if (!conflits.length) return;
      const titre = document.createElement("p");
      titre.textContent = "À savoir : ces réglages s'appliquent tous, mais leur combinaison a un effet à surveiller.";
      zone.appendChild(titre);
      const liste = document.createElement("ul");
      for (const c of conflits) {
        const li = document.createElement("li");
        li.className = "conflit";
        li.dataset.conflit = c.id;
        li.textContent = c.message;
        liste.appendChild(li);
      }
      zone.appendChild(liste);
    },

    afficher(etat) {
      $("adaptations-niveau").textContent = etat.nom_niveau + (etat.niveau_reconnu ? "" : " (classe non reconnue)");
      const pap = $("adaptations-pap"), autres = $("adaptations-autres");
      pap.textContent = ""; autres.textContent = "";
      for (const a of etat.amenagements) (a.rubrique_autres ? autres : pap).appendChild(Adaptations.ligne(a));
      const r = etat.rubrique_autres;
      $("adaptations-autres-titre").textContent = r.page ? `${r.titre} (p. ${r.page})` : r.titre;
      $("adaptations-autres-groupe").classList.toggle("cache", !autres.children.length);
      Adaptations.remplirSelect($("pref-police"), etat.preferences.police);
      Adaptations.remplirSelect($("pref-fond"), etat.preferences.fond);
      $("pref-lecture-automatique").checked = etat.lecture_automatique;
      Adaptations.afficherConflits(etat.conflits);
    },

    async apercu() {
      try {
        const etat = await MS.api("/api/parent/adaptations/apercu", MS.json(Adaptations.lireChoix()));
        Adaptations.afficherConflits(etat.conflits);
        $("adaptations-etat").textContent = "Modifications non enregistrées.";
      } catch (err) { $("adaptations-etat").textContent = `Erreur : ${err.message}`; }
    },

    async charger() {
      Adaptations.afficher(await MS.api("/api/parent/adaptations"));
    },

    preparer() {
      for (const id of ["pref-police", "pref-fond", "pref-lecture-automatique"]) {
        $(id).addEventListener("change", () => Adaptations.apercu());
      }
      $("form-adaptations").addEventListener("submit", async (ev) => {
        ev.preventDefault();
        $("adaptations-etat").textContent = "Enregistrement…";
        try {
          const etat = await MS.api("/api/parent/adaptations", MS.json(Adaptations.lireChoix(), "PUT"));
          Adaptations.afficher(etat);
          $("adaptations-etat").textContent = "Enregistré.";
        } catch (err) { $("adaptations-etat").textContent = `Erreur : ${err.message}`; }
      });
    },
  };

  async function demarrage() {
    await MS.porte("parent", { porte: $("porte"), contenu: $("contenu"), formulaire: $("porte-form"), champ: $("porte-code"), erreur: $("porte-erreur") });
    const infos = await MS.api("/api/infos");
    MS.appliquerCouleurs(infos.persona.couleurs);
    document.title = `${infos.persona.nom} - Espace parent`;
    modules = await MS.api("/api/parent/modules");
    $("jour").value = aujourdhui();
    $("jour").addEventListener("change", () => { chargerRapport(); chargerConversations(); });
    $("form-note").addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const texte = $("note-texte").value.trim();
      if (!texte) return;
      await MS.api("/api/modules/memoire/notes", MS.json({ texte, jusqu_au: $("note-fin").value || null }));
      $("note-texte").value = ""; $("note-fin").value = "";
      chargerNotes();
    });
    $("envoyer-rapport").addEventListener("click", async () => {
      $("etat-envoi").textContent = "Envoi…";
      try {
        const r = await MS.api(`/api/modules/rapport/envoyer?date=${$("jour").value}`, { method: "POST" });
        $("etat-envoi").textContent = r.envoye ? "Envoyé." : (r.erreurs && r.erreurs.length ? `Échec : ${r.erreurs.join(" ; ")}` : "Rien à envoyer ce jour-là.");
      } catch (err) { $("etat-envoi").textContent = `Erreur : ${err.message}`; }
    });
    preparerEffacement();
    Adaptations.preparer();
    $("retours-traites").addEventListener("change", chargerRetours);
    await Promise.all([chargerAlertes(), chargerNotes(), chargerRetours(), chargerConversations(), Adaptations.charger()]);
    chargerRapport();
  }

  // Lecture vocale (EX-007) : constat local, independant du serveur, fait des le chargement.
  LectureVocale.initialiser();
  LectureVocale.indiquer($("lecture-vocale-etat"));

  demarrage().catch((err) => { document.body.innerHTML = `<p class="erreur-page">Erreur : ${MS.echapper(err.message)}</p>`; });
})();
