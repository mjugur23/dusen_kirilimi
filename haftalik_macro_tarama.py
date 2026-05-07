import os
import requests
import yfinance as yf
import pandas as pd
import json
import warnings

warnings.filterwarnings('ignore')

# --- AYARLAR ---
TOKEN = "8729990107:AAHyGbQjcbORktI_h046N0QVUg_d17iTy6g"
CHAT_ID = "5886003690"
MEMORY_FILE = "haftalik_hafiza.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                content = f.read().strip()
                return json.loads(content) if content else {}
        except: return {}
    return {}

def save_memory(memory):
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory, f)
    except: print("Hafiza yazilamadi!")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=20)
    except: print("Telegram hatasi!")

def check_düşen_haftalik(df):
    if len(df) < 40: return None
    highs = df['High'].values
    closes = df['Close'].values
    window = 5
    pivots = []
    
    for i in range(window, len(highs)-window):
        if highs[i] == max(highs[i-window:i+window+1]):
            if not pivots or i - pivots[-1] >= 3:
                pivots.append(i)
                
    if len(pivots) < 2: return None
    
    p1, p2 = pivots[-2], pivots[-1]
    if highs[p1] <= highs[p2]: return None
    
    m = (highs[p2] - highs[p1]) / (p2 - p1)
    b = highs[p1] - m * p1
    
    curr_idx = len(highs) - 1
    cizgi_bugun = m * curr_idx + b
    cizgi_gecen_hafta = m * (curr_idx - 1) + b
    curr_close = closes[curr_idx]
    
    # 1. KIRILIM DURUMU
    if curr_close > cizgi_bugun and closes[curr_idx-1] <= cizgi_gecen_hafta:
        return "KIRDI", round(curr_close, 2), round(cizgi_bugun, 2)
    # 2. YAKIN DURUMU (%3 Marj)
    elif curr_close <= cizgi_bugun and curr_close >= (cizgi_bugun * 0.97):
        return "YAKIN", round(curr_close, 2), round(cizgi_bugun, 2)
        
    return None

def check_turtle_haftalik(df):
    if len(df) < 22: return None
    donchian_high = df['High'].iloc[-21:-1].max()
    current_close = df['Close'].iloc[-1]
    
    # 1. KIRILIM DURUMU
    if current_close > donchian_high:
        return "KIRDI", round(current_close, 2), round(donchian_high, 2)
    # 2. YAKIN DURUMU (%3 Marj)
    elif current_close <= donchian_high and current_close >= (donchian_high * 0.97):
        return "YAKIN", round(current_close, 2), round(donchian_high, 2)
        
    return None

