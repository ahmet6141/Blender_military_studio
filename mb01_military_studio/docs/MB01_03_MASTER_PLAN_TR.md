# MB01 0.3 — Hangar Expansion / uygulama ve kalite planı

**Tarih:** 26 Eylül 2026  
**Kaynak başlangıcı:** MB01 0.2.0-alpha.3 QA + BASE01 Assembly 0.1  
**Bu teslim:** 0.3.0-alpha.1, Blender paket sürümü `(0, 3, 1)`  
**Durum:** İlk uygulama ve saf Python doğrulaması. Blender 4.5 ve Unreal Engine 5.8 uygulama içi kapıları henüz geçilmedi. Kararlı sürüm değil.

## 1. Ürün hedefi ve kapsam kilidi

Amaç, aynı mimari dilde farklı hangarlar ve daha sonra kurumsal binalar oluşturabilen parametrik çevre üreticisidir. Kullanım; oyun, animasyon ve CGI'dır. Modüllerin ölçüleri, kapı hareketleri ve görsel donanımlar gerçek bina imalatı, askerî tesis standardı, statik/yangın hesabı veya koruyucu performans onayı değildir.

İki üretim yolunu ayrı tutuyoruz: **tam hangar tasarımı** ve **küçük parçaları game-ready kitaplığa dönüştürme**. Tam hangar üreticisi tüm mimari bileşenleri ayrı sahne nesneleri olarak kurar. Oyun-kiti derleyicisi ise bu sürümde yalnız altı yeni cephe modülünü opak/cam/hareketli kapı gruplarına ayırır, LOD ve basit collision hazırlar. İkinci yol, birinci yolun tüm binasını otomatik optimize etmiş sayılmaz.

Bu revizyonda uygulanan kapsam: altı yeni cephe modülü; eski dört tipe eklenmiş on türlük sol/sağ cephe seçimi; beş yeni tam hangar önayarı; tek hücre değiştirme paneli; altı modül için üç LOD; sabit pivot, slot ve birleşim verisi; basit açıklık koruyan collision; ayrı FBX LOD paketleme kodu. Kod, veri ve örnekler birlikte verilir.

Bu revizyonda uygulanmayan kapsam: üç yeni büyük kapı mekanizması, iki yeni çatı türü, çift bağımsız ana açıklıklı hangar, servis ofisi/mezzanine, tüm bina LOD/atlas dönüşümü, otomatik Unreal LOD bağlama, ISM/HISM/Nanite, yeni taranmış PBR kütüphanesi ve canlı SW01/AF01/PK01 köprüsü. Mevcut iki çatı ve 4/6/8 kanatlı mekanizma yeni özellik gibi yeniden sayılmaz.

## 2. Önceki öneride düzeltilen teknik kararlar

**Grid bir inşaat standardı değildir.** Önceki mesajda örnek verilen 0,5 m genel grid ile 6/8/10 m hangar bölmeleri uygulamadaki kısıtlarla aynı değildi. Gerçek üretici `derinlik / bölme sayısı = 2,8–6 m` bekliyor. Bu aralık korundu; 8 veya 10 m destekleniyor diye açılmadı. 48 m uzunluğa sahip 10 bölmeli örnekte hücre 4,8 m olur. Pencere ve kapılarını sessizce scale eden yeni grid zorlaması yok.

**Pivotu sürüm değişiminde rastgele taşımıyoruz.** Mevcut kanonik düzen: +X bina içine, +Y sola, +Z yukarı, metre. Statik cephe modülü pivotu dış yüzün alt-orta referansıdır. Sol/sağ bağlantılar kendi socket'leridir. Hareketli kapılar menteşe yerel pivotunu korur. Eski pivotu alt-sol köşeye dönüştürüp bütün mevcut yerleşimleri bozmak yerine yeni sözleşme adaptörüyle açıkça belgeliyoruz.

