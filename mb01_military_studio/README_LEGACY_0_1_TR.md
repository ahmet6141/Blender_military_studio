# MB / 01 — MILITARY BUILDING STUDIO
## Blender mimari üreticisi · AS07 kaynak entegrasyonu · Unreal editör aktarımı

**Sürüm:** 0.1.0 — 26 Eylül 2026
**Durum:** Geliştirme sürümü. Parametrik geometri, yerel PBR kaynakları, Blender eklenti arayüzü ve UE importer kaynak kodu içerir.

> Geometri testleri ve bağımsız görsel inceleme gerçekten yapıldı. Bu üretim ortamında Blender/bpy ve Unreal çalıştırılamadı. Blender 4.5 kurulum/API/export ve UE5.8 importer/shader/collision işlemleri uygulama içinde doğrulanmadı. “Hatasız”, sertifikalı veya üretim ortamında denenmiş ticari ürün iddiası yoktur. Başlangıçta boş bir dosya ve test projesi kullanın.

## 1. Teslim edilenler

Kurulum ZIP'i `mb01_military_studio` klasörünü, Python kaynaklarını ve sekiz PBR doku ailesini içerir. İnternet veya pip kurulumu gerektiren bir eklenti değildir. Harici doku indirmesi otomatik yapılmaz.

Geliştirme paketi ayrıca beş gerçek GLB önizlemesi, 12 bağımsız render, birim testleri, raporlar, modelleri/önizlemeleri tekrar üretmek için araçlar ve kullanıcı bilgisayarında çalıştırılabilecek Blender tanılama scriptini içerir. Bu araçların NumPy/Pillow/VTK/Numba gibi bağımlılıkları vardır; **normal eklenti kullanımı için bunlar kurulmaz.**

**GLB'ler Blender'dan export edilmiş değildir.** Aynı saf geometri çekirdeğinden bağımsız derleyiciyle üretildi. Gömülü dokular 1K önizleme kopyalarıdır. Blender bevel sonucu, tam shader ağı ve native ışık sistemi bu dosyaların eşdeğeri değildir.

## 2. Beş yapı ailesi

| Aile | İlk değerler | İçerik ve sınır |
|---|---|---|
| Karargâh (`HQ`) | 35,2 × 20,4 m, 3 kat | Pencere boşluklu cephe, söve/denizlik, güneşlik, camlı giriş, saçak, parapet, çatı servis kutuları ve mobilyalar. Tam iç mekân/merdiven planı yok. |
| Birlik binası (`UNIT`) | 30,8 × 14,4 m, 2 kat | Aynı mimari aileden daha sade bina; eğimli veya parapetli çatı. Dış kabuk ve giriş hacmi; yatakhane/oda donatısı yok. |
| Bakım hangarı (`HANGAR`) | 28 × 36 m, 7,2 m saçak | I-kesit portal taşıyıcılar, çatı aşıkları, üst bant pencereleri, gerçek ön açıklık, iki rayda dört sürgülü kapı kanadı, iç armatürler ve askıları. Arka personel kapısı bu sürümde sabit. |
| Açık shelter (`SHELTER`) | 24 × 32 m, 4,8 m saçak | Yüklenen AS07 kaynağı; kemerli çatı, panjurlar, bağlantılar, tesisat ve menteşeli arka kapı korunur. Eski scriptin sahne/kamera oluşturma fonksiyonu çağrılmaz. Açıklık nominal çerçeve ölçüsüdür. |
| Atış alanı dekoru (`RANGE_SET`) | Sanatsal set ölçüleri | Gölgelik, bölümlere ayrılmış masalar, numaralar, geometrik hedef panosu dekorları ve hafif sınır elemanları. Film/oyun görsel setidir; silah, balistik hesap, koruyucu malzeme veya gerçek kullanım yeterliliği tasarımı değildir. |

Bütün yapı boyutları görselleştirme parametresidir; statik hesap, gerçek inşaat, erişilebilirlik veya tesis uygunluğu göstermez.

