# MB01 — Hangar Studio 0.2.0-alpha.2
## Tam hangar üretimi · modüler cepheler · iki çatı sistemi · teleskopik kapılar

**Durum:** Uygulanmış geliştirme sürümü. Önceki MB01 0.2.0-alpha.1 paketinin üzerine eklenmiştir; aynı eklentinin güncellemesidir.

**Doğrulama:** 254 Python testi (168 korunmuş + 86 yeni), 24 ek geometri kombinasyonu ve 3 GLB'nin bağımsız yeniden okunması geçti. 9 gerçek geometri görünümü üretildi ve incelendi. **Blender 4.5 / UE5.8 uygulama içi testleri yapılmadı.** Önizlemeler bağımsız CPU görüntüleyicisidir; native bevel, tangent normal, kırılma ve çok sekmeli GI'yi göstermez. Bu sonuçlar tam uygulama onayı veya bütün parametre uzayının testi değildir.

**Kapsam:** Kurgusal CGI / animasyon filmi mimarisi. Gerçek taşıyıcı hesap, rüzgâr/kar yükü, yangın projesi, enerji hesabı, uçak taksi emniyeti, askerî veya imalat sertifikasyonu içermez. Sayısal sınırlar üreticinin geometrik çalışma aralıklarıdır.

Görseller, örnek GLB modeller ve raporlar ayrı geliştirme paketindedir.

## 1. Bu sürümdeki esas ilerleme

Alpha.1'in yeni modüler kısmı tek parça ve düz cephe sırası üretiyordu. Bu güncelleme, o kütüphanenin gerçek dört hangar cephe modülünü yeni bir **tam kapalı hangar üreticisine** bağlıyor. Eski beş bina ailesi, AS07 ve 14 parçalık cephe laboratuvarı korunur.

Eski 56 kayıtlı katalogdaki bütün planlı öğeler birden tamamlandı diye işaretlenmez. Yeni çerçeve, çatı, kapı ve servis parçaları Hangar Studio'nun bileşenleridir; şimdilik eski tek-modül tarayıcısında ayrı düğmeler değildir.

### Üç önayar

| Önayar | Gövde / m | Çatı | Kapı |
|---|---:|---|---|
| DAYLIGHT_MRO | 32 × 36 | Yükseltilmiş, yanları camlı monitor ışıklık | 6 kanat, 3 ray düzlemi |
| CLASSIC_MAINTENANCE | 28 × 36 | Eğimli metal çatı | 4 kanat, 2 ray düzlemi |
| COMPACT_SERVICE | 24 × 24 | Eğimli metal çatı | 4 opak kanat |

Ölçüler referans uçağa göre sertifikalı seçim değildir. Kullanıcı uçağının modelini, ekipmanlarını ve gerçek ölçülerini ayrıca kontrol etmelidir. MRO adı burada görsel önayardır; belirli bakım yetkinliği veya tesis sınıfı onayı ifade etmez.

## 2. İlk kurulum

Bu bir legacy Blender ZIP eklentisidir. Önceki MB01'i aynı anda ikinci kopya olarak kurmayın.

1. Çalışmanızı kaydedin; eski kurulum ZIP'ini yedekleyin.
2. Preferences'tan eski MB01'i devre dışı bırakın ve Blender'ı yeniden başlatın.
3. **Edit → Preferences → Add-ons → Install from Disk** ile `MB01_HangarStudio_Addon_0_2a2.zip` dosyasını seçin.
4. **MB01 | Military Building Studio + Hangar Studio (alpha.2)** kaydını etkinleştirin.
5. Yeni, boş bir .blend dosyasında **Object Mode**, **Unit Scale = 1.0** kullanın.
6. **3D View → N → MB01 → Hangar Studio | alpha.2** paneline geçin.
7. Daylight önayarını seçip **Hangar önayarını yükle** düğmesine basın.
8. İlk üretimde **Draft** seçin. **Geometri kurallarını kontrol et**, ardından **YENİ hangar revizyonu oluştur** düğmesini çalıştırın.

`__init__.py` dosyasını Alt+P ile çalıştırmayın. Paket içindeki assets, vendor, modular ve hangar_studio klasörlerini ayırmayın. Normal eklenti kullanımında pip, VTK veya NumPy gerekmez.

