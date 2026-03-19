import os
import requests
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.signal import argrelextrema
import warnings

warnings.filterwarnings('ignore')

# --- TELEGRAM AYARLARI ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram hatası: {e}")

# --- DÜŞEN KIRILIM FORMÜLÜ ---
def find_downtrend_breakout(df, lookback=90):
    if df is None or len(df) < lookback + 5: return False, None
    high_col = 'High' if 'High' in df.columns else 'high'
    close_col = 'Close' if 'Close' in df.columns else 'close'
    
    df_recent = df.tail(lookback).copy()
    highs, closes = df_recent[high_col].values, df_recent[close_col].values
    peaks = argrelextrema(highs, np.greater, order=5)[0]
    
    if len(peaks) < 2: return False, None
    p1_idx, p2_idx = peaks[-2], peaks[-1]
    p1_val, p2_val = highs[p1_idx], highs[p2_idx]
    
    if p2_val >= p1_val or (p2_idx - p1_idx) < 5: return False, None
        
    m = (p2_val - p1_val) / (p2_idx - p1_idx)
    b = p1_val - m * p1_idx
    last_idx, prev_idx = len(df_recent) - 1, len(df_recent) - 2
    
    trendline_today = m * last_idx + b
    trendline_yesterday = m * prev_idx + b
    
    if closes[prev_idx] <= trendline_yesterday and closes[last_idx] > trendline_today:
        if closes[last_idx] > (p1_val * 1.05): return False, None
        tarih1, tarih2 = df_recent.index[p1_idx].strftime('%Y-%m-%d'), df_recent.index[p2_idx].strftime('%Y-%m-%d')
        
        details = {
            "1. Tepe Tarihi": tarih1, "1. Tepe Fiyatı": round(p1_val, 2),
            "2. Tepe Tarihi": tarih2, "2. Tepe Fiyatı": round(p2_val, 2),
            "Kırılım Fiyatı": round(closes[last_idx], 2), "Direnç Sınırı": round(trendline_today, 2)
        }
        return True, details
    return False, None

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
            df = yf.download(f"{ticker}.IS", period="6mo", progress=False)
            if df.empty: continue
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
    else:
        print("Bugün net bir düşen kırılımı bulunamadı.")

if __name__ == "__main__":
    main()

