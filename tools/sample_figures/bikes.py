"""Six sample figures, one per bike type the analyzer knows, each built from that bike's
geometry (mm, 0.18 px/mm) and a rider solved so the drawn angles are exactly the quoted ones.
The shoulder angle is not imposed: it is measured off the finished drawing, like the tool would."""
import math, json

S = 0.18
GROUND = 299
THIGH, SHIN, TORSO, UARM, FARM = 440*S, 430*S, 520*S, 300*S, 255*S

def sub(a, b): return (a[0]-b[0], a[1]-b[1])
def add(a, b): return (a[0]+b[0], a[1]+b[1])
def mul(a, k): return (a[0]*k, a[1]*k)
def ln(a): return math.hypot(*a)
def unit(a): l = ln(a); return (a[0]/l, a[1]/l)
def P(p): return f'{p[0]:.1f} {p[1]:.1f}'
def two_link(p0, p2, l1, l2, side):
    d = ln(sub(p2, p0)); u = unit(sub(p2, p0))
    a = (l1*l1 - l2*l2 + d*d) / (2*d); h = math.sqrt(max(l1*l1 - a*a, 0))
    return add(add(p0, mul(u, a)), mul((u[1]*side, -u[0]*side), h))
def place(p0, interior, l1, l2, direction):
    th = math.radians(interior)
    return add(p0, mul(unit(direction), math.sqrt(l1*l1 + l2*l2 - 2*l1*l2*math.cos(th))))
def angle(a, b, c):
    v1, v2 = sub(a, b), sub(c, b)
    return math.degrees(math.acos((v1[0]*v2[0]+v1[1]*v2[1])/(ln(v1)*ln(v2))))
def arc(center, a, b, r):
    u1, u2 = unit(sub(a, center)), unit(sub(b, center))
    p1, p2 = add(center, mul(u1, r)), add(center, mul(u2, r))
    sweep = 1 if (u1[0]*u2[1] - u1[1]*u2[0]) > 0 else 0
    return f'M{P(p1)} A{r} {r} 0 0 {sweep} {P(p2)}'

# geometry per bike type: wheel radius, tyre width, seat angle, wheelbase, bb drop, stack, reach,
# seat-tube length, and the rider's posture (knee flexion, torso from horizontal, elbow flexion,
# and how steeply the arm drops to the grips)
BIKES = {
 'road_endurance': dict(R=340, tyre=7,  sta=73.5, wb=990,  drop=70, stack=570, reach=385, st=520, knee=38, torso=48, elbow=13, arm=40, bar='drop'),
 'road_race':      dict(R=338, tyre=6,  sta=74,   wb=975,  drop=70, stack=535, reach=395, st=520, knee=35, torso=37, elbow=20, arm=46, bar='drop'),
 'tt_tri':         dict(R=338, tyre=6,  sta=78,   wb=990,  drop=70, stack=500, reach=420, st=500, knee=34, torso=20, elbow=28, arm=64, bar='tt'),
 'gravel':         dict(R=355, tyre=10, sta=73,   wb=1030, drop=75, stack=590, reach=380, st=500, knee=37, torso=47, elbow=22, arm=44, bar='flare'),
 'mtb':            dict(R=372, tyre=13, sta=76,   wb=1180, drop=35, stack=625, reach=450, st=430, knee=42, torso=52, elbow=28, arm=50, bar='flat'),
 'city':           dict(R=350, tyre=9,  sta=70,   wb=1080, drop=60, stack=640, reach=365, st=480, knee=39, torso=62, elbow=20, arm=34, bar='swept'),
}

G, A, RD = '#2ea44f', '#e0912f', '#f0564d'
FRAME, TYRE, BODY = '#626c7d', '#3b4250', '#8a94a6'
ZONES = dict(knee=[30,40,28,42], elbow=[15,30,8,45], shoulder=[80,95,70,105])
TORSO_Z = dict(road_endurance=[40,50,34,56], road_race=[32,42,28,48], tt_tri=[12,28,8,34],
               gravel=[42,52,36,58], mtb=[46,58,40,64], city=[55,70,48,78])
