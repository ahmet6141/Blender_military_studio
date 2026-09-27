# Standart referansları ve kalite sözleşmesi
**Kontrol tarihi: 26 Eylül 2026.** Bu belge uygunluk sertifikası veya imalat rehberi değildir.

## 1. Birbirine karıştırılmayan üç durum

- **Uygulanmış geometri kuralı:** Kodun ölçü/bağlantı/veri tutarlılığı denetimi; örneğin kapı cebinin kanadı alması.
- **Mimari referans:** Kamuya açık kaynaklardan tasarım dili için okunan genel yaklaşım; örneğin cephe, çatı ve bitişlerin birlikte ele alınması.
- **Uygulanmamış mühendislik/kurum uygunluğu:** Taşıyıcı, yangın, iklim performansı, koruyucu nitelik, erişilebilirlik, gerçek uçak emniyeti ve askerî sertifikasyon.

UI ve metadata yalnız CGI durumunu bildirir. Parametrik profil kalınlıkları hesaplanmış çelik kesiti değildir. Açıklık kontrolü sertifikalı uçak geçiş hesabı değildir. Drenaj geometrisi hidrolik kapasite hesabı değildir.

## 2. Gerçekten açılıp okunan dış kaynaklar

### AFCFS — Facility Quality
https://afcfs.wbdg.org/facility-quality/index.html

Kaynak, kaliteyi tesisin işlevine ve grubuna göre ele alır; dayanıklı ve düşük bakım gerektiren malzeme/bitişleri vurgular. Bu projede bu yaklaşım, sade ve tutarlı kaplama, birleşim ve servis düzeni için sanat yönü referansıdır. Kullanılan dijital malzemenin fiziksel dayanımı ölçülmüş değildir. Kaynaktaki kurum şartlarının tamamı uygulanmaz.

### AFCFS — Facilities Exteriors
https://afcfs.wbdg.org/facilities-exteriors/index.html

Kaynak dış kabuk, giriş, duvar, kapı/pencere ve çatı sistemlerini ayrı ama birlikte ele alınan başlıklar olarak düzenler; iklime duyarlı tasarım yaklaşımından söz eder. Hangar Studio'da kategorize kabuk ve gölgelik/ışıklık görünümü tasarlarken referans alınmıştır. Isıl, enerji veya yerel iklim hesabı yapılmamıştır. ABD kurumsal dokümanını Türkiye veya NATO uygunluğu olarak sunmuyoruz.

### Epic — Physically Based Materials
https://dev.epicgames.com/documentation/en-us/unreal-engine/physically-based-materials-in-unreal-engine

Boya kaplı yüzey ile çıplak metal için farklı metaliklik davranışı temel alınır. Yeni tarifte boya dielektrik, galvaniz metal olarak ayrılır. Sanatçı renkleri ölçülmüş yansıtma değerleri değildir. Roughness ve tile ölçeğinin doğru taşınması native hedefte ayrıca kontrol edilecektir.

### Epic — FBX Static Mesh Pipeline
https://dev.epicgames.com/documentation/en-us/unreal-engine/fbx-static-mesh-pipeline-in-unreal-engine

Referans; pivot, üçgenleme, UV, collision adlandırması ve aynı dosyada çoklu mesh/collision sınırlamalarını açıklar. Export tekil asset ve ilişkili collision yaklaşımını kullanır. Doğru dosya biçimini kullanmak Blender/UE uyumunun çalıştırılarak kanıtı değildir.

## 3. Doğrulanamayan veya bu sürümde uygulanmayan kapsam

UFC 4-211-01'in tam güncel metni bu çalışma sırasında doğrulanamadı; PDF alma girişimi tamamlanmadı. Bu nedenle madde/table numaraları, ölçü tabloları veya "UFC uyumlu hangar" etiketi eklenmedi. Kaynağa bağlantı bulunması tüm standardın okunmuş ya da uygulanmış olduğu anlamına gelmez.

Gerçek kullanıma yönelik askerî yapı, yangın, iş güvenliği, kaçış, kar/rüzgâr yükleri, zemin, drenaj, havalandırma ve enerji uygunluğu uzman proje süreçleridir; bu dijital çevre üreticisinin sonucundan çıkarılamaz.

## 4. Bu sürümde çalıştırılan yazılım kalite kapıları

- Strict sayı/tür, sonlu koordinat ve birim kontrolü.
- Aileye bağlı cephe hücresi; hücre sayısı/uzunluğu eşleşmesi.
- Ana kapıda 4/6/8 kanat, cebin yetmesi ve tam açık konumda gerçek vertexlerin açıklık dışında kalması.
- Ray düzlemlerinin ayrılığı ve aynı düzlemde karşılıklı kanatların örneklenen pozlarda çakışmaması.
- Çatı altında kalan aşık vertexleri, gerçek monitor boşluğu, çatı UV fazı.
- Hem slab hem alt yatakta kesilen drenaj; çizgilerin kanalı köprülememesi.
- Sahanlık/apron temas kotu ve personel portu yüksekliği.
- Özgün AS07 ve önceki modüler geometri kaynaklarının dosya kimliği.
- Çalıştırılmış Python testi ile hazırlanmış fakat çalıştırılmamış Blender/UE araçlarının ayrı raporlanması.

Bir kontrol yalnız kendi kapsamını kanıtlar. Örneğin kapı hareket aralığı testi rüzgâr altında kapının güvenli olduğunu, manifold testi binanın üretilebilir olduğunu göstermez.
