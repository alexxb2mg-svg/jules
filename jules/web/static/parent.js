// Page parent : rapport, signaux, notes, lecture des conversations.
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
      });
      zone.appendChild(bloc);
    }
  }

  async function demarrage() {
    await MS.porte("parent", { porte: $("porte"), contenu: $("contenu"), formulaire: $("porte-form"), champ: $("porte-code"), erreur: $("porte-erreur") });
    const infos = await MS.api("/api/infos");
    MS.appliquerCouleurs(infos.persona.couleurs);
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
    await Promise.all([chargerAlertes(), chargerNotes(), chargerConversations()]);
    chargerRapport();
  }

  demarrage().catch((err) => { document.body.innerHTML = `<p class="erreur-page">Erreur : ${MS.echapper(err.message)}</p>`; });
})();
