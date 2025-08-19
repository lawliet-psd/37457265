import requests
import json
import gzip
from io import BytesIO


def _slugify_category(name: str) -> str:
    """Kategori adını dosya adına uygun bir slug'a çevirir."""
    if not name:
        return "genel"
    # Alfasayısal dışındaki karakterleri alt çizgi yap, art arda gelenleri tekilleştir
    temp = "".join(ch if ch.isalnum() else "_" for ch in name)
    # Baştaki/sondaki ve tekrar eden alt çizgileri sadeleştir
    parts = [p for p in temp.strip("_").split("_") if p]
    slug = "_".join(parts).lower()
    return slug or "genel"

def get_canli_tv_m3u():
    """"""
    
    url = "https://core-api.kablowebtv.com/api/channels"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        "Referer": "https://tvheryerde.com",
        "Origin": "https://tvheryerde.com",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Accept-Encoding": "gzip",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbnYiOiJMSVZFIiwiaXBiIjoiMCIsImNnZCI6IjA5M2Q3MjBhLTUwMmMtNDFlZC1hODBmLTJiODE2OTg0ZmI5NSIsImNzaCI6IlRSS1NUIiwiZGN0IjoiM0VGNzUiLCJkaSI6ImE2OTliODNmLTgyNmItNGQ5OS05MzYxLWM4YTMxMzIxOGQ0NiIsInNnZCI6Ijg5NzQxZmVjLTFkMzMtNGMwMC1hZmNkLTNmZGFmZTBiNmEyZCIsInNwZ2QiOiIxNTJiZDUzOS02MjIwLTQ0MjctYTkxNS1iZjRiZDA2OGQ3ZTgiLCJpY2giOiIwIiwiaWRtIjoiMCIsImlhIjoiOjpmZmZmOjEwLjAuMC4yMDYiLCJhcHYiOiIxLjAuMCIsImFibiI6IjEwMDAiLCJuYmYiOjE3NDUxNTI4MjUsImV4cCI6MTc0NTE1Mjg4NSwiaWF0IjoxNzQ1MTUyODI1fQ.OSlafRMxef4EjHG5t6TqfAQC7y05IiQjwwgf6yMUS9E"  # Güvenlik için normalde token burada gösterilmemeli
    }
    
    try:
        print("📡 CanliTV API'den veri alınıyor...")
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        try:
            with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
                content = gz.read().decode('utf-8')
        except:
            content = response.content.decode('utf-8')
        
        data = json.loads(content)
        
        if not data.get('IsSucceeded') or not data.get('Data', {}).get('AllChannels'):
            print("❌ CanliTV API'den geçerli veri alınamadı!")
            return False
        
        channels = data['Data']['AllChannels']
        print(f"✅ {len(channels)} kanal bulundu")

        # Kanalları kategorilere göre grupla
        kategori_kanallar = {}
        tum_kanallar = []
        kanal_sayisi = 0
        kanal_index = 1

        for channel in channels:
            name = channel.get('Name')
            stream_data = channel.get('StreamData', {})
            hls_url = stream_data.get('HlsStreamUrl') if stream_data else None
            logo = channel.get('PrimaryLogoImageUrl', '')
            categories = channel.get('Categories', [])

            if not name or not hls_url:
                continue

            group = categories[0].get('Name', 'Genel') if categories else 'Genel'
            if group == "Bilgilendirme":
                continue

            tvg_id = str(kanal_index)
            kanal_kaydi = {
                'tvg_id': tvg_id,
                'logo': logo or '',
                'group': group,
                'name': name,
                'url': hls_url
            }

            tum_kanallar.append(kanal_kaydi)
            kategori_kanallar.setdefault(group, []).append(kanal_kaydi)

            kanal_sayisi += 1
            kanal_index += 1

        # Tüm kanalların birleşik dosyası (geriye dönük uyumluluk)
        with open("kablo.m3u", "w", encoding="utf-8") as f_all:
            f_all.write("#EXTM3U\n")
            for k in tum_kanallar:
                f_all.write(f'#EXTINF:-1 tvg-id="{k["tvg_id"]}" tvg-logo="{k["logo"]}" group-title="{k["group"]}",{k["name"]}\n')
                f_all.write(f'{k["url"]}\n')

        # Her kategori için ayrı dosya
        kategori_dosya_sayisi = 0
        for group, kayitlar in kategori_kanallar.items():
            slug = _slugify_category(group)
            dosya_adi = f"kablo_{slug}.m3u"
            with open(dosya_adi, "w", encoding="utf-8") as f_cat:
                f_cat.write("#EXTM3U\n")
                for k in kayitlar:
                    f_cat.write(f'#EXTINF:-1 tvg-id="{k["tvg_id"]}" tvg-logo="{k["logo"]}" group-title="{k["group"]}",{k["name"]}\n')
                    f_cat.write(f'{k["url"]}\n')
            kategori_dosya_sayisi += 1

        print(f"📁 {kategori_dosya_sayisi} kategori için ayrı M3U oluşturuldu")
        print(f"📺 kablo.m3u (toplam {kanal_sayisi} kanal) güncellendi")
        return True
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False

if __name__ == "__main__":
    get_canli_tv_m3u()
          
