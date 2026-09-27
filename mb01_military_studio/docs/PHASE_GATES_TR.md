# Aşamalar ve kabul kapıları

11 aşama, 44 iş paketi. Bunlar çalıştırılmış test sayısı değildir.

`DONE`: tasarım/veri işi tamamlandı. `CORE_PASS_NATIVE_PENDING`: kaynak ve Python testi var, motor testi yok. `PENDING`: hemen sonraki doğrulama. `PLANNED`: geliştirme yapılmadı.

## P0 — Kaynak ve sözleşme

Durum: **DONE**. Bağımlılık: Yok.

| İş | Teslim ve kabul |
|---|---|
| MB2-001 — Kaynak hash ve lisans envanteri | BASELINE_DIFF ve AS07 hash |
| MB2-002 — Kapsam/standart sınırı | Kaynaklı kurallar ile CGI profilinin ayrımı |
| MB2-003 — Modül ve hücre şeması | Kimlik, aile, kategori ve strict JSON |
| MB2-004 — Kategorize katalog | 14 hazır/42 planlanmış kaydın ayrılması |

## P1 — İlk modüler cephe

Durum: **CORE_PASS_NATIVE_PENDING**. Bağımlılık: P0.

| İş | Teslim ve kabul |
|---|---|
| MB2-005 — 14 sınırlı modül üreticisi | Gerçek boşluk, pivot, metre tabanlı UV |
| MB2-006 — Düz cephe sırası ve aile filtreleri | 1–32 hücre, hedef genişlik ve sabit kimlik |
| MB2-007 — Malzeme rolleri ve eski PBR okuyucu | Duvar/çerçeve/kaide, palet, eksik set hatası |
| MB2-008 — Blender paneli ve JSON akışı | Kaynak kod var; native düğme akışı ayrıca test edilecek |
| MB2-009 — Eski exporter adaptörü | Modüler snapshot, özel kökü eski üreticiden ayırma |
| MB2-010 — Saf Python regresyon ve görsel denetim | Birim test raporu ve gerçek geometri önizlemeleri |

## P1-N — Native doğrulama

Durum: **PENDING**. Bağımlılık: P1.

| İş | Teslim ve kabul |
|---|---|
| MB2-011 — Temiz Blender 4.5 kurulumu | Register/unregister ve gerçek panel elle testi |
| MB2-012 — Üretim/kayıt/FBX smoke | BLENDER_MODULAR_SMOKE gerçek raporu |
| MB2-013 — Windows yolu ve kaynak yükleme | Türkçe yol, eksik PBR, salt okunur hedef |
| MB2-014 — UE5.8 ilk ithalat | Kalibrasyon, materyal, collision; gerçek motor raporu |

## P2 — Birleşimler ve kapalı bina

Durum: **PLANNED**. Bağımlılık: P1-N.

| İş | Teslim ve kabul |
|---|---|
| MB2-015 — İç/dış köşe ve sonlandırma | Kalınlık/profil eşleme; çift kaide/parapet yok |
| MB2-016 — Taban ve üst bitiş modülleri | Tek yüzey sahibi, kontrol edilen sahanlık |
| MB2-017 — Dört cephe tek kat demo | Dış kabuk kapanışı ve gerçek giriş boşluğu |
| MB2-018 — Kilit/çatışma sözleşmesi | Eski özel parça ile yeni panel çakışmasının raporu |

## P3 — HQ ve UNIT grameri

Durum: **PLANNED**. Bağımlılık: P2.

| İş | Teslim ve kabul |
|---|---|
| MB2-019 — Kat ve referans düzlemleri | Pencere/söve/kat çizgisi tutarlılığı |
| MB2-020 — L/U ve kanat hacmi | Çözülebilen plan tiplerinin açık aralığı |
| MB2-021 — Simetri ve alternatif cephe dizileri | Kapı/etiket aynalama hatası yok |
| MB2-022 — Görsel varyasyon tarayıcısı | Bina/kaplama/ekipman seed ayrımı |

## P4 — Hangar ve AS07 modülleri

Durum: **PLANNED**. Bağımlılık: P2.

| İş | Teslim ve kabul |
|---|---|
| MB2-023 — Portal ve çatı sistemleri | Geometri açıklık kontrolü; statik hesap değil |
| MB2-024 — Sürgülü ana kapı ve ray | Rest pose, pivot ve görsel hareket sınırı |
| MB2-025 — AS07 parça adaptörü | Kaynak aynılığı, iki eksen dönüşümü yok |
| MB2-026 — Apron eşiği ve servis duvarı | Zemin üst üste binmez, personel yönü açık |

## P5 — PBR ve sanat yönü

Durum: **PLANNED**. Bağımlılık: P1-N.

| İş | Teslim ve kabul |
|---|---|
| MB2-027 — Kaynak manifesti/thumbnail tarayıcı | Lisans, scale, source-method etiketi |
| MB2-028 — Aynı yol değişimini algılama | Texture hash, image reload, doğru cache invalidation |
| MB2-029 — Trim/detail ve UV planı | Yönlü normal, seam kontrolü ve lightmap ayrımı |
| MB2-030 — Durum/ıslaklık/aşınma | Mimariye bağlı maskeler; nötr render kapısı |

## P6 — Birleşik yerleşke köprüleri

Durum: **PLANNED**. Bağımlılık: P2, P4.

| İş | Teslim ve kabul |
|---|---|
| MB2-031 — SW01 giriş-sahanlık bağlantısı | Yaya açıklığı ile yol genişliği ayrılır |
| MB2-032 — AF01 yüzey sahipliği | Apron, eşik, drenajın tek üreticisi |
| MB2-033 — PK01 dışlama güncellemesi | Bitki ve mobilya ayak izi çakışmaz |
| MB2-034 — Taşınmış/kilitli nesneler | Güncel değil durumu ve açık yeniden bağlama |

## P7 — Unreal üretim akışı

Durum: **PLANNED**. Bağımlılık: P1-N, P5.

| İş | Teslim ve kabul |
|---|---|
| MB2-035 — Artımlı FBX/manifest | Farkı göster, ilgisiz asseti ezme |
| MB2-036 — Modüler materyal instance düzeni | Parametreli ana tarif ve override |
| MB2-037 — ISM grupları ve bütçe | Mesh+materyal+collision anahtarına göre gruplama |
| MB2-038 — Native görsel/performans testi | Sürüm ve donanımla ölçülmüş rapor |

## P8 — İç mekân ve çekim durumu

Durum: **PLANNED**. Bağımlılık: P3, P4, P7.

| İş | Teslim ve kabul |
|---|---|
| MB2-039 — Dış çekim/lobi/seçili oda seviyeleri | Cephe ile iç mekân açıklıkları eşleşir |
| MB2-040 — Kapı/ışık bileşenleri | Doğru pivot ve seçilebilir animasyon durumu |
| MB2-041 — Çekim sürekliliği kaydı | Kapı, ekipman, nem, ışık yeniden yüklenir |

## RC — Sürüm adayı

Durum: **PLANNED**. Bağımlılık: P3, P4, P5, P6, P7.

| İş | Teslim ve kabul |
|---|---|
| MB2-042 — Kurulum/upgrade/regresyon | Eski MB01 sahnesi yeni adayda kontrol edilir |
| MB2-043 — Demo ve dokümantasyon | Native kaynak renderları ve bilinen sınırlar |
| MB2-044 — Lisans/asset raporu ve paket | Hash bütünlüğü; yapımcı kaynakları korunmuş |
