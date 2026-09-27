# MB01 alpha.3 QA + BASE01 Assembly 0.1
## Önce birleşim kalitesi, sonra yeni kitler

**26 Eylül 2026.** Bu teslim, Hangar Studio alpha.2 üstüne dar kapsamlı kaynak düzeltmesi ve ortak kalite altyapısı ekler. Yeni bir hava üssü, GSE kütüphanesi veya bütün kitleri yöneten canlı sistem değildir.

## Sonuç

**322 saf Python testi**, **27 geometri konfigürasyonu**, **63 kapı pozu/açıklık karşılaştırması** geçti. Yedi gerçek geometri görüntüsü üretildi: üç eş kamera önce/sonra çifti ve bir yeni genel görünüm. Bir GLB bağımsız okuyucuda yeniden açıldı. Native Blender/UE çalıştırılmadı; kararlı sürüm kapısı açık değildir. `reports/VALIDATION_REPORT.json` sonuçları, `docs/BASE01_MASTER_PLAN_TR.md` olgunlaşmış planı içerir.

## Dosya türleri

- **MB01_AssemblyQA_Addon_0_2a3.zip:** Tam aday eklenti. MB01 alpha.2’nin güncellemesidir; aynı anda ikinci kopya kurulmaz.
- **BASE01_Research_and_Patch_0_1.zip:** Plan, raporlar ve küçük kaynak patch’i. Blender kurulum ZIP’i değildir. Orijinal alpha.2 ZIP’inden yeni kurulum ZIP’i üretilebilir.
- **BASE01_AssemblyQA_Development_0_1.zip:** Kaynak, dokular, testler, native tanılama araçları ve görseller. Eklenti olarak doğrudan kurulmaz.

## İlk Blender denemesi

1. Önce `.blend` dosyanızı ve eski kurulum ZIP’ini yedekleyin. İlk testi boş dosyada yapın.
2. Eski MB01’i Preferences’ta devre dışı bırakın, Blender’ı yeniden başlatın. Tam aday ZIP’i **Install from Disk** üzerinden kurun ve etkinleştirin.
3. Eklenti adı `MB01 | Military Building Studio + Hangar Studio (alpha.3 QA)` olmalıdır. Blender’ın sayısal paket sürümü `(0,2,3)`; ürün adı `0.2.0-alpha.3` şeklindedir.
4. Object Mode ve Unit Scale 1.0 kullanın. `N → MB01 → Hangar Studio | alpha.3` bölümünde Daylight/Draft yükleyip **yeni revizyon** oluşturun.
5. `N → MB01 → BASE01 | Uyum ve kalite denetimi` bölümünde yapının kökünü veya alt mesh’ini seçerek gerçek mesh denetimini çalıştırın. Rapor Blender Text Editor’de `BASE01_QA_...` adlı metinde oluşur.
6. `Son rapordaki sorunlu parçaları seç` düğmesi yalnız seçim yapar; geometriyi düzeltmez/silmez. Görünmeyen diğer koleksiyonları açmaz.

`__init__.py` Text Editor’de Alt+P ile çalıştırılmaz. Panel/native davranışı bu ortamda test edilmemiştir. Kurulum hatası olursa yeni özellikler tamamlanmış sayılmaz; tam traceback ile ilerlenmelidir.

## İki portu kontrol etmek

Tam iki tanımlı Empty seçin. **Doğrudan birleşim** denetimi yüzey kotu, yön, genişlik ve profil kontrolüdür. Nesneleri taşımaz, kaldırım çizmez. Birbirinden metrelerce uzaktaki iki portun hata vermesi beklenir; önce aradaki bağlantı geometrisi üretilmelidir. Personel açıklığı hazır kaldırım ucu değildir; sahanlık adaptörü gerekir.

## Değişen geometri

Ortak envelope, duvar kalınlığını arka köşe/çatı/döşeme/inişlere taşır. Alpha.2 JSON okunur ama dış sınırlar düzeltilmiştir; eski sahnenin yerleşimini kendiliğinden yeniden hesaplamaz. Karşılaştırmayı ayrı kökte yapın. 16/22/36 cm seçenekleri görsel üretici parametreleridir; gerçek bina standardı değildir.

Mevcut AS07 kaynak dosyası, eski bina çekirdeği ve modüler parça üreticisi değiştirilmedi. SW01, PK01, AF01 ZIP’lerine yazılmadı. Canlı köprü/terrain otomasyonu eklendiği iddia edilmez.

## Materyal ve export

Aynı dosya yolunda değişen doku, gerçek içerik hash’iyle farklı kaynak sayılır. Yeni materyal yeni image datablock kullanır; diğer projelerin görüntüleri zorla reload edilmez. Kaynak dosyası materyal kurulduktan sonra değişmişse export ön-denetimi durur; yeniden üretim/kaynak eşlemesi incelenmelidir.

Eski materyallerde içerik hash’i yoksa uyarı oluşabilir. Mevcut 40 prosedürel PNG korunmuştur; yeni tarama/8K kütüphanesi yoktur. Normal/tangent ve modifier UV sonucu native test gerektirir.

Exporter, native değerlendirilmiş mesh/UV ve kaynak hash raporunu manifest’e ekleyecek şekilde güncellendi. Hata varsa yeni exporta başlamaz. Bu bloklayıcı kontroller Blender’da henüz çalıştırılmadı; başarısızlık raporunu atlayıp exportu başarılı saymayın.

UE tarafındaki eski `DRY_RUN=True` ve ayrı FBX+JSON yolu korunuyor. Yeni otomatik ISM/HISM/Nanite, runtime Blueprint veya native Data Validation validator kaydı uygulanmadı.

## Geliştirme ve tanılama

Tam kaynak klasöründe normal Python ile:

```text
python -m unittest discover -s tests -v
```

Blender’a kurmadan bağımsız native deneme için tam geliştirme paketinde `tools/TEST_ASSEMBLY_WINDOWS.cmd` çalıştırılır. Alternatif:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\RUN_ASSEMBLY_NATIVE.ps1 -BlenderExe "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe" -Render
```

Ayrı `--background --factory-startup` süreci açılır; açık çalışma dosyanız yüklenmez. Çıktı ev klasöründeki `BASE01_Diagnostics/<zaman_kimlik>` içine yazılır. Kaydı/exportu/native raporu gerçek deneme oluşturur; bu pakette sahte başarılı Blender raporu yoktur. Render seçeneği isteğe bağlı ve daha ağırdır. Komut yalnız ilgili PowerShell sürecinin yürütme seçeneğini değiştirir; sistem politikasını kalıcı değiştirmez.

## Bilinen sınırlar

Tam self-intersection taraması yok. Kaynak vertex UV denetimi render görüntüsünün yerine geçmez. Kapı örnekleri açıklık/metadata eşleşmesini sınar; bütün hareketli/sabit nesnelerin çarpışma testi değildir. Bağımsız CPU görüntüleri native bevel, tangent normal, kırılma ve zamansal AA içermez. Dry-run güncelleme planlayıcı yalnız veri fonksiyonudur; mevcut sahnenizi otomatik güncellemez. Kararlı sürüme çıkış native Blender/UE sonuçlarına bağlıdır.