**UV1 her proje için zorunlu değildir.** Tekrarlanan UV0 ile lightmap UV birbirinden ayrıdır. Epic, yalnız dinamik ışık kullanılan mesh'lerde lightmap gerekmediğini, baked ışıkta benzersiz ve üst üste binmeyen bir kanal gerektiğini açıklıyor [S2]. Bu adayın hedefi dinamik aydınlatmadır; `UV0_Tile` üzerine lightmap etiketi konulmaz.

**LOD yüzdesi kalite kanıtı değildir.** Sabit %50 azaltım yerine belli küçük elemanlar kontrollü kaldırılır. Açıklık, ana kasalar, güneşlik silueti, cam ve kapı pivotları korunur. LOD2 bütün binanın uzak impostor'u değildir. Yüksek poligon detaylarını texture'a bake etmediğimiz için “trim atlas tamamlandı” demiyoruz.

## 3. Kategoriler ve parça kimlikleri

Katalog, aile ve kategori olmak üzere iki filtreyi korur. Hangar parçaları karargâh veya birlik cephesine varsayılan olarak takılamaz. 56 eski kayıt korunup altı ek kayıt oluşturuldu: toplam 62; geometri üreticisi bulunan 20, hâlâ planlı 42. Tam hangar içindeki ray, taşıyıcı ve armatürler otomatik olarak tek-modül katalog sayısına eklenmez.

| Kod | Modül kimliği / token | Amaç | Ayrıntı |
|---|---|---|---|
| M031 | HANGAR.WALL.CASSETTE / CASSETTE | Kapalı metal cephe | Yatay kaset ritmi, düşey panel, ince gölge çizgileri ve kenar bitişi |
| M032 | HANGAR.WALL.VISION / VISION | Alçak geniş cam bölümü | Gerçek duvar açıklığı, yatay kayıt, söve, denizlik ve başlık |
| M033 | HANGAR.WALL.SHADED / SHADED | Güneş kırıcı üst cam bandı | Gerçek açıklık, dışa uzanan dört kanat ve bağlantı kolları |
| M034 | HANGAR.WALL.DUAL_VENT / DUAL_VENT | Çift panjurlu servis paneli | İki bağımsız duvar boşluğu, panjurlar ve başlık |
| M035 | HANGAR.ENTRY.DOUBLE_SERVICE / DOUBLE_SERVICE | Çift servis kapısı | İki menteşe, kasa, eşik, koruma sacı, saçak ve destek |
| M036 | HANGAR.ENTRY.CANOPY / CANOPY_ENTRY | Saçaklı personel girişi | Tek menteşe, sabit giriş çerçevesi, saçak ve alt aydınlatma geometrisi |

Altı üretici aynı parametrik aralıkta ilk geometri ailesi olarak tanımlıdır. Oyun-kiti paneli genişliği 2,8–6 m, yüksekliği 6–9 m, kalınlığı 0,16–0,36 m aralığında sunar. Bunlar birbirinden bağımsız her türlü mimariyi oluşturma taahhüdü değil, mevcut geometri çalışma alanıdır.

## 4. Mimari estetik kuralları

Cephedeki yüksek cam bandı ortak bir üst referansa bağlı; alçak cam farklı bir işlevsel bölgedir. Kaset panelin yatay ritmi, komşu güneşlik ve başlık çizgisiyle uyumlu seçilir. Kapı modülünü eklediğimizde bitişik kolon, sahanlık ve pencereyi görsel olarak ezmeyiz. Yan yana iki personel/servis girişinin sahanlık çakışması bu sürümde reddedilir.

Yeni modül duvarının arkasında açıklığı kapatan ikinci bir tam duvar bulunmaz. DUAL_VENT üreticisi, iki deliğin kenarlarından düzlem bölümlendirmesi yaparak yalnız gereken duvar hücrelerini kurar. Panjurun koyu arka ekranı görsel elemandır; gerçek havalandırma hesabı değildir.

