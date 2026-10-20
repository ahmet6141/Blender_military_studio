# Karargâh binası (core HQ) — analiz ve uygulama planı

Kapsam: `kind='HQ'`, `office_style` AUTO/COMMAND (eklentideki "Karargâh / idari yapı").
UNIT, SUPPORT ve LOGISTICS stilleri `build_office` üzerinde aynen kalır.

Kurgusal CGI dekor: aşağıdaki "standart" maddeleri, kamuya açık tasarım ilkelerinin görsel
karşılığıdır. Mühendislik, güvenlik veya mevzuat uygunluğu iddiası yoktur.

## 1. Analiz (mevcut model, varsayılan 35,2 × 20,4 m, 3 kat × 3,6 m)

### 1.1 Ölçümler

| Ölçüt | DRAFT | WORKING | HERO |
|---|---|---|---|
| Doğrulama | PASS | PASS | PASS |
| Parça | 57 | 64 | 68 |
| Üçgen (bevel öncesi) | 28,5K | 28,7K | 30,3K |
| Aynı yöne bakan çakışık yüz çifti | 1613 | 1617 | 1617 |
| Çakışık alan | 29,1 m² | 34,7 m² | 34,7 m² |
| Çarpışma kutusu | 385 | 385 | 385 |

Çakışma (z-fight) kaynakları:
- Pencere söveleri ve duvar: 552 yüz, 8,1 m².
- Cam ve kasa: 552 yüz.
- Kayıt (transom) ve kasa: 184 yüz.
- Kat gölge çizgileri ve duvar: 184 yüz.
- Duvar ile duvar: 72 yüz.
- Taban kaplaması ile duvar: 6,8 m².
- Lobi ayakları ile lobi dönüşleri: 9,1 m².
- Parapet köşe kapakları üst üste.
- Portal bıçakları ile taç.
- Çatı perdesi ile direkleri.

### 1.2 Topoloji ve 3D kalite hataları

1. **Duvar parçaları:** cephe, bölmeler arasında 12 mm aralıklı ayrı kutulardan kuruluyor.
   Pencere söveleri ayrı plakalar olarak duvar yüzüne yapışık; bu da kalıcı z-fight demek.
2. **Görünmeyen dolu hacimler:**
   - Kat döşemeleri.
   - Binanın içinde, neredeyse tüm derinlik boyunca uzanan iki "köşe pilastrı" kutusu.
   - Lobi iç kutusu.
3. **Havada duran parçalar:**
   - Cephe bağlantı pulları duvarın 25 cm önünde.
   - Genleşme derzi kapakları duvarın önünde boşlukta.
4. **Yanlış taraftaki detay:** pencere kolları binanın dışında.
5. **Çarpışma:** 385 ayrı kutu, UE5'in UCX sınırı olan 48'i aşıyor. Bu yüzden cephe karmaşık
   (mesh) çarpışmaya düşüyor.
6. **Kutu tipi aksesuarlar:**
   - Banklar, saksılar, yön pilonları.
   - Çatı makine kutuları ve fanları.
   - Arka cephede servis dolapları.
7. **Güneş kırıcılar:** her pencerede 3 bıçak ve 2 konsol var (5,5K üçgen); cephe dağınık görünüyor.

### 1.3 Mimari ve askeri karargâh standartlarına göre eksikler

- **Kimlik:** sıradan bir ofis bloğu gibi okunuyor. Karargâhı karargâh yapan unsurlar yok:
  - simetrik anıtsal giriş;
  - giriş kütlesi (risalit);
  - tören / selamlama balkonu;
  - amblem;
  - bayrak direkleri;
  - tören alanı.
- **Giriş:**
  - 3 katlı tam cam lobi ve giriş camını ortadan kesen ince bir saçak, alışveriş merkezi
    girişi gibi görünüyor.
  - Basamak, rampa, korkuluk ve rüzgârlık (vestibül) yok.
  - Zemin kat döşemesi tören alanıyla aynı kotta.
