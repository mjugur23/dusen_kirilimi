import os
import requests
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.signal import argrelextrema
import warnings

warnings.filterwarnings('ignore')

# --- TELEGRAM AYARLARI ---
TOKEN = os.environ.get("8625940807:AAE_bsrBsj7lojRv6Dhbq0uJjY_kaz7RwMo")
CHAT_ID = os.environ.get("5886003690")
MEMORY_FILE = "dusen_hafiza.json

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot8625940807:AAE_bsrBsj7lojRv6Dhbq0uJjY_kaz7RwMo/sendMessage"
    payload = {"chat_id": 5886003690, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram hatası: {e}")

# --- YENİ VE AKILLI DÜŞEN KIRILIM MOTORU ---
def find_downtrend_breakout(df, window=5, min_distance=10):
    """
    Gerçek (Macro) düşen trend kırılımlarını bulur. 
    İhlal edilmiş sahte çizgileri kesinlikle eler.
    """
    if df is None or len(df) < 30:
        return False, {}
        
    high_col = 'High' if 'High' in df.columns else 'high'
    close_col = 'Close' if 'Close' in df.columns else 'close'
    
    highs = df[high_col].values
    closes = df[close_col].values
    dates = df.index
    
    # 1. Gerçek Tepeleri (Pivot Highs) Bul
    pivot_indices = []
    for i in range(window, len(highs) - window):
        if highs[i] == max(highs[i - window : i + window + 1]):
            if not pivot_indices or i - pivot_indices[-1] >= 3:
                pivot_indices.append(i)

    if len(pivot_indices) < 2:
        return False, {}

    current_idx = len(highs) - 1
    current_close = closes[current_idx]
    prev_close = closes[current_idx - 1]

    # 2. Tepeleri sondan başa doğru tara
    for i in range(len(pivot_indices) - 2, -1, -1):
        for j in range(len(pivot_indices) - 1, i, -1):
            p1_idx = pivot_indices[i]
            p2_idx = pivot_indices[j]

            if p2_idx - p1_idx < min_distance:
                continue

            p1_high = highs[p1_idx]
            p2_high = highs[p2_idx]

            if p1_high <= p2_high:
                continue

            m = (p2_high - p1_high) / (p2_idx - p1_idx)
            b = p1_high - m * p1_idx

            # 3. İHLAL KONTROLÜ (Fiyat çizgiyi önceden kesmiş mi?)
            ihlal_var = False
            for k in range(p1_idx + 1, current_idx): 
                cizgi_degeri = m * k + b
                if highs[k] > cizgi_degeri: 
                    ihlal_var = True
                    break

            if ihlal_var:
                continue

            # 4. KIRILIM KONTROLÜ
            cizgi_dun = m * (current_idx - 1) + b
            cizgi_bugun = m * current_idx + b

            if prev_close <= cizgi_dun and current_close > cizgi_bugun:
                # Kırılım bugünkü fiyatı, birinci tepenin fiyatını çoktan geçmişse bayat kırılımdır
                if current_close > (p1_high * 1.05):
                     continue

                details = {
                    "1. Tepe Tarihi": dates[p1_idx].strftime('%Y-%m-%d'),
                    "1. Tepe Fiyatı": round(p1_high, 2),
                    "2. Tepe Tarihi": dates[p2_idx].strftime('%Y-%m-%d'),
                    "2. Tepe Fiyatı": round(p2_high, 2),
                    "Kırılım Fiyatı": round(current_close, 2),
                    "Direnç Sınırı": round(cizgi_bugun, 2)
                }
                return True, details

    return False, {}

def main():
    # Tarama yapılacak BIST100 hisseleri
    TICKERS = [
       "THYAO","ASELS","ISCTR","AKBNK","YKBNK","KCHOL","TUPRS","TRALT","SASA","ASTOR", 
       "GARAN","PGSUS","EREGL","BIMAS","SAHOL","EKGYO","TCELL","SISE","HALKB","PEKGY",
       "KTLEV","ATATR","TERA","TEHOL","MGROS","FROTO","NETCD","DSTKF","KRDMD","VAKBN",
       "TTKOM","CVKMD","PETKM","GUBRF","DOFRB","TOASO","AEFES","PAHOL","BRSAN","PASEU",
       "MEYSU","KLRHO","ENKAI","CANTE","SARKY","CWENE","IEYHO","ALARK","MANAS","TRMET",
       "TAVHL","KONTR","ULKER","AKHAN","UCAYM","MEGMT","MARMR","EMPAE","MIATK","BTCIM",
       "KUYAS","ADESE","ALVES","ZERGY","ARFYE","BESTE","FRMPL","FENER","CIMSA","TURSG",
       "OYAKC","ALTNY","EUREN","SMRVA","AKSEN","HEDEF","OTKAR","ECILC","DOAS","CCOLA",
       "TSKB","TUKAS","PSGYO","HEKTS","HDFGS","BINHO","OBAMS","SDTTR","ARCLK","EUPWR",
       "SKBNK","BULGS","VAKFA","KATMR","PATEK","QUAGR","ODAS","GSRAY","ZGYO","ISMEN",
       "BERA","ECOGR","TKFEN","ESEN","SURGY","BSOKE","BMSTL","GENKM","SVGYO","PAPIL",
       "TRENJ","GENIL","DAPGM","MAVI","GZNMI","YEOTK","MAGEN","SOKM","GLRMK","GIPTA",
       "ODINE","IZENR","BRYAT","EFOR","ALKLC","MPARK","IHLAS","GESAN","MOPAS","VAKFN",
       "FONET","SEGMN","A1CAP","ISGSY","GUNDG","EDATA","ISKPL","HLGYO","FORMT","RALYH",
       "DOHOL","VSNMD","PRKAB","AKFIS","KBORU","TCKRC","ENJSA","AKCNS","EMKEL","ESCOM",
       "TSPOR","ANSGR","ALBRK","AKSA","ZOREN","ATATP","CEMAS","LYDHO","KLGYO","TRHOL",
       "TABGD","TATEN","LILAK","CEMZY","FORTE","IZFAS","LINK","GEREL","ONCSM","ARDYZ",
       "YYAPI","AYGAZ","RGYAS","USAK","BAHKM","ENERY","ESCAR","BURCE","DERHL","RYSAS",
       "MEKAG","KCAER","IMASM","AGHOL","KAYSE","KZBGY","GRSEL","ARSAN","LMKDC","TTRAK",
       "ECZYT","AHGAZ","KARSN","ALGYO","TUREX","CGCAM","POLTK","TMPOL","VESTL","MRGYO",
       "GRTHO","BALSU","ENTRA","KLYPV","RUBNS","GWIND","INFO","AKFYE","SAFKR","TEKTU",
       "SNGYO","ANHYT","SELVA","FZLGY","REEDR","YYLGD","ALKA","FRIGO","ERCB","OZATD",
       "ISDMR","ENSRI","SMART","LOGO","BMSCH","GOKNR","CLEBI","DITAS","YAPRK","MERCN",
       "KRDMA","BORLS","TRGYO","GENTS","RTALB","SEGYO","TARKM","ADGYO","SRVGY","MERKO",
       "DURKN","SMRTG","BINBN","AYDEM","BLUME","MOGAN","EGEEN","AGROT","DMRGD","VKGYO",
       "TNZTP","ARMGD","NTGAZ","GMTAS","BRKVY","AKGRT","TUCLK","LIDER","RUZYE","IHAAS",
       "AVOD","DCTTR","EKOS","OTTO","TMSN","RYGYO","GLYHO","ADEL","LYDYE","TKNSA",
       "BVSAN","BAGFS","KLKIM","KAPLM","MAKTK","MOBTL","BARMA","SELEC","AGESA","ONRYT",
       "BORSK","PRKME","DOFER","PNLSN","EGGUB","EGEGY","YUNSA","PKENT","ICUGS","NATEN",
       "LRSHO"
    ]
    
    bulunanlar = []
    print("Düşen Kırılım Taraması Başlıyor...")
    
    for ticker in TICKERS:
        try:
            # yfinance'den veri çekerken 6mo yeterli (yaklaşık 125 iş günü)
            df = yf.download(f"{ticker}.IS", period="6mo", progress=False)
            if df.empty: continue
            
            # MultiIndex sorununu çöz
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            is_breakout, details = find_downtrend_breakout(df)
            if is_breakout:
                mesaj = f"📉 *DÜŞEN KIRILIMI YAKALANDI!*\n"
                mesaj += f"📌 Hisse: *{ticker}*\n"
                mesaj += f"💵 Kırılım Fiyatı: {details['Kırılım Fiyatı']} TL\n"
                mesaj += f"🚧 Direnç: {details['Direnç Sınırı']} TL\n"
                bulunanlar.append(mesaj)
        except Exception as e:
            continue

    if bulunanlar:
        send_telegram_message("🔔 *Günlük Düşen Kırılım Raporu* 🔔")
        for msg in bulunanlar:
            send_telegram_message(msg)
        print(f"Tarama bitti, {len(bulunanlar)} adet hisse Telegram'a gönderildi.")
    else:
        print("Bugün net ve kurallara uygun bir düşen kırılımı bulunamadı.")

if __name__ == "__main__":
    main()

