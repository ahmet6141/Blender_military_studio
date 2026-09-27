# MB01 0.3 — gerçek geometri görsel inceleme kaydı

**26 Eylül 2026.** Altı modül + beş tam hangar önayarı: 11 farklı kaynak görünüm. Kart ve karşılaştırma panoları aynı renderların düzenlenmiş sunumudur; yeni açı olarak sayılmaz.

## İncelenenler

`NEW_MODULES_BOARD.png`: kasetlerin ölçülü yatay ritmi; VISION modülünde alçak geniş açıklık; SHADED üst cam bandında dışa uzanan güneş kırıcı; DUAL_VENT iki ayrı panjur; çift/tek girişte saçak ve kapı görünümü. Modüller gerçek geometri üreticisinden gelir.

`EXP_COASTAL_CARD.png`: yeni panel türlerinin mevcut ışıklıklı çatı ve teleskopik kapıyla aynı yapıda birleşmesi; yan cephe alçak/üst cam bölgesi; sahanlık, drenaj ve apron. Açık cephe presetinde yan panellerin ana duvar tonu birlikte uygulanır, çerçeveler ayrı kalır.

`FIVE_PRESETS_BOARD.png`: 24/28/32/36 m gövde çeşitleri ve uzun 48 m seçenek; 6/8/10 bölme ritmi; eğimli/monitor çatı; opak/camlı mevcut kapı farkı. Kadrajlar otomatik uyarlanır, aynı ölçekte kıyas panosu değildir. Gerçek ölçüler karttadır.

## Görünür sınırlar

Bağımsız CPU ray-cast önizlemesi albedo, yaklaşık specular, gölge ve AO kullanır. Native Blender bevel, tangent normal, kırılma ve çok sekmeli ışık yoktur. Camlar final şeffaflık değerlendirmesi için uygun değildir. Altı örnekte ve tam yapıda panel kenetleri/panjurlar düşük örnek sayısından gren veya aliasing gösterebilir. Bunun model hatası mı AA/örnekleme etkisi mi olduğu hedef motordaki hareketli kamera ile ayrıca ayrılır; burada giderildiği iddia edilmez.

Saçaklı girişlerin koyu gölgesinde küçük kulpların okunurluğu sınırlıdır. Yakın native açı ve kontrollü dolgu ışığı kabul aşamasındadır. Asfalt/beton yüksek frekans ayrıntısı bu görüntüleyicinin tam shader eşdeğeri değildir.

## Geometrik denetimin kapsamı

Açıklık ve UV testleri kaynak vertex/yüz verisine dayanır. Yeni iki delikli panel için merkez varsayımı kaldırıldı; her açıklığın gerçek konumu kullanılır. Kit collision denetimi yalnız merkez noktasına değil nominal açıklık hacmine bakar. LOD bağlantı/pivot/material slot testleri bütün seçilen boyut örneklerinde çalıştırılır.

Tam bina üçgen-BVH çakışma taraması, her bağlantının mekanik uygunluğu, bütün kameralar ve parametre kombinasyonları onaylanmış değildir. Bir modülün ön görünüşü, arka/alt native ışık kontrolü yerine geçmez.

## Provenance

Görüntülerin kaynak ayarları, gerçek kamera, çözünürlük, örnek sayısı ve süreleri `reports/RENDER_RECORDS.json` içindedir. Yapay zekâ görüntü üretimi veya dış fotoğraf arka planı kullanılmadı. Hazır GLB'ler aynı saf geometri çekirdeğinden bağımsız yazıldı; Blender/FBX çıktısı değildir.
