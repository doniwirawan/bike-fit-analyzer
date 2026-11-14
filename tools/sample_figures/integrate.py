"""Wire the six bike-type figures into the landing report and the analyzer sample as a carousel.

This was a one-off migration and edits index.html/app.html in place; it will not re-run cleanly on
the already-migrated pages. To change a figure, edit bikes.json (geometry and posture), then
regenerate the <svg> blocks with bikes.build() and samples.js with the SLIDES part of this script."""
import json, re, os, math, sys
sys.path.insert(0, os.path.dirname(__file__))
import bikes
B = json.load(open(os.path.join(os.path.dirname(__file__), 'bikes.json')))
WEB = os.path.join(os.path.dirname(__file__), '..', '..', 'web')
os.chdir(WEB)

NAMES = {
 'road_endurance': (('Endurance', 'Endurance'), ('Road, endurance', 'Road, endurance')),
 'road_race':      (('Race', 'Race'), ('Road, race', 'Road, race')),
 'tt_tri':         (('TT / Tri', 'TT / Tri'), ('TT / Triathlon', 'TT / Triathlon')),
 'gravel':         (('Gravel', 'Gravel'), ('Gravel', 'Gravel')),
 'mtb':            (('MTB', 'MTB'), ('Mountain (MTB)', 'Gunung (MTB)')),
 'city':           (('City', 'Kota'), ('City / Hybrid', 'Kota / Hybrid')),
}
STROKES = dict(road_endurance=5, road_race=6, tt_tri=5, gravel=7, mtb=6, city=5)
FIX = {
 'road_endurance': ('<b>Elbow 13°:</b> arms a touch straight. Soften them slightly for comfort.',
                    '<b>Siku 13°:</b> lengan agak terlalu lurus. Tekuk sedikit biar lebih nyaman.'),
 'road_race': ('Everything is in range. Re-film if you change anything.',
               'Semua sudah pas. Rekam ulang kalau kamu ubah sesuatu.'),
 'tt_tri': ('<b>Torso 20°:</b> low and aero, inside the 12–28° range for a TT bike.',
            '<b>Torso 20°:</b> rendah dan aero, masih di rentang 12–28° untuk sepeda TT.'),
 'gravel': ('<b>Torso 47°:</b> a little more upright than road, inside the 42–52° gravel range.',
            '<b>Torso 47°:</b> sedikit lebih tegak dari road, masih di rentang gravel 42–52°.'),
 'mtb': ('<b>Knee 42°:</b> a little outside 30–40°. Check the camera is square-on and re-film before moving the saddle; if it still reads high, try 2–3 mm up.',
         '<b>Lutut 42°:</b> sedikit di luar 30–40°. Pastikan kamera lurus dari samping dan rekam ulang dulu; kalau masih tinggi, baru naikkan sadel 2–3 mm.'),
 'city': ('<b>Torso 62°:</b> upright, inside the 55–70° range for city and hybrid bikes.',
          '<b>Torso 62°:</b> tegak, masih di rentang 55–70° untuk sepeda kota dan hybrid.'),
}
LABEL = 'Example: a rider on a {name} bike, side view, with the knee, torso and elbow angles drawn on the body'
ORDER = list(B.keys())
RANK = dict(GREEN=0, AMBER=1, RED=2)

slides, figs_tagged, figs_plain = [], [], []
for k in ORDER:
    b = B[k]
    svg_t, info = bikes.build(k, b, True)
    svg_p, _ = bikes.build(k, b, False)
    # hip angle at the top of the stroke, off the drawing (the far leg is the one at the top)
    name_en = NAMES[k][1][0]
    figs_tagged.append(svg_t.replace('{label}', LABEL.format(name=name_en.lower())))
    figs_plain.append(svg_p.replace('{label}', LABEL.format(name=name_en.lower())))
    g = info['grades']
    verdict = max(g.values(), key=lambda x: RANK[x])
    slides.append(dict(key=k, tab=dict(en=NAMES[k][0][0], id=NAMES[k][0][1]), name=dict(en=NAMES[k][1][0], id=NAMES[k][1][1]),
                       strokes=STROKES[k], vals=dict(knee=info['knee'], torso=info['torso'], elbow=info['elbow'], shoulder=info['shoulder']),
                       torsoZone=bikes.TORSO_Z[k], grades=g, verdict=verdict, fix=dict(en=FIX[k][0], id=FIX[k][1]), hip=info['hip']))
    print(k, verdict, info['vals'] if 'vals' in info else '', info['shoulder'], info['hip'])

