# QR Menü — Sunucuya Kurulum Rehberi

Bu rehber projeyi sıfırdan bir sunucuda yayına alır. Toplam süre yaklaşık 30–45 dakikadır.
Her şey Docker ile çalışır; Python, Node.js, MongoDB veya Nginx'i ayrıca kurmanız gerekmez.

Sonuçta şöyle bir yapı olur:

| Adres | Ne açılır |
|---|---|
| `qrmeny.com` | Ürünün tanıtım sitesi (`landing` klasörü) |
| `www.qrmeny.com` | Otomatik olarak `qrmeny.com`'a yönlenir |
| `panel.qrmeny.com` | İşletme paneli: kayıt, giriş, menü yönetimi. Süper admin de buradan girer; `.env`'deki e-postayla giriş yapınca `/admin` paneline yönlenir |
| `kafeadi.qrmeny.com` | O işletmenin müşteri menüsü (QR kod bu adrese gider) |

---

## 1. Sunucu oluşturun (Hetzner)

1. Hetzner Cloud Console → **Add Server**.
2. Lokasyon: **Falkenstein**, **Nürnberg** veya **Helsinki**.
3. İmaj: **Ubuntu 24.04**.
4. Tip: **Shared vCPU → x86 (Intel/AMD)**, en az **2 vCPU / 4 GB RAM** (CX22 veya güncel muadili). Derleme sırasında 2 GB RAM yetmez.
5. **Backups** seçeneğini açın (küçük bir ek ücretle günlük otomatik sunucu yedeği).
6. **Firewalls** → yeni bir firewall oluşturup sadece şu gelen portlara izin verin: **22**, **80**, **443**.
7. Sunucu oluşunca IP adresini not alın.

## 2. Sunucuya bağlanın ve Docker'ı kurun