Kullanılan sanat yönü; okunaklı giriş, düzenli tekrar, ölçülü cephe zenginliği ve sınırlı malzeme ailesidir. AFCFS'nin mimari özellikler sayfası basit/profesyonel detayları ve yerleşke içinde yinelenen duvar, çatı ve giriş dilini vurgular [S3]. Bu kaynak sanat yönü referansıdır; Türkiye/NATO/UFC sertifikasyonu değildir.

Tüm noktalara rastgele kir, çatlak, kamuflaj veya cıvata eklemiyoruz. Yeni parça, bir birleşim veya işlev boşluğunu karşılamalıdır. Sonraki aşamada yağmur izi, servis aşınması ve boya yenileme ayrı maskeler olacaktır; bu teslimde yeni bir eskime simülasyonu yoktur.

## 5. Tam hangar konfigürasyonları

| Önayar | Boyut / m | Bölme | Mimari yön |
|---|---:|---:|---|
| EXP_COASTAL | 32 × 36 | 8 | Işıklıklı çatı, açık cephe, alçak/üst cam dengesi, iki giriş türü |
| EXP_TECHNICAL | 28 × 36 | 8 | Eğimli çatı, zeytin cephe, kaset/çift panjur servis ritmi |
| EXP_COMPACT | 24 × 24 | 6 | Grafit cephe, açık boyalı çatı, küçük servis yapısı |
| EXP_LONG | 32 × 48 | 10 | Uzun bakım hacmi, 4,8 m hücre ve dengeli servis bölmeleri |
| EXP_URBAN | 36 × 36 | 8 | Grafit cephe, 8 kanatlı mevcut kapı ailesi, geniş açıklık |

Bu sayılar uçak uygunluğu veya bakım kapasitesi belirtmez. Beş önayarın tam JSON'u `presets` klasöründedir. Kökü, kapıları, cepheyi ve ekipmanları görüntüleyen kaynak geometri kullanılmıştır. Kamera kadrajı modele göre değiştiğinden önizlemeler ortak ölçekte değildir.

Panelde “cephe tarafı + hücre numarası + modül türü” seçilir. Değişiklik önce tarife uygulanır; mevcut bina silinmez. Yeniden üretim yeni kök oluşturur. Bir hücreyi değiştirmek hâlâ bütün yeni revizyonun oluşmasını gerektirir; sadece o hücreyi aktif bina üstünde yerinde güncelleme tamamlanmış değildir.

## 6. Game-ready modül derleyicisi

### Geometri ayrımı

Opak kabuk ve statik ayrıntılar bir grupta; cam ayrı; her hareketli kapı ayrı render assetidir. Varsayılan altı modülde en fazla dört render mesh hedefi denetlenir. Her assette en fazla sekiz materyal slotu kontrolü vardır. Gerçekte kullanılan sayılar rapordadır; sekiz slotu doldurmak bir kalite hedefi değildir.

Her LOD'un asset anahtarları, pivotu, slot sırası ve birleşim socket'leri LOD0 ile eşleşir. LOD1/2'de kullanılmayan bir slot, indeks kaymasını önlemek için korunabilir. Bu, bilinçli şema sürekliliğidir.

### LOD politikası

LOD0 tasarlanan ana ayrıntıyı içerir. LOD1, DRAFT geometri ve küçük gölge/fitil detaylarının çıkarılmış biçimidir. LOD2, panel kenetleri ve bazı ek bitişlerin de kaldırıldığı temsildir. Güneşlik ve panjur gibi ana silueti etkileyen elemanlar körlemesine yok edilmez.

Bütün LOD'lar kapılar kapalı rest pozunda üretilir. Kapı hareketi ayrı metadata'dır. Bu sayede orta pozdaki bir kanadın konumunu geometriye gömüp menteşe merkezini kaybetmeyiz. Baked normal/trim atlas, otomatik Unreal ekran boyutu eşiği ve hareketli kapı Blueprint'i bu aşamada yoktur.

### Collision politikası

