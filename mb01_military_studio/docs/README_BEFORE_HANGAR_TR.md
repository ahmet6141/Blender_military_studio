# MB01 0.2.0-alpha.1 — Modüler Mimari Laboratuvarı

**Bu teslim iki şey içerir:** ayrıntılı 0.2 geliştirme planı ve ilk modüler geometri/cephe uygulaması. Bütün 0.2 kapsamı bitmiş değildir.

## Şu an ne var?

14 parametrik parça: düz duvar, standart/dar/güneşlikli pencere, panjur, tek/çift personel girişi, HQ camlı bölüm ve saçaklı ana giriş, UNIT pencere, hangar metal/üst bant/panjurlu/servis kapılı yan paneller.

Aile/kategori filtresi; 1–32 hücreli düz ve tek kat cephe sırası; hücre genişliği/sırası; sabit kimlik; strict toplam genişlik kontrolü; gerçek açıklık; ayrı kapı pivotu; ortak malzeme rolleri; JSON planı; eski FBX export yoluna modüler snapshot adaptörü.

Katalogdaki **56 kayıt = 14 kodlanmış + 42 planlanmış**. Planlı modüller çalışan seçenekler değildir. 0.1’in beş tam bina ailesi aynı pakette korunur. AS07’nin özgün tam üreticisi var; yeni modüler kemer/çatı ayırma işlemi henüz yok.

## Test sınırı

Python testleri gerçekten çalıştırıldı. Rapor `reports/VALIDATION_REPORT.json` içindedir. **Blender 4.5 ve Unreal burada çalıştırılamadı**. Bu nedenle kurulum, panel, native bevel/shader, FBX ve UE import onaylanmış değildir. Önizlemeler gerçek kaynak geometriden bağımsız araçlarla oluşturuldu; native render sayılmaz.

## Kurulum

Bu bir **aynı MB01 paketinin aday güncellemesidir**; yeni bir eşzamanlı ikinci MB01 kurulumu değildir.

1. Çalışmanızı ve eski 0.1 kurulum ZIP’ini yedekleyin. İlk denemeyi boş dosyada yapın.
2. Eski MB01’i Preferences içinde devre dışı bırakın; sürüm karmasını önlemek için Blender’ı yeniden başlatın.
3. Add-ons bölümündeki **Install from Disk** ile yalnız `MB01_Modular_Addon_0_2a1.zip` dosyasını seçin. Geliştirme paketi kurulmaz.
4. `MB01 | Military Building Studio + Modular Lab (alpha.1)` eklentisini etkinleştirin. Gerekirse tekrar başlatın; Python dosyalarını Text Editor’de çalıştırmayın.
5. Object Mode, Unit Scale 1.0; `N → MB01` altında yeni **Modüler Mimari** panelini açın.

Eski tam bina panelinde 0.1.0 etiketi kalması bilinçlidir: o üreticinin geometri sürümü değiştirilmedi. Yeni laboratuvar ayrı alpha.1 panelidir. Otomatik eski bina/JSON migration yoktur.

## İlk 2 dakikalık deneme

Aile **Karargâh** → **Aile örnek sırasını yükle** → Detay **Draft** → **Cepheyi YENİ revizyon olarak oluştur**.

Yedi hücreli bir cephe oluşması beklenir. Bu bina değil, cephe örneğidir. Arka/yan duvar veya çatı üretmez. Sonuç; tek kök Empty altında hücrelere ve parçalara ayrılır. Ana kökü taşıyın/döndürün. `Material Preview` paket dokularını gösterir.

Tek parça denemesinde kategori/modül seçip **Modül ölçülerini yükle** ve **Tek modülü 3D Cursor konumuna ekle** düğmelerini kullanın. Aileyi değiştirmek mevcut hücre listesini otomatik dönüştürmez. Hangar sırası için açıkça aile örneğini yükleyin; hangar yüksekliği farklıdır.

Hücre listesinden parça silme, sıralama ve genişlik değiştirme yapılabilir. Hedef genişlik 0 ise hücre toplamı kullanılır; sayı girilmişse toplamla eşleşmesi gerekir. Sistem pencereyi sessizce scale etmez.