Eski bina paneli ve Modüler Mimari paneli ayrıca kalır. Yeni hangar için özellikle **Hangar Studio** panelini kullanın; eski HANGAR düğmesi eski üreticiyi çalıştırır. Önceki nesneler otomatik olarak yeni hangara dönüştürülmez.

## 3. Parametre grupları

### 01 — Aks, gövde, çatı

Gövde genişliği 20–48 m, derinlik 18–60 m, nominal saçak 6–9 m, 4–12 boyuna hücre. Hücre genişliği `derinlik / hücre sayısı` olarak hesaplanır ve 2.8–6 m arasında olmalıdır. Kısıtlar birlikte geçerli olmalıdır; her minimum/maksimum kombinasyonu üretilemez.

Çatı `GABLE` veya `MONITOR` olabilir. Monitor: yükseltilmiş küçük çatı, yan camlar, çerçeveler ve **ana çatıda gerçek boşluk** oluşturur. Altına gizli, kesintisiz opak çatı bırakılmaz. Dökülen doğal ışığın fiziksel miktarı hesaplanmaz.

Çatı panelleri bölmeler halinde üretilir; UV0 uzunluk/yamaç boyunu metre ölçeğinde izler. Aşıklar ana kaplamanın altında yer alır. Gerçek I-kesit geometrisi, bağlantı plakaları ve seçili civatalar görseldir; hesaplanmış taşıyıcı sistem değildir.

### 02 — Cephe hücreleri

Sol/sağ cephe ayrı konfigüre edilir. Boş alan otomatik dizi demektir. Sekiz hücre örneği:

```text
METAL, PERSONNEL, CLERESTORY, CLERESTORY, CLERESTORY, CLERESTORY, CLERESTORY, LOUVER
```

İzinli türler:
- `METAL`: düz metal kabuk ve kaide.
- `CLERESTORY`: yüksek bant pencereli kabuk, gerçek açıklık.
- `LOUVER`: panjurlu bölüm.
- `PERSONNEL`: ayrı hareketli personel kapısı.

Virgülle ayrılan tür sayısı hücre sayısına tam eşit olmalı. Bitişik iki personel sahanlığı bu sürümde desteklenmez. Sahanlık hücreden geniş olduğunda üretim durur; panel veya kapı sessizce esnetilmez.

Arka cephe aynı aile modüllerinden otomatik kurulur; arka personel kapısı kapatılabilir. Bu sürümde arka cephenin her hücresi için ayrı UI düzenleyici yoktur.

### 03 — Ana açıklık ve kapılar

4/6/8 teleskopik kanat; karşılıklı iki yönde açılım; her yanda 2/3/4 ayrı ray düzlemi. Ana açıklık büyüdüğünde kanatların sığacağı yan cepler kontrol edilir. Cebin küçük kalması hatadır.

Ana kapı ile personel kapısı açık oranı bağımsızdır. **Kapı konumlarını uygula** mevcut hangarın kapılarını geometriyi baştan üretmeden taşır. Kapı metadata'sı ve görünür açıklık bilgisi de güncellenir. Kilitli kapı nesnelerinin pozuna zorla müdahale edilmez.

Kapılar kapalıyken küçük bir görsel birleşim boşluğu bırakılır. Sıfır yağmur/sızdırmazlık veya yangına dayanım iddiası yoktur. Fizik tabanlı motor/sensör, sıkışma önleme sistemi veya doğrulanmış mekanik tasarım içermez.

### 04 — Zemin, drenaj ve portlar

Yerel döşeme açıldığında kapalı iç hacim, ön apron, plak derzleri ve isteğe bağlı drenaj üretilir. Drenaj için hem plaklar hem alt yatak gerçekten kesilir. Boya çizgileri kanalı köprülemez. Izgara ve çerçeve ayrı geometridir.

Yerel zemin kapalıysa hiçbir ikinci zemin, sahanlık veya drenaj gövdesi üretilmez. Drenaj konumu `drain_cutout_design` talebi olarak metadata'da kalır; AF01 bunu henüz otomatik uygulamaz.

Yürüyüş yüzeyi `kök Z + base_height` düzeyindedir. Dış apron Z=0 olacaksa ve base_height=.18 ise kökün Z değerini -.18 yapın. Dış yüzey kotunu otomatik tahmin etmeyiz.

