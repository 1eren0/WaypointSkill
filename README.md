<div align="center">

# 🧭 Waypoint

### Kod bilmeden, yapay zekâyla, kaybolmadan proje bitir.

Claude Code, Codex, Antigravity ve diğer yapay zekâ araçları için Türkçe çalışma düzeni.
Tek komutla kurulur; projeyi küçük, kayıtlı ve test edilmiş adımlarla ilerletir.

</div>

---

## Neden?

Yapay zekâyla proje yaparken şunlar tanıdık gelebilir:

- 😵 Yeni oturumda **nerede kaldığını** hatırlamıyorsun, her şeyi baştan anlatıyorsun.
- 🐇 Bir işin ortasında aklına yeni bir fikir geliyor, ona atlıyorsun, **ilk iş yarım kalıyor**.
- 💥 Bir şeyi düzeltirken **başka bir şey bozuluyor** ve fark etmiyorsun.
- 🔁 Yapay zekâ **aynı hatayı tekrar tekrar** yapıyor.
- 🤷 "Bitti" deniyor ama **neyin bittiği** belli değil.

Waypoint bunların her birine bir kural ve bir kontrol koyar. Kurallar rica değil: kayıt anında **otomatik olarak denetlenir.**

## Ne yapar?

| | |
|---|---|
| 🎯 **Tek görev** | Plan küçük görevlere bölünür; aynı anda tek görev yapılır. Yeni fikirler "Sonra yapılacaklar" listesine tek satır olarak park edilir; uzun fikirlerin ayrıntısı `FIKIRLER.md`'ye yazılır. |
| 🧱 **Küçük adımlar** | Her değişiklik tek bir iş yapar ve ayrı bir kayıt noktasıdır. Bozulan adım tek başına geri alınır. |
| ☁️ **Otomatik yedek** | Projenin GitHub bağlantısı varsa her kayıt kendiliğinden GitHub'a yüklenir. Deneysel ya da aynı anda yürüyen işler ayrı dallarda (branch) tutulur. |
| 🧪 **Otomatik testler** | Önemli özelliklerin testi yazılır. Testler geçmezse kayıt **alınmaz**. |
| 📒 **İlerleme defteri** | Hedef, plan, kararlar ve günlük tek dosyada. Kod değiştiği gün günlüğe yazılmadan kayıt **alınmaz**. Defter büyüyünce eski kayıtlar arşive taşınır, hep kısa kalır. |
| 🗺️ **Proje haritası** | Önemli fonksiyonlar ve bağlantıları, Obsidian'da resim olarak görünen bir şemayla. Haritada olmayan yeni fonksiyon kayda **giremez** (JavaScript/TypeScript, Python, Go, Rust, Java, C#, Kotlin, Swift, PHP, Ruby gibi yaygın dillerde). Koddan silinmiş ya da yanlış dosyaya yazılmış fonksiyon haritada **kalamaz**. Haritadaki bir fonksiyon değişince bağlantılarını kontrol etmesi için yapay zekâya hatırlatılır. |
| 📝 **Dersler** | Yapay zekânın hatalarından çıkan kurallar. Düzeltme kayıtlarında ders yazmayı hatırlatır. |
| 🏷️ **Düzenli kayıtlar** | Her kayıt İngilizce ve standart [Conventional Commits](https://www.conventionalcommits.org) biçiminde: `feat: add expense form`, `fix: prevent empty tasks`, `docs: …`. Testsiz hata düzeltmesi kayda **giremez**. |
| 🔤 **Bozuk karakter koruması** | Türkçe harfleri bozulmuş (yanlış kodlanmış) dosyalar ve kayıt mesajları kayda **giremez**. |
| 🔒 **Gizli bilgi koruması** | `.env`, anahtar, sertifika ve servis hesabı dosyaları kayda **giremez**. Koda gömülü GitHub/AWS/Google/yapay zekâ anahtarları ve özel anahtarlar da yakalanır. |
| 🇹🇷 **Sade Türkçe** | Yapay zekâ seninle teknik terim kullanmadan, kısa ve net konuşur. |

## Kurulum

Projenin klasöründe bir terminal aç ve tek komutu yapıştır.

> **Şu an repo gizli** olduğu için kurulum GitHub girişini kullanır. Bilgisayarında [GitHub CLI](https://cli.github.com) kurulu ve `gh auth login` ile giriş yapılmış olmalı.

**Windows (PowerShell):**
```powershell
gh api repos/erenuzman/WaypointSkill/contents/install.ps1 -H "Accept: application/vnd.github.raw" | Out-String | iex
```

**macOS / Linux:**
```bash
gh api repos/erenuzman/WaypointSkill/contents/install.sh -H "Accept: application/vnd.github.raw" | sh
```

Bitti. Şimdi aynı klasörde yapay zekâ aracını aç ve ne yapmak istediğini anlat. Gerisini Waypoint yönetir: önce hedefi netleştirir, sonra planı sana onaylatır, sonra adım adım yapar.

### Gerekenler

- **Git**: kayıt noktaları için. [İndir](https://git-scm.com)
- **Python 3.10+** (zorunlu): kural kontrolleri Python ile çalışır. Python yoksa kontroller atlanmaz, **kayıt engellenir** ve nasıl kurulacağı söylenir. Windows'ta kurarken "Add python.exe to PATH" kutusunu işaretle. [İndir](https://www.python.org/downloads/)
- **GitHub CLI**: repo gizliyken kurulum için. [İndir](https://cli.github.com)

### Güncelleme

Yeni sürüm çıkınca kendin takip etmene gerek yok. Waypoint günde bir kez yeni sürüm var mı diye bakar. Varsa yapay zekâ sana yenilikleri anlatır ve "kurayım mı?" diye sorar. Sen onay vermeden hiçbir şey kurulmaz. Kurulu sürüm `.waypoint/VERSION` dosyasında yazar, yenilikler [CHANGELOG.md](CHANGELOG.md) dosyasında.

Elle güncellemek istersen aynı kurulum komutunu tekrar çalıştır. Kurallar ve kontroller güncellenir; senin ilerleme, ders ve harita dosyalarına **dokunulmaz.**

## Projene ne eklenir?

```
projen/
├── AGENTS.md          ← Codex, Antigravity vb. için tek satırlık yönlendirme
├── CLAUDE.md          ← Claude Code için tek satırlık yönlendirme
└── .waypoint/
    ├── KURALLAR.md    ← yapay zekânın uyduğu çalışma kuralları
    ├── komutlar/      ← uzun komut tarifleri (bitir, güncelleme…), gerektiğinde okunur
    ├── VERSION        ← kurulu Waypoint sürümü
    ├── ILERLEME.md    ← hedef, plan, kararlar, günlük
    ├── DERSLER.md     ← hatalardan çıkan kurallar
    ├── HARITA.md      ← önemli fonksiyonlar + şema
    ├── raporlar/      ← yapay zekânın yazdığı raporlar (tarihli)
    ├── WAYPOINT_GUNLUGU.md ← Waypoint işe yarıyor mu? (oturum notları)
    ├── oto-kayit.log  ← her kayıt ve engel kendiliğinden yazılır (sadece bilgisayarında)
    └── hooks/         ← kayıt anında çalışan kontroller
```

Waypoint'e ait her şey tek klasörde. Senin dosyalarına karışmaz.

## Kullanırken

Yapay zekâya istediğin zaman şunları yazabilirsin:

| Komut | Ne olur |
|---|---|
| `neredeyiz` | Hedef, plan, şu an ne yapıldığı ve sıradaki adım özetlenir. |
| `sos` | Sadece soru: yapay zekâ cevap verir, hiçbir şeyi değiştirmez. |
| `nep` | Ne yaptık: son yapılan işlem kısaca, sade dille anlatılır. |
| `snv` | Sırada ne var: sadece sıradaki adım tek cümleyle söylenir. |
| `parket <fikir>` | Yeni fikir, mevcut iş bölünmeden "Sonra yapılacaklar"a yazılır. |
| `liste` | Yapılanlar ve yapılacaklar alt alta gösterilir. |
| `nasıl açarım` | Projeyi çalıştırma adımları gösterilir. |
| `haritayı göster` | Projenin haritası kutular ve oklarla çizilir. |
| `bitir` | Yarım iş toparlanır, defterler güncellenir, kayıt alınır, günün özeti çıkar. |

Haritayı kendin görmek istersen proje klasörünü **Obsidian**'da aç ve `.waypoint/HARITA.md` dosyasına bak. Şema resim olarak görünür.

## Kontroller nasıl çalışır?

Kontroller yapay zekâ aracına değil **git**'e bağlıdır. Bu yüzden hangi aracı kullanırsan kullan, her kayıtta aynı şekilde çalışırlar:

```mermaid
flowchart LR
  A["Yapay zekâ<br>kayıt almak ister"] --> B{"Kurallar<br>tamam mı?"}
  B -- Hayır --> C["❌ Kayıt engellenir<br>neyin eksik olduğu yazılır"]
  C --> D["Yapay zekâ<br>eksiği düzeltir"]
  D --> A
  B -- Evet --> E{"Testler<br>geçiyor mu?"}
  E -- Hayır --> C
  E -- Evet --> F["✅ Kayıt alınır"]
```

## Sık sorulanlar

**Kod bilmem gerekiyor mu?**
Hayır. Waypoint tam olarak kod bilmeyenler için tasarlandı. Sen ne istediğini söylersin, denersin, "çalışıyor" ya da "çalışmıyor" dersin.

**Hangi yapay zekâ araçlarıyla çalışır?**
`AGENTS.md` dosyasını okuyan her araçla (Codex, Antigravity, Cursor…) ve `CLAUDE.md` üzerinden Claude Code ile. Kontroller git'e bağlı olduğu için hepsinde çalışır.

**Mevcut bir projeye kurabilir miyim?**
Evet. Varsa `AGENTS.md` ve `CLAUDE.md` dosyalarının içeriği korunur, sonuna sadece Waypoint yönlendirmesi eklenir.

**Waypoint'i projeden nasıl kaldırırım?**
`.waypoint` klasörünü sil, `AGENTS.md` ve `CLAUDE.md` içindeki Waypoint satırını kaldır ve terminalde şunu çalıştır:
```bash
git config --unset core.hooksPath
```

---

<div align="center">
<sub>Waypoint · küçük adımlar, kayıtlı ilerleme, kaybolmak yok.</sub>
</div>
