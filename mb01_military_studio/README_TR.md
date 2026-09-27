# MB01 Military Building Studio

> Güncelleme: **0.4 alpha.1 – Building Refinement**  
> HQ / birlik / destek / lojistik bina dili geliştirildi. Yeni `office_style`, `service_bays`, `stair_tower`, `roof_screen` ve `corner_glass` parametreleri eklendi.

## 6 yeni cephe modülü • 5 yeni tam hangar önayarı • küçük modül LOD kiti

**26 Eylül 2026.** Bu, MB01 alpha.3 üstüne aday güncellemedir. Kararlı veya bütün hedef motorlarda doğrulanmış ürün değildir. Gerçek kaynak geometri testleri ve bağımsız görüntüler vardır; Blender 4.5/UE5.8 çalıştırılmadı. Kurgusal CGI mimarisi; inşaat/askerî uygunluk sertifikası yok.

## Tam olarak ne eklendi?

CASSETTE, VISION, SHADED, DUAL_VENT, DOUBLE_SERVICE, CANOPY_ENTRY. Hepsi tekil modül kataloğunda ve tam hangarın sol/sağ cephesinde kullanılabilir. Eski METAL, CLERESTORY, LOUVER, PERSONNEL türleri korunur. Toplam 62 katalog kaydı içinde 20 geometri üreticisi vardır; 42 kayıt hâlâ planlıdır.

EXP_COASTAL, EXP_TECHNICAL, EXP_COMPACT, EXP_LONG ve EXP_URBAN yeni tam hangar önayarlarıdır. Eski üç önayar da kalır. İki mevcut çatı ve mevcut teleskopik ana kapı sistemi yeniden kullanılır; yeni büyük kapı/çatı türü eklendiği iddia edilmez.

Yeni küçük oyun-kiti yalnız altı modülü opak/cam/kapı mesh'lerine ayırır. LOD0/1/2, sabit pivot/slot düzeni, basit wall/door collision ve birleşim yardımcıları içerir. **Tam hangarın tek tuşla LOD/atlas optimizasyonu değildir.**

## Blender 4.5 kurulumu

1. `.blend` dosyanızı ve eski MB01 ZIP'ini yedekleyin. İlk kullanım boş dosyada olsun.
2. Önceki MB01'i devre dışı bırakıp Blender'ı yeniden başlatın. Aynı modülün iki kopyasını yan yana kurmayın.
3. Preferences → Add-ons → Install from Disk ile **MB01_HangarExpansion_Addon_0_3a1.zip** dosyasını seçin ve etkinleştirin.
4. Paket adı `MB01 | Military Building Studio + Hangar Studio (0.3 alpha.1 Expansion)`; Blender sayısal sürümü `(0,3,1)` olmalıdır.
5. Object Mode ve Unit Scale 1.0 kullanın. `__init__.py` Text Editor'de Alt+P ile çalıştırılmaz.

## Tam hangar üretmek

`N → MB01 → Hangar Expansion | 0.3 alpha.1` bölümünde EXP_COMPACT veya EXP_COASTAL seçin. **Hangar önayarını yükle**, sonra Draft, **Geometri kurallarını kontrol et**, **YENİ hangar revizyonu oluştur**.

Yeni üretim önceki yapıyı silmez. Aynı yerde yeniden ürettiklerinizi üst üste bırakmayın; önceki koleksiyonu gizleyin veya 3D Cursor'u taşıyın. Working/Hero tam hangarın bevel ayrıntısını değiştirir; yeni taranmış texture sağlamaz.

`02 · Cephe hücreleri` bölümünde sol/sağ, hücre numarası ve yeni modül seçip değişikliği tarife uygulayın. Mevcut mesh otomatik değişmez; sonra yeni revizyon oluşturun. Virgüllü tam dizi düzeni de korunur. Bölme sayısı dizideki hücre sayısına eşit olmalı. Bitişik iki giriş modülü bu sürümde reddedilir.

Bölme aralığı **2,8–6 m**. Örneğin 48 m / 10 bölme = 4,8 m. Önceki konuşmadaki 8/10 m önerileri bu kodun destek aralığı değildir. Yerel zemin kapalıysa dış apronu `root Z + base_height` seviyesine getirin; otomatik AF01 zemin kesimi yok.

## Küçük modül oyun-kitini üretmek

`N → MB01 → Modül Oyun-Kiti | 0.3 alpha.1` bölümünde altı yeni parçadan birini seçin. Boyut ve LOD seçip **Kit geometri / LOD raporu** ardından **3D Cursor'da yeni LOD örneği** komutunu çalıştırın.

Bu yol tam hangarın kapı açık pozundan bağımsızdır: modül kapıları kapalı rest pozu, ayrı menteşe ve hareket bilgisiyle gelir. Opak/cam/kapı gruplarının slotları ve pivotları LOD'larda korunur. LOD1/2 bazı ince detayları kaldırır; texture'a normal bake yapılmaz. Bu LOD önizlemesine otomatik bevel eklenmez.

Tam `.blend` kaydedin veya mutlak bir export klasörü seçin. **FBX LOD + collision + socket kitini export et** komutu yeni tarih/UUID klasörü açar. Kaynak mesh'lerin yerine geçmez ve eski exportu ezmez.

```
MB03_<modül>_<tarih>_<kimlik>/
  Meshes/SM_..._LOD0.fbx
         SM_..._LOD1.fbx
         SM_..._LOD2.fbx
  Textures/...
  GAME_KIT.json
  IMPORT_README_TR.txt
```

