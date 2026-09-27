# BASE01 — Birleşik Kit Altyapısı ve Kalite Planı
## MB01 / AS07 / AF01 / SW01 / PK01 için araştırma, arayüz sözleşmesi ve kontrollü güncelleme

**Belge:** 0.3 • **Tarih:** 26 Eylül 2026  
**Aday uygulama:** MB01 Hangar Studio 0.2.0-alpha.3 + BASE01 Assembly QA 0.1  
**Durum:** Araştırma ve ilk somut kusur düzeltmeleri tamamlanan kapsamda. Native Blender/Unreal doğrulaması yapılmadığından kararlı sürüm kapısı KAPALI.

Bu çalışma, kurgusal hava üssü sahneleri için bir DCC/CGI üretim sistemi geliştirir. Sayısal eşikler yazılımın görsel birleşim ölçütleridir; inşaat toleransı, askerî uygunluk, yük hesabı, uçuş emniyeti, elektrik/yakıt veya balistik tasarım değildir. Sınırsız parametre uzayında kusursuzluk iddiası yoktur.

## 1. Araştırmanın dayanağı ve karar değişikliği

Önceki plan yeni kitlerin listesini genişletiyordu. Bu revizyonda öncelik değişti: **önce tekil modüllerin birbirine güvenilir biçimde bağlandığı ortak sistem; sonra yeni kitler.**

İnceleme üç ayrı kanıta dayanır: mevcut kaynak kod, aynı koddan üretilen gerçek geometri ve resmî dış teknik belgeler. Önceki raporlardaki “PASS” ifadeleri yeni sürüme taşınmadı; testler yeniden çalıştırıldı. MB01 alpha.2 README’sindeki Blender/UE testlerinin yapılmadığı ve görüntülerin bağımsız görüntüleyiciye ait olduğu sınırı korundu.

AFCFS Architectural Features, basit/profesyonel ayrıntı ve yerleşkeye ait yinelenen çatı-duvar-giriş dilini vurgular [R1]. Bu kaynağı **sanat yönü referansı** olarak kullanıyoruz; gerçek bina sertifikasyonu olarak değil. Aynı sitedeki Building Envelope Standards sayfası “Content Under Development” durumunda [R2]; oradan okunmamış sayısal kural çıkarılmadı.

OpenUSD’nin birim belgesi, farklı ölçekteki varlıkları birleştiren tarafın birim düzeltmesinden sorumlu olduğunu açıklar [R3]. Buradan alınan karar; varlık başına açık birim ve dönüşüm sözleşmesidir. Bu sürüme USD bağımlılığı veya çalışan USD exporter eklenmiş değildir.

Epic’in FBX belgesi pivot, triangulation, collision isimleri ve soketlerin paketlenmesi konusunda somut sınırlar verir [R4]. Epic Data Validation da özel kontrol ve CI akışını destekler; Python validator’ları ayrıca kaydedilmelidir [R5]. Bu nedenle salt “FBX dosyası çıktı” veya genel bir commandlet çalıştı sonucu, bizim kontrollerimizin çalıştığı anlamına gelmeyecek.

## 2. Mevcut kaynakta tespit edilen gerçek kusurlar

| Kimlik | Bulgu | Yeni davranış | Kanıt |
|---|---|---|---|
| GEO-001 | Duvar kalınlığı .16 m iken arka birleşimde +.060 m boşluk; .36 m iken -.140 m örtüşme | Yan/ön/arka duvar aynı envelope verisinden; köşe karesinin sahibi ön/arka duvar | MEASUREMENTS_before/after + 27 geometri örneği |
| UV-001 | Çatı dikey kenarlarına eğim UV’si uygulanması: Daylight 128, Classic 64, Compact 48 sıfır alanlı UV üçgeni | Eğim UV’si yalnız kaplama üst/alt yüzünde; dikey kenarda geçerli düzlemsel UV | Bağımsız yüz/UV taraması |
| DIR-001 | Servis dolabı kapak/kulpları içeri yerine duvara bakıyor | İki tarafta da kapak/kulp odanın içine döndürülüyor | Aynı kameralı önce/sonra render + vertex ölçümü |
| FIT-001 | Askı ayakkabısının çatıya en yakın noktası 84.375 mm aşağıda | Bağlantı plakası eğime döndürülüp üst düzlemi çatı altına oturuyor | Kaynak geometriden ölçüm + yakın render |
| FIT-002 | Makara ray içine sığıyor ama alt raydan 15 mm havada | Aynı nominal yarıçapla ray tabanına temas | Gerçek makara vertex ölçümü |
| DAT-001 | Çatı, döşeme, iniş boruları ve köşe kapaklarında bağımsız sabit ofsetler | Dış kabuk ve yüzey referansları ortak fonksiyonlardan türetiliyor | Kalınlık/regresyon kontrolleri |
| MAT-001 | Doku aynı dosya yolunda değişirse eski görüntü/materyal yeniden kullanılabiliyor | Gerçek dosya bytes hash’i, immutable image datablock ve exportta değişmiş kaynak uyarısı/hatası | Kaynak kimliği testleri; native tekrar kullanım bekliyor |

