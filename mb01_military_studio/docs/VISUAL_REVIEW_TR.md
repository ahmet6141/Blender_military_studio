# MB01 — Görsel denetim ve düzeltme kaydı

**Kapsam:** Bağımsız kaynak geometri ve CPU ray-cast önizlemeleri. Blender/UE uygulama testi değildir. Denetlenen kareler örnek konfigürasyonları gösterir; bütün ayar uzayını kapsamaz.

## Gerçek inceleme sonucu yapılan düzeltmeler

1. **Hangar çatı taşıyıcıları:** İlk görünümde çatı kaplamasını kesen portal/aşık ayrıntıları fark edildi. Taşıyıcı üst zarfı kaplamanın altına alındı. `test_hangar_roof_envelope` her ilgili vertexi kaplama alt sınırına karşı kontrol eder.
2. **Üst bant pencere çerçeveleri:** Komşu modüllerin ortak dikmelerini iki kez üreten döngü kaldırıldı. Aynı konumdaki çerçeve yüzlerinin çakışması azaltıldı.
3. **Armatür askıları:** İç görünüm denetiminde askısız görünen armatürlere gerçek askı geometrisi ve tavan bağlantı plakaları eklendi. Bu bir elektrik/taşıyıcı imalat hesabı değildir.
4. **Sahanlık ile temel sınırı:** Ön temel taşmasının apronla aynı yüzeyde örtüşmesi giderildi; ön sahanlık ayrı aralıkta sonlanır.
5. **Harici zemin modu:** Yerel zemini kapatırken içeride zemin kat döşemesinin aynı kotta kalması engellendi. Üst kat döşemeleri korunur; dış apron binanın yüzey seviyesine eşleştirilir.
6. **Personel çıkışı:** Karargâh ve birlik binasının arka kapı merkeziyle port merkezi eşleştirildi, yerel zemin açıkken arka sahanlık eklendi.
7. **AS07 tabela seçeneği:** Orijinal kaynağın duvar üretiminden gelen SERVICE/EXIT yazıları, tabela kapalı olsa da kalıyordu. Adaptörün tabela filtresi düzeltildi; asıl AS07 dosyası değişmedi.
8. **Bağımsız görüntüleyici:** İlk VTK PBR önizlemelerinde renk/ince çizgi artefaktları görüldü. Bunlar son teslim görüntüsü olarak kullanılmadı. Son inceleme, aynı geometriyi kullanan ayrı CPU ray-cast aracıyla tekrarlandı. Bu değişiklik yeni/farklı geometri veya yapay zekâ görseli değildir.

## İncelenen 12 bakış

| Aile / bakış | İncelenenler | Kalan sınır |
|---|---|---|
| HQ ön | Kütle, cephe ritmi, giriş, plinth ve çatı | Tam iç plan yok |
| HQ arka | Çatı parapeti, servis kutuları, pencere dizisi ve personel çıkışı | Servis ekipmanı dekoratif |
| HQ giriş | Söve, denizlik, güneşlik, saçak destekleri, kapı görünümü | Cam optiği yaklaşık; Blender renderı bekleniyor |
| UNIT ön | Eğik çatı, giriş ritmi, farklı bina ailesiyle tutarlılık | Fotoğraf taraması kullanılmadı |
| UNIT arka | Çatı/arka cephe birleşimi, pencere ritmi | Tam yağmur/drenaj hesabı yok |
| HANGAR ön | Gerçek giriş boşluğu, dört kapı parçası, kaplama | Runtime kapı sistemi yok |
| HANGAR arka | Küçük kapı, yan açıklıklar ve çatı yüzeyi | Arka küçük kapı sabit |
| HANGAR iç | Portal taşıyıcı, aşık, armatür/askılar, boş iç hacim | Blender bevel ve native ışık kontrolü bekliyor |
| SHELTER ön | AS07 silueti, açık kemer ve kaynak ayrıntıları | Yeni kapalı hangar gibi sunulmaz |
| SHELTER arka | Arka kapı/sahanlık, kaplama, yağmur boruları | Kapı hareketi Blender'da test edilecek |
| RANGE_SET ön | Gölgelik, masalar, bölmeler ve tabelalar | Yalnız kurgusal görsel set |
| RANGE_SET arka | Dekor panoları, gölgelik, sınır parçaları | Balistik veya gerçek atış alanı uygunluğu yok |

## Önizleme nasıl oluşturuldu?

12 kare, kaynak modeli doğrudan üçgenlere çeviren bağımsız CPU aracıyla 8 örnek/piksel kullanılarak oluşturuldu. Albedo dosyaları okunur; yumuşak yönlü gölge, yaklaşık specular ve sınırlı ambient occlusion hesaplanır. Tam global illumination, normal haritalama, kırılma veya Blender modifier değerlendirmesi değildir. Hafif örnekleme gürültüsü görülebilir.

Görseller yalnız kırpma/ölçekleme ve sunum başlıklarıyla düzenlendi. Fotoğraf, image-to-image üretimi veya modelde bulunmayan ince ayrıntı eklenmedi. Render araçları geliştirme paketindedir. Gerçek süreler, çözünürlükler ve üçgen sayıları `INDEPENDENT_RENDERS.json` dosyasındadır.

## Gerçek uygulamada yapılması gereken kalite kabulü

Blender kurulum ve operator smoke testi; Cycles nötr ışıkta materyal/bevel incelemesi; hedef Unreal 5.8'de ölçek, pivot, normal/tangent, cam, shader derlemesi ve collision; kamera hareketinde ince çizgi titreşimi; büyük sahnede bellek ve draw-call ölçümü. Bunların hiçbiri yapılmış gibi işaretlenmedi.
