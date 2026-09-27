# MB / 01 — MODÜLER MİMARİ SİSTEMİ
## 0.2 geliştirme planı • Parçadan yapıya, yapıdan yerleşkeye

**Belge sürümü:** 0.2-plan.1 • **Tarih:** 26 Eylül 2026  
**Kod başlangıcı:** 0.2.0-alpha.1 • **Temel:** teslim edilmiş MB01 0.1.0  
**Hedef kullanım:** Blender’da kurgusal askerî mimari/CGI çevre üretimi; Unreal’da sahneleme.  
**Test hedefi:** Önce Blender 4.5.x / Windows, sonra kullanıcının UE5.8 projesi. Hedef yazmak, o sürümde çalıştırılmış olmak değildir.

> Bu belgedeki durumlar ayrıdır: **kaynakta mevcut**, **bu sürümde kodlandı**, **Python’da test edildi**, **native uygulama testi bekliyor**, **planlandı**. Bu teslimde Blender veya Unreal çalıştırılamadı. Kod/geometri testleri, kurulum ve motor uyumluluğu testlerinin yerine geçmez.

## 1. Karar özeti

MB01 0.1.0’ın beş tam bina üreticisi korunacak. Yeni modüler mimari, bunların yerini tek hamlede alan riskli bir yeniden yazım değil, ayrı bir düzenleme ve geometri katmanı olacak. İlk sürüm bir pencereli panelden düzenli cephe sırasına kadar çalışacak; çatı, köşe ve kat birleşimi çözülmeden «tam modüler bina tamamlandı» denmeyecek.

**Üretim zinciri:** ayrıntı → mimari modül → cephe hücresi → cephe sırası → kat/kanat → kapalı bina → sahanlık/zemin bağlantısı → yerleşke → Unreal assetleri ve yerleşim.

Askerî görünüm; ortak malzeme ailesi, sade numaralandırma, düzenli cephe aksları, uygun endüstriyel parçalar ve ölçülü kullanım izleriyle kurulacak. Her yüzeyi kamuflajla kaplamak veya gereksiz güvenlik cihazı eklemek tasarım ölçütü olmayacak.

### “Standart” ifadesinin kapsamı

Ülke, kurum, tesis sınıfı ve uygulanacak belgenin adı/sürümü tanımlanmış değil. Bu yüzden gerçek askerî tesis, yapı, yangın, erişilebilirlik, patlama veya balistik uygunluk iddiası yok. Modülün metal görünmesi ona koruyucu performans kazandırmaz. Atış alanına ilişkin genişletmeler eğitim/film dekoru sınırında kalır.

Şimdiki profil `MIL_CGI_NEUTRAL` adlı **kurgusal görsel profil** olacak. Bir dış standart ileride referans alınacaksa kural kimliği, kaynak, baskı, alıntılanan bölüm, uygulanma koşulu ve test ayrı kaydedilecek. Kaynağı olmayan sayısal limitler yalnızca “bu üreticinin desteklediği görsel aralık” olarak etiketlenecek. Sertifikasyon rozeti üretilecek bir özellik değildir.

## 2. Mevcut kaynaklardan çıkan başlangıç durumu

MB01 README ve kaynakları; HQ, UNIT, HANGAR, SHELTER, RANGE_SET ailelerini, PBR harita okuyucusunu, `UV0_Tile` ve `SW01_Tint` düzenini, Blender üretim kodunu ve UE aktarım scriptini içeriyor. Tam iç mekân, modüler cephe editörü, otomatik HISM/Nanite ve otomatik arazi/yol birleşimi mevcut tamamlanmış özellikler değil. Kaynak: `README_LEGACY_0_1_TR.md`, `core.py`, `materials.py`, `blender_backend.py`, `exporter.py`.

AS07 özgün kaynak ve lisansı korunacak. `span` net geçiş açıklığı değil çerçeve aks ölçüsüdür. Kaynak dosyada giriş -Y, MB01’de bina içi +X olarak tanımlıdır; adaptör dönüşümü bir defa uygulanmalı. Kaynak geometri üretimini kullanırken eski sahne/kamera/dünya kurulumuna girilmeyecek. Bu dosyanın özgün hash’i rapora alınmıştır.