Statik duvar collision'ı, açıklıklar etrafındaki duvar parçalarının ayrı kapalı kutularından türetilir. Test yalnız deliğin merkezini kontrol etmez: nominal dikdörtgen açıklık hacmiyle pozitif hacim kesişimini reddeder. Sınırda temas hata değildir. Kapı collision'ı LOD0 kapalı kanadın yerel sınır kutusundan gelir; diğer LOD'larda değişmez. Cam collision'ı üretilmez.

Bu başlangıç collision'ı küçük çerçeveleri, saçağı ve bütün dekor ayrıntılarını kapsamaz. Oyuncu hareketi/iz testi Unreal'da ayrıca yapılmalıdır. Tek bir büyük kutu bütün pencere ve kapıları kapatmaz. Collision teması, gerçek yapı güvenliği veya taşıyıcı dayanım anlamına gelmez.

### Export politikası

Her render asseti için ayrı LOD0/1/2 FBX dosyası yazan Blender kodu hazırlandı. LOD0'a eşleşen `UCX_...` gövdeleri ve statik arayüz `SOCKET_...` yardımcıları eklenir. Epic'in FBX akışındaki tek dosyada çoklu mesh/collision/socket sınırlamaları nedeniyle bu ayrım seçildi [S1]. Dosya yazılması tek başına import doğrulaması değildir.

`GAME_KIT.json` kimlik, pivot, LOD dosyaları, SHA256, materyal sırası, kapı ve socket verisini taşır. Export önce tamamlanmamış işaret dosyası oluşturur; yalnız başarılı sonunda kaldırır. Başarısızlıkta kaynak sahne korunur, tanılama dosyası bırakılır. Yeni export klasörü zaman/UUID ile açılır; önceki teslimin üzerine sessizce yazılmaz.

UE tarafında bu küçük kitin LOD0'ı içe alınır, LOD1 ve LOD2 aynı Static Mesh'e manuel eklenir. Otomatik Unreal LOD bağlayıcı henüz yok. Tam hangarın mevcut `MB01_Import.py` yolu bundan ayrıdır; kit manifestini o scriptle açmak desteklenmez.

## 7. Materyal, texel yoğunluğu ve doku kaynakları

Mevcut sekiz prosedürel ailedeki kırk PNG aynen korunur. Harici kaynak indirilmiş, tarama doğrulanmış veya 8K paket hazırlanmış sayılmaz. Base Color sRGB; ORM doğrusal R=AO/G=Roughness/B=Metallic; Blender NormalGL ve Unreal NormalDX; Height kaynak dosyası fakat bağlı displacement yok.

Materyal reçetesi fiziksel `tile_size_m` alanını korur. Önceki 512/256 px/m değerleri gelecek bütçe önerisiydi; mevcut kaynaklara uygulanan tek zorunlu yoğunluk değildir. Yüzeye göre raporlanmış çözünürlük/kaplama ölçeği kullanılır. Yeni iki render motorunun her pikseli aynı vermesi beklenmez.

Özel PBR ailesi eklenirse beş haritası birlikte sağlanır; kısmi set eski haritalarla sessizce karıştırılmaz. Gerçek içerik hash'i korunur. Boyalı metal, metal altlık görünümüyle karıştırılmaz. AO maskesinin kaydı, her renderer'ın aynı şekilde kullanacağı anlamına gelmez; reçete gerçek shader davranışını takip etmelidir.

P5'te eklenecek trim sisteminin kabulü: gerçek atlas dosyası, UV adaları, fiziksel ölçek, materyal slot etkisi ve bake karşılaştırması birlikte teslim edilmeden “trim sheet hazır” denmeyecek.

## 8. AS07 / SW01 / AF01 / PK01 sınırları

AS07 orijinal dosyası değişmez. Beş eski bina ailesi ve üç eski Hangar Studio önayarı yeni kaynakla tekrar üretilip geometri imzaları baseline ile karşılaştırılır. Dokular, eski materyal kurucusu ve diğer eklenti ZIP'leri değiştirilmez.