## 3. Blender 4.5'te kurulum

1. Mevcut dosyanızı kaydedin ve yeni bir dosya açın.
2. `Edit → Preferences → Add-ons` bölümünde üst sağ menüden **Install from Disk** seçin.
3. **MB01_Blender_Addon_0_1_0.zip** dosyasını açmadan seçin. Listede **MB01 | Military Building Studio** eklentisini etkinleştirin.
4. 3D Viewport'ta `N → MB01` panelini açın. `Object Mode` ve `Scene → Units → Unit Scale = 1.0` kullanın.
5. Yapı ailesini seçin ve mutlaka **Seçilen aile ölçülerini yükle** düğmesine basın. Aile menüsünü değiştirmek tek başına önceki ölçüleri sıfırlamaz.
6. İlk denemede **Draft** seçin. **3D Cursor konumunda YENİ yapı** düğmesine basın.
7. Geometriyi kontrol edin; ardından **Working** veya **Hero** seçip aktif yapıyı yeniden üretin.

Bu, klasik/legacy ZIP eklentisidir; `__init__.py` dosyasını Text Editor'e yapıştırıp Alt+P ile çalıştırmayın. Tek `.py` dosyasını assets klasöründen ayırmayın. Geliştirme ZIP'i kurulum ZIP'i değildir.

### Ayarlar

Genişlik, derinlik, kat sayısı, kat/saçak yüksekliği, bölme sayısı, uygun ailelerde çatı tipi, üç detay profili, üç renk paleti, seed, tabela, hizmet ekipmanları, güneşlik, zemin ve kapı açıklığı bulunur.

`Seed` pencere perde/recess varyasyonları için kullanılır; her ayarın veya yapı ailesinin tamamen farklı şekle dönüşmesi anlamına gelmez. `Yüzey pürüzlülük varyasyonu` shader roughness çarpanıdır: ayrı pas, çatlak, ıslaklık veya kir simülasyonu değildir.

**Draft** bevel ve bazı küçük ayrıntıları azaltır. **Working** ana ayrıntı ve iki segment bevel; **Hero** üç segment bevel ve AS07 için daha yoğun kemer geometrisi kullanır. Bunlar otomatik UE LOD'ları veya fotogerçekçilik düğmesi değildir.

## 4. Düzenleme ve yeniden üretim

Her yeni yapı ayrı kök Empty ve koleksiyon alır. Yeni yapı 3D Cursor konumuna ve paneldeki yöne yerleşir. Bütün binayı kök Empty üzerinden taşıyın/döndürün. Yeniden üretim kökün dünya dönüşümünü korumayı hedefler.

**Yeniden üretim, kilitlenmemiş üretilmiş parçaları değiştirir.** Özel düzenlediğiniz MB01 parçalarını seçip **Seçilenleri yeniden üretimde koru** düğmesine basın. Kilitli parçalar korunur; MB01 sahiplik etiketleri durduğu için kendi projesinin exportunda kalırlar.

MB01 köküne eklenmiş, MB01'e ait olmayan kullanıcı nesneleri yeniden üretimde korunur; otomatik export kapsamına alınmaz. Kilitli nesne, kullanıcı nesnesi veya mevcut materyal başka projelerin genel temizliğiyle silinmez. Yine de staging ve Undo bir yedek sistemi değildir: önemli dosyanızı yedekleyin.

Üretim parça adımlarında iptal edilebilir; ilk saf geometri hesaplaması içinde Esc anında çalışmayabilir. Aynı anda ikinci üretim başlatmayın ve işlem sırasında sahne değiştirmeyin. Commit aşamasında hata olursa korunan nesneleri silmek yerine staging/eski sonuçlar bırakılabilir; hata raporunu inceleyin.

Kapı açıklığını değiştirmek için **Kapı açıklığını uygula** düğmesi vardır. Kapalı hangarın dört sürgülü kanadı ve AS07'nin arka personel kapısı hareket eder. HQ/unit giriş camı ve hangarın arka küçük kapısı bu araçla açılmaz. UE'de bunlar yerleşim anındaki konumda gelir; hazır runtime Blueprint/animasyon klibi yoktur.