İlk 0.2 adayında `core.py`, `materials.py`, `coordinates.py`, AS07 kaynağı ve doku dosyaları değiştirilmedi. Kayıt, eski paneli yeni kökten koruma ve exporter metadatası için sınırlı adaptör değişiklikleri yapıldı. Ayrıntılı değişiklikler `reports/BASELINE_DIFF.json` içindedir.

## 3. Kapsam ve sürüm sınırı

| Alan | alpha.1 durumu | Sonraki hedef |
|---|---|---|
| Parça kataloğu | 56 kayıt; 14 kaynak üretici, 42 planlanmış | Test kapılarıyla kademeli açılma |
| Tek parça | Sınırlı ölçülerle 14 cephe modülü | Köşe, üst/alt bitiş ve bağlantılar |
| Cephe | 1–32 hücreli düz, tek kat sıra | Köşe, çoklu cephe, kat üst üste koyma |
| Mevcut tam binalar | 0.1 üreticileri korunuyor | Modüler tariflere açık ve geri alınabilir geçiş |
| PBR | Eski 8 doku ailesi ve seçili malzeme rolleri | Görsel tarayıcı, içerik hash’i, yerel yenileme |
| Kapılar | Yeni modüllerde ayrı pivot ve açıklık pozu | Doğrulanmış runtime bileşeni ve çekim durumları |
| Site bağlantısı | Cephe birleşim portları; giriş “sahanlık gerekli” kaydı | SW01/AF01/PK01 bağlantı yöneticisi |
| Unreal | Eski FBX akışına modüler metadatayı taşıyan adaptör | Motor içi test, fark raporu ve artımlı aktarım |
| Native test | Çalıştırılacak smoke test sağlandı, burada çalıştırılmadı | Gerçek Blender ve UE raporları |

Alpha.1, bitmiş 0.2 değildir. Bir cephenin arkasına eski binayı üst üste yerleştirip eski duvarı gizleyerek modüler bina varmış gibi gösterilmeyecek. Eski duvarın sökülmesi, köşe ve döşeme sahipliği çözülmesi ayrı aşamadır.

## 4. Katalog düzeni

Katalog iki bağımsız filtre taşıyacak: **yapı ailesi** ve **mimari kategori**. Aynı işlevi paylaşan modüller ortak kökte duracak; hangar gibi farklı oran/detay isteyen modüller ayrı aile altında tanımlanacak.

### Yapı aileleri

**COMMON:** HQ, birlik ve destek yapılarında tekrar kullanılan paneller, personel girişleri, köşeler ve bitişler.  
**HANGAR:** Geniş açıklıklı yapı kabuğu, taşıyıcı görünüşü, özel ana kapı ve servis parçaları.  
**SHELTER / AS07:** Mevcut açık kemerli kimlik; kemer, çatı hücresi, panjur, arka duvar ve servis girişi.  
**HQ:** Karargâha özgü ana giriş, camlı bölüm, portik ve seçili iç mekân.  
**UNIT:** Tekrarlayan pencereler, yan giriş, koridor/merdiven hacmi ve seçili personel odaları.  
**SUPPORT:** Küçük depo, eğitim gölgeliği ve nötr pano gibi dekoratif destek modülleri.

### Kategoriler

Duvar/panel; giriş/kapı; cam; güneşlik; köşe/sonlandırma; çatı; taban/sahanlık; görsel taşıyıcı; hangar kabuğu; hangar girişi; tesisat/detay; iç mekân; bina hacmi; adaptör.

Katalogdaki bir kayıt seçilebilir hâle gelmeden `implemented_core`, geometri testleri ve en az iki görüntü denetimi koşullarını sağlamalı. “Planlandı” kaydı menüde çalışan bir düğme gibi sunulmaz. Native test durumu ayrıca tutulur; saf çekirdek etiketi motor uyumluluğu değildir.

Tam kayıt listesi: `MODULE_CATALOG_TR.md` ve eklenti içindeki `modular/module_catalog.json`.

## 5. Mimari modül sözleşmesi

Her modülde sabit kimlik, sınıf, izin verilen aileler, sürüm, genişlik/yükseklik aralıkları, üretici adı, malzeme rolleri, nominal kutu ve durum bilgisi olacak. Şema dışında alan sessizce kabul edilmeyecek.

