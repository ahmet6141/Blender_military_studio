# MB01 0.4 alpha.2 — Hangar topoloji/UV kalitesi ve UE5 game-ready pipeline

Bu sürümdeki her madde gerçek Blender 5.0.1 (pip `bpy`, headless) içinde çalıştırılarak
doğrulandı; "pure Python PASS, native PENDING" dönemi bu sürümle kapandı.

## Doğrulama durumu

| Kontrol | Sonuç |
|---|---|
| `register()` — 6 modül + MB01 Studio paneli | PASS |
| `core.build` + `preview_scene` — 5 aile | PASS |
| Canlı mesh QA (`scan_live`) — 5 aile × WORKING/HERO | 10/10 PASS |
| Canlı mesh QA — 12 Hangar Studio önayarı × WORKING/HERO | 24/24 PASS |
| Kapı animasyonu (MRO_WIDEBODY: 15 kapı, 4 ray) — kapalı/açık/kapalı pozlar sözleşmeyle birebir, menteşe açısı doğru | PASS |
| Animasyonlu FBX geri-import — kanat L1 1→97. karede 18.0 m kayıyor | PASS |
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

## Yeni üs konfigürasyonları (Hangar Studio önayarları)

| Önayar | Ölçü | Çatı | Kapı | Özellik |
|---|---|---|---|---|
| `DEPOT_STORAGE` | 24 × 48 m, 10 bölme | GABLE, gümüş | 10 m, 4 kanat, camsız | arka **yükleme doku** + 1:8 rampa, panjur/servis kapısı cephe |
| `DEPOT_VEHICLE` | 30 × 42 m, 10 bölme | GABLE, grafit | 14 m, 4 kanat | yükleme doku, çift havalandırma, WOODLAND palet |
| `MRO_WIDEBODY` | 48 × 60 m, 12 bölme, 9 m saçak | MONITOR 8 m ışıklık | 36 m, 8 kanat | üreticinin üst sınırlarında geniş gövdeli bakım hangarı |
| `ALERT_QRA` | 20 × 18 m, 4 bölme | GABLE, grafit | 12 m, tam açık | kompakt alarm barınağı, 8 m apron, URBAN palet |

`HangarConfig.loading_dock`: döşeme kotunda platform (rampa 1:8, 1.15 m alçak servis
avlusu), çelik burun, kauçuk tamponlar, dok dengeleyici plakalar, babalar, korkuluk ve
`DOCK_SERVICE` (SERVICE_ROAD) portu; arka personel kapıları doğrudan platforma açılır.

## Kapı animasyonu (`hangar_studio/animation.py`)

- `animate_doors(root, frames, loop)`: her kapının `mb01_door` sözleşmesinden
  gerçek F-curve üretir — teleskopik kanatlar ray sırasına göre kademeli başlar,
  birlikte varır; personel kapıları menteşe pivotundan döner; `loop` ile
  aç–bekle–kapat döngüsü. Kapılar kapalı pozda (kanonik) dinlenir.
- `export_door_animation`: kapılar + kabuk tek animasyonlu FBX (bake). Unreal'da
  aynı sözleşme Blueprint timeline ile sürülür; FBX önizleme/sinematik teslimidir.
- Hangar panelinde ve MB01 Studio'da düğmeler: *Kapı animasyonu oluştur*,
  *Animasyonlu FBX dışa aktar*.

## Viewport incelemesi (Workbench, dokusuz) ve düzeltmeler

DEPOT_STORAGE ve MRO_WIDEBODY HERO seviyesinde 7'şer inceleme açısı + kapı
animasyonu kareleri (kapalı / %25 / %50 / %75 / açık, personel kapısı kapalı/açık)
Workbench ile çekilip tek tek incelendi.

- **Kapı başlığı boşluğu (düzeltildi).** `HG_GateHeader` açıklık üst kotunun 31.5 cm
  üstünde başlıyordu; kanat üstleri ile ray arasındaki bantta duvar düzlemi açıktı ve
  dışarıdan kapının üstünden iç makaslar görünüyordu. Başlık artık açıklık üst
  kotundan saçak kanopisine kadar iner (`z+oh … z+oh+.645`); kanat üstüne kauçuk
  üst fitil eklendi. Z-fight çifti sayısı değişmedi (DEPOT 69, MRO 151; hepsi
  önceki, gizli/alt-cm sınıfı).
- **Çift kanatlı personel kapıları** iki kanadı da ters yönlerde (−96° / +96°) dışa
  açıyor; kare incelemesinde doğrulandı.
- **Teleskopik kanat kademesi** raya göre sıralı başlıyor, cep tarafında üst üste
  biniyor; açık pozda kanatlar ray kanopisinin altında kalıyor.
- **Tabela alt yazısı** artık `HangarConfig.subtitle` (en çok 32 ASCII karakter, boş
  bırakılırsa yazılmaz): depo önayarları "STORAGE DEPOT / CGI", "VEHICLE DEPOT / CGI",
  MRO "WIDEBODY MRO / CGI", QRA "QRA ALERT / CGI". Hangar panelinde alan olarak var.

## Kimlik tabelası ve kapı ray sistemi (viewport incelemesi sonrası yeniden tasarım)

- **Tabela** (`_identity_sign`): ön alın duvarına 6 cm mesafe çubuklarıyla asılan
  antrasit mat kabin (`HG_SignFace`), fırçalanmış alüminyum çerçeve, cetvel çizgisi ve
  başlık kapakları (`HG_Alu`), sarı dikey vurgu çubuğu, 12 mm kabartma pahlı başlık
  harfleri, 6 mm alt yazı (`HG_SignSub`), iki kol üzerinde LED ışık çubuğu
  (`LightWarm` mercek). Genişlik bina genişliğinin %20'si (4.2–6.4 m), alın üçgeni
  içinde kalacak şekilde otomatik alçalır; uzun adlarda yazı boyutu küçülür.
  `label()` artık `extrude` / `bevel` taşır (çekirdek binalar eski değerleriyle kalır).
- **Ray sistemi** (`_track_system`, `_trolley`): her ray sırası için altı yarıklı
  kutu-kesit ray (üst plaka, iki gövde, iki iç koşu flanşı), rayın üstünde sürekli
  taşıyıcı kiriş, 1.5 m aralıkla kanopi tavanına bağlanan askı plakaları ve kirişler
  arası ara bağlantılar, uçlarda kauçuk tamponlu durdurucu plakalar, zeminde U-kanal
  kılavuz. Kanat başına iki araba: kanat üst rayına oturan braket, yarıktan geçen gövde,
  aks taşıyıcı ve iç flanşlarda koşan dört tekerlek (sözleşme kontrolü
  `roller_checks_design` ile boşluk içinde doğrulanır), kanal yarığında alt kılavuz
  pabucu. Eski C-profil ray (askısı rayın tabanından geçiyordu) ve düz zemin şeridi
  kaldırıldı.
- Doğrulama: 12 önayar × WORKING/HERO canlı QA 28/28 PASS; kapı animasyonu ve
  animasyonlu FBX değişmedi; EXP_COASTAL export–geri-import (kabartma harfler dahil)
  PASS; z-fight çiftleri temel değerlerde (DEPOT 69, MRO 151). HERO üçgen:
  DEPOT_STORAGE 86K → 94K, MRO_WIDEBODY 159K → 175K (8 kanat × 2 araba × 4 tekerlek).

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
