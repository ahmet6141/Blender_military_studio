# Kabul planı — çalıştırılmış rapordan ayrı

Bu dosya gelecek denetimleri tanımlar. `reports/VALIDATION_REPORT.json` yalnızca bu oturumda çalıştırılan kontrollerin sonuçlarını taşır.

| Kapı | Senaryo | Beklenen davranış | alpha.1 durumu |
|---|---|---|---|
| Veri | Tanımsız modül/şema/alan | Açık hata; Python çalıştırma yok | Python testi geçti |
| Veri | Yinelenen hücre kimliği | Kaydetmeden/üretmeden reddet | Python testi geçti |
| Geometri | Min/default/max modül boyutları | Geçerli yüzler, UV ve malzemeler | Seçili 42 kombinasyon geçti |
| Geometri | NaN/sonsuz/boolean ölçü | Reddet | Python testi geçti |
| Yerleşim | Hedef genişlik tutmuyor | Kapı/pencereyi scale etme; hata ver | Python testi geçti |
| Yerleşim | Hücre sıra değişikliği | Kimlik/metadata varyasyonu sabit | Python testi geçti |
| Açıklık | Pencere/kapı merkezi | Arkada gizli duvar gövdesi yok | Python testi geçti |
| Port | Kapı açıklığı → kaldırım | Sahanlık gerekliliği açık | Metadata testi geçti; köprü yok |
| Native | Temiz 4.5 kurulum | Tek paket, iki panel, hatasız register | Bekliyor |
| Native | Family/category değişimi | Uygun seçenekler, anlaşılır boş kategori | Bekliyor |
| Native | JSON aç/kaydet | Snapshot geri yüklenir, sahne değişmez | UI testi bekliyor |
| Native | Kapı açılması | Doğru menteşe, kasa sabit | Bekliyor |
| Native | Eski bina seçimi | Yeni modül paneli eskisini dönüştürmez | Bekliyor |
| Native | Yeni kök eski panelde | Yanlış türde yeniden üretim engellenir | Bekliyor |
| Native | Eksik PBR | Eski sahne korunur, açık mesaj | Bekliyor |
| Native | Kayıt/yeniden açma | Katalog/hücre snapshot’ı kaybolmaz | Bekliyor |
| Native | FBX export | Değerlendirilmiş kopya; source mesh korunur | Bekliyor |
| UE | Asimetrik kalibrasyon | Ölçek, yön, pivot ölçümü doğru | Bekliyor |
| UE | Mesh/materyal | İçe aktarım, slot, normal yönü doğru | Bekliyor |
| UE | Kapı collision | Açıklığı kapatan toplu kutu yok | Bekliyor |
| UE | Tekrar import | İlgisiz varlıklar değişmez | Bekliyor |
| Görsel | Nötr gün ışığı | Bozuk normal ve dikiş görünmüyor | Bağımsız preview var; native bekliyor |
| Görsel | Hareketli kamera | İnce çizgi titreşimi denetlenmiş | Planlandı |
| Entegrasyon | Köşe/döşeme/parapet | Tek geometri sahibi ve düzgün bitiş | Planlandı |
| Entegrasyon | SW01/PK01/AF01 | Tip, taban ve yüzey seviyesi eşleşir | Planlandı |
| Performans | Kalabalık yerleşke | Donanım/sürümle ölçülmüş kayıt | Planlandı |

Başarısız test “bekliyor” olarak örtülmez; gerçekten çalıştırılırsa FAIL ve hata kaydı tutulur. Uygulama kurulamadığı için hiç çalıştırılmayan test NOT_RUN olmalıdır. Birim test sayısı, bu tablodaki plan maddeleri eklenerek büyütülmez.
