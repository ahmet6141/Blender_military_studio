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

## Tabela tasarımı v2 ve doku kiti

- **Tabela**: tek oranlı ızgara (birim = panel yüksekliği H). Amber numara bloğu
  (H x H) + antrasit ad alanı; başlık, alüminyum çizgi ve aralıklı alt yazı aynı sol
  kenarda; eşit kenar boşlukları; alüminyum çerçeve; gölge boşluklu gizli taşıyıcı.
  Ad hangar adından çözülür (`HG_VEHICLE_DEPOT_01` → "VEHICLE DEPOT" + "01"), alt yazı
  görev satırıdır. Harfler paketlenmiş Big Shoulders Bold (SIL OFL 1.1) ile kabartma;
  denenen diğer fontlar Blender'da bozuk glif dolgusu verdiği için alınmadı.
  `blender_backend.label_object`: font, aralık, cap-height / azami genişlik sığdırma,
  görünür glif sınırına göre hizalama.
- **Doku kiti** (`game_ready/texture_kit.py`): her doku seti kendi yerleşimiyle —
  DÖŞEMELİ (Cladding, Roof, Concrete: 4 m seamless, 4K'da 1024 px/m), TRIM (Structure,
  Metal, Signage: uzun elemanlar kesit-çevresi bantları, kalan parçalar aynı yoğunlukta
  benzersiz), BENZERSİZ (Gates, Glazing). UV_Paint (0) + çakışmasız UV_Mask (1),
  MaterialID vertex rengi, aynı parçalar UV_Paint'te istiflenir. Çıktı: FBX, .blend,
  set başına tam boy tel kafes + önizleme PNG, `texture_sets.json`.
- `scripts/hangar_deliverables.py`: doku kiti + 8 açılı turntable + kapı animasyon
  videosu (3 çekim, H.264) + Türkçe README. `deliverables/DEPOT_STORAGE/` ilk çıktı.
- Doğrulama: 12 önayar × WORKING/HERO canlı QA 28/28 PASS; kit FBX geri-import:
  263 nesne, 2 UV kanalı, 8 TS_ malzemesi, sıfır alanlı UV_Paint yüzü 0.

## Kapı, duvar paneli ve çatı detay geçişi (yakın plan gerçekçilik)

Dört alan (ana kapı, duvar kaplaması, çatı, personel kapıları) ayrı ayrı tasarlandı,
çekişmeli tasarım incelemesinden geçti, kendi worktree'lerinde uygulandı, dokusuz
yakın plan render'larla iki tur sanat yönetmeni incelemesi ve düzeltme turu yapıldı,
sonra birleştirildi.

- **Duvar kaplaması** (`modular/geometry.py` wall/clad/profile_sheet/opening_trims/louvre/
  cassettes, `hangar_studio/geometry.py` _facades/_copy_module): 35 mm derin, 250 mm
  adımlı trapez profilli çelik sac (tepe ortası ritmi, modül birleşimleri tepe tepeye),
  geri çekilmiş çekirdek, taban damlalık flaşingi, saçak trimi, HERO'da vida sıraları,
  pencere/menfez/kapı çevresinde başlık flaşingi, söve trimleri, eğimli denizlik;
  baskı kapaklı alüminyum camlama, gömülü kanatlı menfezler + kuş teli, kaset paneller
  gölge derzli, köşe dönüş kaplaması ve kenetli köşe açısı; ön cep, başlık ve alınlar aynı
  sac ile kaplı.
- **Ana kapı kanatları** (`_gates`, `_track_system`): çelik çerçeveli kanat, dış yüzde
  trapez sac, üst cam/polikarbon bandı, alt fırça/kauçuk conta, düşey kenar contaları ve
  bindirmeli karşılaşma dikmeleri, tekme sacı, çekme kolları, öndeki kanatlarda yer
  sürgüsü ve sarı-siyah ikaz şeritleri; kapı başı pelmeti ve koyu sofit; park eden
  kanatları saklayan **kapı evleri** (kaplı uç duvarlar, köşe açısı, üst trim); kısa
  kanat yığınlarında kapı evi ve ray kanopisi yığının 300 mm ötesinde biter.
- **Çatı** (`_roof` ve yardımcıları, `_gutters`): 58 mm yükseklikli konik dikişli standing-seam
  paneller (saçakta konik dikiş uçları), mahya/saçak/bordür flaşingleri ~3 m'de bindirme
  ve bağlantı kayışlarıyla, kutu oluk (geniş gövdeli hangarda 260 mm / DN125 iniş),
  duvar sacına oturan boru kelepçeleri, opal GRP çatı ışıklıkları (içeriden açık renkli
  nervürlü), mahya havalandırıcıları, havalandırma bacaları, düşme önleme hattı;
  çatı altında nervürlü astar sac, aşık kulakları; fener (lantern) çatısında kaplı uç
  duvarlar, nervürlü alt yüz ve ara aşıklar; iniş boruları güneşlik kanatlarından
  ≥ 300 mm uzak.
