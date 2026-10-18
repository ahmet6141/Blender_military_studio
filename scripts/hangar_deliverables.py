"""Hangar deliverables, headless: texture kit, 8-angle turntable, door animation video.

    python scripts/hangar_deliverables.py DEPOT_STORAGE            # everything
    python scripts/hangar_deliverables.py DEPOT_STORAGE kit turntable
    python scripts/hangar_deliverables.py MRO_WIDEBODY video

Needs the pip `bpy` module (Blender 5.x). Turntable and video use the Workbench engine;
on a machine without a GPU, Mesa llvmpipe works:
    EGL_PLATFORM=surfaceless LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe python ...
The video also needs `imageio-ffmpeg` (pip) for the H.264 encode. Output goes to
deliverables/<PRESET>/{texture_kit,turntable,video}.
"""
import sys, os, json, shutil, subprocess, tempfile
from math import radians, cos, sin
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
import bpy
from mathutils import Vector
import mb01_military_studio as mb01
from mb01_military_studio import blender_backend as B
from mb01_military_studio.hangar_studio.contracts import preset
from mb01_military_studio.hangar_studio.blender_tools import BuildJob
from mb01_military_studio.hangar_studio import animation
from mb01_military_studio.game_ready.texture_kit import build_texture_kit

GROUND = ('Apron', 'Dock', 'Landing', 'Yard', 'Ramp', 'Kerb', 'Bollard', 'Guard', 'Bumper', 'Leveller',
          'Nosing', 'Floor', 'Grate', 'Drain', 'Walkway')
TURNTABLE = ('000_front', '045_front_left', '090_left', '135_rear_left',
             '180_rear', '225_rear_right', '270_right', '315_front_right')


def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.scale_length = 1.


def build(pid, **overrides):
    job = BuildJob(preset(pid, detail='HERO', **overrides))
    for _ in job.steps():
        pass
    return job.root


def bounds(root, shell=False):
    lo = Vector((1e9,) * 3);hi = Vector((-1e9,) * 3)
    for o in B.descendants(root):
        if o.type == 'MESH' and not (shell and any(t in o.name for t in GROUND)):
            for c in o.bound_box:
                w = o.matrix_world @ Vector(c);lo = Vector(map(min, lo, w));hi = Vector(map(max, hi, w))
    return lo, hi


def viewport_scene(res):
    sc = bpy.context.scene
    cam = bpy.data.objects.new('DELIVERY_CAM', bpy.data.cameras.new('DELIVERY_CAM'))
    sc.collection.objects.link(cam);sc.camera = cam;cam.data.clip_end = 1000
    sc.render.engine = 'BLENDER_WORKBENCH';sh = sc.display.shading
    sh.light = 'STUDIO';sh.color_type = 'MATERIAL';sh.show_cavity = True;sh.cavity_type = 'BOTH'
    sh.cavity_ridge_factor = sh.cavity_valley_factor = 1.5;sh.show_object_outline = True
    sh.show_shadows = True;sh.shadow_intensity = .35
    world = bpy.data.worlds.new('DELIVERY_BG');world.color = (.16, .18, .20);sc.world = world
    sc.display.render_aa = '8';sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100;sc.render.image_settings.file_format = 'PNG'
    return cam


def look(cam, eye, target, lens):
    cam.location = Vector(eye);cam.data.lens = lens
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()