# ------------------------------------------------------------------ samples.js
JS = '''/* The sample reports: one per bike type the analyzer grades, with the figure and numbers
   drawn from that bike's geometry (scripts that built them are not shipped; the numbers are
   the angles actually drawn). Shared by the landing page and the analyzer, plus the small
   carousel both use to step through them. */
(function () {
  var SLIDES = %s;
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
      i = (k + n) %% n;
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
''' % json.dumps(slides, ensure_ascii=False, indent=1)
open('samples.js', 'w', encoding='utf-8', newline='\n').write(JS)

PAUSE = '<svg class="i-pause" viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5v14M16 5v14" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/></svg>'
PLAY = '<svg class="i-play" viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.5v13l11-6.5z" fill="currentColor"/></svg>'
def controls(indent):
    btn = ''.join(f'\n{indent}  <button type="button" data-i="{j}" aria-pressed="{str(j == 0).lower()}">{s["tab"]["en"]}</button>' for j, s in enumerate(slides))
    return (f'{indent}<div class="carctl">\n{indent}<div class="bikes" role="group" aria-label="Bike type">{btn}\n{indent}</div>\n'
            f'{indent}<button type="button" class="cplay" aria-label="Pause slideshow">{PAUSE}{PLAY}</button>\n{indent}</div>')

def stack(figs, cls, indent):
    out = [f.replace('<svg class="figure"', '<svg class="figure on"' if j == 0 else '<svg class="figure" aria-hidden="true"', 1) for j, f in enumerate(figs)]
    return f'<div class="{cls}">\n{indent}' + f'\n{indent}'.join(out) + f'\n{indent[:-2]}</div>\n' + controls(indent[:-2])

def sub1(s, pat, rep, flags=re.S):
    s2, n = re.subn(pat, lambda m: rep, s, count=1, flags=flags); assert n == 1, pat[:60]; return s2

# ------------------------------------------------------------------ landing
s = open('index.html', encoding='utf-8').read()
s = sub1(s, r'<svg class="figure" viewBox="40 6 400 312".*?</svg>', stack(figs_tagged, 'figstack', '        '))
s = sub1(s, r'<span data-i18n="mock.meta">[^<]*</span>', '<span id="bikeName">Road, endurance</span> · <span data-i18n="mock.side">side view</span>')
s = sub1(s, r'<span data-i18n="mock.verdict">Minor tweaks</span>', '<span class="vtext">Minor tweaks</span>')
s = sub1(s, r'<span data-i18n="mock.count">5 pedal strokes</span>', '<span class="ctext">5 pedal strokes</span>')
s = s.replace('<span class="vdot AMBER"></span><span class="vtext">', '<span class="vdot AMBER" id="vdot"></span><span class="vtext">', 1)
s = sub1(s, r'<p class="fixline" data-i18n="mock.fix">', '<p class="fixline" id="fixline">')
s = s.replace(' class="pill GREEN" data-i18n="legend.dialed"', ' class="pill GREEN"').replace(' class="pill AMBER" data-i18n="legend.borderline"', ' class="pill AMBER"')
# i18n: the old fixed strings go, the carousel's labels come in
for k in ('mock.meta', 'mock.verdict', 'mock.count', 'mock.fix'):
    s = re.sub(r'\n    "' + re.escape(k) + r'":\{[^\n]*\},', '', s)
s = s.replace('    "mock.knee":', '''    "mock.side":{en:"side view",id:"tampak samping"},
    "mock.strokes":{en:"pedal strokes",id:"kayuhan"},
    "vd.GREEN":{en:"Dialed",id:"Pas"}, "vd.AMBER":{en:"Minor tweaks",id:"Perlu sedikit tweak"}, "vd.RED":{en:"Fix needed",id:"Perlu diperbaiki"},
    "car.pause":{en:"Pause slideshow",id:"Jeda slideshow"}, "car.play":{en:"Play slideshow",id:"Putar slideshow"},
    "mock.knee":''', 1)
