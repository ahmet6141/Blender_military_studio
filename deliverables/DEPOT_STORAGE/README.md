# HG_DEPOT_01 (DEPOT_STORAGE) — doku kiti, 360° görünümler, kapı animasyonu

Bu klasör `scripts/hangar_deliverables.py DEPOT_STORAGE` ile üretildi (Blender 5.x, HERO detay).
Kit, kapılar kapalı (dinlenme pozu) olarak dışa aktarıldı.

## İçerik

| Klasör | Ne var |
|---|---|
| `texture_kit/HG_DEPOT_01_texture_kit.fbx` | Boyama için mesh: Substance Painter / Blender / UE5 |
| `texture_kit/HG_DEPOT_01_texture_kit.blend` | Aynı kit, Blender dosyası |
| `texture_kit/UV_*_4096.png` | Tam boy (4096 px) şeffaf UV tel kafes katmanı (Photoshop'ta üst katman) |
| `texture_kit/UV_*_preview.png` | 1024 px renkli önizleme (renk = MaterialID) |
| `texture_kit/texture_sets.json` | Setler, yoğunluklar, bant yerleşimi, malzeme kimlikleri |
| `turntable/` | 45° aralıkla 8 açıdan 1920x1080 viewport görüntüsü |
| `video/DEPOT_STORAGE_door_animation.mp4` | Kapı animasyonu: ana kapı aç-bekle-kapat, ray/araba yakın plan, personel kapısı |

## UV kanalları

- **UV_Paint (kanal 0)** — doku buraya çizilir. Yerleşim sete göre değişir (aşağıdaki tablo).
- **UV_Mask (kanal 1)** — her set için çakışmasız benzersiz 0..1 açılım: AO / curvature bake,
  kir-pas maskeleri. Döşemeli setlerde benzersiz kirlenme bu kanal üzerinden verilir.
- **MaterialID** vertex rengi — orijinal MB01 malzeme ayrımı (ör. Metal içinde galvaniz /
  alüminyum / kauçuk). Substance'ta *ID* bake'i için kaynak: Vertex Color.
- Tekrarlanan modüller ve aynı parçalar (cıvata, taban pabucu, braket) UV_Paint'te tek adaya
  istiflenir: birini boyamak hepsini boyar. UV_Mask'te istif yoktur.

## Doku setleri (malzeme = Substance texture set)

Yoğunluk 4096 px doku için piksel/metre. TRIM satırında "bant / benzersiz bölge".

| Set | Yerleşim | İçerik | UV_Paint px/m | UV_Mask px/m | MaterialID renkleri |
|---|---|---|---|---|---|
| `TS_Signage` | Trim bantları + benzersiz | Sign letters, number block, sign field, floor and safety markings | 1000 / 995 | 773 | HG_SignFace `#d39952`, HG_SignInk `#329ae5`, HG_SignSub `#4a37cc`, Red `#b04dcc`, White `#755fef`, Yellow `#5456f7` |
| `TS_Glazing` | Benzersiz | Glass, window backing, light lenses | 739 | 551 | Interior `#6e54d3`, LightWarm `#4848d6` |
| `TS_Gates` | Benzersiz | Main sliding gate leaves (panels, ribs, kick plates) | 218 | 250 | HG_Gate `#dd3341`, HG_GateBeacon `#9de550`, HG_GateHazard `#9160f2`, HG_GateHazardInk `#5befa7`, HG_GateLiner `#d15979`, HG_GateTrack `#343aed`, HG_GateTrim `#32e2f2` |
| `TS_Roof` | Döşemeli (seamless) | Roof skin, ridge, monitor, roof trims and bargeboards | 1024 | 45 | HG_Roof `#db5e3f`, HG_RoofDownpipe `#4153db`, HG_RoofFlashing `#f72e71`, HG_RoofLight `#ef2680`, HG_RoofLightInner `#e234c8`, HG_RoofLiner `#464bdb`, HG_RoofRainwater `#f7ef59`, HG_RoofSeam `#2cf7f3` |
| `TS_Cladding` | Döşemeli (seamless) | Wall cladding, facade modules, seams and reveals, personnel doors | 1024 | 44 | HG_Wall `#e09d50`, HG_WallCassette `#31d63c`, HG_WallLiner `#9e27d1`, HG_WallTrim `#ed34d1`, Joint `#f26a73`, RoofOlive `#2865d6` |
| `TS_Structure` | Trim bantları + benzersiz | Painted steel: portal frames, girders, jambs, headers, window frames | 122 / 127 | 91 | SteelDark `#a5ce35` |
| `TS_Concrete` | Döşemeli (seamless) | Floor slabs, apron, plinths, loading dock, landings | 1024 | 61 | Concrete `#ce48b3`, HG_Concrete_EXPOSED_0 `#542fce`, HG_Concrete_EXPOSED_1 `#37cc9f`, HG_Concrete_EXPOSED_2 `#c7ea60`, HG_Concrete_EXPOSED_3 `#a8dd63`, HG_Concrete_INDOOR_0 `#43d343`, HG_Concrete_INDOOR_1 `#cea621`, HG_Concrete_INDOOR_2 `#52f429`, HG_Concrete_INDOOR_3 `#47efe4` |
| `TS_Metal` | Trim bantları + benzersiz | Galvanised and aluminium hardware: rails, trolleys, gutters, pipes, rubber | 212 / 205 | 122 | Galvanized `#5cf23e`, HG_Alu `#5079e0`, LightGreen `#d33d32`, Rubber `#f449ef` |

Yerleşim türleri:

- **Döşemeli**: Kenarları birleşen 4 m x 4 m tek doku çiz; UV_Paint metre ölçekli, model boyunca tekrarlar.
- **Trim**: Alt kısım yatay bantlar: her bant bir profilin çevresi (V) ve boyu (U, yatayda tekrar eder); bantları yatayda kesintisiz çiz. Üst kısım benzersiz parçalar.
- **Benzersiz**: Klasik benzersiz açılım: her ada modelde tek bir yere karşılık gelir.

Structure ve Metal setlerinde 8K doku kullanırsan yoğunluk iki katına çıkar.

## UV görselleri

| Set | UV_Paint tel kafes | UV_Paint önizleme | UV_Mask tel kafes | UV_Mask önizleme |
|---|---|---|---|---|
| Signage | UV_Paint_Signage_4096.png | UV_Paint_Signage_preview.png | UV_Mask_Signage_4096.png | UV_Mask_Signage_preview.png |
| Glazing | UV_Paint_Glazing_4096.png | UV_Paint_Glazing_preview.png | UV_Mask_Glazing_4096.png | UV_Mask_Glazing_preview.png |
| Gates | UV_Paint_Gates_4096.png | UV_Paint_Gates_preview.png | UV_Mask_Gates_4096.png | UV_Mask_Gates_preview.png |
| Roof | (döşeme rehberi) | UV_Paint_Roof_preview.png | UV_Mask_Roof_4096.png | UV_Mask_Roof_preview.png |
| Cladding | (döşeme rehberi) | UV_Paint_Cladding_preview.png | UV_Mask_Cladding_4096.png | UV_Mask_Cladding_preview.png |
| Structure | UV_Paint_Structure_4096.png | UV_Paint_Structure_preview.png | UV_Mask_Structure_4096.png | UV_Mask_Structure_preview.png |
| Concrete | (döşeme rehberi) | UV_Paint_Concrete_preview.png | UV_Mask_Concrete_4096.png | UV_Mask_Concrete_preview.png |
| Metal | UV_Paint_Metal_4096.png | UV_Paint_Metal_preview.png | UV_Mask_Metal_4096.png | UV_Mask_Metal_preview.png |

## Substance Painter akışı

1. *New project* → `HG_DEPOT_01_texture_kit.fbx`, *Document resolution* 4096, *Normal map format* DirectX (UE5).
2. *UV Tile workflow* kapalı; her `TS_*` malzemesi ayrı texture set olur.
3. Bake: döşemeli setlerde UV_Paint üst üste bindiği için AO/curvature'ı **UV_Mask** kanalıyla bake et
   (Texture Set Settings → UV set), ID bake'i için *Color Source: Vertex Color*.
4. Döşemeli setlerde (Cladding, Roof, Concrete) dolgu katmanı *UV projection* + tile boyu 4 m;
   kenarları kesintisiz olmalı.
5. Dışa aktarım: *Unreal Engine 4 (Packed)* şablonu UE5 için de uygundur (BaseColor, Normal, OcclusionRoughnessMetallic).

## UE5'e alma

FBX'i *Import Uniform Scale 1.0*, *Combine Meshes* kapalı al. Malzemede UV_Paint = TexCoord 0,
maske/AO = TexCoord 1. Oyun için LOD ve UCX çarpışma setleri ayrı `export_project` çıktısındadır.
