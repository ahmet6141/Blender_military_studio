# Hangar Studio — görsel inceleme kaydı
**26 Eylül 2026 · 0.2.0-alpha.2**

## Görüntüler nasıl oluşturuldu?

`tools/render_hangars.py`, Blender/Unreal dışındaki bağımsız CPU ray-cast görüntüleyicisini kullanır. Geometri, eklentinin gerçekten oluşturduğu veridir. Albedo, yaklaşık rough-specular, yumuşak güneş gölgesi ve kısa menzilli AO gösterilir. Kamera/ton eşleme render araçlarında kayıtlıdır; çevre fotoğrafı eklenmemiştir.

Native Blender bevel, normal haritası, cam kırılması, çok sekmeli GI veya UE Lumen/Path Tracer davranışı bu görüntülerde yoktur. Camlar yaklaşık gökyüzü yansımasıyla gösterilir; pencere şeffaflığına ilişkin nihai karar bu görüntüden verilemez. İç görünüm iki örnekli düşük maliyetli inceleme olduğundan grenlidir. Bu bir final reklam/CGI kalite render seti değildir.

## İncelenen dokuz görünüm

| Görünüm | Kontrol edilen kısımlar |
|---|---|
| Daylight genel | Çatı/gövde oranı, monitor, ön giriş, kapı cepleri ve modül ritmi |
| Classic genel | Eğimli çatı/mahya, dört kanat, ikinci malzeme yönü |
| Compact genel | Küçük gövde, opak kanatlar, altı boyuna hücre |
| Ön kapalı | Karşılıklı kanatların merkezde birleşmesi ve üst cam bandı |
| Ön tam açık | Kanatların yan ceplere gitmesi; girişte opak tam duvar olmaması |
| Arka çapraz | Arka modüller, panjurlar, kapı/sahanlık ve oluk inişleri |
| İç görünüm | Portal/aşıkların çatı altında kalması, ışıklık, askı ve kablo düzeni |
| Kapı yakın | Ayrı ray düzlemleri, kanat çerçevesi, panel ve cam bandı |
| Drenaj yakın | Slab kesisi, ızgara, kılavuzlar ve kesilen zemin boyası |

Dokuz kaynak görüntü ayrıca `examples/HANGAR_STUDIO_REVIEW_BOARD.png` panosunda bir araya getirildi. Pano yeni bir render açısı sayılmaz. Ana Daylight görüntüsü daha yüksek örnek sayısıyla yeniden alındı; tek açı iki kez sayılmadı.

## Yapılan düzeltmeler

1. **Arka sahanlık açıklığı:** Yan cephedeki .43 m başlangıç ofsetinin arka cepheye aynen uygulanması .41 m boşluk bırakıyordu. Arkada .02 m ofset kullanıldı; sahanlık alt sınırı, arka apronun +.24 m sınırına getirildi. Gerçek geometri koordinatlarıyla regresyon testi eklendi.
2. **Tekrarlanan monitor dikmesi:** Birinci bölmenin başındaki yakın iki dikme kaldırılarak aks başına tek üretim sağlandı. Dikme primitive sayısı ve benzersizliği kontrol edildi.
3. **Kapı metadata sürekliliği:** Pose uygulandığında yalnız nesne konumu değil, kanat açık oranı ve geçiş genişliği kaydı da güncellenecek şekilde düzeltildi. Hazırlanan native smoke bu davranışı ayrıca kontrol edecek; native test çalıştırılmış değildir.
4. **Önizleme zemini:** Bağımsız görüntüleyicinin sonsuz sahne zemini, modellenmiş drenaj çukurunun tabanını kapatabiliyordu. Geçici önizleme düzlemi kanal ayak izinden kesildi. Bu değişiklik asset geometrisi değil yalnız inceleme sahnesidir. Drenaj yakın görüntüsü düzeltilmiş sahneyle alındı.
5. **Kesit önizlemesi:** Çatı kaplaması gizlendiğinde bazı ince çatı detayları havada kalıyordu. İlgili detaylar da viewport kesit grubuna dahil edildi; önceki görünürlük durumunu geri yükleme eklendi. UI tarafındaki bu davranış native deneme bekliyor.

6. **Ray/makara temas denetimi:** İlk makara çapı, C-rayın iç yüksekliğinden büyüktü. Makara ve askı geometrisi değiştirildi; gerçek makara vertexlerinin rayın iç boşluğunda kaldığını kontrol eden test eklendi. Bu, görünür geometri çakışmasını düzeltir; mekanizma kapasitesini doğrulamaz. Son dokuz görünüm ve üç GLB bu düzeltmeden sonra yeniden üretildi.

## Açık görsel kontroller

İnce çatı kenetleri/panjurlar, düşük örnek sayılı görüntülerde aliasing ve gren gösterebilir. Hareketli kamera ve hedef render AA yöntemiyle kontrol edilmelidir. UV/normal eşleşmesi, emissive difüzör parlaklığı, cam, bevel highlight ve boya yüzeyleri native Blender/UE incelemesi bekler.

Bütün muhtemel parametre birleşimlerinde görsel kusursuzluk iddia edilmez. 24 ek kombinasyonun testleri geometri/veri kontrolleridir; 24'ünün her biri render edilmedi. Görünür montaj temasları, Boolean birleşimi veya imalat onayı değildir.
