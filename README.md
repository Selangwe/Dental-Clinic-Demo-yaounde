# dentist237 — v2

Refonte complète de dentist237.com, à partir de `dentist237-site-audit.md`.
**33 pages**, HTML statique, sans dépendance npm.

```bash
npm run dev      # http://localhost:5173 — rebuild + live reload
npm run build    # génère le site (équivaut à: python build.py)
npm run clean    # supprime les dossiers générés
```

`npm run dev` a besoin de Node ≥ 18 et de `python` dans le PATH.
Aucun `npm install` n'est nécessaire : il n'y a aucune dépendance.

---

## Architecture

```
src/
  layout.html            Gabarit unique (head, en-tête, nav, pied, sprite SVG)
  footer.html            Pied de page
  _sprite.html           Icônes SVG (<use href="#i-...">)
  pages/*.html           Une page = un fragment + un bloc <!--meta {...} -->
  templates/quartier.html Gabarit des pages de quartier
  data/quartiers.json    Contenu propre à chacun des 10 quartiers
build.py                 Assembleur
dev.mjs                  Serveur de dev (zéro dépendance)
styles.css               Design system (840 lignes)
main.js                  En-tête collant, menu, révélations, formulaire RDV
```

Le reste — `index.html`, `soins/`, `tarifs/`, `yaounde/`… — est **généré**.
Ne pas éditer ces fichiers : ils sont écrasés à chaque build.

**Pourquoi un build.** 33 pages partagent le même en-tête et le même pied de
page. Les dupliquer garantit qu'ils divergeront. Le gabarit vit à un seul endroit.

`build.py` génère aussi, sans intervention :

- le fil d'Ariane, visuel **et** en JSON-LD `BreadcrumbList`, déduit de l'URL
- les 10 pages de quartier
- `sitemap.xml` (29 URL indexables), `robots.txt`, et `404.html` à la racine
- l'état actif de la navigation, via le champ `nav` de chaque page

Une page se déclare ainsi :

```html
<!--meta
{ "url": "/soins/detartrage/", "title": "…", "desc": "…", "nav": "soins" }
-->
<section class="phead">…</section>

<!--jsonld
[ { "@type": "FAQPage", … } ]
-->
```

## Les pages

| Section | Pages |
|---|---|
| Accueil | `/` |
| Soins | archive + 7 fiches (consultation, détartrage, carie, implant, orthodontie, enfant, blanchiment) |
| Tarifs | `/tarifs/` — grille complète + FAQ |
| Urgences | `/urgences/` — 10 situations, conduite à tenir, 3 réflexes à éviter |
| Cabinets | `/cabinets/` + `/cabinets/yaounde-omnisport/` |
| Quartiers | `/yaounde/` + 10 pages |
| Cabinet | `/a-propos/`, `/a-propos/equipe/`, `/contact/`, `/rendez-vous/` |
| Légal | mentions, confidentialité, cookies, plan du site |

## Décisions

- **Le lien mort est réparé.** `/cabinets/yaounde-omnisport/` existe désormais :
  c'était un 404 en production, lié depuis l'accueil.
- **Rendez-vous : formulaire → WhatsApp.** Le formulaire ne poste sur aucun
  serveur. Il compose un message dans le navigateur et ouvre WhatsApp ; le
  patient appuie sur envoyer. Pas de backend à maintenir, pas de données de
  santé hébergées, et c'est le canal que les patients utilisent déjà.
  Sans JavaScript, le champ caché garde son texte par défaut et le formulaire
  ouvre quand même WhatsApp — seul le champ `text` porte un `name`.
- **Pages de quartier générées, pas dupliquées.** Chacune a son propre trajet,
  ses repères et son angle (Odza mentionne le cabinet 2027, Nkolbisson prévient
  que c'est loin, Biyem-Assi parle des enfants). Dix copies du même texte
  seraient traitées comme du contenu mince.
- **Aucune antenne de quartier inventée.** Chaque page de quartier dit
  explicitement que le cabinet est unique et se trouve à Mfandena.
- **Odza reste « prévu 2027 »**, sans date ni adresse — c'est l'état réel.
- **Slugs canoniques** : `/soins/blanchiment-dentaire/`,
  `/soins/consultation-dentaire/`. Prévoir des 301 depuis les variantes
  (`/soins/blanchiment/`, `/soins/dentiste-enfant/` est conservé tel quel).
- **Pages légales en `noindex`**, sitemap excepté.

## Prudence éditoriale

Les pages de santé engagent la responsabilité du cabinet. Trois règles
appliquées partout :

1. **Aucune citation attribuée à une personne.** Les phrases d'accroche sont des
   phrases du cabinet, jamais des déclarations du Dr Zouna.
2. **Aucune affirmation clinique inventée.** Les fiches décrivent des faits
   établis et renvoient au bilan pour tout ce qui dépend du patient. Les
   contre-indications du blanchiment et les facteurs de risque implantaire sont
   signalés plutôt que passés sous silence.
3. **Un encadré « information générale »** ferme chaque fiche de soin.

## À fournir avant mise en ligne

1. **Photographies** — emplacements réservés et commentés dans le HTML
   (accueil 4:5, portraits 3:4, façade 4:3). Chacun indique la balise `<img>` à
   substituer.
2. **Numéro ONCDC** de la direction médicale et **RCCM Bamacours SARL** —
   marqués `à compléter` en or dans le pied de page et les mentions légales.
   Obligation légale pour un cabinet médical.
3. **Hébergeur** — nom et adresse, dans les mentions légales.
4. **Identité de la praticienne** — l'accueil nomme le Dr Nadia Zouna, les
   mentions légales du site actuel gardent « Dr [Nom partenaire] ». La v2 retient
   Dr Nadia Zouna partout, y compris en JSON-LD. À confirmer.
5. **Équipe** — deux fiches vides sur `/a-propos/equipe/` sont des emplacements,
   pas des personnes. Nom, fonction et numéro d'inscription à fournir.
6. **Durée de conservation du dossier patient** — à préciser dans la politique
   de confidentialité.
7. **contact@dentist237.com** — adresse reprise de l'audit, à vérifier.

## Vérifications automatiques

Après chaque build, ces contrôles passent :

- 0 placeholder `{{…}}` non remplacé
- 0 bloc JSON-LD invalide (33 pages)
- 0 lien interne cassé
- 0 débordement horizontal