- **Personel kapıları** (`entry`, `_canopy`): preslenmiş çelik kasa ve stop, 50 mm
  kenarlı kanat, görünür menteşeler, levye kol + rozet + silindir, kapı kapatıcı, tekme
  sacı, eşik, iç tarafta panik bar (çift kapıda aktif/pasif kanat ve kayıt), duvar
  trimleriyle birleşen kapı açıklığı, duvar tipi aydınlatma, kanopi kolları ve kart
  okuyucu sac tepelerine hizalı. HQ/UNIT/SUPPORT kapıları değişmedi (digest korumalı).
- **Yapı**: uç portal çerçeveleri kaplama bölgesinin içine alındı (`_frame_y`); taban
  plakaları ve saçak bağlantı plakaları flanş yüzünün 3 mm içinde biter.
- Doğrulama: 12 önayar × WORKING/HERO `verify_fast` PASS, 100 modül PASS, HQ/UNIT/SUPPORT
  geometrisi bayt bayt aynı; aynı yöne bakan çakışık yüz çifti (z-fighting adayı)
  her önayarda ~%60 azaldı (MRO_WIDEBODY 385 → 136); HERO bevel öncesi üçgen yaklaşık
  iki katı (MRO_WIDEBODY 51.8K → 106.7K, DEPOT_STORAGE 29.5K → 62.0K).
- Bilinen eksikler: düşme önleme hattına erişim merdiveni ve fener duman tahliye
  kapakları üçgen bütçesi nedeniyle yok; kapı kapatıcı kolu kanatla rijit döner.

### Son yakın plan incelemesi ve düzeltmeler

88 son yakın plan görüntüsü bağımsız ve çekişmeli bir incelemeden geçti; 12 kusur
doğrulandı ve dört alanda düzeltildi (her alan ayrı inceleme + onarım turu).

- **Portal çerçeve** (`_structure`, `_frame_y`): kolon gövdesi çerçeve düzleminde, iç
  flanş hangara bakar (önceden 90° dönüktü); saçakta cıvatalı alın plakası, konik guse
  (haunch) ve kolon başlık plakası, mahyada gönye kesimli kiriş + alın plakası çifti ve
  mahya gusesi (galvaniz bloklar kaldırıldı, V boşluğu kapandı); dik çatılarda başlık
  plakası kirişe oturur, saçak aşığı içeri kayar. Aşıklar ~1,7 m aralıkla (MRO'da 4 m
  idi), kolon başlarında saçak aşığı, beşik çatıda çift mahya aşığı; uç çerçevelerde
  ankraj cıvataları yalnız hangar tarafında.
- **Ana kapı** (`_gates`): cam bandı kayıtları dikme ızgarasında (dikme bant boyunca
  kayıt olarak devam eder), öndeki dikmede iç astar kapatma şeridi, pelmet ve kanopi
  alınlığı ~3 m boylarda ek kayışlarıyla (fenerlerden 200 mm uzak); kapı başlığının
  astar önündeki şeridi uç kolonun iç flanşından 3 mm önce biter.
- **Arka cephe** (`_facades`, `_monitor`): arka kaplama yarım adım kaydırıldı; kart
  okuyucu ve duvar armatürü artık sac tepesine oturur (önceden oluk üzerinde 34 mm
  boşlukta asılıydı); fener uç duvar köşe triminin ayağı eğimi izleyip taban
  flaşingine gömülür.
- **Duvar açıklıkları** (`opening_trims`, `_shaded`): denizlik flaşingi söve triminin
  50 mm ötesine uzanır, uç dönüşleri kesit boyunca kalkar (siyah çentik yok); güneşlik
  bölmesinde kanatlar .36 eğim sınırına kadar oluk tabanının ≥ 250 mm altında.
- Doğrulama: `verify_fast` 12 önayar × WORKING/HERO PASS, 100 modül PASS; aynı yöne
  bakan çakışık yüz çifti 10 önayarda 0, DEPOT önayarlarında 7 (rampa); canlı Blender
  mesh QA 28/28 PASS (12 önayar + CORE HANGAR/SHELTER, WORKING/HERO). HERO bevel
  öncesi üçgen: MRO_WIDEBODY 114.6K, DEPOT_STORAGE 67.4K. Kiriş yarıları ayrı süpürülür
  (mahyada gönye), böylece doku kitinde trim bandı olarak kalırlar: DEPOT_STORAGE
  Structure seti 122 px/m (tek parça bükük kirişte 52 px/m idi).

## Shelter ve hızlı hangar ailesi (core SHELTER / HANGAR)

- **HANGAR** (`core.hangar_config`): eski kutu tabanlı hangar kaldırıldı; core HANGAR
  ayarları beşik çatılı bir Hangar Studio yapılandırmasına çevrilir (açıklık genişliğin
  ~%64'ü, genişliğe göre 4/6/8 kanat, Hangar Studio aralıkları `Settings.checked` içinde
  doğrulanır: genişlik 20–48 m, saçak 6–9 m, bölme 2,8–6 m). Profilli cephe, teleskopik
  kapılar, portal çerçeve, kenet çatı, oluklar ve personel kapıları Hangar Studio ile aynı.
  Core Blender üretimi ve exporter bu kökler için hangar malzeme tariflerini kullanır.