def turntable(pid, out):
    """Eight views at 45 deg steps, 22 deg elevation; each auto-framed to 88 % of the frame."""
    fresh();root = build(pid);cam = viewport_scene((1920, 1080));sc = bpy.context.scene
    lo, hi = bounds(root);c = (lo + hi) / 2
    corners = [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
    tgt = Vector((c.x, c.y, (lo.z + hi.z) * .42));cam.data.sensor_fit = 'HORIZONTAL'
    tx = cam.data.sensor_width / (2 * 40.);ty = tx * 1080 / 1920
    out.mkdir(parents=True, exist_ok=True)
    for k, name in enumerate(TURNTABLE):
        az = radians(k * 45);el = radians(22)
        dvec = Vector((-cos(az) * cos(el), sin(az) * cos(el), sin(el)));near, far = 5., 600.
        for _ in range(50):
            d = (near + far) / 2;look(cam, tgt + dvec * d, tgt, 40);bpy.context.view_layer.update()
            inv = cam.matrix_world.inverted()
            fits = all((v := inv @ q).z < -.1 and abs(v.x / -v.z) <= tx * .88 and abs(v.y / -v.z) <= ty * .88 for q in corners)
            near, far = (near, d) if fits else (d, far)
        look(cam, tgt + dvec * far, tgt, 40)
        sc.render.filepath = str(out / f'{pid}_{name}.png');bpy.ops.render.render(write_still=True)
        print('turntable', name, flush=True)


def video(pid, out, frames_dir):
    """Three shots: gate open-hold-close (wide), track hardware (close), personnel door."""
    import imageio_ffmpeg
    fresh();root = build(pid);cam = viewport_scene((1280, 720));sc = bpy.context.scene
    sc.display.render_aa = '5';sc.render.fps = 24
    lo, hi = bounds(root);slo, shi = bounds(root, shell=True);sy = (slo.y + shi.y) / 2
    s = animation.animate_doors(root, frames=96, hold=24, loop=True)
    rail = next(o for o in B.descendants(root) if o.get('mb01_element', '').startswith('SM_MB01_HG_GateRail_0'))
    r = sum((rail.matrix_world @ Vector(v) for v in rail.bound_box), Vector()) / 8
    shots = [('a_gate_wide', range(s['start'], s['end'] + 1), ((slo.x - 27, sy - 9, 5.5), (slo.x + 3, sy, 3.6), 30)),
             ('b_tracks', range(s['start'], s['open_at'] + 1), ((r.x - 4.5, r.y - 6.5, r.z - 1.9), (r.x + .3, r.y - 2.2, r.z + .1), 34))]
    hinge = [o for o in B.descendants(root) if o.get('mb01_door') and json.loads(o['mb01_door']).get('angle')]
    if hinge:
        p = hinge[0].matrix_world.translation.copy();side = -1 if p.y > sy else 1
        shots.append(('c_personnel_door', range(s['start'], s['open_at'] + 1),
                      ((p.x - 3.2, p.y - side * 4.2, p.z + 1.9), (p.x, p.y, p.z + 1.1), 36)))
    ff = imageio_ffmpeg.get_ffmpeg_exe();parts = []
    for tag, frames, (eye, target, lens) in shots:
        look(cam, eye, target, lens);folder = frames_dir / tag
        shutil.rmtree(folder, ignore_errors=True);folder.mkdir(parents=True)
        for i, f in enumerate(frames):
            sc.frame_set(f);sc.render.filepath = str(folder / f'{i:04d}.png');bpy.ops.render.render(write_still=True)
        clip = frames_dir / f'{tag}.mp4'
        subprocess.run([ff, '-y', '-loglevel', 'error', '-framerate', '24', '-i', str(folder / '%04d.png'),
                        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'slow', str(clip)], check=True)
        parts.append(clip);print('shot', tag, len(frames), flush=True)
    listing = frames_dir / 'concat.txt';listing.write_text(''.join(f"file '{p}'\n" for p in parts))
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run([ff, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(listing), '-c', 'copy',
                    str(out / f'{pid}_door_animation.mp4')], check=True)


def kit(pid, out):
    """Texture kit on a closed-gate build (rest pose), see game_ready/texture_kit.py."""
    fresh();root = build(pid, gate_open=0., personnel_open=0.)
    shutil.rmtree(out, ignore_errors=True)
    summary = build_texture_kit(root, out, stem=preset(pid).name)
    for name, d in summary['texture_sets'].items():
        print(f"kit {name:10s} {d['mode']:6s} paint {d['paint_density_px_per_m']:7.1f} px/m  mask {d['mask_density_px_per_m']:6.1f} px/m")


MODE_TR = {'TILING': 'Döşemeli (seamless)', 'TRIM': 'Trim bantları + benzersiz', 'UNIQUE': 'Benzersiz'}
HOW_TR = {
    'TILING': 'Kenarları birleşen {tile:g} m x {tile:g} m tek doku çiz; UV_Paint metre ölçekli, model boyunca tekrarlar.',
    'TRIM': 'Alt kısım yatay bantlar: her bant bir profilin çevresi (V) ve boyu (U, yatayda tekrar eder); '
            'bantları yatayda kesintisiz çiz. Üst kısım benzersiz parçalar.',
    'UNIQUE': 'Klasik benzersiz açılım: her ada modelde tek bir yere karşılık gelir.'}


def readme(pid, root_out):
    """deliverables/<PRESET>/README.md from texture_sets.json (Turkish, user-facing)."""
    kit_dir = root_out / 'texture_kit';data = json.loads((kit_dir / 'texture_sets.json').read_text(encoding='utf-8'))
    res = data['resolution'];tile = data['tile_m'];name = data['asset']
    rows = []
    for ts, d in data['texture_sets'].items():
        paint = f"{d['paint_density_px_per_m']:.0f}"
        if d['mode'] == 'TRIM' and d.get('unique_region_density_px_per_m'):
            paint += f" / {d['unique_region_density_px_per_m']:.0f}"
        rows.append(f"| `TS_{ts}` | {MODE_TR[d['mode']]} | {d['contents']} | {paint} | {d['mask_density_px_per_m']:.0f} | "
                    + ', '.join(f"{k} `{v}`" for k, v in d['material_ids'].items()) + ' |')
    images = []
    for ts, d in data['texture_sets'].items():
        paint = f'UV_Paint_{ts}_{res}.png' if d['mode'] != 'TILING' else '(döşeme rehberi)'
        images.append(f"| {ts} | {paint} | UV_Paint_{ts}_preview.png | UV_Mask_{ts}_{res}.png | UV_Mask_{ts}_preview.png |")
    text = f"""# {name} ({pid}) — doku kiti, 360° görünümler, kapı animasyonu

Bu klasör `scripts/hangar_deliverables.py {pid}` ile üretildi (Blender 5.x, HERO detay).
Kit, kapılar kapalı (dinlenme pozu) olarak dışa aktarıldı.

## İçerik

| Klasör | Ne var |
|---|---|
| `texture_kit/{name}_texture_kit.fbx` | Boyama için mesh: Substance Painter / Blender / UE5 |
| `texture_kit/{name}_texture_kit.blend` | Aynı kit, Blender dosyası |
| `texture_kit/UV_*_{res}.png` | Tam boy ({res} px) şeffaf UV tel kafes katmanı (Photoshop'ta üst katman) |
| `texture_kit/UV_*_preview.png` | 1024 px renkli önizleme (renk = MaterialID) |
| `texture_kit/texture_sets.json` | Setler, yoğunluklar, bant yerleşimi, malzeme kimlikleri |
| `turntable/` | 45° aralıkla 8 açıdan 1920x1080 viewport görüntüsü |
| `video/{pid}_door_animation.mp4` | Kapı animasyonu: ana kapı aç-bekle-kapat, ray/araba yakın plan, personel kapısı |

## UV kanalları

- **UV_Paint (kanal 0)** — doku buraya çizilir. Yerleşim sete göre değişir (aşağıdaki tablo).
- **UV_Mask (kanal 1)** — her set için çakışmasız benzersiz 0..1 açılım: AO / curvature bake,
  kir-pas maskeleri. Döşemeli setlerde benzersiz kirlenme bu kanal üzerinden verilir.
- **MaterialID** vertex rengi — orijinal MB01 malzeme ayrımı (ör. Metal içinde galvaniz /
  alüminyum / kauçuk). Substance'ta *ID* bake'i için kaynak: Vertex Color.
- Tekrarlanan modüller ve aynı parçalar (cıvata, taban pabucu, braket) UV_Paint'te tek adaya
  istiflenir: birini boyamak hepsini boyar. UV_Mask'te istif yoktur.

## Doku setleri (malzeme = Substance texture set)

Yoğunluk {res} px doku için piksel/metre. TRIM satırında "bant / benzersiz bölge".

| Set | Yerleşim | İçerik | UV_Paint px/m | UV_Mask px/m | MaterialID renkleri |
|---|---|---|---|---|---|
""" + chr(10).join(rows) + f"""

Yerleşim türleri:

- **Döşemeli**: {HOW_TR['TILING'].format(tile=tile)}
- **Trim**: {HOW_TR['TRIM']}
- **Benzersiz**: {HOW_TR['UNIQUE']}

Structure ve Metal setlerinde 8K doku kullanırsan yoğunluk iki katına çıkar.

## UV görselleri

| Set | UV_Paint tel kafes | UV_Paint önizleme | UV_Mask tel kafes | UV_Mask önizleme |
|---|---|---|---|---|
""" + chr(10).join(images) + f"""

## Substance Painter akışı

1. *New project* → `{name}_texture_kit.fbx`, *Document resolution* {res}, *Normal map format* DirectX (UE5).
2. *UV Tile workflow* kapalı; her `TS_*` malzemesi ayrı texture set olur.
3. Bake: döşemeli setlerde UV_Paint üst üste bindiği için AO/curvature'ı **UV_Mask** kanalıyla bake et
   (Texture Set Settings → UV set), ID bake'i için *Color Source: Vertex Color*.
4. Döşemeli setlerde (Cladding, Roof, Concrete) dolgu katmanı *UV projection* + tile boyu {tile:g} m;
   kenarları kesintisiz olmalı.
5. Dışa aktarım: *Unreal Engine 4 (Packed)* şablonu UE5 için de uygundur (BaseColor, Normal, OcclusionRoughnessMetallic).

## UE5'e alma

FBX'i *Import Uniform Scale 1.0*, *Combine Meshes* kapalı al. Malzemede UV_Paint = TexCoord 0,
maske/AO = TexCoord 1. Oyun için LOD ve UCX çarpışma setleri ayrı `export_project` çıktısındadır.
"""
    (root_out / 'README.md').write_text(text, encoding='utf-8')


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    pid = args[0] if args else 'DEPOT_STORAGE';jobs = set(args[1:]) or {'kit', 'turntable', 'video'}
    mb01.register()
    root_out = REPO / 'deliverables' / pid
    if 'kit' in jobs:
        kit(pid, root_out / 'texture_kit')
    if jobs & {'kit', 'readme'}:
        readme(pid, root_out)
    if 'turntable' in jobs:
        turntable(pid, root_out / 'turntable')
    if 'video' in jobs:
        with tempfile.TemporaryDirectory() as tmp:
            video(pid, root_out / 'video', Path(tmp))
    print('DELIVERABLES DONE', root_out)