Hangarın personel sahanlık portları eski sözleşmeyi kullanmaya devam eder. Uçak giriş portu yaya portuna çevrilmez. Harici apron seçildiğinde yerel zemini üretmeme davranışı korunur. Gerçek birleşik kesim/terrain/peyzaj güncellemesi henüz yoktur.

Gelecekte yön değiştiğinde giriş portları, yüzey kotu ve kesim talepleri birlikte güncellenmelidir. Ancak bu gerçekleşmeden sadece aynı alan adını taşıyor diye “tam uyumlu” etiketi verilmez.

## 9. Aşamalar, iş paketleri ve geçiş kapıları

| Faz | İş kapsamı | Bu teslim | Sonraki kapı |
|---|---|---|---|
| F0 Kaynağı sabitle | Orijinal ZIP hash, AS07, eski aile regresyonu | Uygulandı | Gerçek kaynak kimlikleri korunmalı |
| F1 Modül genişlemesi | 6 parça, kategori, aile, boşluk, menteşe | Uygulandı; Python testli | Temiz Blender üretimi |
| F2 Konfigürasyon | 5 ek önayar, 10 token, tek hücre düzenleme | Uygulandı; kaynak geometri testli | Panel/yeniden üretim native kontrol |
| F3 Oyun-kiti | Opak/cam/kapı grubu, 3 LOD, collision, socket, FBX kodu | Kaynak derleyici testli; native export bekliyor | FBX gerçek import ve ölçüm |
| F4 Native doğrulama | Blender register, shader, modifier, kayıt, FBX; UE ölçek/LOD/collision | Araç hazır, çalıştırılmadı | BLOCKED: gerçek sonuç gerekli |
| F5 Görsel malzeme | Doğrulanmış PBR, trim/bake, kaynak lisansı, ölçülü eskime | Planlandı | Gerçek atlas ve motor karşılaştırması |
| F6 Mimari büyüme | Ek büyük kapı/çatı tipleri, HQ/UNIT girişleri, servis iç hacmi | Planlandı | Aile başına geometri ve sahne testleri |
| F7 Yerleşke / runtime | Kit bağlantıları, artımlı reimport, ISM, kapı Blueprint'i | Planlandı | Kullanıcı düzenlemesi ve UE testleri |

F4 tamamlanmadan kararlı/beta etiketi verilmez. Deneysel kaynak üretimi ayrı aday dalında ilerleyebilir; bu çalışmayı native test yerine saymayız. Saat/gün taahhüdü yerine ilk gerçek makinede üretim ve export süresi kaydedilir.

Her yeni özellik için dört teslim gerekir: veri sözleşmesi, geometri veya aktarım kodu, hata senaryoları/testler ve gerçek kaynak görseli. “Planlandı” kaydı tamamlanmış parça sayısına eklenmez. Çalıştırılmamış testin durumuna PASS yazılmaz.

## 10. Kabul senaryoları

Veri: bilinmeyen modül/aile, NaN/sonsuz, desteklenmeyen genişlik, aynı kimlik, eski/yeni JSON sürümü, yan yana giriş ve yanlış dizi uzunluğu.

Geometri: açıklık arkasında duvar yok; sıfır alanlı yüz/UV yok; bağlantı noktaları ve yüzey kotu değişmiyor; düşük/varsayılan/yüksek boyut örnekleri; iki panjurun gerçekten iki ayrı açıklığı var.

LOD: LOD0/1/2 anahtarları, pivot, socket, kapı rest pozu ve materyal slot sırası aynı; üçgen sayısı artmıyor; cam hareketli kapıyla yanlış gruplandırılmıyor. LOD sınırında küçük dekor sınırlarının küçülmesi normaldir; ana çerçeve ve delik korunmalıdır.

Collision: nominal delik hacmine duvar kutusu girmiyor; kapı convex gövdesi kapı pivotuyla yerel; cam kapalı; tüm render modelini bir dev kutuyla tıkayan üretim yok. Dekor collision eksikleri raporlanır.