Yerel sahanlıklar açıkken PK01/SW01 uyum alanları (`pk01_width`, `pk01_height`, `pk01_role`) eklenir. Kapalıyken yalnız `PEDESTRIAN_OPENING` işaretleri vardır; açıklık işaretçisi hazır kaldırım portu değildir. Otomatik kaldırım/park/terrain bağlantısı bu sürümde yoktur.

### 05 — Ayrıntı ve kimlik

Oluklar, inişler, kelepçeler, kablo tavaları, servis kutuları, askılı lineer armatürler, kimlik panosu ve seçili bağlantılar ayrı seçeneklerdir. Kimlikte ASCII harf, rakam, `_` ve `-` kullanın. Gerçek birlik arması veya kurum logosu dahil değildir.

Ekipmanlar rastgele bütün duvarlara saçılmaz. Servis kutuları uygun opak hücrelere, çaprazlar penceresiz/kapısız hücrelere bağlıdır.

### 06 — PBR yüzey rolleri

Cephe: Light / Olive / Graphite. Çatı: Olive / Graphite / Silver painted. Palette: Coastal / Woodland / Urban. Beton ve metal fiziksel doku kapsamı, normal şiddeti ve açık apron ıslaklığı ayarlanabilir.

Boyalı kaplama dielektrik, açık galvaniz ayrı metal rolüdür. Silver seçeneği açık renkli boya görünümüdür; bir anda ham alüminyum standardına dönüşmez.

**Islaklık:** Açık aprona ayrı roughness/albedo tarifi uygulanır. Kapalı döşeme aynı ayardan etkilenmez. Islaklık mekânsal yağmur simülasyonu değildir; yan sahanlıklar bu alfa içinde kuru döşeme rolünü kullanır. Normal haritaları, roughness ve geniş yüzey tonu ayrı mantıklardır; gerçek damla/birikinti geometrisi yoktur.

Mevcut sekiz aile ve 40 PNG korunur. Hepsi orijinal prosedürel kaynaklardır; yeni tarama indirilmedi. Kaynaklar 1K/2K, GLB önizleme kopyaları 1K'dır. Hero seviyesi dokuları otomatik 8K yapmaz.

Harici PBR örneği:

```text
D:/PBR/
  Concrete/
    Concrete_BaseColor.png
    Concrete_ORM.png
    Concrete_NormalGL.png
    Concrete_NormalDX.png
    Concrete_Height.png
```

Üst klasör `D:/PBR/` seçilir. Sadece değiştirmek istediğiniz aileyi ekleyebilirsiniz. Bir aile klasörü varsa beş haritanın tamamı gereklidir. BaseColor sRGB, diğer veri haritaları doğrusal; ORM R=AO/G=Roughness/B=Metallic. Boyalı kaplamanın metaliklik rolü doku altlığından bağımsızdır. Height kaynak dosyası vardır; otomatik displacement yoktur. Keyfi Blender node düzenlemeleri birebir Unreal'a çevrilmez.

### 07 — Kontrol, JSON ve aktarım

JSON yalnız veri taşır, kod yürütmez; sürüm/alanlar/boyut denetimi yapılır. 256 KiB dosya sınırı vardır. JSON tarifi, çalışma .blend dosyasındaki elle yapılan mesh düzenlemelerinin yedeği değildir.

**Çatı kesit görünümü** yalnız viewport görünürlüğünü değiştirir; önceki gizleme durumu geri yüklenir. Tam model export kapsamı korunur.

**Kamera + ışık düzeni** isteğe bağlıdır: dünya, render, aktif kamera ve gerçek Blender area light nesneleri oluşturur. Önce dosyanızı kaydedin. Bu ışıklar UE'ye otomatik light aktörü olarak çevrilmez.

## 4. Yeniden üretim güvenliği

Her yeni üretim yeni kök ve koleksiyondur. Önceki hangar, AS07, AF01 ve kullanıcı nesneleri silinmez. Aynı cursor konumunda tekrar üretirseniz iki bina üst üste görünür; karşılaştırma için eski koleksiyonu gizleyin veya 3D Cursor'u taşıyın.