## 5. AF01 / SW01 / PK01 bağlantı sözleşmesi

**Mevcut eklentilerin kodu ve nesneleri değiştirilmez.** MB01 ayrı isim alanı/sahiplik kimliği kullanır.

| Veri | Uygulama |
|---|---|
| Birim | Sayısal metre, Unit Scale 1.0 |
| Yerel eksen | +X binanın içine, +Y sola, +Z yukarı |
| Yüzey UV | `UV0_Tile`; metre bazlı tekrarlı koordinatlar |
| Vertex renk | `SW01_Tint`; varsayılan nötr beyaz; başka maske için ezilmez |
| Personel portu | Empty, `pk01_width`, `pk01_height`, `pk01_role='OUT'` |
| Port tabanı | Yaya portu kaynak taban düzleminde; yürüyüş yüzeyi port Z + `height` |
| Uçak portu | Ayrı HANGAR rolü; yaya portuna dönüşmez |
| Yerel zemin | Kapatılabilir; dış apronla üst üste zemin üretmemek için |

PK01'in mevcut port okuyucusundaki veri alanları esas alınmıştır. PK01 arayüzünde canlı bağlama işlemi burada çalıştırılmadı. MB01 kaldırım üretmez, AF01 apronunu otomatik kesmez ve PK01 peyzaj maskelerini güncellemez. Unreal'da otomatik soket oluşturma/live graph binding yoktur; portlar JSON'da saklanır.

**Zemin seviyesini eşleştirin:** Binanın yürüyüş/iç zemin yüzeyi, kök konumunun Z değerine `base_height` eklenerek oluşur. `Yerel zemin` kapalıysa dış apron aynı yüzey seviyesinde olmalıdır. Örneğin dış yüzey Z=0 ve base_height=0,18 ise bina kökü Z=-0,18 konumuna alınır. Farklı bir yaya kotu gerekiyorsa kendi kaldırım/sahanlık düzeninizi ayrıca ayarlayın. Bu bir otomatik arazi oturtma aracı değildir.

SW01 varsayılan genişliği 2,4 m; MB01 varsayılanı 3,2 m olabilir. Uç genişliği ve yükseklik eşleşmeden PK01 köprü aracı bağlantıyı reddedebilir. Ortak UV/metadata korunur ancak **MB01 materyalleri ayrı `M_MB01_...` tarifleridir**; eski SW01/AF01 materyallerini sessizce değiştirmez veya birebir shader eşdeğerliği iddia etmez.

## 6. PBR kaynakları

**Sekiz aile, her ailede beş dosya:** Concrete, Asphalt, CoatedSteel, Galvanized, Plaster, Stone, Timber, Membrane. Concrete/Asphalt/Plaster 2K; diğerleri 1K. Kaynak sayacı ve SHA256 kayıtları assets/manifest.json içindedir.

Tüm setler **prosedüreldir**. İlk dört aile önceki AF01 kaynaklarından aynen kopyalandı; dört yeni aile bu sürüm için üretildi. Fotogrametri taraması, ücretli premium paket veya yeni indirilmiş Poly Haven malzemesi değildir. Harici indirme girişimi ağ erişimi nedeniyle sonuçlanmadı; lisansı doğrulanmamış dış doku paketlenmedi.

- BaseColor: sRGB.
- ORM: doğrusal; R=AO, G=Roughness, B=Metallic.
- NormalGL: Blender yönü; NormalDX: UE yönü için yeşil kanal dönüşümü.
- Height: 16-bit kaynak; varsayılan shader'da displacement bağlı değildir.

Boyalı metal dielectric olarak, galvaniz ayrı metal yüzey olarak ayarlandı. Renkler sanatsal lineer tints'tir; ölçülmüş malzeme verisi değildir. Harita çözünürlüğü tek başına final görünüm kalitesi veya belli FPS sağlamaz.

### Kendi taranmış PBR setlerini kullanma

