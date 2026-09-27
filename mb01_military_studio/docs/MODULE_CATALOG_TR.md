# MB01 0.2 — Kategorize Modül Kataloğu

**56 kayıt:** 14 geometri üreticisi kodlandı; 42 kayıt ileri aşama kapsamıdır. Bu sayı, 56 hazır model olduğu anlamına gelmez. Native Blender/UE doğrulaması bütün yeni modüller için bekliyor.

Bir katalog girdisi tam bir bina değil; nominal ölçüsü, komşuluk kuralı ve malzeme rolü olan bir modüldür. AS07’nin eski tam model üreticisi korunuyor; AS07’nin modüllere ayrılması aşağıda planlanmış olarak işaretlidir.

| Kimlik | Başlık | Kategori | Aileler | Durum |
|---|---|---|---|---|
| `COMMON.WALL.PLAIN` | Düz duvar paneli | WALL | HQ, UNIT, SUPPORT | Geometri kodu + Python test |
| `COMMON.WALL.WINDOW` | Pencereli duvar | WALL | HQ, UNIT, SUPPORT | Geometri kodu + Python test |
| `COMMON.WALL.NARROW` | Dar pencereli duvar | WALL | HQ, UNIT, SUPPORT | Geometri kodu + Python test |
| `COMMON.WALL.SUNSHADE` | Güneşlikli pencere | SHADING | HQ, UNIT, SUPPORT | Geometri kodu + Python test |
| `COMMON.WALL.VENT` | Panjurlu havalandırma paneli | WALL | HQ, UNIT, SUPPORT | Geometri kodu + Python test |
| `COMMON.ENTRY.SERVICE` | Tek kanat servis kapısı | ENTRY | HQ, UNIT, SUPPORT | Geometri kodu + Python test |
| `COMMON.ENTRY.DOUBLE` | Çift kanat personel girişi | ENTRY | HQ, UNIT, SUPPORT | Geometri kodu + Python test |
| `HQ.FACADE.GLAZED` | Camlı cephe bölümü | GLAZING | HQ | Geometri kodu + Python test |
| `HQ.ENTRY.LOBBY` | Saçaklı camlı ana giriş | ENTRY | HQ | Geometri kodu + Python test |
| `UNIT.WALL.WINDOW` | Birlik binası pencere modülü | WALL | UNIT | Geometri kodu + Python test |
| `HANGAR.WALL.METAL` | Hangar metal yan panel | HANGAR_ENVELOPE | HANGAR | Geometri kodu + Python test |
| `HANGAR.WALL.CLERES` | Hangar üst bant penceresi | HANGAR_ENVELOPE | HANGAR | Geometri kodu + Python test |
| `HANGAR.WALL.LOUVER` | Hangar havalandırma bölmesi | HANGAR_ENVELOPE | HANGAR | Geometri kodu + Python test |
| `HANGAR.ENTRY.PERSONNEL` | Hangar yan personel girişi | HANGAR_ENTRY | HANGAR | Geometri kodu + Python test |
| `COMMON.CORNER.OUTER90` | Dış köşe | CORNER | HQ, UNIT, SUPPORT | Planlandı |
| `COMMON.CORNER.INNER90` | İç köşe | CORNER | HQ, UNIT, SUPPORT | Planlandı |
| `COMMON.CORNER.TERMINAL` | Uç bitiş | CORNER | HQ, UNIT, SUPPORT | Planlandı |
| `COMMON.ROOF.PARAPET` | Parapet | ROOF | HQ, UNIT, SUPPORT | Planlandı |
| `COMMON.ROOF.COPING` | Parapet kapak profili | ROOF | HQ, UNIT, SUPPORT | Planlandı |
| `COMMON.ROOF.EAVE` | Saçak bitişi | ROOF | HQ, UNIT, SUPPORT | Planlandı |
| `COMMON.ROOF.DRAIN` | Oluk ve iniş bağlantısı | ROOF | HQ, UNIT, SUPPORT | Planlandı |
| `COMMON.BASE.PLINTH` | Kaide | BASE | HQ, UNIT, SUPPORT | Planlandı |
| `COMMON.BASE.LANDING` | Personel sahanlığı | BASE | HQ, UNIT, SUPPORT | Planlandı |
| `COMMON.BASE.RAMP` | Görsel rampa | BASE | HQ, UNIT, SUPPORT | Planlandı |
| `COMMON.BASE.DRAIN` | Zemin drenaj yuvası | BASE | HQ, UNIT, SUPPORT | Planlandı |
| `COMMON.DETAIL.SIGN` | Nötr numara rozeti | DETAIL | HQ, UNIT, SUPPORT | Planlandı |
| `COMMON.DETAIL.LIGHT` | Opal armatür | DETAIL | HQ, UNIT, SUPPORT | Planlandı |
| `COMMON.DETAIL.CABINET` | Servis kutusu | DETAIL | HQ, UNIT, SUPPORT | Planlandı |
| `HANGAR.STRUCTURE.PORTAL` | Portal çerçeve | STRUCTURE | HANGAR | Planlandı |
| `HANGAR.STRUCTURE.PURLIN` | Aşık modülü | STRUCTURE | HANGAR | Planlandı |
| `HANGAR.STRUCTURE.BRACE` | Görsel çapraz | STRUCTURE | HANGAR | Planlandı |
| `HANGAR.GATE.SLIDING` | Çok kanat sürgülü ana kapı | HANGAR_ENTRY | HANGAR | Planlandı |
| `HANGAR.GATE.RAIL` | Ray başlığı ve kılavuz | HANGAR_ENTRY | HANGAR | Planlandı |
| `HANGAR.ROOF.SKIN` | Modüler çatı kaplaması | ROOF | HANGAR | Planlandı |
| `HANGAR.ROOF.LIGHT` | Çatı ışıklığı | ROOF | HANGAR | Planlandı |
| `HANGAR.FLOOR.THRESHOLD` | Apron eşiği | BASE | HANGAR | Planlandı |
| `HANGAR.SERVICE.PLATFORM` | Bakım platformu dekoru | DETAIL | HANGAR | Planlandı |
| `HANGAR.SERVICE.WALL` | Tesisat duvarı | DETAIL | HANGAR | Planlandı |
| `HANGAR.LIGHT.LINEAR` | Askılı lineer armatür | DETAIL | HANGAR | Planlandı |
| `SHELTER.AS07.ADAPTER` | Mevcut AS07 bina adaptörü | ADAPTER | SHELTER | Planlandı |
| `SHELTER.AS07.ARCH` | AS07 kemer hücresi ayrıştırma | STRUCTURE | SHELTER | Planlandı |
| `SHELTER.AS07.ROOF` | AS07 çatı hücresi | ROOF | SHELTER | Planlandı |
| `SHELTER.AS07.LOUVER` | AS07 panjur hücresi | WALL | SHELTER | Planlandı |
| `SHELTER.AS07.REAR` | AS07 arka duvar ve servis kapısı | ENTRY | SHELTER | Planlandı |
| `HQ.ENTRY.PORTICO` | Temsil giriş portiği | ENTRY | HQ | Planlandı |
| `HQ.FACADE.CORNERGLASS` | Köşe camı | GLAZING | HQ | Planlandı |
| `HQ.FACADE.MEETING` | Toplantı salonu cephe paketi | GLAZING | HQ | Planlandı |
| `HQ.INTERIOR.LOBBY` | Giriş holü | INTERIOR | HQ | Planlandı |
| `HQ.INTERIOR.OFFICE` | Seçili ofis | INTERIOR | HQ | Planlandı |
| `UNIT.ENTRY.SIDECANOPY` | Yan giriş saçağı | ENTRY | UNIT | Planlandı |
| `UNIT.FACADE.CORRIDOR` | Koridor penceresi | WALL | UNIT | Planlandı |
| `UNIT.VOLUME.STAIR` | Merdiven hacmi dış kabuğu | VOLUME | UNIT | Planlandı |
| `UNIT.INTERIOR.ROOM` | Seçili oda seti | INTERIOR | UNIT | Planlandı |
| `SUPPORT.CANOPY.BAY` | Eğitim gölgeliği | STRUCTURE | SUPPORT | Planlandı |
| `SUPPORT.WALL.STORE` | Ekipman deposu dış kabuğu | WALL | SUPPORT | Planlandı |
| `SUPPORT.DETAIL.BOARD` | Nötr eğitim panosu | DETAIL | SUPPORT | Planlandı |