Blender: temiz profil kurulum/kaldırma, yeni panel ve hücre operatörü, placeholder yerine gerçek mesh, slot/UV/normal, yeni revizyon, kaynak dosyası değişimi, salt-okunur çıktı, kayıt ve export. Açık kullanıcı dosyası tanılama sürecinde yüklenmez.

Unreal: ölçek ve eksen kalibrasyonu, aynı pivotlu LOD ekleme, görsel siluet geçişi, materyal slotları, tangent normal yönü, oyuncu collision trace, kapı pivot hareketi, socket yönü, tekrar import. Film incelemesiyle oyuncu navigasyonu ayrı sonuçtur.

## 11. Görsel inceleme protokolü

Önce tek modül ve nötr ışık; sonra tam hangar genel görünümü. Farklı hava/yağış görünümü, geometrik kusuru saklamak için kullanılmaz. Düşük çözünürlükte panjur ve kenetlerde aliasing görülebilir; hareketli kamera testi Unreal/Blender içinde ayrıca yapılmalıdır.

Bu teslimde altı modül ve beş tam konfigürasyon gerçek geometriyle görüntülenir. Bağımsız CPU görüntüleyicisi; albedo, yaklaşık specular, gölge ve AO gösterir. Native bevel, tangent normal, kırılma, çok sekmeli GI ve temporal AA göstermez. Yapay zekâ konsept resmi üretilmez.

Hatalar “çözüldü” diye kapatılmadan ayar dosyası, sorunlu parça, kaynak ölçüm, önce/sonra veya regresyon sonucu bulunmalıdır. Tam bina self-intersection ve bütün mekanizma çarpışma uzayı bu sonlu testlerin yerine geçen iddialar değildir.

## 12. Dağıtım, kayıt ve sonraki somut işlem

Kurulum ZIP'i sadece `mb01_military_studio/` altında kaynak ve gerekli mevcut dokuları içerir. Ayrı geliştirme paketi plan, test, native çalıştırıcı, gerçek GLB ve PNG'leri taşır. Plan ZIP'i Blender'a kurulmaz. Font, lisansı belirsiz doku veya ücretli asset yeniden dağıtılmaz.

Native Windows tanılaması `tools/TEST_EXPANSION_WINDOWS.cmd` ile ayrı Blender sürecinde yapılır; sonuç `MB01_Expansion_Diagnostics` içinde oluşur. Bu scriptin hazırlanması çalıştırıldığı anlamına gelmez. UI testinden sonra küçük oyun-kiti FBX'i Unreal test projesine alınır. Bu sonuçlar olmadan final game-ready onayı verilmez.

## Kaynaklar ve destek kapsamı

[S0] Konuşmadaki MB01 alpha.3 README ve BASE01 planı; mevcut kaynak ZIP'i. Temel algoritmalar ve sınırlar buradan okunmuştur. Önceki raporlar yeni test sonucu yerine kullanılmamıştır.

[S1] Epic, FBX Static Mesh Pipeline. Pivot, collision/socket isimleri, triangulation ve LOD aktarım sınırları için. `https://dev.epicgames.com/documentation/en-us/unreal-engine/fbx-static-mesh-pipeline-in-unreal-engine`

[S2] Epic, Understanding Lightmapping. Dynamic-only / baked ışık ve UV ayrımı için. `https://dev.epicgames.com/documentation/en-us/unreal-engine/understanding-lightmapping-in-unreal-engine`

[S3] AFCFS, Architectural Features. Profesyonel ölçülü detay ve yerleşke mimari tutarlılığı sanat yönü referansı için. `https://afcfs.wbdg.org/facilities-exteriors/architectural-features/index.html`

Resmî kaynaklar 26 Eylül 2026'da kontrol edildi. Blender doküman/binary erişimi çalıştırma sağlamadı; Blender/UE runtime bu ortamda yok. Bu plan tam bir askerî standardın uygulanmış olduğu anlamına gelmez.