**Nominal ölçü / gerçek geometri / net açıklık ayrı kavramlardır.** Hücre genişliği 3,6 m olduğunda penceresi 3,6 m değildir. Saçak çıkıntısı, nominal hücre sınırını aşabilir; cephe tasarımcısı bunu ayrıca kontrol eder. Kapının net geçişi, kasa dış ölçüsü ve açılma hacmi ayrı kayıtlardır. Bunlar ölçülmüş inşaat performansı anlamına gelmez.

Yerel koordinatlar: +X içeri, +Y sola, +Z yukarı. Önden bakış -X tarafından yapılır. Bir modülün taban/ön merkezinde pivotu bulunur. Kapı kanatlarında pivot menteşe veya sürgü dinlenim noktasındadır. Negatif scale ile kapı/sayı aynalama varsayılan işlem değildir; sağ/sol varyant açıkça üretilir.

Cephe birleşim portunda rol, konum, normal, profil, yükseklik ve kalınlık bulunur. `FACADE_JOIN`, `PEDESTRIAN_OPENING`, `PEDESTRIAN_PATH`, `APRON` birbirinin yerine geçmez. İlk modül giriş portu yalnız açıklığı işaretler; hazır kaldırım veya erişilebilir sahanlık değildir.

Birleşim toleransı için kaynak geometrisinde başlangıç hedefi 1 mm; salt sayı toplama testlerinde daha sıkı hata payı kullanılır. Bu bir imalat toleransı standardı değil, modelleme tutarlılık hedefidir. UE ithal sonucu ayrıca ölçülür.

## 6. Cephe grameri ve yerleşim çözücüsü

İlk çözücü explicit bir hücre listesi okur. Her hücrenin sabit kimliği, modül kimliği ve genişliği vardır. Hücre konumu kümülatif genişlikten hesaplanır. Hedef toplam girilmişse tam eşleşme aranır; model scale edilmez. Alpha.1 yalnız düz sıra ve ortak yükseklik/kalınlık kullanır.

İleri aşamada `STRICT`, `FILL_WITH_ALLOWED_PANEL` ve `REBALANCE_APPROVED_BAYS` seçenekleri ayrı açılacak. Filler yalnız izin verilen boş duvar aralığında oluşturulacak; pencere, kapı veya taş dokusu esnetilmeyecek. Artan mesafe bazen mimari olarak çözülemeyebilir; çözücü bunu hata olarak gösterecek.

Her cephe kenarı için pencere alt/üst referansı, yatay bant, kaide üstü ve çatı bitiş referansı tutulacak. Simetri komutu bütün hücreleri kör biçimde aynalamayacak; kapı menteşesi ve tabela yönü korunarak uygun karşılık seçilecek.

Katlar üst üste getirilirken taban ve tepe bağlantıları eşleşecek. Üst katta zemin girişi üretilmeyecek. L/U biçimleri, iç/dış köşe geometrisi ve döşeme paylaşımı tamamlanmadan sunulmayacak. Duvar kalınlığı, köşe dönüşü ve cam köşe bitişleri için ayrı birleşim detayı gerekecek.

## 7. Aileye özel tasarım kuralları

### 7.1 Hangar

Modüler hangar başlangıcı, yan kabuk üzerinde metal panel, üst bant pencere, panjur ve personel girişi olacaktır. Bunlar bugün kodlanmıştır; tüm taşıyıcı hangar yeniden modülerleştirilmiş değildir.

Sonraki paket: portal çerçeve, görünür bağlantı başları, aşıklar, çatı kaplaması, alın bitişi, büyük sürgülü kapı, ray başlığı/alt kılavuz, kapı kanat modülü, apron eşiği ve servis duvarı. Ray, kolon ve kanat kalınlıklarının kaba geometrik çakışmaları denetlenecek. Statik taşıma, motor boyutlandırma veya gerçek mühendislik yeterliliği hesaplanmayacak.

Hangar içi ve dışı malzeme rollerinde boyalı metal ile açık metal ayrılacak. Panjur kanatları ince ve tekrar eden geometri olduğundan yakın/uzak temsil seçenekleri test edilecek. Ana kapı ile servis kapısı ayrı hareket sınıfı olacaktır. Arkaya bir kapı koymak otomatik güvenli çıkış tasarımı sayılmayacak.

### 7.2 AS07 açık shelter