- **Güvenlik tasarımı:** UFC 4-010-01 asgari antiterör ilkelerinin görsel karşılıkları eksik:
  - araç bariyeri / mesafe hattı;
  - cephenin önünde, saklanmaya izin veren eşya bulunmayan boş bölge (banklar ve saksılar bunu
    ihlal ediyor);
  - zemin katta korunaklı (parmaklıklı) pencereler;
  - derin söveli, sağlam kasalı pencereler.
- **Kaçış:** yan cephelerde acil çıkış kapısı yok. Arka giriş zemin kotunda, basamaksız.
- **Çatı:**
  - Parapet 0,58 m; yürünebilir çatı için düşmeye karşı korumada ≥ 1,0–1,1 m beklenir.
  - Çatı çıkış kulesi, süzgeç ve taşma ağzı, paratoner yok.
  - Makine perdesi ince ve dağınık.
- **Cephe dili:**
  - Taban, gövde ve taç üçlüsü (taş kaplı taban kat, sıvalı orta katlar, saçak / attika) zayıf.
  - Pilastr ve kat bantları birbirini kesiyor.

## 2. Hedef tasarım (yeni `hq/command.py`)

Koordinatlar core.Model ile aynıdır: x cephe boyunca, y binanın içine, z yukarı. Ön yüz y = 0.

### 2.1 Kütle ve kotlar

- Tören alanı (plaza) b kotunda. Bina zemini **kaide** üzerinde: zf = b + 0,48.
  Ön ve arka girişe 3 basamakla çıkılır (rıht 16 cm, basamak genişliği 32 cm).
- Ön cephe tek sayıda bölmeye ayrılır (~3,6–4,0 m). Ortadaki 3 bölme, 1,0 + `facade_relief`
  kadar öne çıkan **giriş kütlesi** olur. Bu kütle parapetten 0,6 m yüksek bir attika ile biter.
- Dış duvar 0,40 m kalınlıkta. Parapet çatı bitişinden 1,05 m yüksek, üstünde metal harpuşta var.

### 2.2 Cephe sistemi (çakışmasız döşeme)

- Her bölme kendi aralığında dört dolu parçadan oluşur: sol ayak, sağ ayak, denizlik altı ve
  lento üstü. Parçalar birbirine yalnızca değer.
- Pencere boşluğunun yan yüzleri doğal söveyi oluşturur; ayrı söve plakası kullanılmaz.
- Taban kat taştır; orta katlar sıva veya prekast. Kat bantları pilastrlar arasında kesilir.
- Pilastrlar kaideden parapet üstüne kadar kesintisiz uzanır.
- Köşelerde, iki cephenin pilastrlarını birleştiren köşe bloğu vardır.

### 2.3 Pencere (askeri bina görünümü)

- Kasa, dış yüzden 115 mm içeride (derin söve). Kasa: 70 mm alüminyum profil, dikme, üstte
  vasistas kaydı. Cam, kasanın ortasında, kasa yüzlerinden ayrı düzlemde.
- Dışarıda prekast denizlik ve lento üstü saçak (`sunshades`).
- İçeride karanlık iç panel ve rastgele yükseklikte jaluzi. Kol yok; iç taraf görünmüyor.
- Zemin kat pencerelerinde söve içinde dikey güvenlik parmaklığı (WORKING ve HERO).

### 2.4 Ana giriş

- Dört taş sütunlu revak. Revak döşemesi birinci kat kotunda ve aynı zamanda tören /
  selamlama balkonu:
  - taş korkuluk duvarı ve harpuşta;
  - birinci katta balkona açılan camlı kapı.
- Revak altında, kütle yüzüne gömülü çift kanatlı ana kapı, üst ışık ve yan ışıklar.
- Saçak alnında bina adı yazısı, attikada kabartma amblem madalyonu.
- Revak tavanında gömme (yüzeyle aynı hizada) aydınlatma panelleri (`night_lighting`). Kutu
  armatür kullanılmaz.
- Orta bölmede, `atrium_floors` katı boyunca dikmeli dikey cam şerit.
- Terasın önünde 3 basamak ve ara korkuluklar. Bir yanda 1:12 eğimli erişilebilir rampa;
  iki yanında korkuluk ve bordür.