RENDER = r'''
  // The sample report steps through the six bike types. Every number comes from samples.js,
  // which holds the angles each figure actually draws and the analyzer's own target zones.
  const S = window.BFA_SAMPLES, WORD = {GREEN:'legend.dialed', AMBER:'legend.borderline', RED:'legend.fixit'};
  const L = () => document.documentElement.lang === 'id' ? 'id' : 'en';
  const tr = k => (I18N[k] && (I18N[k][L()] || I18N[k].en)) || k;
  function renderSample(i, s){
    const z = S.zonesFor(s), lang = L();
    document.getElementById('bikeName').textContent = s.name[lang] || s.name.en;
    report.querySelectorAll('.bikes button').forEach((b, j) => b.textContent = S.SLIDES[j].tab[lang] || S.SLIDES[j].tab.en);
    for (const m of ['knee', 'torso', 'elbow']){
      const row = report.querySelector('.metric[data-limb="' + m + '"]'), v = s.vals[m], g = s.grades[m], sc = S.scale(z[m]);
      row.querySelector('.val').firstChild.textContent = v + '°';
      const pill = row.querySelector('.pill'); pill.className = 'pill ' + g; pill.textContent = tr(WORD[g]);
      const zone = row.querySelector('.zone'); zone.style.left = sc.pos(sc.glo) + '%'; zone.style.width = (sc.pos(sc.ghi) - sc.pos(sc.glo)) + '%';
      row.querySelector('.mk').style.left = sc.pos(v) + '%';
      const lab = row.querySelectorAll('.rlab span');
      lab[0].textContent = sc.glo + '°'; lab[0].style.left = sc.pos(sc.glo) + '%';
      lab[1].textContent = sc.ghi + '°'; lab[1].style.left = sc.pos(sc.ghi) + '%';
    }
    document.getElementById('vdot').className = 'vdot ' + s.verdict;
    report.querySelector('.vtext').textContent = tr('vd.' + s.verdict);
    report.querySelector('.ctext').textContent = s.strokes + ' ' + tr('mock.strokes');
    document.getElementById('fixline').innerHTML = s.fix[lang] || s.fix.en;
  }
  const car = S ? S.carousel(report, {onShow: renderSample, labels: () => ({pause: tr('car.pause'), play: tr('car.play')})}) : null;
'''
s = sub1(s, r"\n  // Threads posts load on demand", RENDER + "\n  // Threads posts load on demand")
s = s.replace("    langBtns.forEach(b=>{ b.classList.toggle('active', b.dataset.lang===lang); b.setAttribute('aria-pressed', String(b.dataset.lang===lang)); });\n  }",
              "    langBtns.forEach(b=>{ b.classList.toggle('active', b.dataset.lang===lang); b.setAttribute('aria-pressed', String(b.dataset.lang===lang)); });\n    if (typeof car !== 'undefined' && car) car.refresh();\n  }", 1)
assert 'car.refresh()' in s
s = s.replace('\n<script>\n  const I18N = {', '\n<script src="samples.js"></script>\n<script>\n  const I18N = {', 1)
assert 'src="samples.js"' in s
# the moving-marker intro would replay on every slide; it now only plays on first view as before
open('index.html', 'w', encoding='utf-8', newline='\n').write(s)

# ------------------------------------------------------------------ analyzer
s = open('app.html', encoding='utf-8').read()
s = sub1(s, r'<svg class="demoimg" viewBox="40 6 400 312".*?</svg>', stack(figs_plain, 'figstack demoimg', '          '))
s = sub1(s, r'<div class="verdict"><span class="vdot AMBER"></span><span data-i18n="ex.verdict">[^<]*</span></div>',
         '<div class="verdict"><span class="vdot AMBER" id="exvdot"></span><span id="exverdict">Minor tweaks · 5 pedal strokes</span></div>')