Mevcut kemerli siluet korunacak. Kaynak kopyası fork edilmeden adaptör üzerinden parçalara ayrılacak. Önce tam modelin aynılığı, sonra kemer hücresi/çatı hücresi ayrıştırması sınanacak. Orijinal apron ile AF01 zemini aynı anda üretilmeyecek. `span` gerçek net giriş açıklığı olarak kullanılmayacak.

### 7.3 Karargâh

Ana giriş kuvvetli, yan servis girişleri daha sade tasarlanacak. Giriş saçağı, camlı bölüm ve pencere ritmi aynı aks sisteminden beslenecek. Lobi camı ile arkasındaki seçili iç mekân birbirini karşılayacak. Kurgu isimlik/numara alanları bulunacak; gerçek birlik arması varsayılan dağıtılmayacak.

### 7.4 Birlik/personel yapıları

Daha sade, tekrar eden fakat birkaç varyantla ritim kazanan pencere modülleri kullanılacak. Pencerelerde kör rastgelelik yerine küçük perde/derinlik farkları uygun mesafede sunulacak. Yan giriş, koridor ve merdiven hacmi dış kabuğu ana aileyi bozmayacak.

### 7.5 Destek/eğitim dekoru

Küçük depo dış kabuğu, gölgelik, ekipman rafı ve nötr eğitim panosu. Katalog sınıflandırması bir korunma/silah kullanım iddiası taşımayacak. Gerçek atış tesisinin mesafe, malzeme, balistik koruma ve emniyet sistemi bu üreticinin kapsamı değildir.

## 8. Malzeme, UV ve kaynak yönetimi

Bina görünümü rol tablosundan kontrol edilecek: ana duvar, kaide, çerçeve, boyalı metal, galvaniz, çatı, cam, kauçuk, iç yüzey, tabela ve aydınlatma. Roller her modülde aynı anlama gelecek. Alpha.1, mevcut tariflerden duvar/çerçeve/kaide seçimini ve paleti uygular; gelişmiş thumbnail tarayıcısı henüz yoktur.

`UV0_Tile` metre referanslı yüzey koordinatı, `SW01_Tint` nötr/renk çarpanı olarak korunacak. Bunlar lightmap UV veya kir maskesi adı altında ezilmeyecek. Benzersiz boya atlası, trim atlası ve lightmap ayrı katmanlar olacaktır. Bitişik panellerde doku fazı ve yön sürekliliği ileriki çözümde ayrı test edilecek; ilk modüller bağımsız yerel UV taşır.

PBR harita politikası: BaseColor sRGB; ORM doğrusal ve R=AO/G=Roughness/B=Metallic; NormalGL ve NormalDX yön ayrımı; Height 16-bit kaynak. Height dosyası otomatik displacement demek değildir. Boyalı metalin her pikselini metal yapmak yerine kaplama ve açık alt malzeme ayrılacaktır.

Yeni yüksek kaliteli kaynaklar eklendiğinde sağlayıcı, asset ID, üretim yöntemi, lisans, fiziksel tekrar boyutu, çözünürlük ve içerik hash’i kaydedilecek. Eksik set uyarı verecek. Arayüz, “tarama” ile “prosedürel” etiketlerini ayrı gösterecek. Alpha.1’de yeni taranmış dokular indirilmedi; 0.1’deki sekiz aile yeniden kullanıldı.

Gelişmiş PBR aşamasında aynı dosya yolunun içeriği değişince image reload ve materyal cache invalidation uygulanacak. Şimdiki temel cache, tarif ve yol temellidir; aynı dosyayı dışarıdan değiştirme durumunun otomatik yönetildiği varsayılmayacak.

## 9. Estetik ve görsel kalite ekleri

Kalite katmanları “silüet / birleşim / yüzey / kullanım izi / sunum” sırasıyla değerlendirilecek. Kötü birleşim, dramatik ışıkla gizlenmeyecek.

**Yeni ayrıntılar:** pencere sövesi ve denizliği, alt damlalık izi, ince başlık gölge çizgisi, kapı süpürgelik/kickplate yüzeyi, sade kulp, güneşlik braketi, giriş saçağı alt yüzeyi, opal armatür alanı, kaide bandı ve metal panel kenetleri. Alpha.1’de bu ayrıntıların ilgili modüllerde temel geometrisi var. Native bevel ve malzeme görünümü henüz onaylanmadı.

