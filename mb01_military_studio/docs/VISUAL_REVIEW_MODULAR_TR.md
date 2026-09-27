# MB01 alpha.1 — Görsel inceleme kaydı

## İncelenen malzeme

14 yeni modülün kaynak geometrisi bağımsız CPU ray-cast görüntüleyicisinde ayrı ayrı görüntülendi; bunlardan bir katalog panosu oluşturuldu. HQ ve hangar cephe sıraları ayrıca CPU görüntüleyicide değerlendirildi. HQ/UNIT/HANGAR için önden, arkadan ve çapraz bakışlı VTK önizlemeleri de dosyalarda vardır.

**Görüntüleyiciler Blender/Cycles veya Unreal değildir.** CPU yolu yüzey albedosu, yaklaşık specular, yumuşak gölge ve sınırlı AO kullanır. Native bevel, shader ağı, normal haritası, cam kırılması, katmanlı boya veya çok sekmeli GI onaylanmış sayılmaz.

## Gerçek gözlemler ve işlemler

**Katalogdaki ilk 14 parça:** duvar, pencere/dar pencere/güneşlik, panjur ve kapı açıklıkları ayrışıyor; karargâh girişi ve hangar yüksek panel ailesi aynı nominal ölçekte tek bir düz panel gibi sunulmuyor. Girişlerde kaide bandı kapı boşluğundan kesiliyor. Karargâh ana girişinde saçak ve askı/braket elemanları var.

**Zemin sunumu:** İlk VTK denemesi, eski tam bina önizleme kodundan kalan -0,34 m sahne düzlemini kullanıyordu. Modüllerin tabanı 0 m olduğundan bu, parça sanki yerden kopukmuş gibi gösteriyordu. Önizleme düzlemi -0,012 m’ye alındı; modelin gerçek vertexleri değiştirilmedi. CPU görüntüleyicinin düzlemi zaten -0,015 m idi.

**İnce çizgiler:** Uzak VTK görüntülerinde başlık gölge çizgisi ve metal panel kenetlerinde aliasing görüldü. CPU örneklemesiyle ikinci görünümler alındı. Bu, bütün temporal titreşim problemlerinin çözüldüğü anlamına gelmez; native hareketli kamera testinde değerlendirilmelidir. Uzak LOD’da bu ayrıntıların sadeleştirilmesi ileriki aşamadadır.

**Cam:** CPU ve VTK kaynak görüntülerindeki cam, Blender/UE’de nihai cam davranışı için referans değildir. Nötr native ışıkta transmission, arka mekân görünümü ve roughness kontrolü açık kabul maddesidir.

**Sıra görünümü:** HQ örneğinde yedi hücre giriş etrafında simetriktir. Hangar örneğinde metal/pencere/personel giriş/panjur modülleri bir arada çalışır. Sıranın arkasının açık olması hata gizleme değil, alpha.1’in cephe laboratuvarı kapsamıdır. Çatı ve yan duvar üretildiği iddia edilmiyor.

**Kod gözden geçirmesi:** Eski panelin kök nesne seçimi, yeni modüler kökü normal bina gibi yeniden üretmeye çalışmaması için ayrıca sınırlandırıldı. Bu davranış kaynak düzeyinde yazıldı; native seçim/panel testi smoke listesinde bekliyor.

## Görsel onay sayılmayan alanlar

Bütün ölçü kombinasyonları, gerçek Windows kurulumu, materyalin yerelde yüklenmesi, FBX sonucu, UE collision ve shader, Lumen/Path Tracer sonucu, kamera hareketindeki titreşim, gerçek yapı standartları. Bunlar hakkında başarı raporu üretilmedi.

## Sonraki zorunlu çekimler

Native Blender’da standart/dar pencere ve ana girişe yakın üç açı; kapılar kapalı/açık iki durum; metal panjurda yatay kamera kayması; beyaz/albedo kartıyla doku ölçeği; Unreal’da aynı görüşlerin karşılığı. Testlerde motor, çözünürlük, örnekleme, pozlama, donanım ve kullanılan texture kaynağı kaydedilecek.