Her render alt-varlığı ayrı dosya grubudur. Yalnız LOD0 FBX'inde o assete eşleşen UCX collision ve gerektiğinde SOCKET yardımcıları bulunur. Üç LOD dosyasını UE'ye üç bağımsız bina gibi yerleştirmek yerine LOD1/2'yi aynı Static Mesh'e manuel LOD olarak ekleyin. Otomatik UE LOD bağlayıcı bu sürümde yoktur. `GAME_KIT.json` pivot ve modül içi yerleşimleri taşır; kapı/cam mesh'lerini bu koordinatlarla birleştirin.

**Kit manifestini eski tam-bina MB01_Import.py ile açmayın.** Tam hangarın mevcut FBX+JSON exporter/importer yolu ayrıdır ve tam hangara yeni modül LOD'larını otomatik uygulamaz.

## Materyal ve ışık sınırı

Mevcut 8 aile/40 prosedürel PNG korunur. Yeni tarama, premium ücretli kaynak veya 8K set yok. Tam hangarda cephe/çatı/kapı/döşeme rolleri ve fiziksel tile boyutu korunur. Kendi PBR seti için aynı ailenin BaseColor, ORM, NormalGL, NormalDX ve Height dosyalarını birlikte verin. `Harici PBR üst klasörü` tüm ailelerin üst klasörüdür.

`UV0_Tile` tekrar eden yüzey UV'sidir. **Unique lightmap UV1 yok; hedef dinamik aydınlatma.** Baked ışık için ayrıca unwrap/UV denetimi gerekir. Height kaynak olarak taşınır; varsayılan displacement bağlı değildir. Özel Blender shader düzenlemesi Unreal'a birebir çevrilmez.

Kit wall collision'ı açıklıkları çevreleyen kutulardan gelir; camda collision yok, kapı ayrıdır. Saçak, küçük çerçeve ve dekorların tamamının collision'ı yoktur. Oyuncu trace ve kapı hareketini UE'de kontrol edin. Tam bina self-intersection, bütün mekanizma çarpışmaları ve kusursuz navigasyon iddiası yok.

## Gerçek örnekler

`examples/NEW_MODULES_BOARD.png` altı modülü, `FIVE_PRESETS_BOARD.png` beş yeni tam hangarı gösterir. Her kartta ayarlar vardır. `KIT_*_LODs.glb` dosyalarında LOD0/1/2 yan yana 6 m aralıkla sunulur; bu bir LOD karşılaştırma sahnesi, native Unreal LOD asseti değildir. İki tam hangar GLB'si ayrıca verilir.

Görseller actual source geometry + bağımsız CPU ray-cast'tir; image AI yok. Native Blender bevel, tangent normal, cam kırılması, çok sekmeli GI ve temporal AA gösterilmez. Kaynak PNG'ler oyun içi FPS, native shader veya final CGI kalite onayı değildir.

## Testler ve tanılama

`reports/VALIDATION_REPORT.json` bu revizyonda gerçekten çalıştırılan kaynak testlerini içerir. `reports/LEGACY_REGRESSION.json` eski üç hangar ve beş bina ailesinin kaynak geometri karşılaştırmasıdır. Tarihî raporların sürümü başlığında yazılıdır; yeni doğrulama yerine sayılmaz.

Geliştirme paketindeki `tools/TEST_EXPANSION_WINDOWS.cmd`, ayrı `--background --factory-startup` Blender süreci açar. İki tam hangar, altı modül, panel operatörleri, kayıt ve iki modülün FBX/LOD exportunu test edecek şekilde hazırlanmıştır. Açık çalışma dosyanızı açmaz. Çıktı `~/MB01_Expansion_Diagnostics/<tarih_kimlik>` altındadır. Script burada çalıştırılmadı; gerçek raporu çalıştırma oluşturur.

Alternatif: `powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\RUN_EXPANSION_NATIVE.ps1 -BlenderExe "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe" -Render`

Bu yalnız başlatılan PowerShell sürecini etkiler, kalıcı sistem politikası değiştirmez. Render isteğe bağlıdır. Kaynak Python testleri: `python -m unittest discover -s tests -v`. Görsel araçlar NumPy/Pillow/VTK/Numba/Trimesh gibi ek bağımlılıklar kullanır; normal eklenti kurulumunda bunları ayrıca kurmanız gerekmez.

## Olgunluk

Native Blender kurulumu/modifier/export ve UE5.8 import/LOD/shader/collision çalıştırılmadan kararlı veya tamamen game-ready onayı verilmez. Yeni büyük kapılar/çatılar, trim bake, yeni PBR taramaları, tüm-bina LOD, otomatik ISM/Nanite/LOD binding, canlı AF01/SW01/PK01, artımlı yerinde güncelleme ve tam iç mekân sonraki aşamalardır. Ayrıntılı plan: `docs/MB01_03_MASTER_PLAN_TR.md`.


## 0.4 alpha.1 MCP / CGI PBR katmanı
Glonorce Blender MCP ile `execute_blender_code` üzerinden çağrılabilen `mb01_military_studio.agent_api` eklendi. HQ için EXECUTIVE/TECHNICAL/MONOLITHIC varyantları, daha derin cephe artikülasyonu, AO+normal+height kullanan zengin PBR shader ve whole-building game-ready audit eklendi. Ayrıntı: `docs/MCP_CGI_GAME_READY_0_4a1_TR.md`.
