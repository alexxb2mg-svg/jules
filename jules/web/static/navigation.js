// Jules - barre laterale unique des pages eleve (docs/spec/NAVIGATION.md, EX-201 a EX-212).
// Un seul composant pour /, /cours, /studio et /discuter : chaque page l'appelle une fois, apres la porte
// et /api/infos, avec l'etat de session que MS.porte a lu (EX-206 : aucun second appel a /api/session).
//
// Petites pages (EX-209), une seule visible a la fois :
//   etape 1 : le menu ; etape 2 : les matieres d'une rubrique ; etape 3 : les chapitres d'une matiere (Mes fiches
//   seulement) ; etape 4 : les elements (fiches, lecons, notions du studio).
// Les listes viennent de MS.api, dont le cache (commun.js, EX-210) partage les reponses deja demandees par la
// page : la barre ne connait ni cours.js ni studio.js.
// Securite : aucun innerHTML ; tout texte passe par textContent.
"use strict";

const Navigation = (() => {
  // Recopie de docs/spec/navigation-reference.json (etape 1) ; les tests comparent le rendu au JSON.
  const RUBRIQUES = [
    {
      titre: "Apprendre",
      entrees: [
        { libelle: "Mes fiches", sousPages: "fiches", page: "/", icone: "F" },
        { libelle: "Mes leçons", sousPages: "lecons", page: "/cours", icone: "L" },
      ],
    },
    {
      titre: "M'entraîner",
      entrees: [{ libelle: "Exercices et supports", sousPages: "supports", page: "/studio", icone: "E" }],
    },
    {
      titre: "Discuter",
      entrees: [{ libelle: "Discuter avec Jules", href: "/discuter", page: "/discuter", icone: "D" }],
    },
    {
      titre: "Mon espace",
      entrees: [{ libelle: "Espace parent", href: "/parent", page: "/parent", icone: "P" }],
    },
  ];
  const ID_BARRE = "barre-jules";
  const ID_BOUTON = "barre-jules-bouton";
  const ID_REPLIER = "barre-jules-replier";

  // La liste de chaque rubrique a sous-pages : les trois chemins du cache de MS.api.
  const SOURCES = {
    fiches: "/api/eleve/fiches_visuelles/notions",
    lecons: "/api/eleve/cours/parcours",
    supports: "/api/eleve/studio/notions",
  };
  const PAGE_DE_RUBRIQUE = { lecons: "/cours", supports: "/studio" };
  const SANS_CHAPITRE = "Autres notions";

  const etat = {
    barre: null,
    menu: null,
    zone: null,       // conteneur de la petite page (etapes 2 a 4)
    vue: { etape: 1 },
    courante: null,   // matiere de depart des rubriques : celle de l'adresse, sinon la matiere retenue
    notion: null,     // notion ouverte dans la page (aria-current a l'etape 4)
    sequence: 0,      // la derniere demande d'affichage gagne (reponses arrivees dans le desordre)
    ecouteurs: [],    // pages qui suivent la matiere choisie dans la barre (EX-216, surChoixMatiere)
  };

  function creer(balise, classe, texte) {
    const e = document.createElement(balise);
    if (classe) e.className = classe;
    if (texte !== undefined) e.textContent = texte;
    return e;
  }

  function decor(classe, texte) {
    const s = creer("span", classe, texte);
    s.setAttribute("aria-hidden", "true");
    return s;
  }

  function libelleRubrique(rubrique) {
    for (const r of RUBRIQUES) for (const e of r.entrees) if (e.sousPages === rubrique) return e.libelle;
    return rubrique;
  }

  // EX-203 : l'entree active se choisit sur le seul pathname (ni ?..., ni #...).
  function entreeActive(chemin) {
    for (const rubrique of RUBRIQUES) {
      for (const entree of rubrique.entrees) {
        if (entree.page === chemin) return entree;
      }
    }
    return null;
  }

  // EX-206 : la protection annoncee vient de la reponse /api/session deja lue par MS.porte.
  function etiquetteParent(session) {
    if (!session || session.role === "parent") return null;
    const tag = creer("span", "barre-etiquette");
    tag.id = "barre-etat-parent";
    if (session.parent === false) {
      tag.classList.add("barre-etiquette-code");
      const cadenas = creer("span", "barre-cadenas", "🔒");
      cadenas.setAttribute("aria-hidden", "true");
      tag.append(cadenas, " code parent");
    } else {
      tag.classList.add("barre-etiquette-libre");
      tag.textContent = "non protégé";
    }
    return tag;
  }

  function entreeDom(entree, active, session) {
    const ligne = creer("li", "barre-ligne");
    // Barre repliee (EX-207) : seule l'icone reste visible ; le libelle garde le nom accessible.
    const icone = creer("span", "barre-icone", entree.icone);
    icone.setAttribute("aria-hidden", "true");
    const libelle = creer("span", "barre-libelle", entree.libelle);
    let cible;
    if (entree.sousPages) {
      cible = creer("button", "barre-entree barre-rubrique-bouton");
      cible.type = "button";
      cible.dataset.sousPages = entree.sousPages;
      cible.setAttribute("aria-expanded", "false");
      const chevron = creer("span", "barre-chevron", "›");
      chevron.setAttribute("aria-hidden", "true");
      cible.append(icone, libelle, chevron);
      cible.addEventListener("click", () => ouvrirRubrique(entree.sousPages));
    } else {
      cible = creer("a", "barre-entree");
      cible.href = entree.href;
      cible.append(icone, libelle);
    }
    if (entree === active) {
      cible.setAttribute("aria-current", "page");
      cible.classList.add("barre-active");
    }
    ligne.appendChild(cible);
    if (entree.page === "/parent") {
      const tag = etiquetteParent(session);
      if (tag) {
        ligne.appendChild(tag);
        cible.setAttribute("aria-describedby", tag.id);
      }
    }
    return ligne;
  }

  // --- donnees des petites pages ------------------------------------------------------------------------

  function charger(rubrique, matiere) {
    if (rubrique === "fiches") return MS.api(SOURCES.fiches);
    return MS.api(MS.cheminMatiere(SOURCES[rubrique], matiere));
  }

  // Notions groupees par chapitre, dans l'ordre d'arrivee.
  function parChapitre(notions) {
    const chapitres = [];
    const index = new Map();
    for (const n of notions) {
      const titre = n.chapitre || SANS_CHAPITRE;
      if (!index.has(titre)) {
        index.set(titre, { titre, notions: [] });
        chapitres.push(index.get(titre));
      }
      index.get(titre).notions.push(n);
    }
    return chapitres;
  }

  // Resout une vue demandee en vue affichable, avec ses donnees (un appel au plus, souvent servi par le cache).
  // Matiere ou chapitre absents de la liste : on remonte d'une etape, sans toucher a la memoire.
  async function resoudre(vue) {
    if (vue.etape === 1) return { vue };
    const rubrique = vue.rubrique;
    if (rubrique === "fiches") {
      const matieres = (await charger("fiches")).matieres || [];
      const matiere = vue.etape > 2 ? matieres.find((m) => m.id === vue.matiere) : null;
      if (!matiere) {
        return {
          vue: { etape: 2, rubrique },
          matieres: matieres.map((m) => ({ id: m.id, nom: m.nom, nombre: (m.notions || []).length })),
        };
      }
      const chapitres = parChapitre(matiere.notions || []);
      const chapitre = vue.etape === 4 ? chapitres.find((c) => c.titre === vue.chapitre) : null;
      if (!chapitre) return { vue: { etape: 3, rubrique, matiere: matiere.id }, matiere, chapitres };
      return { vue: { etape: 4, rubrique, matiere: matiere.id, chapitre: chapitre.titre }, matiere, chapitre };
    }
    // Mes lecons, Exercices : une reponse porte toutes les matieres et les notions d'une seule. L'etape 2 reprend
    // la reponse de la matiere en cours (meme cle de cache que la page : aucun appel de plus).
    const demandee = vue.etape === 2 ? etat.courante : vue.matiere;
    const r = await charger(rubrique, demandee);
    const matieres = (r.matieres || []).map((m) => ({ id: m.id, nom: m.nom }));
    if (vue.etape === 2 || !vue.matiere || r.matiere !== vue.matiere) return { vue: { etape: 2, rubrique }, matieres };
    const nom = (matieres.find((m) => m.id === r.matiere) || { nom: r.matiere }).nom;
    let notions = r.notions || [];
    if (rubrique === "lecons") notions = notions.filter((n) => n.lecon);
    return {
      vue: { etape: 4, rubrique, matiere: r.matiere },
      matiere: { id: r.matiere, nom },
      chapitres: parChapitre(notions),
    };
  }

  // --- rendu --------------------------------------------------------------------------------------------

  function boutonRetour(libelle, vers, focusSur) {
    const b = creer("button", "barre-entree barre-retour", libelle);
    b.type = "button";
    b.addEventListener("click", () => afficher(vers, { focusSur, utilisateur: true }));
    return b;
  }

  // Matiere ou chapitre : un bouton qui ouvre la petite page suivante (chevron, effectif, pastille de matiere).
  function ligneBouton(classe, libelle, nombre, courant, action) {
    const li = creer("li", "barre-ligne");
    const b = creer("button", `barre-entree ${classe}`);
    b.type = "button";
    b.setAttribute("aria-expanded", "false");
    if (classe === "barre-matiere") b.append(decor("barre-pastille", ""));
    b.append(creer("span", "barre-libelle", MS.typo(libelle)));  // #46 : ponctuation haute jamais en debut de ligne
    b.title = libelle;  // EX-212 : texte complet d'un titre affiche sur quelques lignes
    if (nombre !== undefined) b.append(creer("span", "barre-effectif", String(nombre)));
    b.append(decor("barre-chevron", "›"));
    if (courant) b.setAttribute("aria-current", "true");
    b.addEventListener("click", action);
    li.appendChild(b);
    return { li, bouton: b };
  }

  function ligneLien(libelle, href, courant, mention) {
    const li = creer("li", "barre-ligne");
    const a = creer("a", "barre-entree barre-element");
    a.href = href;
    a.append(creer("span", "barre-libelle", MS.typo(libelle)));
    a.title = libelle;
    if (mention) a.append(creer("span", "barre-mention", mention));
    if (courant) a.setAttribute("aria-current", "true");
    li.appendChild(a);
    return li;
  }

  // Exercices : une notion sans lecon n'a pas de support possible (studio.creer() la refuse) ; son lien ouvre
  // /studio sur sa matiere, sans designer de notion (EX-209, spec-nav-fige-2).
  function lienElement(rubrique, matiere, notion, avecLecon = true) {
    if (rubrique === "fiches") return `/#${encodeURIComponent(notion)}`;
    const q = `?matiere=${encodeURIComponent(matiere)}`;
    if (rubrique === "supports" && !avecLecon) return PAGE_DE_RUBRIQUE[rubrique] + q;
    return PAGE_DE_RUBRIQUE[rubrique] + q + `&notion=${encodeURIComponent(notion)}`;
  }

  function choisirMatiere(rubrique, id) {
    const change = id !== etat.courante;
    etat.courante = id;
    MS.retenirMatiere(id);
    const suite = rubrique === "fiches" ? { etape: 3, rubrique, matiere: id } : { etape: 4, rubrique, matiere: id };
    // EX-216 : sur /cours et /studio, la zone centrale suit la matiere choisie dans la barre (adresse ?matiere=,
    // puis la page, qui lit sa liste dans le cache de MS.api) : jamais deux matieres differentes a l'ecran.
    if (rubrique === rubriqueDeLaPage()) {
      if (change) etat.notion = null;  // la notion de l'adresse appartenait a l'autre matiere
      ecrireMatiereAdresse(id);
      for (const ecouteur of etat.ecouteurs) ecouteur(id);
    }
    afficher(suite, { utilisateur: true });
  }

  // Rubrique dont la page courante affiche la liste au centre (/cours : lecons, /studio : supports), sinon null.
  function rubriqueDeLaPage() {
    return Object.keys(PAGE_DE_RUBRIQUE).find((r) => PAGE_DE_RUBRIQUE[r] === location.pathname) || null;
  }

  // ?matiere=<id> sans rechargement (EX-216) ; une notion demandee par l'ancienne adresse ne vaut plus.
  function ecrireMatiereAdresse(id) {
    const p = new URLSearchParams(location.search);
    p.set("matiere", id);
    p.delete("notion");
    history.replaceState(history.state, "", location.pathname + "?" + p.toString() + location.hash);
  }

  function titrePage(texte) {
    const titre = creer("h2", "barre-page-titre", MS.typo(texte));
    titre.title = texte;
    titre.id = "barre-page-titre";
    titre.tabIndex = -1;
    return titre;
  }

  function pageDom(res) {
    const { vue } = res;
    const section = creer("section", "barre-page");
    section.dataset.etape = String(vue.etape);
    section.dataset.rubrique = vue.rubrique;
    section.setAttribute("aria-labelledby", "barre-page-titre");
    const liste = creer("ul", "barre-liste");
    const libelle = libelleRubrique(vue.rubrique);

    if (vue.etape === 2) {
      section.append(
        boutonRetour("← Menu", { etape: 1 }, { rubrique: vue.rubrique }),
        titrePage(libelle),
        creer("p", "barre-consigne", "Choisis une matière"),
      );
      for (const m of res.matieres) {
        const { li, bouton } = ligneBouton("barre-matiere", m.nom, m.nombre, m.id === etat.courante,
          () => choisirMatiere(vue.rubrique, m.id));
        bouton.dataset.matiere = m.id;
        liste.appendChild(li);
      }
      if (!res.matieres.length) section.append(creer("p", "barre-vide", "Rien pour le moment."));
    } else if (vue.etape === 3) {
      section.append(
        boutonRetour("← Matières", { etape: 2, rubrique: vue.rubrique }, { matiere: vue.matiere }),
        creer("p", "barre-fil", libelle),
        titrePage(res.matiere.nom),
      );
      const ouvert = chapitreDeLaNotion(res.chapitres);
      for (const c of res.chapitres) {
        const suite = { etape: 4, rubrique: vue.rubrique, matiere: vue.matiere, chapitre: c.titre };
        const { li, bouton } = ligneBouton("barre-chapitre", c.titre, c.notions.length, c.titre === ouvert,
          () => afficher(suite, { utilisateur: true }));
        bouton.dataset.chapitre = c.titre;
        liste.appendChild(li);
      }
    } else if (vue.rubrique === "fiches") {
      section.append(
        boutonRetour("← Chapitres", { etape: 3, rubrique: vue.rubrique, matiere: vue.matiere }, { chapitre: vue.chapitre }),
        creer("p", "barre-fil", `${libelle} › ${res.matiere.nom}`),
        titrePage(res.chapitre.titre),
      );
      for (const n of res.chapitre.notions) {
        liste.appendChild(ligneLien(n.titre, lienElement("fiches", vue.matiere, n.id), n.id === etat.notion));
      }
    } else {
      section.append(
        boutonRetour("← Matières", { etape: 2, rubrique: vue.rubrique }, { matiere: vue.matiere }),
        creer("p", "barre-fil", libelle),
        titrePage(res.matiere.nom),
      );
      const courante = PAGE_DE_RUBRIQUE[vue.rubrique] === location.pathname ? etat.notion : null;
      for (const c of res.chapitres) {
        const bloc = creer("li", "barre-groupe");
        // EX-212 : le chapitre en intertitre porte son effectif, comme les chapitres de Mes fiches.
        const intertitre = creer("h3", "barre-intertitre");
        intertitre.title = c.titre;
        intertitre.append(creer("span", "barre-libelle", MS.typo(c.titre)), creer("span", "barre-effectif", String(c.notions.length)));
        bloc.appendChild(intertitre);
        const sous = creer("ul", "barre-liste");
        for (const n of c.notions) {
          const sansLecon = vue.rubrique === "supports" && !n.lecon;
          const lien = lienElement(vue.rubrique, vue.matiere, n.id, !sansLecon);
          sous.appendChild(ligneLien(n.titre, lien, n.id === courante, sansLecon ? "pas encore de leçon" : ""));
        }
        bloc.appendChild(sous);
        liste.appendChild(bloc);
      }
      if (!res.chapitres.length) {
        const vide = vue.rubrique === "lecons" ? "Pas encore de leçon dans cette matière." : "Aucune notion dans cette matière.";
        section.append(creer("p", "barre-vide", vide));
      }
    }
    if (liste.childElementCount) section.appendChild(liste);
    return section;
  }

  function chapitreDeLaNotion(chapitres) {
    if (!etat.notion) return null;
    const c = chapitres.find((ch) => ch.notions.some((n) => n.id === etat.notion));
    return c ? c.titre : null;
  }

  function pageErreur(message) {
    const section = creer("section", "barre-page");
    section.setAttribute("aria-labelledby", "barre-page-titre");
    section.append(
      boutonRetour("← Menu", { etape: 1 }, null),
      titrePage("Liste indisponible"),
      creer("p", "barre-erreur", `Impossible de charger cette liste : ${message}`),
    );
    return section;
  }

  // Etat de la barre dans l'adresse : #nav=<rubrique>[/<matiere>[/<chapitre>]] (segments encodes).
  function fragment(vue) {
    if (!vue.rubrique || vue.etape < 2) return "";
    const segments = [vue.rubrique, vue.matiere, vue.chapitre].filter(Boolean);
    return "nav=" + segments.map(encodeURIComponent).join("/");
  }

  function lireFragment() {
    const brut = location.hash.slice(1);
    if (!brut.startsWith("nav=")) return null;
    let segments;
    try {
      segments = brut.slice(4).split("/").map(decodeURIComponent);
    } catch (_) {
      return null;  // %zz ou autre segment illisible : etape 1
    }
    const [rubrique, matiere, chapitre] = segments;
    if (!Object.prototype.hasOwnProperty.call(SOURCES, rubrique) || segments.some((s) => !s)) return null;
    if (segments.length === 1) return { etape: 2, rubrique };
    if (rubrique === "fiches") {
      if (segments.length === 2) return { etape: 3, rubrique, matiere };
      if (segments.length === 3) return { etape: 4, rubrique, matiere, chapitre };
      return null;
    }
    return segments.length === 2 ? { etape: 4, rubrique, matiere } : null;
  }

  function ecrireFragment(vue) {
    const f = fragment(vue);
    history.replaceState(history.state, "", location.pathname + location.search + (f ? "#" + f : ""));
  }

  // /cours et /studio : quand la barre montre les notions de la rubrique de la page, la page masque sa propre
  // liste (regle CSS de la page, a partir de 900 px) : jamais deux listes de notions cote a cote (EX-209 (k)).
  function signalerListe(vue) {
    if (vue.etape === 4 && PAGE_DE_RUBRIQUE[vue.rubrique] === location.pathname) {
      document.body.dataset.barreNotions = vue.rubrique;
    } else {
      delete document.body.dataset.barreNotions;
    }
  }

  function trouver(selecteur, cle, valeur) {
    for (const e of etat.barre.querySelectorAll(selecteur)) if (e.dataset[cle] === valeur) return e;
    return null;
  }

  // options.utilisateur : action de l'eleve (adresse mise a jour, focus deplace).
  // options.focusSur : au retour, l'element qui avait ouvert la page quittee.
  async function afficher(vue, options = {}) {
    const numero = ++etat.sequence;
    let res = null;
    let erreur = null;
    try {
      res = await resoudre(vue);
    } catch (err) {
      erreur = err;
    }
    if (numero !== etat.sequence) return;
    const vueFinale = erreur ? { etape: 0, rubrique: vue.rubrique } : res.vue;
    etat.vue = vueFinale;
    for (const b of etat.menu.querySelectorAll("[data-sous-pages]")) {
      b.setAttribute("aria-expanded", String(vueFinale.etape !== 1 && b.dataset.sousPages === vue.rubrique));
    }
    if (vueFinale.etape === 1) {
      etat.zone.replaceChildren();
      etat.zone.hidden = true;
      etat.menu.hidden = false;
    } else {
      etat.zone.replaceChildren(erreur ? pageErreur(erreur.message) : pageDom(res));
      etat.zone.hidden = false;
      etat.menu.hidden = true;
      etat.barre.scrollTop = 0;
    }
    signalerListe(vueFinale);
    if (options.utilisateur && !erreur) ecrireFragment(vueFinale);
    if (!options.utilisateur) return;
    const f = options.focusSur;
    let cible = null;
    if (f && f.rubrique) cible = trouver("[data-sous-pages]", "sousPages", f.rubrique);
    else if (f && f.matiere) cible = trouver("[data-matiere]", "matiere", f.matiere);
    else if (f && f.chapitre) cible = trouver("[data-chapitre]", "chapitre", f.chapitre);
    if (!cible && !etat.zone.hidden) cible = etat.zone.querySelector(".barre-page-titre");
    if (cible) cible.focus();
  }

  // Clic sur une rubrique a l'etape 1 (EX-209) : matiere retenue presente dans la liste -> etape suivante
  // directement ; absente ou aucune -> etape 2 (resoudre remonte d'une etape), memoire intacte.
  function ouvrirRubrique(rubrique) {
    const m = etat.courante;
    if (!m) return afficher({ etape: 2, rubrique }, { utilisateur: true });
    const vue = rubrique === "fiches" ? { etape: 3, rubrique, matiere: m } : { etape: 4, rubrique, matiere: m };
    return afficher(vue, { utilisateur: true });
  }

  // Sur /, un #<id> de notion ouvre la fiche (accueil.js) : la barre se place sur l'etape 4 de sa matiere, qui
  // devient la matiere retenue. Il l'emporte sur #nav=.
  async function suivreNotionDeLAccueil() {
    let id;
    try {
      id = decodeURIComponent(location.hash.slice(1));
    } catch (_) {
      return false;
    }
    if (!id || id.startsWith("nav=")) return false;
    let matieres;
    try {
      matieres = (await charger("fiches")).matieres || [];
    } catch (_) {
      return false;
    }
    for (const m of matieres) {
      const n = (m.notions || []).find((x) => x.id === id);
      if (!n) continue;
      etat.notion = id;
      etat.courante = m.id;
      MS.retenirMatiere(m.id);
      await afficher({ etape: 4, rubrique: "fiches", matiere: m.id, chapitre: n.chapitre || SANS_CHAPITRE });
      return true;
    }
    return false;
  }

  // Une page a choisi une matiere dans sa zone centrale (liste « Choisis une matière » de /cours et /studio) : la
  // barre en repart et, symetrie d'EX-216, se place sur cette matiere dans la rubrique de la page (etape 4). La
  // liste vient du cache de MS.api (meme cle que la page) : aucun appel de plus. Le focus reste dans la page.
  function suivreMatiere(id) {
    etat.courante = id;
    const rubrique = rubriqueDeLaPage();
    if (!rubrique || !etat.barre) return;
    ecrireMatiereAdresse(id);
    etat.notion = null;
    afficher({ etape: 4, rubrique, matiere: id }).then(() => { if (etat.vue.etape > 0) ecrireFragment(etat.vue); });
  }

  // La page s'abonne au choix d'une matiere dans la barre (rubrique de la page) : elle recharge sa liste.
  function surChoixMatiere(ecouteur) {
    etat.ecouteurs.push(ecouteur);
  }

  // EX-207 : sous 900 px, tiroir ; a partir de 900 px, barre repliable en icones (etat dans localStorage).
  const CLE_REPLI = "jules.nav.repliee";
  const TIROIR = "(max-width: 899.98px)";

  function lireRepli() {
    try {
      return localStorage.getItem(CLE_REPLI) === "true";
    } catch (_) {
      return false; // stockage indisponible : barre depliee
    }
  }

  function ecrireRepli(repliee) {
    try {
      localStorage.setItem(CLE_REPLI, String(repliee)); // booleen seul : "true" ou "false"
    } catch (_) {
      /* stockage indisponible : l'etat ne survit pas au rechargement */
    }
  }

  function appliquerRepli(replier, repliee) {
    document.body.classList.toggle("barre-repliee", repliee);
    replier.setAttribute("aria-expanded", String(!repliee));
    replier.firstChild.textContent = repliee ? "»" : "«";
  }

  function ouvrir(bouton, barre) {
    barre.classList.add("ouverte");
    document.body.classList.add("barre-tiroir-ouvert");
    bouton.setAttribute("aria-expanded", "true");
  }

  // A la fermeture du tiroir, le focus revient toujours au bouton ☰ (EX-207).
  function fermer(bouton, barre) {
    if (!barre.classList.contains("ouverte")) return;
    barre.classList.remove("ouverte");
    document.body.classList.remove("barre-tiroir-ouvert");
    bouton.setAttribute("aria-expanded", "false");
    bouton.focus();
  }

  // session : objet renvoye par MS.porte ; infos : /api/infos (seuls persona et prenom sont lus, EX-210).
  function monter(session, infos) {
    if (document.getElementById(ID_BARRE)) return;
    const nomPersona = (infos && infos.persona && infos.persona.nom) || "Jules";
    const prenom = (infos && infos.prenom) || "";
    const active = entreeActive(location.pathname);

    const bouton = creer("button", "barre-jules-bouton");
    bouton.id = ID_BOUTON;
    bouton.type = "button";
    bouton.setAttribute("aria-controls", ID_BARRE);
    bouton.setAttribute("aria-expanded", "false");
    const icone = creer("span", "", "☰");
    icone.setAttribute("aria-hidden", "true");
    bouton.append(icone, creer("span", "", " Menu"));

    const barre = creer("nav", "barre-jules");
    barre.id = ID_BARRE;
    barre.setAttribute("aria-label", "Sections de Jules");

    const marque = creer("p", "barre-marque", nomPersona);
    const point = creer("span", "barre-marque-point", ".");
    point.setAttribute("aria-hidden", "true");
    marque.appendChild(point);
    barre.appendChild(marque);

    const menu = creer("div", "barre-menu");
    for (const rubrique of RUBRIQUES) {
      menu.appendChild(creer("h2", "barre-rubrique", rubrique.titre));
      const liste = creer("ul", "barre-liste");
      for (const entree of rubrique.entrees) liste.appendChild(entreeDom(entree, active, session));
      menu.appendChild(liste);
    }
    const zone = creer("div", "barre-sous-page");
    zone.hidden = true;
    barre.append(menu, zone, creer("p", "barre-pied", prenom));

    // A partir de 900 px : bouton de repli, hors du <nav> (la liste des entrees reste celle de la reference).
    const replier = creer("button", "barre-replier");
    replier.id = ID_REPLIER;
    replier.type = "button";
    replier.setAttribute("aria-controls", ID_BARRE);
    replier.setAttribute("aria-label", "Libellés de la barre");
    const fleche = creer("span", "", "«");
    fleche.setAttribute("aria-hidden", "true");
    replier.appendChild(fleche);

    // Voile sous le tiroir ouvert : un clic en dehors ferme le tiroir sans agir sur la page dessous.
    const voile = creer("div", "barre-voile");
    voile.setAttribute("aria-hidden", "true");

    document.body.prepend(bouton, replier, barre, voile);
    document.body.classList.add("avec-barre");
    Object.assign(etat, { barre, menu, zone });
    appliquerRepli(replier, lireRepli());

    // EX-211 : titre d'onglet = nom de la persona - libelle de l'entree active.
    if (active) document.title = `${nomPersona} - ${active.libelle}`;

    bouton.addEventListener("click", () => {
      if (barre.classList.contains("ouverte")) fermer(bouton, barre);
      else ouvrir(bouton, barre);
    });
    replier.addEventListener("click", () => {
      const repliee = !document.body.classList.contains("barre-repliee");
      appliquerRepli(replier, repliee);
      ecrireRepli(repliee);
    });
    // Fermetures du tiroir : Echap, clic en dehors, choix d'une entree feuille (lien). Une rubrique a
    // sous-pages (<button>) ouvre une petite page : le tiroir reste ouvert.
    document.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape") fermer(bouton, barre);
    });
    // Decision sur le chemin d'origine du clic (fige au debut de la distribution), pas sur le DOM au moment de
    // la bulle : un vrai clic laisse afficher() remplacer la petite page (matiere, chapitre, retour) avant que
    // l'evenement n'arrive ici, et la cible est alors detachee de la barre.
    document.addEventListener("click", (ev) => {
      if (!barre.classList.contains("ouverte")) return;
      const chemin = ev.composedPath();
      if (chemin.includes(bouton)) return;
      const lien = chemin.some((n) => n instanceof Element && n.tagName === "A");
      if (!chemin.includes(barre) || lien) fermer(bouton, barre);
    });
    // Passage au-dessus de 900 px tiroir ouvert : il n'y a plus de tiroir, on le referme sans voler le focus.
    const tiroir = window.matchMedia(TIROIR);
    const quitterTiroir = () => {
      if (tiroir.matches || !barre.classList.contains("ouverte")) return;
      barre.classList.remove("ouverte");
      document.body.classList.remove("barre-tiroir-ouvert");
      bouton.setAttribute("aria-expanded", "false");
    };
    if (tiroir.addEventListener) tiroir.addEventListener("change", quitterTiroir);

    // Point de depart (EX-209). Sur /cours et /studio, ?matiere= (clic explicite) l'emporte sur la memoire et sur
    // la matiere de #nav= ; seule la rubrique de #nav= est alors reprise.
    const rubriquePage = rubriqueDeLaPage();
    const parametres = new URLSearchParams(location.search);
    const matiereAdresse = rubriquePage ? parametres.get("matiere") : null;
    etat.courante = matiereAdresse || MS.matiereRetenue();
    if (rubriquePage) etat.notion = parametres.get("notion");

    if (location.pathname === "/") {
      addEventListener("hashchange", () => { suivreNotionDeLAccueil(); });
      suivreNotionDeLAccueil().then((suivie) => { if (!suivie) restaurer(null); });
    } else {
      restaurer(matiereAdresse);
    }
  }

  function restaurer(matiereAdresse) {
    let vue = lireFragment();
    if (!vue) return;
    if (matiereAdresse) {
      vue = vue.rubrique === "fiches" ? { etape: 3, rubrique: "fiches", matiere: matiereAdresse }
        : { etape: 4, rubrique: vue.rubrique, matiere: matiereAdresse };
    }
    afficher(vue).then(() => { if (etat.vue.etape > 0) ecrireFragment(etat.vue); });
  }

  return { monter, suivreMatiere, surChoixMatiere, RUBRIQUES };
})();