Bilgisayarınızda terminali (Windows'ta PowerShell) açın:

```bash
ssh root@SUNUCU_IP_ADRESI
```

Sunucuda:

```bash
apt update && apt upgrade -y
curl -fsSL https://get.docker.com | sh
docker --version
```

## 3. Projeyi indirin ve ayarlayın

```bash
git clone https://github.com/doaliz/Qr-Menu-New.git /opt/qrmenu
cd /opt/qrmenu
cp .env.example .env
openssl rand -hex 32
```

Son komutun çıktısını (uzun harf/rakam dizisi) kopyalayın, sonra ayar dosyasını açın:

```bash
nano .env
```

Doldurun:

- `MENU_DOMAIN` → `qrmeny.com` (zaten dolu gelir)
- `SUPER_ADMIN_EMAIL` → süper admin olarak kullanacağınız e-posta
- `JWT_SECRET_KEY` → az önce kopyaladığınız değer

Kaydetmek için `Ctrl+O`, `Enter`, çıkmak için `Ctrl+X`.

> `.env` dosyası GitHub'a gönderilmez ve gönderilmemelidir. `JWT_SECRET_KEY` boş veya kısaysa uygulama bilerek başlamaz.

## 4. Uygulamayı başlatın

```bash
docker compose up -d --build
```

İlk seferde 5–10 dakika sürer (frontend derleniyor). Bitince kontrol edin:

```bash
docker compose ps
curl -s localhost/api/health
```

Üç servis (`mongo`, `backend`, `web`) "running" görünmeli ve ikinci komut `{"status":"ok"}` dönmeli.

## 5. Süper admin hesabını oluşturun

```bash
docker compose exec backend python create_super_admin.py
```

Şifre sorulacak (en az 12 karakter). Şifreyi unutursanız aynı komutla sıfırlayabilirsiniz.

## 6. Cloudflare ile alan adı ve SSL

1. cloudflare.com'da ücretsiz hesap açın → **Add a site** → alan adınızı girin → **Free** plan.
2. Cloudflare'in verdiği iki **nameserver** adresini, alan adını aldığınız firmanın panelinde (GoDaddy, İsimtescil, Natro vb.) eskilerinin yerine yazın. Aktif olması birkaç dakika ile birkaç saat sürebilir.
3. Cloudflare → **DNS → Records** bölümünde üç kayıt ekleyin. Hepsinde bulut simgesi **turuncu (Proxied)** olsun:

   | Type | Name | Content |
   |------|------|---------|
   | A | `@` | SUNUCU_IP_ADRESI |
   | A | `www` | SUNUCU_IP_ADRESI |
   | A | `*` | SUNUCU_IP_ADRESI |

   `*` kaydı hem `panel.qrmeny.com` adresini hem de her işletmenin `kafeadi.qrmeny.com` adresini otomatik çalıştırır; işletme başına ayrı DNS kaydı açmanız gerekmez.

4. **SSL/TLS → Overview** → modu **Full** yapın. (**Flexible** kullanmayın.)
5. **SSL/TLS → Edge Certificates** → **Always Use HTTPS** açık olsun.

Artık `https://qrmeny.com` tanıtım sitesini, `https://panel.qrmeny.com` paneli açmalı.

### (Önerilen) Full (strict) için Origin sertifikası

Sunucu kurulumda kendinden imzalı bir sertifikayla gelir; **Full** modu bununla çalışır. Daha sıkı güvenlik için:

1. Cloudflare → **SSL/TLS → Origin Server → Create Certificate** → varsayılanlar (`qrmeny.com` ve `*.qrmeny.com`, 15 yıl) → **Create**.
2. Sunucuda iki dosya oluşturup Cloudflare'in gösterdiği metinleri yapıştırın:

   ```bash
   nano /opt/qrmenu/certs/origin.pem   # "Origin Certificate" metni
   nano /opt/qrmenu/certs/origin.key   # "Private Key" metni
   chmod 600 /opt/qrmenu/certs/origin.key
   docker compose restart web
   ```

3. Cloudflare'de SSL modunu **Full (strict)** yapın.

## 7. Test

1. `https://qrmeny.com` → tanıtım sitesi açılmalı; "Ücretsiz dene" butonu panelin kayıt sayfasına gitmeli.
2. `https://panel.qrmeny.com/login` → süper admin ile giriş yapın; `/admin` paneli açılmalı.
3. Çıkış yapıp kayıt sayfasından deneme bir işletme açın, kategori ve fotoğraflı ürün ekleyin.
4. **Ayarlar → Menü Adresi** alanında işletmenin adresini görün/değiştirin (örn. `denizkafe`).
5. **QR Kod** sayfasındaki QR'ı telefonla okutun; `https://denizkafe.qrmeny.com` açılmalı.

## 8. Tanıtım sitesini düzenleme

Tanıtım sitesi `landing/index.html` dosyasıdır. Yayına almadan önce şunları kendinize göre değiştirin:

- İletişim e-postası: dosyada `iletisim@qrmeny.com` geçen tüm yerler.
- Fiyat: `999 ₺` ve "Ayda yaklaşık 83 ₺" metinleri ile en üstteki `"price": "999"` satırı.

Tanıtım sitesindeki değişiklikler için derleme gerekmez: dosyayı GitHub'da güncelleyip sunucuda `git pull` yapmanız yeterli.

## 9. Otomatik yedek

Hetzner yedeği tüm sunucuyu kapsar. Ek olarak veritabanı ve görsellerin her gece ayrı yedeğini almak için:

```bash
crontab -e
```

En alta şunu ekleyin:

```
0 3 * * * /opt/qrmenu/scripts/yedekle.sh >> /var/log/qrmenu-yedek.log 2>&1
```

Yedekler `/opt/qrmenu-yedek` klasöründe tutulur, 14 günden eskiler silinir.
Elle yedek almak için: `/opt/qrmenu/scripts/yedekle.sh`

## 10. Güncelleme

GitHub'a yeni kod gönderdikten sonra sunucuda:

```bash
cd /opt/qrmenu
git pull
docker compose up -d --build
```

Veritabanı ve görseller Docker volume'larında durduğu için güncellemede silinmez.

## Sorun giderme

| Durum | Komut |
|---|---|
| Backend hataları | `docker compose logs -f backend` |
| Nginx / sayfa açılmıyor | `docker compose logs -f web` |
| Her şeyi yeniden başlat | `docker compose restart` |
| Durumu gör | `docker compose ps` |

- **Backend sürekli yeniden başlıyor:** büyük ihtimalle `.env` içinde `JWT_SECRET_KEY` veya `SUPER_ADMIN_EMAIL` eksik; loglarda Türkçe açıklama görünür.
- **Cloudflare "Error 521":** sunucu kapalı ya da 80/443 portları firewall'da kapalı.
- **Cloudflare "Error 525/526":** SSL modu yanlış. Origin sertifikası koymadıysanız mod **Full** olmalı, **Full (strict)** değil.
- **İşletme adresi (`kafeadi.qrmeny.com`) panel giriş sayfasını açıyor:** `.env` içindeki `MENU_DOMAIN` yanlış ya da değiştirildikten sonra `docker compose up -d --build` çalıştırılmadı.
- **`qrmeny.com` tanıtım sitesi yerine paneli açıyor:** `MENU_DOMAIN` değeri `www` ile yazılmış olabilir; `qrmeny.com` olmalı.

## Bilinen eksik: online ödeme

Stripe entegrasyonu kaldırıldı. Abonelik butonuna basan işletmeye "bizimle iletişime geçin" mesajı gösterilir.
Ödemeyi aldıktan sonra süper admin panelinden işletmeye lisans tanımlayın. PayTR/iyzico entegrasyonu sonraki adımdır.