İleri ayrıntılar; köşe kapakları, kapı rayı sonlandırıcıları, tesisat güzergâhı/kelepçeleri, bakım cep kutuları ve binaya bağlı ıslaklık maskesidir. Ayrıntı boyutu kamerada anlamlı değilse gerçek geometri yerine sade temsil seçilecek.

“Maintained / In Use / Repainted / After Rain” durumları; boyama, toz ve nemi bağımsız kontrol eder. Çatı altı daha kuru görünüm bir artist maskesidir; fiziksel yağış veya drenaj mühendisliği değildir. Aynı seed ve hücre kimliğiyle tutarlı varyasyon üretilecek. Alpha.1’de varyasyon anahtarı metadata olarak üretilir; yeni kir sistemi uygulanmış değildir.

## 10. Kullanıcı arayüzü ve düzenleme güvenliği

Tek MB01 eklentisi içinde iki açık alan bulunacak: eski tam bina üreticisi ve yeni **Modüler Mimari** laboratuvarı. Eski yapı seçiliyken modüler yeniden üretim, modüler kök seçiliyken eski tam bina yeniden üretimi karıştırılmayacak.

Arayüz: Aile → Kategori → Modül → Boyutlar → Sıraya Ekle → Hücre Listesi → Kontrol → Üretim. Liste hücreleri yukarı/aşağı taşınabilir, silinebilir, genişliği değiştirilebilir. JSON preset veri taşır; Python çalıştırmaz.

Alpha.1 her üretimde yeni bir kök oluşturur. Eski yapı otomatik silinmez veya migration uygulanmaz. Sonraki aşamada “yalnız farkı uygula”, parça kilidi, durum kaydı ve geri alma geliştirilecek. Kilitli pencereye yeni duvarı üst üste koymak koruma sayılmayacak; conflict çözümü gerekecek.

Arayüz geri bildirimi eksik PBR, uyumsuz aile, genişlik toplamı ve aşırı hücre sayısı için açık hata verecek. Hata metni Text datablock’a kaydedilecek. Üretim dünya, ışık, kamera ve sahne birimlerini gizlice değiştirmeyecek. Ağ erişimi ve pip yükleme normal kullanım için gerekli olmayacak.

## 11. Site araçlarıyla entegrasyon

MB01/AF01/SW01/PK01 arasında paylaşılacak olan bir “isim” değil, veri sözleşmesidir. Birimler, baz düzlemi, yürüyüş yüzeyi, normal, profil ve nesne sahipliği anlaşılır olmalı.

Yeni modülün personel açıklığına önce sahanlık eklenmeli. Kapı açıklığı genişliği kaldırım genişliğiyle karıştırılmayacak. Mevcut portlarda kullanılan taban + yükseklik kuralı korunacak. AF01 apron bağlantısında bir yüzeyin tek üreticisi olacak; beton plaka, eşik, drenaj ve işaretleme ayrı sahipliklerle yönetilecek.

PK01 için bina/zemin/yol ayak izleri dışlama maskesine çevrilecek; mevcut eklentinin bunu bugün otomatik okuduğu iddia edilmeyecek. İlk sahne düzlemde test edilecek; eğimli araziye otomatik oturma ve geospatial koordinatlar ayrı kapsamdır.

## 12. Unreal aktarım sözleşmesi

Geometri Blender’da oluşturulur; UE ilk aşamada modelleri ve yerleşimleri içe alır. Python akışı editör otomasyonudur. Modüler cephe JSON’unu UE runtime üreticisi olarak sunmayacağız.

FBX başına bir render asseti, ilgili collision ve varsa uygun socket yardımcıları politikası korunacak. Epic birden çok render mesh + socket/collision kombinasyonlarında sınırlar açıklıyor [E1]. Statik duvarlarda açıklıkları koruyan collision; hareketli kanatlarda ayrı basit hull gerekir. Tek büyük kutuyla bütün kapı boşluğunu kapatmak kabul edilmez.

İlk exporter modüler snapshot’ı mevcut manifestin ek alanında taşır. Eski importer ile biçim uyumu kaynak incelemesine dayanır; çalıştırılmış UE testi değildir. Ölçek/pivot/yön için mevcut asimetrik kalibrasyon parçaları korunur. Tekrar içe aktarma kullanıcı değişiklikleri üzerine sessiz yazmayacak şekilde sürümlenmelidir.