- **SHELTER** (`shelter/geometry.py`, yeni): AS07 sözleşmesi (açıklık 18–40 m, derinlik
  20–60 m, saçak 4,1–8 m, kemer yükselişi, bölme 2,3–6,5 m) korunarak geometri sıfırdan
  yazıldı; `vendor/as07_reference.py` bayt bayt aynı kaldı. Gövdesi I kesitli (gövde
  çerçeve düzleminde) kolonlar, taban plakası + ankraj, kolon başlığı ve kemer oturma
  pabucu; ~4,5 m'lik parçalardan cıvatalı ek levhalarıyla birleşen kemer kirişleri;
  kemer üstünde dudaklı C aşıklar ve bağlantı kulakları; yalıtımlı iç astar üstünde
  0,60 m adımlı kavisli kenet çatı (saçakta kapalı dikiş uçları), saçak damlalığı, sarı
  şeritli kemer alın flaşingleri; harç yatağı üstünde 10 mm derzli prekast beton plak
  duvarlar ve kapaklar, Z kanatlı panjur bandı (kaynaklı kutu çerçeve, ≤2,6 m kayıt),
  saçak kirişi ve saçak dolgusu; arkada rüzgar dikmeleri, prekast dado, 35/250 trapez
  sac, taban damlalığı, köşe trimleri, egzoz fanları, kanopili çelik personel kapısı
  (pres kasa, 50 mm kanat, menteşe, kol, tekme sacı, panik bar, dışa açılır); oluklar,
  kazboynu iniş boruları ve kelepçeler; kimlik tabelası; ön kolon bariyerleri; zemin
  derzleri, kanal ızgarası ve işaretler; armatürler, kablo tavası, yangın dolapları.
- Doğrulama: 18×20 … 40×60 m aralığında doğrulama PASS, n-gon 0, aynı yöne bakan çakışık
  yüz çifti 0; canlı Blender mesh QA (CORE HANGAR/SHELTER, WORKING/HERO) PASS; export
  (LOD1/LOD2, UV1 lightmap, UCX) her iki aile için çalışır. HERO bevel öncesi üçgen:
  SHELTER (24×32) 80,6K, HANGAR (28×36) 63,0K.

## Korunaklı shelter (SHELTER, `shelter_style='HARDENED'`)

- `shelter/hardened.py` (yeni): bölme bölme dökülmüş, derzleri girintili ve kalıp izli
  betonarme tonoz (duvar + segmental kemer); önde kalın beton **portal kemer** (gömülü çelik
  conta plakası, dış kenarında zemine kadar inen çelik kaplama, kenarda LED projektörler).
  Yan duvar / uç blok yok: kapı sistemi doğrudan zemine entegre.
- **Yuvarlak ağır çelik kapı:** üst kenarları kemeri izleyen iki kanat (700 mm kutu gövde);
  kapalıyken portal kemere oturan tek bir yuvarlak kapı gibi okunur. Her kanat, öne eğimli
  destek ayağı üzerinde iki kren rayına basan bojilerle taşınır (açıklığın üstünden geçen
  kiriş yok) ve açılınca tamamen shelter'ın yanına park eder. Kemerli üst bant, dikmeler,
  panel derzleri, karşılaşma contaları ve darbe şeritleri, iç yüzde bindirme bölgesinde
  lastik conta ve berkitme lamaları, kremayer tahrik, kaldırma kulakları. Raylar apron
  betonuna dökülmüş kanallarda: ray başı döşemenin 5 mm altında, galvaniz kenar köşebentleri
  döşemeyle aynı kotta, taban plakası ve klipsler kanal tabanında; tekerlekler kanalda döner.
  Zemin üstünde yalnız ray sonlarındaki tamponlu stoplar ve uyarı babaları kalır. Kanat
  hareket hacmi sabit parçalarla çakışmaz (kontrol edildi).
- Arka: panjurlu egzoz ağzı, beton püskürtme saptırıcı, kalın duvarda kasalı çelik
  personel kapısı ve kanopi. İçeride duvar projektörleri, tepe havalandırma kanalı, kablo
  tavası, yangın dolapları; önde apron, kapı hattı uyarı çizgisi.
- Doğrulama: 18×20 … 40×60 m, DRAFT/HERO: doğrulama PASS, n-gon 0, aynı yöne bakan
  çakışık yüz çifti 0; canlı Blender mesh QA PASS; export: 48 asset, hepsinde UV1,
  kapı kanatlarında UCX. HERO bevel öncesi ~20,8K üçgen (24×32).
- `scripts/hangar_deliverables.py CORE_SHELTER_HARDENED turntable video anim`: 8 açı, kapı
  animasyon videosu ve animasyonlu kapı FBX'i (`deliverables/CORE_SHELTER_HARDENED/`).
- Kurgusal CGI dekor: kalınlıklar ve profiller sanatsaldır; koruma/yapısal iddia yoktur.

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
