/* dentist237 v2 — interactions
   Volontairement léger : pas de librairie, ~2 Ko.
   La cible est un téléphone Android sur réseau mobile à Yaoundé. */

(function () {
  'use strict';

  /* ---- 1. En-tête collant ---- */
  var head = document.getElementById('head');
  var onScroll = function () {
    head.classList.toggle('stuck', window.scrollY > 12);
  };
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  /* ---- 2. Menu mobile ---- */
  var burger = document.getElementById('burger');
  var drawer = document.getElementById('drawer');

  function setDrawer(open) {
    burger.setAttribute('aria-expanded', String(open));
    burger.setAttribute('aria-label', open ? 'Fermer le menu' : 'Ouvrir le menu');
    drawer.classList.toggle('open', open);
    document.body.style.overflow = open ? 'hidden' : '';
  }

  burger.addEventListener('click', function () {
    setDrawer(burger.getAttribute('aria-expanded') !== 'true');
  });

  drawer.addEventListener('click', function (e) {
    if (e.target.closest('a')) setDrawer(false);
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && drawer.classList.contains('open')) {
      setDrawer(false);
      burger.focus();
    }
  });

  /* ---- 3. Révélations au défilement ---- */
  var targets = document.querySelectorAll('.reveal');

  if (!('IntersectionObserver' in window) ||
      window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    targets.forEach(function (el) { el.classList.add('in'); });
    return;
  }

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('in');
      io.unobserve(entry.target);
    });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

  targets.forEach(function (el) { io.observe(el); });
})();

/* ---- 4. Formulaire de rendez-vous -> message WhatsApp ----
   Le formulaire n'a pas de backend : il compose un message et laisse
   l'utilisateur l'envoyer depuis WhatsApp. C'est le canal que les
   patients utilisent deja, et ca evite d'heberger des donnees de sante.
   Sans JS, le champ cache garde son texte par defaut et le formulaire
   ouvre quand meme WhatsApp. */
(function () {
  'use strict';

  var form = document.getElementById('rdv-form');
  if (!form) return;

  var hidden = document.getElementById('rdv-text');
  var out = document.getElementById('rdv-preview-text');

  function val(id) {
    var el = document.getElementById(id);
    if (!el) return '';
    return el.type === 'checkbox' ? el.checked : el.value.trim();
  }

  function compose() {
    var nom = val('rdv-nom');
    var tel = val('rdv-tel');
    var quartier = val('rdv-quartier');
    var motif = val('rdv-motif');
    var creneau = val('rdv-creneau');
    var urgence = val('rdv-urgence');
    var message = val('rdv-message');

    var lines = [];

    if (urgence) {
      lines.push('Bonjour, j’ai une urgence dentaire.');
    } else {
      lines.push('Bonjour, je souhaite prendre rendez-vous.');
    }

    var moi = [];
    if (nom) moi.push('Je m’appelle ' + nom);
    if (quartier) moi.push((moi.length ? 'je suis à ' : 'Je suis à ') + quartier);
    if (moi.length) lines.push(moi.join(', ') + '.');

    if (motif) lines.push('Motif : ' + motif + '.');
    if (creneau) lines.push('Disponibilité : ' + creneau + '.');
    if (tel) lines.push('Téléphone : ' + tel + '.');
    if (message) lines.push(message);

    return lines.join('\n');
  }

  function sync() {
    var text = compose();
    hidden.value = text;
    if (out) out.textContent = text;
  }

  form.addEventListener('input', sync);
  form.addEventListener('change', sync);
  sync();
})();