`Harici PBR üst klasörü` şu üst klasörü gösterir:

```text
D:/My_PBR/
  Concrete/
    Concrete_BaseColor.png
    Concrete_ORM.png
    Concrete_NormalGL.png
    Concrete_NormalDX.png
    Concrete_Height.png
```

Yalnız değiştirmek istediğiniz aileyi koyabilirsiniz; hiç bulunmayan aileler paket kaynağında kalır. Ancak bir aile klasörü mevcutsa beş haritanın tamamı gerekir; kısmi setler sessizce karıştırılmaz. Var olmayan üst klasör hata verir. Dış modellerin/dokuların lisansı ayrıca size aittir.

Özel Blender node değişiklikleri otomatik Unreal shader çevirisi değildir. Export ortak tarifleri kullanır. Kendi Unreal cam materyalinizi `GLASS_MATERIAL_PATH` alanından atayın; böylece mevcut materyal düzenlenmez.

## 7. Görsel denetim

Beş ailenin ön/arka görünümleri, HQ giriş yakın planı ve hangar içi olmak üzere **12 açı** üretildi. Bunlar aynı geometriyle çalışan bağımsız CPU ray-cast görüntüleyicisinden alındı; Blender/Cycles/UE renderı değildir. Önizlemede yumuşak gölge, albedo, yaklaşık specular ve ambient occlusion kullanılır. Tam node ağı, Blender bevel, normal haritalama, kırılma veya çok sekmeli GI gösterilmez.

`docs/VISUAL_REVIEW_TR.md`, neyin fark edildiğini, neyin düzeltildiğini ve hangi kontrollerin uygulamada beklediğini açıklar. Kontrol edilen bakışlarda bir sorun görünmemesi, bütün parametre kombinasyonlarının veya final film çekiminin onaylandığı anlamına gelmez.

## 8. Unreal Engine 5.8 hedefli aktarım

Önce `.blend` dosyanızı kaydedin veya mutlak export klasörü seçin. `FBX + PBR + UE yerleşimini export et` düğmesi, her denemede ayrı zaman/kimlik klasörü üretir. Kaynak modeldeki modifier'ları uygulamak yerine export kopyaları değerlendirilip üçgenlenir.

```text
MB01_Building_<tarih>_<kimlik>/
  Meshes/*.fbx
  Textures/*.png
  MB01_scene.json
  MB01_Import.py
  mb01_coordinates.py
  START_HERE_TR.txt
```

Tek render asseti başına ayrı FBX hedeflenir. Hareketli kapılara kapı-yerel convex `UCX_...` gövde yazılır. Büyük mimari kabuklarda static complex-as-simple collision hedeflenir; bütün hangarı kapatan tek collision kutusu kullanılmaz. Dekorasyon/camda collision kapalıdır. Bu politika fizik simülasyonlu dinamik binalar için değildir.

**Hazır FBX/BLEND dosyası bu teslimde yoktur; Blender işlemi bunları üretir.** Export burada çalıştırılmadı.

UE test projesinde Python Editor Script Plugin ve Editor Scripting Utilities etkinleştirilip editör yeniden başlatılır. `File → Execute Python Script` ile **export klasöründeki** MB01_Import.py seçilir. Eklentinin kaynak klasöründeki kopyayı çalıştırmayın: henüz scene JSON'u yoktur.

`DRY_RUN=True` varsayılanı dosya yollarını ve mesh hash'lerini kontrol eder; asset/aktör oluşturmaz. İnceledikten sonra `False` yapın. İçerik varsayılanı `/Game/MB01_Architecture01`dir. Importer asimetrik iki referans FBX ile ölçek/pivot/XY yönünü ölçüp sonra yerleşim matrislerini dönüştürür.

Yeni materyal/geometri değişikliği mevcut içerikten farklıysa yeni CONTENT_ROOT kullanın veya bilinçli `REIMPORT_OWN_ASSETS=True` seçin. Sahnenin aynı proje kimliği zaten varsa, `REPLACE_SAME_SCENE=True` açıkça seçilmeden eski aktörler korunur. Bu seçenek açıkken **önceki üretilmiş MB01 aktörleri değiştirilir; üzerlerindeki elle yapılan düzenlemeler korunmaz**. Unowned assetler otomatik ezilmez.

