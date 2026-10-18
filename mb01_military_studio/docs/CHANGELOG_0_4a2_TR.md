# MB01 0.4 alpha.2 — Hangar topoloji/UV kalitesi ve UE5 game-ready pipeline

Bu sürümdeki her madde gerçek Blender 5.0.1 (pip `bpy`, headless) içinde çalıştırılarak
doğrulandı; "pure Python PASS, native PENDING" dönemi bu sürümle kapandı.

## Doğrulama durumu

| Kontrol | Sonuç |
|---|---|
| `register()` — 6 modül + MB01 Studio paneli | PASS |
| `core.build` + `preview_scene` — 5 aile | PASS |
| Canlı mesh QA (`scan_live`) — 5 aile × WORKING/HERO | 10/10 PASS |
| Canlı mesh QA — 8 Hangar Studio önayarı × WORKING/HERO | 16/16 PASS |
| `export_project` HQ → FBX geri-import | 66 asset, 66 UV1, 22 LOD, 6 UCX |
| `export_project` Hangar Studio EXP_COASTAL → FBX geri-import | 234 asset / 334 yerleşim, 234 UV1, 45 LOD, kapılarda UCX |
| Cycles render — HQ, HANGAR, SHELTER, Hangar Studio, Modüler | görsel regresyon yok |

Önceki durum: çekirdek HANGAR ve SHELTER ile **bütün** Hangar Studio önayarları
`BASE01 export ön-denetimi başarısız` ile export edilemiyordu (bevel kaynaklı
sıfır alanlı UV yüzeyleri). UE importer ise exporter'ın yazdığı `mb01.scene/0.2`
şemasını reddediyordu.

## Hangar geometrisi (topoloji / UV)

`mb_common.polish_part` her üretilmiş parçaya `Model.finish()` içinde uygulanır:

- **Sadece quad ve üçgen.** Silindir/boru uç kapakları (n-gon) üçgen yelpazeye
  çevrilir. Çekirdek hangar 216 → 0, Hangar Studio önayarları 472–508 → 0 n-gon.
- **Gerilmesiz UV.** Dünya eksenine hizalı olmayan her yüz (eğimli makaslar,
  dikiş çıtaları, yağmur boruları, kemer kabukları) kendi düzleminde metre
  ölçekli gerçek düzlemsel izdüşüm alır; komşu eş-düzlemli yüzlerle süreklidir.
  Gerilmiş yüz sayısı: çekirdek hangar 1416 → 0, Hangar Studio 3278–3666 → 0.
  Yazarın elle tanımladığı çatı chart'ları (oran 1) dokunulmaz.
- **Smooth + açıya göre keskin kenar.** Tüm yüzler smooth; `mesh_for` 40°
  üstü kenarları keskin işaretler. Kutular keskin kalır, 16 kenarlı borular
  yuvarlak okunur.
- **Bevel kuralı** (`mb_common.bevel_segments`): prizma/kemer/silindir
  primitifleri tek segment; HERO 3 → 2 segment (4–5 mm'de görünmez, üçüncü halka
  pencere boşluklarında UV'yi bozuyordu); gönyeli borular bevel'sız; 2 mm altı
  bevel'lar (cıvatalar, dikiş çıtaları, ızgara çubukları, kaplama çıtaları) hiç
  uygulanmaz — bu parçaların üçgen sayısını 8–9 kat şişiriyordu. HERO seviyesinde
  değerlendirilmiş üçgen: çekirdek hangar 104K → 43K, EXP_COASTAL 184K → 102K,
  DAYLIGHT_MRO 173K → 95K; sıfır n-gon, sıfır non-manifold, sıfır dejenere,
  sıfır sıfır-alanlı UV (sadece zemin işaretleri, tasarım gereği açık düzlemler).
- **Z-fighting** (aynı düzlemde aynı yöne bakan çakışan yüzler) poligon kırpma
  dedektörüyle bulunup kaynağında düzeltildi: ışıklık dikmeleri ray çerçevesinden
  1 cm taşkın, damlalık 1 cm kısa; köşe kapakları üst üste binmek yerine alın
  alına; drenaj kenar çıtası uç blokların arasında; klerestori dikmeleri 1 cm
  taşkın; portal makasları mahyada yeni `RidgeSplice` plakası altında kısa
  biter; sürgülü kapı kanatları 2 cm bindirme yerine 4 mm derzle buluşur;
  `rect_frame` başlık/denizlik tam boy dikmelerin arasına oturur.
  Görünür çakışan yüz çifti: çekirdek hangar 321 → 139 (kalanlar döşeme altı),
  DAYLIGHT_MRO 424 → 248 (kalanlar duvar içinde gizli).
- AS07 (SHELTER) adaptöründe vendor bevel değerleri 4 mm ile sınırlandı,
  oluk/boru ve duvar ekipmanı bevel'sız; vendor kaynağı değiştirilmedi.

## UE5 game-ready pipeline (`game_ready/ue5.py`, `exporter.py`)

- **UV1_Lightmap**: her static mesh için eş-düzlemli UV0 adalarından
  shelf-pack ile 0..1 benzersiz lightmap kanalı (saf veri, edit-mode operatörü
  yok; 49K üçgenli parçada 0.4 s).
- **Gerçek LOD'lar**: LOD1 = aynı primitifler bevel modifier'sız (silüet ve UV
  aynı, üçgen ≈ 1/8); LOD2 = LOD1'in %50 collapse'ı, yalnız küçültüyorsa.
  600 üçgen altı asset'ler LOD0 ile kalır. Monotonluk kontrolü manifestte.
- **UCX_ collision**: üreticilerin primitif başına yazdığı collision kutuları
  nesne üzerinde saklanır (`mb01_collision_boxes`) ve FBX'e `UCX_<asset>_NN`
  olarak girer; kapı/pencere boşlukları açık kalır. 48 kutudan fazlası
  complex-as-simple'da kalır. Kapılar tek hull taşır.
- Manifest `mb01.scene/0.3`: asset başına `lods`, `collision_hulls`,
  `uv1_lightmap`, `triangles`.
- `unreal/MB01_Import.py`: 0.1–0.3 şemalarını kabul eder, LOD'ları
  `StaticMeshEditorSubsystem.import_lod` ile bağlar, `light_map_coordinate_index=1`.

## Diğer

- `schema.py` → `docs/ASSET_SCHEMA.json` / `.html`: aile → grup → parça ağacı,
  port uyumluluk matrisi (SW01/AF01 dahil), hangar cephe grameri, modül
  kataloğu, materyal rolleri, game-ready politikası. Elle yazılmaz.
- `preview_scene()` Blender 5.0 Sky Texture (`NISHITA` → `MULTIPLE_SCATTERING`).
- Materyal: `wear` ile ölçeklenen nesne-uzayı kir/aşınma katmanı; doku
  çözünürlük denetimi (`materials.resolution_report`) game-ready audit'e bağlı.
- MB01 Studio paneli: Build / Materials / QA / Export sekmeli tek ön yüz.

## Bilinen sınırlar

- Doku kütüphanesi hâlâ 1K/2K karışık (Concrete/Plaster/Asphalt 2K, diğer 5 aile
  1K); audit uyarır, dosyalar değişmedi.
- Hangar Studio için tek `mb01_config` köprüsü dışında generator collision
  kutusu yok; kabuklar complex-as-simple ile gider.
- Unreal tarafı hâlâ hedef projede koşturulmadı; importer kodu UE 5.x Python
  API'sine göre yazıldı.
