# Görsel ve geometrik denetim kaydı — alpha.2 → alpha.3 QA

Tarih: 26 Eylül 2026. Aynı parametreler, aynı kameralar ve aynı bağımsız CPU görüntüleyicisi kullanıldı. BEFORE baseline alpha.2, AFTER düzeltilmiş adaydır. Kaynak modül yolu, kamera, örnek sayısı ve süre her `RENDER_*.json` içinde kayıtlıdır.

## Gerçekte incelenenler

**Dolap:** Önceki renderda iç mekândan bakınca düz arka yüz görülüyordu. Sonraki görünümde kapak ve kulp görülebiliyor. Sayısal kontrol; kapak merkezinin gövdeye göre içeri yönde kalmasını her iki taraf için doğruluyor. İzole incelemede hangarın diğer bileşenleri çıkarıldı; bu görüntü duvara montaj kapasitesini doğrulamaz.

**Arka köşe:** İnce duvarda iki yüzey arasında hatalı kanal ve kenar aralıkları vardı. Yeni görünümde L bitiş profili süreklilik sağlıyor. Ancak bir köşe profili altındaki boşluğu yalnız perspektif renderdan kesin ölçmek mümkün değildir. Bu nedenle actual wall bounds’tan X–Y izdüşümü de üretildi; 16 cm duvarda +60 mm boşluk, 36 cm duvarda -140 mm örtüşme ayrı görülüyor. Yeni adayda ölçülen iki birleşim farkı 0 mm. 22 cm referans örneği de sayısal kontrolde bulunuyor.

**Armatür:** Önce yatay ayakkabı çatı altında 84.375 mm boşluk bırakıyordu. Yeni geometri ayakkabıyı eğimli roof normaline döndürüyor; üst düzlem çatı altına temas ediyor. Görüntüde bu parça daha yüksek ve eğime bağlı; gerçek kapasite/ankraj hesabı yapılmadı.

**Makara:** Baseline doğrulayıcı makaranın ray içine sığmasını kontrol ediyordu ama alt raya temasını sınamıyordu. Gerçek makara z-min ile ray tabanı arasındaki 15 mm boşluk giderildi; fark kayan nokta düzeyinde sıfır. Ayrı yeni ray renderı çekilmedi; bu bulgunun kanıtı vertex ölçümü ve testtir.

**UV:** Daylight/Classic/Compact için 128/64/48 UV üçgeni sıfır alana düşüyordu. Bunun normal haritasındaki nihai görünüşünü bağımsız renderer göstermediği için “renderda düzeldi” denmedi. Kanıt, yüz ve UV koordinatlarından bağımsız alan ölçümüdür. Yeni sonuç üç önayarda da 0.

**Genel görünüm:** Yeni hangarın çatı, üst ışıklık, kapı cepleri ve yan cephe ritmi ayrıca genel kamerada incelendi. Tek bir genel görüntü küçük temas sorunlarının kanıtı olarak kullanılmadı.

## Dosyalar

`BASE01_Before_After.png`: altı gerçek renderın karşılaştırma panosu, yeni açı sayılmaz.  
`BASE01_Joint_Analysis.png`: actual vertex sınırlarından ortak ölçekli teknik çizim; renderer görüntüsü değildir.  
`after_HERO.png`: yeni adayın genel görünümü.  
`BASE01_QA_Hangar.glb`: aynı geometri ve 1K gömülü önizleme dokuları; Blender exportu değildir.

## Sınırlamalar ve açık kontroller

CPU ray-cast albedo, yaklaşık yansıma, güneş gölgesi ve AO gösterir. 8 örnekli görüntülerde özellikle çatı ve dar metal elemanlarda gren/aliasing kalır. Native bevel, normal, kırılma, çok sekmeli GI ve Unreal Lumen/Path Tracer bu görünümlerde yoktur. Hareketli kamera alınmadı. Yerleşimdeki bütün nesnelerin self-intersection taraması yapılmadı.

Bir sonraki görsel kabul; gerçek Blender’da nötr Cycles/EEVEE, ardından UE’de hedef render yoluyla yapılacak. “Kusursuz” etiketi bu statik önizlemelere dayanarak verilmez.