## Şu anki geometri aralıkları

Bunlar inşaat/askerî standart ölçüleri değil; ilk üreticinin desteklediği yazılım parametre aralıklarıdır.

| Modül | Genişlik / m | Yükseklik / m | Başlangıç / m |
|---|---|---|---|
| Düz duvar paneli | 2.4–5.4 | 3.0–4.4 | 3.6 × 3.6 |
| Pencereli duvar | 2.4–5.4 | 3.0–4.4 | 3.6 × 3.6 |
| Dar pencereli duvar | 2.4–5.4 | 3.0–4.4 | 3.6 × 3.6 |
| Güneşlikli pencere | 2.4–5.4 | 3.0–4.4 | 3.6 × 3.6 |
| Panjurlu havalandırma paneli | 2.4–5.4 | 3.0–4.4 | 3.6 × 3.6 |
| Tek kanat servis kapısı | 2.4–5.4 | 3.0–4.4 | 3.6 × 3.6 |
| Çift kanat personel girişi | 3.0–5.4 | 3.2–4.4 | 3.6 × 3.6 |
| Camlı cephe bölümü | 3.0–5.4 | 3.0–4.4 | 3.6 × 3.6 |
| Saçaklı camlı ana giriş | 3.2–5.4 | 3.3–4.4 | 3.6 × 3.6 |
| Birlik binası pencere modülü | 2.4–5.4 | 3.0–4.4 | 3.6 × 3.6 |
| Hangar metal yan panel | 2.8–6.0 | 4.0–9.0 | 4.5 × 6.4 |
| Hangar üst bant penceresi | 2.8–6.0 | 4.0–9.0 | 4.5 × 6.4 |
| Hangar havalandırma bölmesi | 2.8–6.0 | 4.0–9.0 | 4.5 × 6.4 |
| Hangar yan personel girişi | 2.8–6.0 | 4.0–9.0 | 4.5 × 6.4 |