def grade(v, z):
    glo, ghi, rlo, rhi = z
    return 'RED' if v < rlo or v > rhi else ('AMBER' if v < glo or v > ghi else 'GREEN')
COLOR = dict(GREEN=G, AMBER=A, RED=RD)

def build(key, b, tagged):
    L = (lambda n: f' data-limb="{n}"') if tagged else (lambda n: '')
    R = b['R']*S
    rear = (150 - (b['wb']-990)*S*0.35, GROUND - R)
    front = (rear[0] + b['wb']*S, rear[1])
    bb = (rear[0] + 410*S, rear[1] + b['drop']*S)
    sta = math.radians(b['sta']); seat_dir = (-math.cos(sta), -math.sin(sta))
    st_top = add(bb, mul(seat_dir, b['st']*S))
    head_top = (bb[0] + b['reach']*S, bb[1] - b['stack']*S)
    head_bot = add(head_top, (math.cos(math.radians(72))*140*S, math.sin(math.radians(72))*140*S))
    crank = 172.5*S
    pedal = add(bb, (crank*math.sin(math.radians(8)), crank*math.cos(math.radians(8))))
    far_pedal = sub(mul(bb, 2), pedal)
    ankle = add(pedal, (-60*S, -62*S))
    hip = place(ankle, 180-b['knee'], THIGH, SHIN, seat_dir)
    knee = two_link(hip, ankle, THIGH, SHIN, +1)
    saddle = add(hip, (5, 9))
    t = math.radians(b['torso'])
    shoulder = add(hip, (TORSO*math.cos(t), -TORSO*math.sin(t)))
    a = math.radians(b['arm'])
    wrist = place(shoulder, 180-b['elbow'], UARM, FARM, (math.cos(a), math.sin(a)))
    elbow = two_link(shoulder, wrist, UARM, FARM, -1)
    ha = math.radians(b['torso'] + 10)
    head = add(shoulder, (26*math.cos(ha), -26*math.sin(ha)))
    far_ankle = add(far_pedal, (-60*S, -62*S))
    far_knee = two_link(hip, far_ankle, THIGH, SHIN, +1)
    shoulder_ang = angle(hip, shoulder, elbow)
    check = (180-angle(hip, knee, ankle), 180-angle(shoulder, elbow, wrist),
             math.degrees(math.atan2(hip[1]-shoulder[1], shoulder[0]-hip[0])))

    # cockpit: built around the hands, from the head tube
    stem_base = add(head_top, (0, -6))
    kind = b['bar']; cockpit = ''
    if kind in ('drop', 'flare'):
        hood = add(wrist, (4, 5)); clamp = add(hood, (-78*S, 2))
        flare = 'q9 2 8 13 q-1 13 -13 15' if kind == 'flare' else 'q7 2 6 12 q-1 12 -11 14'
        cockpit = f'<path d="M{P(head_top)} L{P(stem_base)} L{P(clamp)}" stroke-width="4"/><path d="M{P(clamp)} L{P(hood)} {flare}" stroke-width="3.5"/>'
    elif kind == 'tt':
        grip = add(wrist, (3, 4)); clamp = add(grip, (-46*S, -4))
        ext_start = add(clamp, (0, -9)); ext_end = add(ext_start, (300*S, -2))
        cockpit = (f'<path d="M{P(head_top)} L{P(stem_base)} L{P(clamp)}" stroke-width="4"/>'
                   f'<path d="M{P(clamp)} Q{P(add(grip, (0, -6)))} {P(grip)}" stroke-width="4"/>'
                   f'<path d="M{P(ext_start)} L{P(ext_end)} q4 0 5 -4" stroke-width="3"/>'
                   f'<path d="M{P(add(ext_start, (-2, 0)))} l0 -4 h14" stroke-width="3"/>')
    elif kind == 'flat':
        grip = add(wrist, (2, 4)); clamp = add(grip, (-8, 3))
        cockpit = (f'<path d="M{P(head_top)} L{P(stem_base)} L{P(clamp)}" stroke-width="4.5"/>'
                   f'<path d="M{P(clamp)} L{P(grip)}" stroke-width="4"/><path d="M{P(add(grip, (-4, 1)))} L{P(add(grip, (4, -1)))}" stroke-width="7"/>')
    else:  # swept-back city bar
        grip = add(wrist, (2, 4)); clamp = add(grip, (16, 4))
        cockpit = (f'<path d="M{P(head_top)} L{P(add(stem_base, (0, -8)))} L{P(clamp)}" stroke-width="4.5"/>'
                   f'<path d="M{P(clamp)} Q{P(add(grip, (8, -8)))} {P(grip)}" stroke-width="4"/><path d="M{P(add(grip, (-5, 0)))} L{P(add(grip, (5, 0)))}" stroke-width="7"/>')
    stem_len = ln(sub(clamp, stem_base))/S

    # frame
    if kind == 'swept':   # step-through: the top tube drops from the head tube to low on the seat tube
        low = add(bb, mul(seat_dir, b['st']*S*0.35))
        frame = (f'<path d="M{P(rear)} L{P(bb)} L{P(st_top)} L{P(rear)} Z"/>'
                 f'<path d="M{P(head_top)} L{P(head_bot)} L{P(bb)}"/>'
                 f'<path d="M{P(add(head_top, (2, 8)))} Q{P(add(low, (30, -20)))} {P(low)}"/>')
    else:
        frame = (f'<path d="M{P(rear)} L{P(bb)} L{P(st_top)} Z"/>'
                 f'<path d="M{P(st_top)} L{P(head_top)} L{P(head_bot)} L{P(bb)}"/>')
    if kind == 'flat':   # suspension fork: stanchions into fatter lowers
        mid = add(head_bot, mul(sub(front, head_bot), 0.45))
        fork = f'<path d="M{P(head_bot)} L{P(mid)}" stroke-width="5"/><path d="M{P(mid)} L{P(front)}" stroke-width="9"/>'
    else:
        fork = f'<path d="M{P(head_bot)} Q{P(add(front, (-14, -30)))} {P(front)}" stroke-width="4"/>'
    fw = 7 if kind == 'tt' else 5

    spokes = ''.join(
        f'M{P(add(c, (R*.86*math.cos(th), R*.86*math.sin(th))))} L{P(add(c, (-R*.86*math.cos(th), -R*.86*math.sin(th))))}'
        for c in (rear, front) for th in [math.radians(k*30+8) for k in range(6)])
    tyre = b['tyre']
    knobs = (f'<circle cx="{rear[0]:.1f}" cy="{rear[1]:.1f}" r="{R:.1f}" stroke="#4a5262" stroke-width="{tyre+3}" stroke-dasharray="2 3.2"/>'
             f'<circle cx="{front[0]:.1f}" cy="{front[1]:.1f}" r="{R:.1f}" stroke="#4a5262" stroke-width="{tyre+3}" stroke-dasharray="2 3.2"/>') if kind == 'flat' else ''
    disc = f'<circle cx="{rear[0]:.1f}" cy="{rear[1]:.1f}" r="{R-4:.1f}" fill="#262c36"/>' if kind == 'tt' else ''
    extras = ''
    if kind == 'swept':   # mudguards and a rack
        extras = (f'<path d="{arc(rear, add(rear, (-R, -6)), add(rear, (R*0.5, -R*0.9)), round(R+8, 1))}" stroke="#4d5566" stroke-width="3"/>'
                  f'<path d="{arc(front, add(front, (-R*0.6, -R*0.85)), add(front, (R, -4)), round(R+8, 1))}" stroke="#4d5566" stroke-width="3"/>'
                  f'<path d="M{P(add(rear, (-30, -R-14)))} L{P(add(st_top, (-4, 4)))} M{P(add(rear, (-22, -R-14)))} L{P(rear)}" stroke="#4d5566" stroke-width="3"/>')

    g_knee, g_torso, g_elbow = grade(b['knee'], ZONES['knee']), grade(b['torso'], TORSO_Z[key]), grade(b['elbow'], ZONES['elbow'])
    horiz_end = add(hip, (40, 0))
    svg = f'''<svg class="figure" viewBox="40 6 400 312" role="img" aria-label="{{label}}">
          <rect x="40" y="6" width="400" height="312" rx="14" fill="#0e131b" style="fill:var(--figure)"/>
          <ellipse cx="{(rear[0]+front[0])/2:.1f}" cy="{GROUND+3}" rx="155" ry="5" fill="#000" opacity=".35"/>
          <line x1="64" y1="{GROUND+1}" x2="416" y2="{GROUND+1}" stroke="#262d39" stroke-width="1.5"/>
          <g fill="none" stroke="{BODY}" stroke-opacity=".09" stroke-linecap="round" stroke-linejoin="round">
            <path d="M{P(hip)} L{P(far_knee)}" stroke-width="17"/><path d="M{P(far_knee)} L{P(far_ankle)}" stroke-width="12"/>
          </g>
          <path d="M{P(far_pedal)} L{P(bb)}" stroke="#4a5262" stroke-width="4" stroke-linecap="round"/>
          <g fill="none">
            <path d="{spokes}" stroke="#2a313d" stroke-width="1"/>{disc}{knobs}
            <circle cx="{rear[0]:.1f}" cy="{rear[1]:.1f}" r="{R:.1f}" stroke="{TYRE}" stroke-width="{tyre}"/>
            <circle cx="{front[0]:.1f}" cy="{front[1]:.1f}" r="{R:.1f}" stroke="{TYRE}" stroke-width="{tyre}"/>
            <circle cx="{rear[0]:.1f}" cy="{rear[1]:.1f}" r="{R-tyre/2-4:.1f}" stroke="#2f3643" stroke-width="2"/>
            <circle cx="{front[0]:.1f}" cy="{front[1]:.1f}" r="{R-tyre/2-4:.1f}" stroke="#2f3643" stroke-width="2"/>{extras}
          </g>
          <g fill="#4d5566"><circle cx="{rear[0]:.1f}" cy="{rear[1]:.1f}" r="3.5"/><circle cx="{front[0]:.1f}" cy="{front[1]:.1f}" r="3.5"/></g>
          <g fill="none" stroke="{FRAME}" stroke-width="{fw}" stroke-linecap="round" stroke-linejoin="round">
            {frame}{fork}
            <path d="M{P(st_top)} L{P(add(saddle, (-1, 3)))}" stroke-width="3.5"/>
            {cockpit}
          </g>
          <path d="M{P(add(saddle, (-17, 1)))} Q{P(add(saddle, (-2, -4)))} {P(add(saddle, (15, 1)))} L{P(add(saddle, (-12, 4)))} Z" fill="#7a8496"/>
          <circle cx="{bb[0]:.1f}" cy="{bb[1]:.1f}" r="13" fill="none" stroke="#7a8496" stroke-width="2.5"/>
          <path d="M{P(bb)} L{P(pedal)}" stroke="#97a1b2" stroke-width="4.5" stroke-linecap="round"/>
          <rect x="{pedal[0]-7:.1f}" y="{pedal[1]-2:.1f}" width="14" height="4" rx="2" fill="#97a1b2"/>
          <g fill="none" stroke="{BODY}" stroke-opacity=".34" stroke-linecap="round" stroke-linejoin="round">
            <path d="M{P(hip)} L{P(shoulder)}" stroke-width="26"/>
            <path d="M{P(hip)} L{P(knee)}" stroke-width="19"/>
            <path d="M{P(knee)} L{P(ankle)}" stroke-width="13"/>
            <path d="M{P(ankle)} L{P(add(pedal, (9, -1)))}" stroke-width="8"/>
            <path d="M{P(shoulder)} L{P(elbow)}" stroke-width="12"/>
            <path d="M{P(elbow)} L{P(wrist)}" stroke-width="10"/>
            <path d="M{P(shoulder)} L{P(add(head, mul(unit(sub(shoulder, head)), 10)))}" stroke-width="10"/>
          </g>
          <circle cx="{head[0]:.1f}" cy="{head[1]:.1f}" r="12" fill="{BODY}" fill-opacity=".34"/>
          <path d="M{P(add(head, (-14, 2)))} Q{P(add(head, (-8, -17)))} {P(add(head, (10, -11)))} L{P(add(head, (16, -2)))} Z" fill="#6f7a8d"/>
          <g fill="none" stroke-linecap="round" stroke-linejoin="round">
            <g{L("torso")}><path d="M{P(hip)} L{P(horiz_end)}" stroke="#8792a6" stroke-width="1.5" stroke-dasharray="3 4"/>
              <path d="{arc(hip, horiz_end, shoulder, 24)}" stroke="{COLOR[g_torso]}" stroke-width="2.5"/>
              <path d="M{P(hip)} L{P(shoulder)}" stroke="{COLOR[g_torso]}" stroke-width="5"/></g>
            <g{L("knee")}><path d="{arc(knee, hip, ankle, 15)}" stroke="{COLOR[g_knee]}" stroke-width="2.5"/>
              <path d="M{P(hip)} L{P(knee)} L{P(ankle)}" stroke="{COLOR[g_knee]}" stroke-width="5"/></g>
            <g{L("elbow")}><path d="{arc(elbow, shoulder, wrist, 12)}" stroke="{COLOR[g_elbow]}" stroke-width="2.5"/>
              <path d="M{P(shoulder)} L{P(elbow)} L{P(wrist)}" stroke="{COLOR[g_elbow]}" stroke-width="5"/></g>
          </g>
          <g fill="#fff" stroke="#0e131b" stroke-width="1.5">
            <circle cx="{hip[0]:.1f}" cy="{hip[1]:.1f}" r="4.5"/><circle cx="{knee[0]:.1f}" cy="{knee[1]:.1f}" r="4.5"/><circle cx="{ankle[0]:.1f}" cy="{ankle[1]:.1f}" r="4.5"/>
            <circle cx="{shoulder[0]:.1f}" cy="{shoulder[1]:.1f}" r="4.5"/><circle cx="{elbow[0]:.1f}" cy="{elbow[1]:.1f}" r="4.5"/><circle cx="{wrist[0]:.1f}" cy="{wrist[1]:.1f}" r="4.5"/>
          </g>
          <g font-family="Mona Sans,system-ui,sans-serif" font-weight="800" font-size="13" text-anchor="middle">
            <g{L("torso")}><rect x="{hip[0]-46:.1f}" y="{hip[1]-48:.1f}" width="44" height="21" rx="10.5" fill="{COLOR[g_torso]}"/><text x="{hip[0]-24:.1f}" y="{hip[1]-33:.1f}" fill="#0e131b">{b['torso']}&#176;</text></g>
            <g{L("knee")}><rect x="{knee[0]+14:.1f}" y="{knee[1]-10:.1f}" width="44" height="21" rx="10.5" fill="{COLOR[g_knee]}"/><text x="{knee[0]+36:.1f}" y="{knee[1]+5:.1f}" fill="#0e131b">{b['knee']}&#176;</text></g>
            <g{L("elbow")}><rect x="{elbow[0]-2:.1f}" y="{elbow[1]-40:.1f}" width="44" height="21" rx="10.5" fill="{COLOR[g_elbow]}"/><text x="{elbow[0]+20:.1f}" y="{elbow[1]-25:.1f}" fill="#0e131b">{b['elbow']}&#176;</text></g>
          </g>
        </svg>'''
    info = dict(key=key, knee=b['knee'], torso=b['torso'], elbow=b['elbow'], shoulder=round(shoulder_ang),
                grades=dict(knee=g_knee, torso=g_torso, elbow=g_elbow, shoulder=grade(round(shoulder_ang), ZONES['shoulder'])),
                stem=round(stem_len), clamp=clamp, bb=bb, hip=round(angle(shoulder, hip, far_knee)), check=[round(c, 1) for c in check])
    return svg, info

if __name__ == '__main__':
    for k, b in BIKES.items():
        _, i = build(k, b, False)
        print(k, i)