Level otomatik kaydedilmez. Importer hata verirse işlem tamamlanmış sayılmaz; Output Log ve traceback'i saklayın. `MB01_last_unreal_run.json` ancak gerçek başarılı UE çalıştırmasında oluşur; pakete sahte UE raporu konulmadı.

**UV0 tekrarlıdır; unique lightmap UV değildir.** Bu sürüm dinamik aydınlatmayı hedefler. Otomatik LOD, HISM/Foliage, Nanite, lightmap unwrap, gece ışık aktörleri veya runtime kapı animasyonu oluşturmaz. Shader camı basit önizleme fallback'idir; Blender camının birebir çevrildiği anlamına gelmez.

## 9. Kullanıcı bilgisayarında tanılama

Geliştirme paketindeki `tools/TEST_BLENDER_WINDOWS.cmd`, ayrı `--background --factory-startup` Blender sürecinde beş yapı üretimi, kayıt, kilitli nesne koruma ve tek FBX export dener. Sonuç ev klasöründeki `MB01_Diagnostics/<zaman_kimlik>` altına yazılır. Kullanıcının açık sahnesi üzerinde çalışmaz.

Script hazırlandı fakat burada çalıştırılmadı. Test başlatıldığında oluşturacağı rapor ile teslimdeki saf Python raporu farklıdır. Varsayılan tanılama render almaz; isteğe bağlı komut:

```text
blender --background --factory-startup --python-exit-code 1 --python tools/BLENDER_SMOKE.py -- --export --render
```

## 10. Bilinen sınırlar ve hata yakalama

Blender 4.5 hedefi vardır; 5.x için uyumluluk garantisi yok. Unreal 5.8'in FBX/Interchange seçenekleri ve Python property adları gerçek uygulamada doğrulanmalıdır. Windows/Türkçe dosya yolu davranışı kullanıcı tanılamasıyla ayrıca ölçülmelidir.

“Unknown building family / roof” durumunda yeni aileyi seçtikten sonra preset düğmesine basın. “Missing PBR” için ZIP içindeki assets klasörünü ayırmayın. “Unit Scale” hatasında binayı sessizce küçültmek yerine sahnenin birimini kontrol edin. Hatalar `MB01_Last_Error` adlı Text datablock ve konsola yazılır.

Görsel kabuklar bir boolean birleşimi, 3D baskıya hazır tek katı veya BIM belgesi değildir. Montaj parçaları fiziksel temas amacıyla kesişebilir; kaynak toleranslar görsel üreticiye aittir. Sıfır açık kenar testi yalnız kapanması gereken parçalara uygulanır.

## 11. Kaynaklar ve lisans

Yeni kod MIT; orijinal AS07 MIT bildirimi korunmuştur. Orijinal prosedürel doku/üretilmiş model kaynakları için CC0 bildirimi eklenmiştir. Font dosyası, gerçek birlik arması veya lisansı belirsiz hazır model dağıtılmadı.

AS07 kaynak hash'i `reports/SOURCE_MANIFEST.json`; testler `reports/VALIDATION_REPORT.json`; gerçek render kayıtları `reports/INDEPENDENT_RENDERS.json`.

Dış teknik referanslar (26 Eylül 2026 erişimi):
- Epic — FBX Static Mesh Pipeline: https://dev.epicgames.com/documentation/en-us/unreal-engine/fbx-static-mesh-pipeline-in-unreal-engine
- Epic — Scripting the Unreal Editor Using Python: https://dev.epicgames.com/documentation/en-us/unreal-engine/scripting-the-unreal-editor-using-python

Blender kılavuzuna bu ortamdan erişim sonuçlanmadı; kurulum menüsü ve API davranışı uygulama içinde doğrulanmış sayılmadı.