s = sub1(s, r'<div class="foot" style="margin-top:10px" data-i18n="ex.hip">.*?</div>', '<div class="foot" style="margin-top:10px" id="exhip"></div>')
s = sub1(s, r'<ul class="fixes"><li data-i18n="ex.fix">.*?</li></ul>', '<ul class="fixes" id="exfix"></ul>')
old = s[s.index('// The sample card set is pinned'):s.index('function renderSide(){')]
s = s.replace(old, '''// The sample card set comes from samples.js: one per bike type, with the angles each figure
// actually draws, graded against that bike's own zones. It never follows the user's
// bike choice in its grading, only in which sample is showing.
let exIdx=0, exCar=null;
function renderExample(){
  const box=document.querySelector("#excards"); if(!box||!window.BFA_SAMPLES) return;
  const S=window.BFA_SAMPLES, s=S.SLIDES[exIdx], z=S.zonesFor(s);
  const ZZ={knee_flexion_bdc:z.knee, torso_from_horiz:z.torso, elbow_flexion:z.elbow, shoulder_angle:z.shoulder};
  const V={knee_flexion_bdc:s.vals.knee, torso_from_horiz:s.vals.torso, elbow_flexion:s.vals.elbow, shoulder_angle:s.vals.shoulder};
  const G={knee_flexion_bdc:s.grades.knee, torso_from_horiz:s.grades.torso, elbow_flexion:s.grades.elbow, shoulder_angle:s.grades.shoulder};
  box.innerHTML=Object.keys(ZZ).map(m=>angleCard(m,V[m],G[m],`${ZZ[m][0]}–${ZZ[m][1]}°`,ZZ)).join("");
  $("#exvdot").style.background=CSSCOL[s.verdict];
  $("#exverdict").textContent=`${t('vd.'+s.verdict)} · ${s.strokes} ${t('word.strokes')}`;
  $("#exhip").textContent=DX.hipInfo(String(s.hip));
  $("#exfix").innerHTML=`<li>${s.fix[LANG]||s.fix.en}</li>`;
  document.querySelectorAll("#example .bikes button").forEach((b,j)=>b.textContent=S.SLIDES[j].tab[LANG]||S.SLIDES[j].tab.en);
}
''')
s = s.replace('  if(bikeSel){ bikeSel.onchange=e=>{ bikeType=e.target.value; applyBikeType(); if(lastSide) renderSide(); }; } }',
              '''  if(bikeSel){ bikeSel.onchange=e=>{ bikeType=e.target.value; applyBikeType(); if(lastSide) renderSide();
    // the sample follows the bike you pick, and stops cycling once you have picked one
    const k=window.BFA_SAMPLES?BFA_SAMPLES.SLIDES.findIndex(x=>x.key===bikeType):-1; if(k>=0&&exCar) exCar.show(k,true); }; } }
if(window.BFA_SAMPLES){ exCar=BFA_SAMPLES.carousel($("#example"),{onShow:i=>{exIdx=i; renderExample();},
  labels:()=>({pause:t('car.pause'),play:t('car.play')})}); }''', 1)
assert 'exCar=BFA_SAMPLES.carousel' in s
s = s.replace('  "ex.verdict":{en:"Minor tweaks · 5 pedal strokes",id:"Perlu sedikit tweak · 5 kayuhan"},\n', '')
s = s.replace('  "ex.hip":', '  "car.pause":{en:"Pause slideshow",id:"Jeda slideshow"}, "car.play":{en:"Play slideshow",id:"Putar slideshow"},\n  "ex.hip":', 1)
s = s.replace('<script type="module">', '<script src="samples.js"></script>\n<script type="module">', 1)
open('app.html', 'w', encoding='utf-8', newline='\n').write(s)

# ------------------------------------------------------------------ shared styles
c = open('base.css', encoding='utf-8').read()
if '.figstack' not in c:
    c += '''
/* ------------------------------------------------------- sample carousel */
/* The six sample figures sit on top of each other and cross-fade; only the current one is
   visible to sight and to assistive tech. */
.figstack{display:grid}
.figstack > svg{grid-area:1 / 1;width:100%;height:auto;display:block;border-radius:12px;opacity:0;visibility:hidden;
  transition:opacity .45s var(--ease),visibility 0s linear .45s}
.figstack > svg.on{opacity:1;visibility:visible;transition-delay:0s}
.carctl{display:flex;align-items:center;gap:8px;margin:12px 0 0}
.bikes{display:flex;gap:2px;flex:1;min-width:0;overflow-x:auto;scrollbar-width:none;padding:2px;
  border:1px solid var(--line);border-radius:11px;background:var(--bg)}
.bikes::-webkit-scrollbar{display:none}
.bikes button{flex:1 0 auto;border:0;background:transparent;color:var(--mut);font:inherit;font-weight:700;font-size:.82rem;
  min-height:40px;padding:0 11px;border-radius:8px;white-space:nowrap}
.bikes button:hover{color:var(--fg)}
.bikes button[aria-pressed="true"]{background:var(--card);color:var(--fg);box-shadow:0 0 0 1px var(--line)}
.cplay{width:46px;height:46px;flex:none;border:1px solid var(--line);border-radius:11px;background:var(--card);color:var(--fg);
  display:inline-flex;align-items:center;justify-content:center}
.cplay:hover{border-color:color-mix(in srgb,var(--fg) 30%,var(--line))}
.cplay svg{width:16px;height:16px}
.cplay .i-play,.cplay.paused .i-pause{display:none}
.cplay.paused .i-play{display:block}
'''
    open('base.css', 'w', encoding='utf-8', newline='\n').write(c)
print('integrated')