İlk iki hata önceki geometri doğrulayıcısında görünmüyordu. Eski UV sürekliliği testinin bir beklentisi de yanlış projeksiyonu doğruluyordu; yalnızca eğimli yüzleri kapsayacak şekilde düzeltildi. Orijinal test referans kopyasında saklandı. Yeni bağımsız testler tüm görünür yüzlerin UV alanını ayrıca inceliyor.

Bu bulgular, bütün binaların baştan kötü veya bütün yeni parametrelerin şimdi kusursuz olduğu anlamına gelmez. Tam çakışma taraması, tüm kapı hacimleri, normal/tangent, native bevel ve render kontrolü açık işlerdir.

## 3. Ortak sistemin katmanları

**Kaynak → sözleşme → yerleşim → geometri → materyal → sahne → export → hedef editör doğrulaması.**

- **BASE01 çekirdeği:** birim, kimlik, port, tolerans, materyal kaynak kimliği ve güncelleme farkı. Saf Python; `bpy` zorunlu değil.
- **Aile üreticileri:** Hangar, AS07, HQ/UNIT, apron, kaldırım, peyzaj kendi geometrilerini üretmeye devam eder. Hepsi bir anda yeniden yazılmaz.
- **Sürüm adaptörleri:** eski veri isimleri ve yönleri açık olarak çevrilir. Sessiz varsayım veya otomatik geometrik scale yapılmaz.
- **DCC adaptörü:** Blender nesneleri ve modifier sonrası geometri. Kullanıcının dosyası değiştirilmeden rapor üretilebilir.
- **Export adaptörü:** birim/pivot/UV/material verisi ve sahiplik kayıtları. Başarısız ön-denetimde export durur.
- **Unreal adaptörü:** ayrı import ve doğrulama. İlk aşamada mevcut FBX+JSON yolu korunur.

Yeni BASE01, bugün beş eklentinin tamamını birleştiren bağımsız bir süper-addon değildir. İlk uygulaması MB01 içinde bir altyapı/denetim katmanıdır; diğer kitlerin canlı sahne davranışı için ayrı test ve adaptör gerekiyor.

## 4. Boyut, sınır ve datum sözleşmesi

Her geometrinin **nominal yerleşim ölçüsü, fiziksel dış sınırı ve net açıklığı** farklı alanlar olacak. Örneğin bir taşıyıcının aks açıklığı, kolon ve ekipman sonrası kullanılabilir uçak açıklığı değildir.

Bu aday hangarda `width/depth` içerideki nominal referans düzlemlerini tanımlar; taşıyıcıların içeri taşabileceği için “net uçak açıklığı” değildir. `wall_thickness` değişince dış duvar, çatı bitişi, oluk, iniş, arka cephe ve döşeme sınırı birlikte hesaplanır. Ön/arka duvar köşe karesini sahiplenir; yan duvar o kareye iki kez girmez.

Kaynak bina düzeni +X içeri, +Y sola, +Z yukarı ve metre cinsindedir. AS07 orijinali giriş -Y olan farklı kaynak düzenini kullanır; dosya değiştirilmeden adaptörle dönüştürülür. Unreal dönüşümü raw sayıdan değil dünya matrisi ve doğrulanan eksen tabanından gelir.