def main():
    print("--- PROGRAM BASLADI ---")
    TICKERS = ["THYAO","ASELS","ISCTR","AKBNK","YKBNK","KCHOL","TUPRS","TRALT","SASA","ASTOR","GARAN","PGSUS","EREGL","BIMAS","SAHOL","EKGYO","TCELL","SISE","HALKB","PEKGY","KTLEV","ATATR","TERA","TEHOL","MGROS","FROTO","NETCD","DSTKF","KRDMD","VAKBN","TTKOM","CVKMD","PETKM","GUBRF","DOFRB","TOASO","AEFES","PAHOL","BRSAN","PASEU","MEYSU","KLRHO","ENKAI","CANTE","SARKY","CWENE","IEYHO","ALARK","MANAS","TRMET","TAVHL","KONTR","ULKER","AKHAN","UCAYM","MEGMT","MARMR","EMPAE","MIATK","BTCIM","KUYAS","ADESE","ALVES","ZERGY","ARFYE","BESTE","FRMPL","FENER","CIMSA","TURSG","OYAKC","ALTNY","EUREN","SMRVA","AKSEN","HEDEF","OTKAR","ECILC","DOAS","CCOLA","TSKB","TUKAS","PSGYO","HEKTS","HDFGS","BINHO","OBAMS","SDTTR","ARCLK","EUPWR","SKBNK","BULGS","VAKFA","KATMR","PATEK","QUAGR","ODAS","GSRAY","ZGYO","ISMEN","BERA","ECOGR","TKFEN","ESEN","SURGY","BSOKE","BMSTL","GENKM","SVGYO","PAPIL","TRENJ","GENIL","DAPGM","MAVI","GZNMI","YEOTK","MAGEN","SOKM","GLRMK","GIPTA","ODINE","IZENR","BRYAT","EFOR","ALKLC","MPARK","IHLAS","GESAN","MOPAS","VAKFN","FONET","SEGMN","A1CAP","ISGSY","GUNDG","EDATA","ISKPL","HLGYO","FORMT","RALYH","DOHOL","VSNMD","PRKAB","AKFIS","KBORU","TCKRC","ENJSA","AKCNS","EMKEL","ESCOM","TSPOR","ANSGR","ALBRK","AKSA","ZOREN","ATATP","CEMAS","LYDHO","KLGYO","TRHOL","TABGD","TATEN","LILAK","CEMZY","FORTE","IZFAS","LINK","GEREL","ONCSM","ARDYZ","YYAPI","AYGAZ","RGYAS","USAK","BAHKM","ENERY","ESCAR","BURCE","DERHL","RYSAS","MEKAG","KCAER","IMASM","AGHOL","KAYSE","KZBGY","GRSEL","ARSAN","LMKDC","TTRAK","ECZYT","AHGAZ","KARSN","ALGYO","TUREX","CGCAM","POLTK","TMPOL","VESTL","MRGYO","GRTHO","BALSU","ENTRA","KLYPV","RUBNS","GWIND","INFO","AKFYE","SAFKR","TEKTU","SNGYO","ANHYT","SELVA","FZLGY","REEDR","YYLGD","ALKA","FRIGO","ERCB","OZATD","ISDMR","ENSRI","SMART","LOGO","BMSCH","GOKNR","CLEBI","DITAS","YAPRK","MERCN","KRDMA","BORLS","TRGYO","GENTS","RTALB","SEGYO","TARKM","ADGYO","SRVGY","MERKO","DURKN","SMRTG","BINBN","AYDEM","BLUME","MOGAN","EGEEN","AGROT","DMRGD","VKGYO","TNZTP","ARMGD","NTGAZ","GMTAS","BRKVY","AKGRT","TUCLK","LIDER","RUZYE","IHAAS","AVOD","DCTTR","EKOS","OTTO","TMSN","RYGYO","GLYHO","ADEL","LYDYE","TKNSA","BVSAN","BAGFS","KLKIM","KAPLM","MAKTK","MOBTL","BARMA","SELEC","AGESA","ONRYT","BORSK","PRKME","DOFER","PNLSN","EGGUB","EGEGY","YUNSA","PKENT","ICUGS","NATEN","LRSHO"]
    
    memory = load_memory()
    
    # Gruplama Listeleri
    turtle_kiranlar = []
    turtle_yaklasanlar = []
    dusen_kiranlar = []
    dusen_yaklasanlar = []
    
    print(f"{len(TICKERS)} adet hisse taranmaya basliyor...")
    
    for ticker in TICKERS:
        try:
            df = yf.download(f"{ticker}.IS", period="5y", interval="1wk", progress=False)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            # --- DÜŞEN KONTROLÜ ---
            dusen_sonuc = check_düşen_haftalik(df)
            if dusen_sonuc:
                durum, fiyat, direnc = dusen_sonuc
                if durum == "KIRDI" and memory.get(f"{ticker}_D") != "KIRDI":
                    dusen_kiranlar.append(f"🔹 *{ticker}* (Fiyat: {fiyat} / Direnç: {direnc})")
                    memory[f"{ticker}_D"] = "KIRDI"
                elif durum == "YAKIN" and f"{ticker}_D" not in memory:
                    dusen_yaklasanlar.append(f"🔸 *{ticker}* (Fiyat: {fiyat} / Direnç: {direnc})")
                    memory[f"{ticker}_D"] = "YAKIN"
            
            # --- TURTLE KONTROLÜ ---
            turtle_sonuc = check_turtle_haftalik(df)
            if turtle_sonuc:
                durum, fiyat, zirve = turtle_sonuc
                if durum == "KIRDI" and memory.get(f"{ticker}_T") != "KIRDI":
                    turtle_kiranlar.append(f"🔹 *{ticker}* (Fiyat: {fiyat} / Zirve: {zirve})")
                    memory[f"{ticker}_T"] = "KIRDI"
                elif durum == "YAKIN" and f"{ticker}_T" not in memory:
                    turtle_yaklasanlar.append(f"🔸 *{ticker}* (Fiyat: {fiyat} / Zirve: {zirve})")
                    memory[f"{ticker}_T"] = "YAKIN"
                    
        except Exception as e:
            continue
        
    # --- RAPOR OLUŞTURMA ---
    if turtle_kiranlar or turtle_yaklasanlar or dusen_kiranlar or dusen_yaklasanlar:
        rapor = "🗓️ *HAFTALIK MACRO TARAMA RAPORU*\n\n"
        
        if turtle_kiranlar:
            rapor += "🐢 *TURTLE AL VERENLER*\n" + "\n".join(turtle_kiranlar) + "\n\n"
        if turtle_yaklasanlar:
            rapor += "⏳ *TURTLE KIRILIMINA YAKIN OLANLAR (%3)*\n" + "\n".join(turtle_yaklasanlar) + "\n\n"
        if dusen_kiranlar:
            rapor += "📉 *DÜŞEN KIRILIMI YAPANLAR*\n" + "\n".join(dusen_kiranlar) + "\n\n"
        if dusen_yaklasanlar:
            rapor += "👀 *DÜŞEN KIRILIMINA YAKIN OLANLAR (%3)*\n" + "\n".join(dusen_yaklasanlar) + "\n"
            
        send_telegram_message(rapor)
        save_memory(memory)
        print("Telegram mesajlari gonderildi.")
    else:
        print("Yeni haftalik sinyal yok.")

if __name__ == "__main__":
    main()