### 2.5 Arka, yan ve çatı

- **Arka:** ortada çelik çift kapı, saçak, sahanlık ve basamaklar; arka servis şeridi.
- **Yanlar:** her yanda bir acil çıkış kapısı, sahanlığı ve basamakları.
- **Çatı:**
  - membran;
  - parapet iç yüzü;
  - çatı çıkış kulesi (merdiven kovası; kapı ve saçaklı);
  - içi boş, panjurlu makine perdesi (ekipmanı kullanıcı ekler);
  - süzgeçler;
  - arka parapette taşma ağızları ve iniş boruları;
  - paratoner: köşe yakalama uçları, harpuşta iletkeni, iniş iletkenleri ve test klemensleri.

### 2.6 Saha (askeri standartların görsel karşılığı)

- Döşeme taşlı tören alanı ve bordür.
- Ön sınırda anti-ram babalar (Ø 0,27 m, h 1,0 m, aralarında ≤ 1,2 m net açıklık).
  Yayalar geçebilir, araçlar geçemez.
- Taş kaide üzerinde üç bayrak direği (ortadaki en yüksek). Bayraklar sonra eklenecek.
- Cephe önündeki boş bölgede eşya yok: banklar, saksılar ve pilonlar kaldırılır.
- Kutu tipi ekipmanlar (çatı makinesi, fan, servis dolabı) kaldırılır. Kullanıcı hazır modelle
  ekleyecek.

### 2.7 Oyun motoru ve topoloji ölçütleri

- Kapalı katılar. Yüzeyler 1–3 mm gömülü ya da karşılıklı bakan temasla birleşir.
  **Aynı yöne bakan çakışık yüz: 0** (ölçek ve varyant taramasında).
- Görünmeyen iç hacim yok (kat döşemeleri ve iç pilastrlar kaldırılır).
- UCX: varlık başına ≤ 48 basit gövde (duvarlar bölme başına değil, cephe başına).
  Kapı açıklıkları boş.
- Malzeme sayısı sınırlı; dünya ölçekli UV; bevel kuralları (ince parça > 2 × bevel).
- Varyantlar:
  - **EXECUTIVE:** taş + sıva + zeytin metal.
  - **TECHNICAL:** prekast beton; `vertical_fins` > 0 ise derin pilastr kanatları.
  - **MONOLITHIC:** her yer taş, daha dar ve daha derin pencereler.

## 3. Uygulama adımları

1. `mb01_military_studio/hq/command.py`: kotlar, bölme ızgarası, cephe döşemesi, pencere, giriş,
   revak ve balkon, arka / yan kapılar, çatı, paratoner, saha ve UCX.
2. `core.build`: HQ + AUTO/COMMAND için yeni üreteç; diğer stiller eski yolda.
3. Arayüz: COMMAND'de kullanılmayan `corner_glass` gizlenir.
4. Doğrulama:
   - z-fight taraması (genişlik 14–56, 1–4 kat, üç varyant, DRAFT/HERO);
   - kaçak / gizli hacim ve UCX kontrolü;
   - canlı Blender QA'ya CORE:HQ eklenir;
   - export testi;
   - `verify_fast`.
5. Kısa yakın plan kontrolü (birkaç kare), değişiklik günlüğü, commit ve push.

## 4. Sonuç (uygulandı)

- Ölçümler (varsayılan, HERO):

  | Ölçüt | Önce | Sonra |
  |---|---|---|
  | Aynı yöne bakan çakışık yüz çifti | 1617 (34,7 m²) | **0** (9 kombinasyon × 3 detay) |
  | Asset | 70 | 49 |
  | LOD0 / LOD1 üçgen | 214K / 36,5K | 180K / 40,3K |
  | UCX | 385 kutu (sınır aşımı) | varlık başına en çok 40 |

- Kapı açıklıkları çarpışmadan bağımsız. Canlı Blender QA PASS.
- Ayrıntılar: `CHANGELOG_0_4a2_TR.md`, "Karargâh binası yeniden tasarımı".