Üç ayrı kot tutulur: **kök tabanı, bitmiş yürüyüş yüzeyi, bağlantı noktasının ofseti**. İki kök aynı Z’de olmak zorunda değildir; iki yürüyüş yüzeyi birleşiyorsa bitmiş kotlar eşleşmelidir.

İlk yazılım eşikleri: konum/boyut farkı 1 mm, yön farkı 0.1 derece. Bunlar sanatsal mesh birleşimi için başlangıç kontrol eşikleridir. Tam paket LOD toleransı, gerçek imalat standardı veya bütün Blender/UE kayan nokta durumları için garanti değildir.

## 5. Portlar: tip, yön ve profil

Yeni `Port` veri modeli kimlik, sahip, rol, kaynak noktası, yön, yukarı ekseni, genişlik, yüzey ofseti, profil ve yön konvansiyonu taşır. Tanımsız ölçek, aynalama veya shear varsa doğrudan bağlantı denetimi reddeder; nesneleri kendisi taşımaz.

| Kaynak | Yönün anlamı | Uyarlama |
|---|---|---|
| SW01 OUT | güzergâh ilerleme yönü; çıkışta dışa bakar | olduğu gibi |
| SW01 IN | güzergâha giriş yönü; parçanın içine bakar | doğrudan birleşim normaline çevrilirken terslenir |
| MB01 personel sahanlığı | dışa yön + taban kotu/height | bitmiş kot = taban + ofset |
| Personel kapısı açıklığı | bina kabuğu üzerindeki delik | hazır kaldırım portu sayılmaz; sahanlık gerekir |
| HANGAR / APRON | araç yüzeyi bağlantı rolleri | aynı profil ve genişlik varsa doğrudan aday |
| PK01 giriş/çıkış | türüne bağlı OUT/IN anlamı | belgelenen alanlar okunur; bilinmeyen şema tahmin edilmez |

**Doğrudan birleşim denetimi yol çizme aracı değildir.** Aralarında 20 m bulunan iki portun SURFACE_GAP vermesi doğru sonuçtur; onlar için önce SW01 güzergâh/köprü üreticisi gerekir. Bitişik parçalarda ölçülen gap ve facing kontrol edilir.

Blender paneli iki Empty üzerinde bu kontrolü yapacak şekilde kodlandı. Native testi yapılmadı. Yeni araç mevcut SW01 veya PK01 kaynaklarını değiştirmez.

## 6. Yüzey sahipliği ve kesim talepleri

Bir yüzey bölgesinin tek geometrik sahibi olacak: hangar yerel döşemesi, AF01 ortak apronu veya başka bir sağlayıcı. İki zemini birkaç milimetre Z kaydırarak saklamak çözüm sayılmayacak.

Drenaj, personel sahanlığı ve bina temeli birbirini değiştirirken bir **kesim talebi** üretilecek. Talep geometriyi otomatik düzenlemeden önce önizleme gösterecek. Kabulde sınır paylaşımı, kot ve boyaların deliği kapatmaması kontrol edilecek.

Bu adayda hangarın yerel drenaj/geometri davranışı korunup envelope sınırları düzeltildi. AF01’e yeni delik açan canlı işlem **henüz uygulanmadı**. Yeni metadata’yı yazmak, eski eklentinin onu otomatik anladığı anlamına gelmez.

## 7. Mimari aile ve parça uyumu

Ortak kit kategori düzeni: kabuk, açıklık, çatı/bitiş, taşıyıcı görünüşü, zemin, tesisat, hareketli parça ve kimlik. Hangar için büyük açıklık/kapı/ray/ışıklık; HQ ve UNIT için pencere ritmi/giriş/kat bitişi; GSE için şasi/tekerlek/servis yüzü gibi ayrı aile kuralları kullanılacak.

Sanat yönü varsayılanları; aynı yerleşkede sınırlı metal tonları, ortak beton ölçeği, aynı tabela tipografisi, tutarlı kenar yarıçapları ve görevine uygun ayrıntı yoğunluğu. Bir binaya daha fazla civata eklemek, hatalı bir köşe birleşimini telafi etmez.