**Her üretim yeni bir kök oluşturur; eski cephe silinmez.** Eski ve yeni kökü aynı yerde bırakırsanız üst üste görünürler. Karşılaştırma için önce 3D Cursor’u başka konuma taşıyın veya eski kökü gizleyin. Gerçek artımlı yeniden üretim sonraki aşamadır.

## Malzemeler

Yeni laboratuvarda duvar/çerçeve/kaide rolleri ve üç palet seçilebilir. Hangarın ana kabuğu aileye özel boyalı metal rolünü korur. Yeni tarama dokusu indirilmedi; mevcut 8 aile / 40 prosedürel PNG aynen kullanıldı. Harici PBR üst klasörü, 0.1 şemasıyla beş harita gerektirir; ayrıntı `README_LEGACY_0_1_TR.md` içindedir.

Panelde malzeme seçimi yeni üretime uygulanır. Aktif bütün materyaller anlık olarak değiştirilmez. Aynı dosya yolundaki PNG’yi dışarıdan değiştirdiğinizde otomatik reload garanti edilmez; native testte kontrol edin.

## Export

Modüler kökü veya parçasını seçip yeni paneldeki **Aktif cephe: FBX + UE manifest** komutunu kullanın. `.blend` kaydedilmemişse mutlak çıktı klasörü seçin. Export, aynı kaynak sahnedeki eski binaları değiştirmez; yeni zaman/kimlik klasörü oluşturur.

Exporter kaynak kodu eklendi fakat burada çalıştırılmadı. Üretilen klasördeki `MB01_Import.py` önce `DRY_RUN=True` ile dosya kontrolü yapar. UE’ye gerçek aktarım ayrı testtir; kaynak eklenti klasöründeki importer doğrudan çalıştırılmaz.

`FACADE_JOIN` ve `PEDESTRIAN_OPENING` portları metadata’dır. Personel açıklığı hazır SW01 kaldırım portu değildir; sahanlık gerekir. Bu alfa otomatik sahanlık/terrain kesimi, dört eklenti arasında canlı bağlantı, HISM/LOD/Nanite, tam iç mekân veya runtime Blueprint üretmez.

## Tanılama

Geliştirme paketindeki `tools/TEST_BLENDER_WINDOWS.cmd`, ayrı factory-startup Blender sürecinde modüler üretim ve FBX denemesi yapar. Varsayılan yol Blender 4.5’tir; farklı yol için `RUN_NATIVE_TESTS.ps1 -BlenderExe "..."` kullanın. Bu araç burada çalıştırılmadı. Gerçek çıktı `$HOME/MB01_Modular_Diagnostics` altında oluşur; açık çalışma dosyanıza dokunmaz.

Normal eklenti kullanımında pip, NumPy veya VTK kurulmaz. Bağımsız render/test geliştirme araçlarının ek bağımlılıkları `requirements-dev.txt` içindedir.

## Belgeler

`docs/MB01_02_MASTER_PLAN_TR.md`: kapsam, sanat yönü, gramer, materyaller, motor akışı ve riskler.  
`docs/MODULE_CATALOG_TR.md`: 56 kaydın aile/kategori/durum ayrımı.  
`docs/PHASE_GATES_TR.md` ve `docs/ROADMAP.json`: aşamalar, iş paketleri, bağımlılıklar ve kabul koşulları.  
`docs/VISUAL_REVIEW_MODULAR_TR.md`: yapılan geometri incelemesi, sınırlamalar.  
`reports/VALIDATION_REPORT.json`: çalıştırılmış test özeti.  
`reports/BASELINE_DIFF.json`: eski kaynağa yapılan gerçek değişiklikler.

**Kapsam:** Kurgusal CGI mimari; gerçek askerî yapı/yangın/erişilebilirlik veya balistik sertifikasyonu değildir. “Hatasız” garantisi verilmez. API, görüntü ve parametre kapsamı raporlanır.