Materyal tarifinin Blender ve UE için ayrı kurucuları bulunacak. UE Material Instance sistemi, parametreli ana materyalden görünüm varyasyonları üretmek için uygundur [E2]. Özel Blender node ağının birebir taşındığı varsayılmaz.

Tekrarlanan modüller geometri/materyal/collision anahtarıyla gruplandırılır. UE ISM yaklaşımı aynı mesh kopyalarını gruplar; birçok malzeme/collision özelliği component seviyesinde ortak olduğundan farklı gereksinimler ayrı gruplar olmalıdır [E3]. Otomatik HISM/Nanite düğmesi performans garantisi olmayacak. Bu optimizasyonlar alpha.1’de uygulanmadı.

## 13. Test stratejisi ve görsel onay

**L0 veri:** Şema, kimlik, enum, sayısal sonluluk, boyut sınırı ve planlanmış üretici reddi.  
**L1 geometri:** Yüz indisleri, alan, UV köşe sayısı, malzeme kimliği, gerekli kapalı gövdeler ve açıklık merkezinde duvar bulunmaması.  
**L2 birleşim:** Bay toplamı, komşu port aralığı/normal, bağımsız kimlik, köşe/kat bağlantısı.  
**L3 Blender:** Temiz kurulma, register/unregister, panel aksiyonları, Object Mode, dosya yeniden açma, seçim koruma, materyal yükleme ve FBX.  
**L4 Unreal:** Gerçek motor içe aktarımı, kalibrasyon, materyal, collision, kapı pivotu ve duplicate import.  
**L5 görsel:** Ön/arka/yan yakın görünüm; sert yan ışık; PBR ölçek; cam ve kapı çevresi; hareketli kamera titreşimi.  
**L6 operasyonel yazılım dayanıklılığı:** Türkçe/uzun yol, eksik doku, salt okunur disk, bozuk JSON, offline ve iptal.

Bu teslimde çalıştırılmış test sayısı `reports/VALIDATION_REPORT.json` içindedir. Gelecek aşamaların kabul senaryoları çalıştırılmış test gibi bu sayıya eklenmez. Kaynak aralıklarında min/default/max örnekleri tüm kombinasyonların kanıtı değildir.

Native test kapısı tamamlanmadan sürüm “Blender/UE uyumlu final” olarak etiketlenmeyecek. Windows ve Linux farklı test satırlarıdır. Headless test ile arayüzün elle kullanımı da farklıdır.

## 14. Aşamalı geliştirme ve bağımlılıklar

| Aşama | Ana iş | Çıkış ölçütü | Bu teslimdeki durum |
|---|---|---|---|
| P0 | Kaynak envanteri, risk ve kapsam, şemalar | Kaynak hash’leri, aile sınırları, veri şeması | Tamamlandı |
| P1 | 14 modül, katalog, tek cephe sırası | Geometri ve sözleşme testleri | Kodlandı; Python testleri geçti |
| P1-N | Native başlangıç doğrulaması | Gerçek Blender kurulum/üretim/export raporu | Bekliyor |
| P2 | Köşe, uç bitiş, kaide, parapet, çoklu cephe | Kapalı tek kat bina; sızdıran/çift yüzey yok | Planlandı; P1-N bağımlı |
| P3 | Katlar, L/U plan, HQ/UNIT grameri | Açıklık/kat/çatı hizaları, tutarlı roller | Planlandı; P2 bağımlı |
| P4 | Hangar ana kapı/taşıyıcı/çatı ve AS07 ayrıştırma | Eski AS07 regresyonu ve hareket boşluğu | Planlandı; P2 bağımlı |
| P5 | PBR tarayıcı, atlas, duruma bağlı yüzey | Lisans/ölçek/kanal ve nötr render incelemesi | Planlandı |
| P6 | SW01/AF01/PK01 yüzey ve port köprüleri | Tek zemin sahibi ve canlı çakışma raporu | Planlandı |
| P7 | UE artımlı import, grup/instancing | Native UE import ve tekrar-import testleri | Planlandı |
| P8 | Seçili iç mekânlar, animasyon/çekim durumları | Aynı sahnenin farklı çekimlerde sürekliliği | Planlandı |
| RC | Paketleme, kullanım belgeleri, demo, bilinen sorunlar | Tüm hedef test kapılarının somut raporu | Planlandı |