Parçaların görünen servis yüzü, bakım yönü ve açılma alanı ayrı işaretlenecek. Bu sayede dolap yüzünün yanlış yöne bakması gibi hata, yalnız kamera incelemesine kalmayacak. İleride modülün fiziksel izi ile etkileşim boşluğu ayrı kutu/hacim olarak tutulacak; gerçek kullanım güvenlik hesabı yapılmayacak.

## 8. Materyal, UV ve içerik kimliği

PBR dosyasının adı tek başına kimlik değildir. Yeni uygulama gerçek dosya bytes’ından SHA256 hesaplar, materyal tarifini buna bağlar ve değişen görüntü için yeni Blender image datablock oluşturur. Başka projedeki ortak görüntü zorla reload edilmez. Export sırasında kaynak değişmişse açık hata verilir; eski native malzemede hash yoksa uyarı oluşur.

Materyal rollerinde `tile_size_m`, renk uzayı, NormalGL/NormalDX, map listesi ve üretim yöntemi tutulur. `SW01_Tint` başka maskeler için ezilmez. Tekrarlı UV’nin 0–1 dışına çıkması hata değildir; sıfır alanlı UV yüzü farklı bir problemdir.

Eğimli çatı yüzeyinde uzunluk/yamaç koordinatı; ince dik kenarda geçerli yüz projeksiyonu kullanılacak. UV rotasyonu, tangent normal yönü ve negatif ölçek ayrı test gerektirir. Bu sürüm native tangent sonucunu doğrulamış değildir.

Mevcut 40 PNG prosedürel kaynak korunmuştur; yeni tarama indirilmedi. Materyal satın alma/CC0 tarama seçimi ileride kaynak lisansı, fiziksel boyutu ve gerçek indirme kaydıyla yapılacaktır. 8K etiketi kalite kabulü değildir. Boya/metal ayrımı için Epic’in PBR rehberi kullanılır [R6]; mevcut sanatsal değerler ölçülmüş yansıtma verisi sayılmaz.

## 9. Güncelleme ve kullanıcı düzenlemeleri

Geometri, malzeme ve dönüşüm ayrı değişiklik alanları olacak. Yeni dry-run çekirdeği CREATE, UNCHANGED, UPDATE, CONFLICT_LOCKED ve KEEP_ORPHAN sonuçları üretir. Bu saf veri fonksiyonu **dosya/nesne yazmaz veya silmez**.

Kilitli parçada değişiklik varsa otomatik üzerine yazma yerine çakışma gösterilir. Kaynaktan kalkmış parça önce “artık kaynakta yok, korunuyor” olarak listelenir. Kullanıcının aktif sahnesinde bu planı otomatik uygulayan işlem bu adayın kapsamı değildir.

Mevcut Hangar Studio yeni revizyon oluşturmaya devam eder. Alpha.2 JSON tarifleri okunabilir, fakat yeni envelope sınırları nedeniyle dış boyutlarda değişiklik vardır; eski mesh’ler otomatik taşınmaz. İlk karşılaştırma farklı koleksiyonda yapılmalı.

## 10. Katmanlı kalite kapıları

| Kapı | Kontrol | Başarı ne demek değildir? |
|---|---|---|
| Q0 Kaynak | ZIP/dosya hash, sürüm ve lisans kaydı | eklenti çalıştı demek değil |
| Q1 Veri | tipler, birim, profil, bilinmeyen alan, aynı kimlik | geometri doğru demek değil |
| Q2 Geometri | gerçek vertex/UV ve seçili birleşim ölçümleri | tüm bina çakışmaları tarandı demek değil |
| Q3 Statik görsel | nötr genel, izole yakın, kesit, UV/ölçüm panosu | native materyal/ray tracing eşdeğeri değil |
| Q4 Blender | temiz kurulum, UI, modifier sonucu, texture, kayıt, export | UE’ye doğru gitti demek değil |
| Q5 Unreal | asimetrik ölçü referansı, UV/normal/material/collision, tekrar import | gerçek tesis uygunluğu değil |
| Q6 Hareket | kapı pozları + hedef render AA ile hareketli kamera | sonlu örnekler bütün hareket uzayı değil |
| Q7 Sürüm | bilinen hata listesi, kullanıcı verisi korunması, rollback | sonsuz kusursuzluk garantisi değil |