Eski MB01 yeniden üret düğmesi yeni Hangar Studio kökünde çalışmaz. Yeni laboratuvar gerçek artımlı/yerinde bina güncellemesi yapmaz; önceki bina düzenlemeleri yeni revizyona otomatik taşınmaz. İlk saf geometri hesabı sırasında Esc hemen kesmeyebilir; nesne üretim adımları arasında iptal işlenir. Üretim sırasında sahne değiştirmeyin.

Bütün binayı kök Empty üzerinden taşıyın/döndürün. Mesh düzeyindeki non-uniform scale, açıklık ve doku hesabının yerine geçmez. Aktarım shear/uygunsuz dönüşümlerde durabilir.

## 5. Unreal Engine 5.8 hedefli aktarım

Mevcut exporter yeni hangarın kaynak tarifini okur. Ayrı FBX assetleri, doku dosyaları, materyal tarifleri, dünya matrisleri, portlar ve kapı hareket metadata'sı çıkarır. **Henüz gerçek Blender FBX exportu veya UE importu burada çalıştırılmadı.**

Export klasörü:

```text
Meshes/*.fbx
Textures/*.png
MB01_scene.json
MB01_Import.py
mb01_coordinates.py
START_HERE_TR.txt
```

İki asimetrik referans model ölçek/yön kontrolü için korunur. Kapılar yerel convex collision; büyük statik kabuklar complex collision yaklaşımını kullanır. Boş hangarı tek dev collision kutusuyla kapatma yaklaşımı yoktur. Tüm geometri birleştirilmiş CAD katısı değildir; montaj temasları bileşen kesişimleri içerebilir.

UE test projesinde Python Editor Script Plugin ve Editor Scripting Utilities etkinleştirilir. Yalnızca **export klasöründeki** `MB01_Import.py` çalıştırılır. `DRY_RUN=True` ilk durumda dosyaları kontrol eder, aktör oluşturmaz. Gerçek import açıkça False yapılınca denenir. Level otomatik kaydedilmez.

Kapı hareket metadata'sı hazır bir runtime Blueprint veya animasyon klibi değildir. Kapılar o anki pozlarında taşınır. Cam için importer içindeki `GLASS_MATERIAL_PATH` ile kendi Unreal materyaliniz kullanılabilir.

UV0 tekrarlı yüzey UV'sidir; unique lightmap atlası değildir. Bu sürüm dinamik aydınlatmayı hedefler. Otomatik Nanite, HISM, LOD, native Water/PCG, fizik simülasyonlu kapı veya standart ışık hesabı yoktur.

## 6. Gerçek native testi çalıştırmak

Geliştirme ZIP'indeki `tools/TEST_HANGAR_WINDOWS.cmd` ayrı Blender sürecinde üç önayarı üretip pose, operator, kesit, kayıt ve FBX export dener. Açık dosyanızı kullanmaz. Çıktı kullanıcı klasöründeki `MB01_Hangar_Diagnostics/<zaman>` altındadır.

Alternatif:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\RUN_HANGAR_NATIVE.ps1 -BlenderExe "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe" -Render
```

Bu komut yalnız başlatılan PowerShell sürecinin yürütme seçeneğini değiştirir; sistem politikası kalıcı değiştirilmez. Render isteğe bağlıdır. Oluşacak gerçek `NATIVE_BLENDER_REPORT.json`, paketteki saf Python raporundan ayrıdır. Başarılı sonuç önceden üretilmiş gibi paketlenmez.

## 7. Kaynaklar, değişiklikler ve kalan kapsam

`docs/STANDARDS_AND_QUALITY_TR.md`: kamuya açık mimari ve motor referansları; uygulanmayan mühendislik kapsamı.
`docs/ARCHITECTURE_AND_COMPONENTS_TR.md`: yeni modüller, veri ve kategori düzeni.
`docs/VISUAL_REVIEW_TR.md`: incelenen görüntüler, düzeltilen sorunlar, devam eden görsel sınırlar.
`reports/VALIDATION_REPORT.json`: gerçekten çalıştırılan testler.
`reports/BASELINE_ALPHA1_DIFF.json`: önceki paket ile dosya farkları.

Kaynak kod MIT; önceki lisans bildirimleri ve AS07 kaynağı korunur. Orijinal prosedürel assetlerin mevcut CC0 bildirimi aynen kalır. Eklediğiniz üçüncü taraf varlıkların hakları ayrıca kontrol edilmelidir. Başka bir sitenin model/texture paketi otomatik yeniden dağıtılmaz.
