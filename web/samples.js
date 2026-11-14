/* The sample reports: one per bike type the analyzer grades, with the figure and numbers
   drawn from that bike's geometry by tools/sample_figures/ (the numbers are the angles the
   figures actually draw, not targets typed in by hand). Shared by the landing page and the analyzer, plus the small
   carousel both use to step through them. */
(function () {
  var SLIDES = [
 {
  "key": "road_endurance",
  "tab": {
   "en": "Endurance",
   "id": "Endurance"
  },
  "name": {
   "en": "Road, endurance",
   "id": "Road, endurance"
  },
  "strokes": 5,
  "vals": {
   "knee": 38,
   "torso": 48,
   "elbow": 13,
   "shoulder": 86
  },
  "torsoZone": [
   40,
   50,
   34,
   56
  ],
  "grades": {
   "knee": "GREEN",
   "torso": "GREEN",
   "elbow": "AMBER",
   "shoulder": "GREEN"
  },
  "verdict": "AMBER",
  "fix": {
   "en": "<b>Elbow 13°:</b> arms a touch straight. Soften them slightly for comfort.",
   "id": "<b>Siku 13°:</b> lengan agak terlalu lurus. Tekuk sedikit biar lebih nyaman."
  },
  "hip": 60
 },
 {
  "key": "road_race",
  "tab": {
   "en": "Race",
   "id": "Race"
  },
  "name": {
   "en": "Road, race",
   "id": "Road, race"
  },
  "strokes": 6,
  "vals": {
   "knee": 35,
   "torso": 37,
   "elbow": 20,
   "shoulder": 88
  },
  "torsoZone": [
   32,
   42,
   28,
   48
  ],
  "grades": {
   "knee": "GREEN",
   "torso": "GREEN",
   "elbow": "GREEN",
   "shoulder": "GREEN"
  },
  "verdict": "GREEN",
  "fix": {
   "en": "Everything is in range. Re-film if you change anything.",
   "id": "Semua sudah pas. Rekam ulang kalau kamu ubah sesuatu."
  },
  "hip": 51
 },
 {
  "key": "tt_tri",
  "tab": {
   "en": "TT / Tri",
   "id": "TT / Tri"
  },
  "name": {
   "en": "TT / Triathlon",
   "id": "TT / Triathlon"
  },
  "strokes": 5,
  "vals": {
   "knee": 34,
   "torso": 20,
   "elbow": 28,
   "shoulder": 83
  },
  "torsoZone": [
   12,
   28,
   8,
   34
  ],
  "grades": {
   "knee": "GREEN",
   "torso": "GREEN",
   "elbow": "GREEN",
   "shoulder": "GREEN"
  },
  "verdict": "GREEN",
  "fix": {
   "en": "<b>Torso 20°:</b> low and aero, inside the 12–28° range for a TT bike.",
   "id": "<b>Torso 20°:</b> rendah dan aero, masih di rentang 12–28° untuk sepeda TT."
  },
  "hip": 40
 },
 {
  "key": "gravel",
  "tab": {
   "en": "Gravel",
   "id": "Gravel"
  },
  "name": {
   "en": "Gravel",
   "id": "Gravel"
  },
  "strokes": 7,
  "vals": {
   "knee": 37,
   "torso": 47,
   "elbow": 22,
   "shoulder": 85
  },
  "torsoZone": [
   42,
   52,
   36,
   58
  ],
  "grades": {
   "knee": "GREEN",
   "torso": "GREEN",
   "elbow": "GREEN",
   "shoulder": "GREEN"
  },
  "verdict": "GREEN",
  "fix": {
   "en": "<b>Torso 47°:</b> a little more upright than road, inside the 42–52° gravel range.",
   "id": "<b>Torso 47°:</b> sedikit lebih tegak dari road, masih di rentang gravel 42–52°."
  },
  "hip": 59
 },
 {
  "key": "mtb",
  "tab": {
   "en": "MTB",
   "id": "MTB"
  },
  "name": {
   "en": "Mountain (MTB)",
   "id": "Gunung (MTB)"
  },
  "strokes": 6,
  "vals": {
   "knee": 42,
   "torso": 52,
   "elbow": 26,
   "shoulder": 86
  },
  "torsoZone": [
   46,
   58,
   40,
   64
  ],
  "grades": {
   "knee": "AMBER",
   "torso": "GREEN",
   "elbow": "GREEN",
   "shoulder": "GREEN"
  },
  "verdict": "AMBER",
  "fix": {
   "en": "<b>Knee 42°:</b> a little outside 30–40°. Check the camera is square-on and re-film before moving the saddle; if it still reads high, try 2–3 mm up.",
   "id": "<b>Lutut 42°:</b> sedikit di luar 30–40°. Pastikan kamera lurus dari samping dan rekam ulang dulu; kalau masih tinggi, baru naikkan sadel 2–3 mm."
  },
  "hip": 67
 },
 {
  "key": "city",
  "tab": {
   "en": "City",
   "id": "Kota"
  },
  "name": {
   "en": "City / Hybrid",
   "id": "Kota / Hybrid"
  },
  "strokes": 5,
  "vals": {
   "knee": 39,
   "torso": 62,
   "elbow": 28,
   "shoulder": 81
  },
  "torsoZone": [
   55,
   70,
   48,
   78
  ],
  "grades": {
   "knee": "GREEN",
   "torso": "GREEN",
   "elbow": "GREEN",
   "shoulder": "GREEN"
  },
  "verdict": "GREEN",
  "fix": {
   "en": "<b>Torso 62°:</b> upright, inside the 55–70° range for city and hybrid bikes.",
   "id": "<b>Torso 62°:</b> tegak, masih di rentang 55–70° untuk sepeda kota dan hybrid."
  },
  "hip": 69
 }
];
  var ZONES = { knee: [30, 40, 28, 42], elbow: [15, 30, 8, 45], shoulder: [80, 95, 70, 105] };
  function zonesFor(s) { return { knee: ZONES.knee, torso: s.torsoZone, elbow: ZONES.elbow, shoulder: ZONES.shoulder }; }
  // same scale as the analyzer's bars, so a sample bar and a real one read alike
  function scale(z) {
    var pad = Math.max(4, (z[3] - z[2]) * 0.28), lo = z[2] - pad, hi = z[3] + pad;
    return { glo: z[0], ghi: z[1], pos: function (v) { return Math.max(2, Math.min(98, (v - lo) / (hi - lo) * 100)); } };
  }

  /* root holds .figstack > svg (one per slide), .bikes button[data-i] and a .cplay button.
     It advances on its own every few seconds; hovering or focusing inside holds it, the
     pause button stops it, choosing a bike stops it, and with reduced motion it never starts. */
  function carousel(root, opts) {
    var figs = root.querySelectorAll('.figstack > svg'), btns = root.querySelectorAll('.bikes button'),
        play = root.querySelector('.cplay'), n = figs.length, i = 0, held = false,
        reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches,
        playing = !reduce, every = opts.interval || 5000;
    function label() {
      if (!play) return;
      var l = opts.labels ? opts.labels() : { pause: 'Pause slideshow', play: 'Play slideshow' };
      play.setAttribute('aria-label', playing ? l.pause : l.play);
      play.classList.toggle('paused', !playing);
    }
    function show(k, byUser) {
      i = (k + n) % n;
      for (var j = 0; j < n; j++) {
        figs[j].classList.toggle('on', j === i);
        figs[j].setAttribute('aria-hidden', String(j !== i));
        if (btns[j]) btns[j].setAttribute('aria-pressed', String(j === i));
      }
      if (byUser) { playing = false; label(); }
      opts.onShow(i, SLIDES[i]);
    }
    for (var j = 0; j < btns.length; j++) (function (j) { btns[j].addEventListener('click', function () { show(j, true); }); })(j);
    if (play) play.addEventListener('click', function () { playing = !playing; label(); });
    root.addEventListener('mouseenter', function () { held = true; });
    root.addEventListener('mouseleave', function () { held = false; });
    root.addEventListener('focusin', function () { held = true; });
    root.addEventListener('focusout', function () { held = false; });
    setInterval(function () {
      if (playing && !held && !document.hidden && root.offsetParent !== null) show(i + 1, false);
    }, every);
    label();
    show(0, false);
    return { show: show, refresh: function () { label(); opts.onShow(i, SLIDES[i]); }, index: function () { return i; } };
  }

  window.BFA_SAMPLES = { SLIDES: SLIDES, zonesFor: zonesFor, scale: scale, carousel: carousel };
})();