Bu aday Q0–Q3’ün belirtilen bölümünü çalıştırdı. Q4/Q5 ve native hareketli görüntüleme açık olduğu için **genel sürüm onayı BLOCKED**. Test sayısı artışı bu kapıları atlatmaz.

## 11. Görsel inceleme protokolü

Önce nötr ışıkta siluet, ölçek ve ritim; sonra sert yanal ışıkta birleşimler; ardından izole köşe, kapı rayı, dolap önü ve askı teması incelenir. Görüntüde küçük kalan hata için gerçek geometri ölçümü ve izdüşüm çizimi kullanılır. Islak gece/gün batımı son aşamadır, gündüz kusurunu saklamak için kullanılmaz.

Bu oturumda üç eş kamera önce/sonra çifti ve bir yeni genel görünüm üretildi: dolap, arka köşe, armatür askısı ve genel hangar. İzole renderlarda diğer parçalara geçici görünürlük filtresi uygulandı; kaynak geometri değiştirilmedi. Bağımsız CPU renderer normal haritası, native bevel, çok sekmeli ışık ve kırılmayı simüle etmiyor.

Ek olarak gerçek duvar bounds’larından ortak ölçekli X–Y yakın plan çizildi. Bu çizim bir mimari proje veya renderer sonucu değil; boşluğun/örtüşmenin geometrik kanıtıdır.

Native geçişte 3 mesafe × 3 ışık durumu; checker/albedo/normal/materyal görünümü; sabit pozlama ve kayıtlı kamera kullanılacak. İki motorun aynı pikseli vermesi beklenmeyecek. İnce kenet, panjur, çizgi ve cam üzerinde kamera hareketi incelenecek. Temporal aliasing testi bu oturumda yapılmadı.

## 12. Test uzayı ve hata ciddiyeti

Varsayılan güzel örnek yeterli değildir. Üç hangar önayarı × üç duvar kalınlığı × üç detay seviyesi = 27 somut geometri konfigürasyonu kontrol edildi. Üç önayarda 21’er kapı pozu = 63 gerçek kanat geometrisi/açıklık metadata karşılaştırması yapıldı; bu tam kapı-duvar çarpışma çözücüsü değildir.

**Bloklayıcı:** çöken üretim, kullanıcı dosyası kaybı, yanlış ölçek, geçersiz indeks/UV, zorunlu birleşimde ayrılma. **Önemli:** yanlış servis yüzü, askı teması yokluğu, materyal kaynağı tutarsızlığı. **Görsel iyileştirme:** ayrıntı ritmi, AA, tekstür tekrarı. Her bulgu için tekrar üretme tarifi, önce/sonra kanıtı, regresyon testi ve açık sınır yazılır.

Manifold kuralı her yüzeye uygulanmaz: açık boya düzlemi kasıtlıdır; montaj temasları Boolean birleşimi değildir. AABB örtüşmesi tek başına hata sayılmaz; yapı birleşimlerinde kasıtlı temas vardır. Henüz uygulamadığımız dar faz üçgen/BVH kesişme taramasına “tam çakışma kontrolü” demiyoruz.

## 13. Unreal aktarımı ve performans

FBX başına tek ana render asseti ve ilişkili collision/helper politikası korunur; isim eşleşmesi ayrıca kontrol edilir [R4]. Görünüş tarifleri, Blender node ağının aynen taşındığı varsayılmadan yeniden kurulur. Ön-denetim artık değerlendirilmiş mesh verisini ve materyal kaynak hash’lerini kontrol eder; bu native kod yazıldı fakat burada çalıştırılmadı.

Epic Data Validation’a ileride isim, bağımlılık ve bütçe validator’ları kaydedilecek [R5]. Sadece `-run=DataValidation` demek bizim Python kurallarımızın kendiliğinden çalışması değildir; kayıt testi gereklidir.