Süre tahmini native prototipin üretim/export ölçümleri sonrasında yapılacak. “Bütün sistemi bir adımda hatasız bitirme” hedefi yerine her kapıdaki eksiklik görünür olacak. Paralel geliştirilecek belgeler ve sanat denemeleri, onaylanmamış çekirdeğin üstüne bağımlı özellik koymayı haklı çıkarmaz.

## 15. İlk iki uygulama sahnesi

**FACADE_HQ:** Düz duvar → güneşlikli pencere → normal pencere → ana giriş → normal pencere → güneşlikli pencere → düz duvar. Tek kat, cephe laboratuvarı; arkasında tam bina yok. İlk amaç ritim, kapı boşluğu, modül fit’i ve ortak PBR davranışı.

**FACADE_HANGAR:** Metal panel → üst bant pencere → personel girişi → üst bant pencere → panjur → metal panel. İlk amaç yüksek duvar oranı, panel kenetlerinin açıklığı kesmemesi ve hangara özgü sınıf ayrımı.

UNIT ve SUPPORT örnekleri de yardımcı test setidir. AS07’nin mevcut tam üreticisi eski panelde kalır. Yeni modüler AS07 hücreleri bu ilk cephe setinin içinde varmış gibi gösterilmez.

## 16. En önemli riskler ve kararlar

**Kapsam şişmesi:** 56 kaydın hepsine aynı anda düğme açılmayacak; tamamlanan ve taslak ayrılır.  
**Geometri temasları:** Mimari montaj temasları ile istenmeyen yüzey çakışması ayrı test edilir. Her temas “non-manifold hatası” sayılmaz.  
**PBR görünümü:** Bağımsız preview cam ve shader eşdeğeri değildir; native nötr render şart.  
**Eski proje güvenliği:** Aynı paket adıyla aday kurulum güncellemedir; 0.1 ZIP’i yedek tutulmalı, önce yeni dosyada denenmeli. Otomatik veri migration yok.  
**Paylaşılan kimlikler:** Katalog sürümü ve sabit hücre kimliği saklanır; listede kaydırmak kimliği değiştirmez.  
**Performans:** UV, materyal slotları, draw call ve texture belleği ölçülür; yalnız poligon sayısı üzerinden FPS vaat edilmez.  
**Dosya yolu ve kaynak:** UTF-8, açık schema, checked relative paths; indirilmeyen asset “kurulu” diye gösterilmez.

## 17. Sürümün bitmiş sayılması

Bir özellik için UI düğmesi, kaynak kod, geometri testi, beklenen hata davranışı, örnek preset, gerekli native test ve belge birlikte tamamlanmalı. Görsel kalite en az önden/arkadan ve bir yakın görünümde değerlendirilir. Sonradan ortaya çıkan hata kayıt altına alınır; “hatasız” etiketiyle kapatılmaz.

**Öncelik:** kullanıcı verisini koruma → modül/bağlantı doğruluğu → aileye özgü mimari → PBR/UV → native aktarım → ileri detay/optimizasyon.

## Kaynak ve araştırma sınırı

[P1] Konuşmada teslim edilmiş MB01 0.1.0 README ve kaynak paketi; bu çalışma için yeniden okundu ve açıldı.  
[P2] Kullanıcının AS07_Shelter_Generator.py kaynağı; MIT bildirimi ve hash’i korundu.  
[E1] Epic, FBX Static Mesh Pipeline: https://dev.epicgames.com/documentation/unreal-engine/fbx-static-mesh-pipeline-in-unreal-engine  
[E2] Epic, Creating and Using Material Instances: https://dev.epicgames.com/documentation/en-us/unreal-engine/creating-and-using-material-instances-in-unreal-engine  
[E3] Epic, Instanced Static Mesh Component: https://dev.epicgames.com/documentation/en-us/unreal-engine/instanced-static-mesh-component-in-unreal-engine

Epic sayfaları 26 Eylül 2026’da açıldı. Blender 4.5 Asset Catalog / Extensions / Threading belgelerine web erişimi bu oturumda sonuçlanmadı. Bu nedenle onlara dayalı güncel API doğrulaması iddia edilmedi. Bu kod Blender 4.5’i hedefleyen mevcut proje desenleriyle yazıldı ve native smoke test sağlandı; bu ortamda `bpy` yok, Blender indirme girişimi DNS aşamasında başarısız oldu. Askerî inşaat mevzuatı araştırılıp uygulanmış değildir.