Tekrarlanan parçalar, aynı mesh + uyumlu materyal/collision anahtarlarıyla instance gruplarına adaydır. ISM’de bazı özellikler bileşen düzeyinde paylaşılır [R7]. Bu sürüm yeni ISM/HISM/Nanite uygulamaz. Sahneye göre ölçülmüş bütçe kullanacağız: mesh çeşitliliği, material slot, VRAM, ışık, draw call ve hedef kamera. Poligon sayısı tek başına FPS garantisi değildir.

## 14. Olgunlaşmış geliştirme sırası

| Faz | Çıktı | Çıkış koşulu | Bu revizyonda |
|---|---|---|---|
| A Kaynak dondurma | eski paket hash ve arayüz envanteri | tekrar üretilebilir baseline | Yapıldı |
| B Birleşim çekirdeği | envelope, port, UV/resource QA, salt fark planı | yeni regresyon testleri | Kodlandı ve Python’da denendi |
| C Hedef kusur düzeltme | köşe/UV/dolap/askı/makara/tesisat ofsetleri | ölçüm + önce/sonra | Yapıldı; belirtilen kapsam |
| D Native Blender | register/reload, modifiyeli UV, operator, kayıt/export | gerçek makine raporu, kritik hata yok | Bekliyor |
| E Native UE | import kalibrasyonu, shader/collision, normal yönü | gerçek UE raporu | Bekliyor |
| F Kit köprüleri | SW01/AF01/PK01 uçtan uca bağlantı ve tek yüzey sahibi | birleşik örnek sahne + yeniden üretim | Planlandı |
| G Kontrollü yeni içerik | bir bakım platformu + bir servis dolabı üreticisi | temas, parametre, PBR, native kapılar | Planlandı |
| H Geniş kütüphane | GSE/HIN, ardından kule ve lojistik | her aile kendi test rig’i ile | Planlandı |

Böylece yeni bir yer destek kiti, eski hangarın yanlış köşesinin üzerine kurulmayacak. Saat/gün taahhüdü, native üretim ve export ölçümlerinden önce verilmez. Kod deposuna yayın, mevcut canlı projeyi değiştirme veya otomatik kurulum yapılmadı.

## 15. Teslim ve sürüm kabulü

Tam aday ZIP kurulabilir paket biçimindedir; yine de kararlı sürüm değildir. Tam kaynak/plan paketi, çalıştırılmış raporlar ve gerçek ölçüm görselleri ayrıdır. Kısa patch paketi yalnız doğrulanan alpha.2 kaynak hash’ine uygulanır; orijinal ZIP’i değiştirmeden yeni bir ZIP yazar.

Native test başarısız olursa beta yayımlamak yerine traceback, `.blend` tanılama örneği ve ilgili ayarlar hata listesine eklenir. Korunan AS07 dosyası byte düzeyinde aynı kalır; kaynak modelin hatalarını başkalaştırarak “aynı dosya” diye sunmayız.

### Dış kaynaklar — 26 Eylül 2026 kontrolü
[R1] AFCFS Architectural Features — https://afcfs.wbdg.org/facilities-exteriors/architectural-features/index.html  
[R2] AFCFS Building Envelope Standards — https://afcfs.wbdg.org/facilities-exteriors/building-envelope-standards/index.html — içerik geliştirme aşamasında.  
[R3] OpenUSD Encoding Stage Linear Units — https://openusd.org/release/api/group___usd_geom_linear_units__group.html  
[R4] Epic FBX Static Mesh Pipeline — https://dev.epicgames.com/documentation/en-us/unreal-engine/fbx-static-mesh-pipeline-in-unreal-engine  
[R5] Epic Data Validation — https://dev.epicgames.com/documentation/en-us/unreal-engine/data-validation-in-unreal-engine  
[R6] Epic Physically Based Materials — https://dev.epicgames.com/documentation/en-us/unreal-engine/physically-based-materials-in-unreal-engine  
[R7] Epic Instanced Static Mesh Component — https://dev.epicgames.com/documentation/en-us/unreal-engine/instanced-static-mesh-component-in-unreal-engine

Blender API/binary indirme denemesi başarılı olmadı; Blender sağlayıcı eklenti araması sonuç vermedi. Bu yüzden native çalıştırma desteği varmış gibi sunulmadı. Bu kaynakça bütün askerî/UFC standartlarının okunduğu anlamına gelmez.
