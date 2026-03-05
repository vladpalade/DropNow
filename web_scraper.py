from playwright.sync_api import sync_playwright
import time
import re

# Regex (Regular Expressions): Unstructured Data Parsing
# Aceasta functie este un normalizator. Ia texte haotice ("50pcs", "Set de 50", "Pachet 50 bucati")
# si extrage cu precizie matematica o valoare INT (Integer) pentru a putea face calcule financiare.
def extrage_cantitate(text, sursa_debug=""):
    if not text:
        return 1
    t = text.lower()
    
    # Prinde: "50pcs", "50 buc", "50 pieces", "50x", "50 pack"
    matches1 = re.findall(r'(\d+)\s*(?:pcs|buc|bucati|pieces|x\b|pack|set|role)', t)
    # Prinde: "set 50", "set de 50", "pachet 50"
    matches2 = re.findall(r'(?:set|pachet)\s*(?:de\s*)?(\d+)', t)
    
    toate_numerele = [int(m) for m in matches1 + matches2 if 0 < int(m) < 5000]
    
    cantitate = max(toate_numerele) if toate_numerele else 1
    
    return cantitate 

def curata_pret_aliexpress(text_pret):
    if not text_pret: 
        return 0.0
    match = re.search(r'(\d+)[.,](\d+)', text_pret)
    if match: 
        return float(f"{match.group(1)}.{match.group(2)}")
    match = re.search(r'\d+', text_pret)
    if match: 
        return float(match.group(0))
    return 0.0

def curata_pret_emag(text_pret):
    if not text_pret: 
        return 0.0
    cifre = re.sub(r'[^\d]', '', text_pret)
    if len(cifre) >= 3: 
        return float(cifre[:-2] + "." + cifre[-2:])
    elif cifre: 
        return float(cifre)
    return 0.0

# Motor de traducere si keyword generation pentru cautare pe eMAG
def genereaza_cuvinte_emag(titlu):
    titlu_low = titlu.lower()
    rezultat = []
    dictionar = {
        "charger": "incarcator", "cable": "cablu", "case": "husa", "cover": "husa",
        "earphone": "casti", "headphone": "casti", "watch": "smartwatch",
        "strap": "curea", "glass": "folie sticla", "holder": "suport telefon",
        "stand": "suport", "light": "lampa", "sponge": "burete vase", "trimmer": "aparat tuns",
        "cleaning": "curatare"
    }
    for eng, ro in dictionar.items():
        if eng in titlu_low: 
            rezultat.append(ro); 
            break
    if "iphone" in titlu_low: 
        rezultat.append("iphone")
    elif "samsung" in titlu_low: 
        rezultat.append("samsung")
    elif "xiaomi" in titlu_low: 
        rezultat.append("xiaomi")
    match_w = re.search(r'\b(\d+w)\b', titlu_low)

    if match_w: 
        rezultat.append(match_w.group(1))
    if "type c" in titlu_low or "usb-c" in titlu_low: 
        rezultat.append("type c")
    if not rezultat:
        cuvinte = titlu.split()
        return " ".join(cuvinte[1:4]) if len(cuvinte) > 3 else titlu[:20]
    return " ".join(rezultat)

def extrage_recenzii(url_produs):
    with sync_playwright() as p:
        # Lansam un browser invizibil, nu consuma resurse pentru interfata grafica
        browser = p.chromium.launch(headless=True, args=["--start-maximized"])
        context = browser.new_context(
            # Deghizare Anti-Blocare drept User
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            no_viewport=True, locale="en-US"
        )
        pagina = context.new_page()

        try:
            pagina.goto(url_produs, timeout=30000, wait_until="domcontentloaded")
            time.sleep(3)
        except: 
            return {"titlu": "Produs Necunoscut", "recenzii": [], "cantitate": 1, "pret_ali": 0.0, "transport": 0.0, "pret_emag": 0.0, "link_emag": ""}

        # Extragem textul RAW
        titlu_produs = pagina.title().split('|')[0].strip()
        if not titlu_produs: titlu_produs = "Produs AliExpress"
        
        text_pentru_cantitate = titlu_produs
        try:
            # Clasele CSS cu cuvantul 'sku' sunt de obicei zonele unde apar mărimile, culorile sau cantitățile
            elemente_sku = pagina.locator('[class*="sku"]').all_inner_texts()
            text_pentru_cantitate += " " + " ".join(elemente_sku)
        except: pass
        
        cantitate_ali = extrage_cantitate(text_pentru_cantitate, "AliExpress")

        # Cautare pret folosind selectori CSS 
        pret_ali_numar = 0.0
        try:
            pret_ali_text = pagina.locator('.product-price-value, span[class*="price"]').first.inner_text(timeout=3000)
            pret_ali_numar = curata_pret_aliexpress(pret_ali_text)
        except: pass

        # UI Bypass: Inchidem cookie-uri si reclamele
        try: pagina.locator('.next-dialog-close, [aria-label="Close"]').first.click(timeout=2000)
        except: pass

        try: pagina.locator("button", has_text="Accept cookies").first.click(timeout=2000)
        except: pass

        # Cautare buton "VIEW MORE", pentru a extrage numarul dorit de recenzii
        modal_deschis = False
        for i in range(8):
            pagina.mouse.wheel(0, 600)
            time.sleep(1.5)
            buton = pagina.locator("text='View All'").first
            if not buton.is_visible(): buton = pagina.locator("text='View more'").first
            if buton.is_visible():
                try:
                    buton.click(timeout=3000)
                    time.sleep(3)
                    modal_deschis = True
                    break
                except: pass

        # Extragere Recenzii
        extrase = []
        if modal_deschis:
            try:
                fereastra = pagina.locator('[role="dialog"], .comet-modal, .next-dialog').last
                fereastra.wait_for(state="visible", timeout=3000)
                box = fereastra.bounding_box()
                pagina.mouse.click(box['x'] + (box['width'] / 2), box['y'] + (box['height'] / 2))
            except: pass

            time.sleep(1)
            
            for j in range(25): 
                pagina.mouse.wheel(0, 1500)
                time.sleep(1.2)

            tot_textul = pagina.locator("body").inner_text()
            linii = tot_textul.split('\n')
            
            # Scoatem textele irelevante
            gunoaie_ui = ["color:", "helpful", "reviews |", "all from verified", "sort by", "stars", "aliexpress", "customer reviews", "cookie", "technologies", "personalise", "personalize", "advertisement", "privacy", "ads", "marketing"]
            gunoaie_livrare = ["shipping", "delivery", "arrived", "packaging", "box", "courier", "packed", "fast service", "post office", "tracking"]

            for linie in linii:
                linie = linie.strip()
                if len(linie) > 20:
                    este_curat = True
                    linie_low = linie.lower()
                    for g in gunoaie_ui:
                        if g in linie_low: 
                            este_curat = False
                            break
                    if este_curat:
                        for c in gunoaie_livrare:
                            if c in linie_low: 
                                este_curat = False
                                break
                    if "***" in linie and "|" in linie: 
                        este_curat = False
                    if este_curat and linie not in extrase: 
                        extrase.append(linie)

            if len(extrase) > 1: 
                extrase.pop(0)
        
        pret_emag_estimat = 0.0
        link_competitor = ""

        # Market Arbitrage pe eMAG
        # Cautam produsul pe piata locala, extragem rezultatele si facem scalarea preturilor per unitate
        try:
            cautare_inteligenta = genereaza_cuvinte_emag(titlu_produs)
            
            url_emag = f"https://www.emag.ro/search/{cautare_inteligenta.replace(' ', '%20')}"
            pagina_emag = context.new_page()
            pagina_emag.goto(url_emag, timeout=15000)
            carduri = pagina_emag.locator('.card-v2').all()[:15] 
            
            preturi_normalizate = []
            
            for i, card in enumerate(carduri):
                try:
                    # Selectam titlul si pretul pentru fiecare card (produs) gasit
                    element_titlu = card.locator('.card-v2-title')
                    if element_titlu.is_visible():
                        titlu_emag = element_titlu.first.inner_text().strip()
                        link_emag = element_titlu.first.get_attribute('href')
                    else:
                        titlu_emag = card.locator('h2 a').first.inner_text().strip()
                        link_emag = card.locator('h2 a').first.get_attribute('href')
                        
                    pret_text = card.locator('.product-new-price').first.inner_text()
                    
                    cantitate_emag = extrage_cantitate(titlu_emag, f"eMAG Item {i+1}")
                    pret_brut = curata_pret_emag(pret_text)
                    
                    if pret_brut > 0:
                        # Comparam cantitati egale
                        pret_unitar = pret_brut / cantitate_emag
                        pret_echivalent = pret_unitar * cantitate_ali
                        
                        preturi_normalizate.append({
                            "pret_unitar": pret_unitar,
                            "pret_echivalent": pret_echivalent,
                            "link": link_emag
                        })
                except: pass
            
            if preturi_normalizate:
                preturi_normalizate.sort(key=lambda x: x["pret_unitar"])
                # Pastram adresa principalului competitor pe piata
                link_competitor = preturi_normalizate[0]["link"]
                                
                if len(preturi_normalizate) >= 5:
                    preturi_normalizate = preturi_normalizate[:-2]
                
                jumatate = max(1, len(preturi_normalizate) // 2)
                preturi_ieftine = preturi_normalizate[:jumatate]
                # Calculam media pietei pe zona de produse accesibile
                pret_emag_estimat = sum(p["pret_echivalent"] for p in preturi_ieftine) / len(preturi_ieftine)
                
            pagina_emag.close()
        except : pass

        
        return {
            "titlu": titlu_produs, 
            "recenzii": extrase[:200], 
            "cantitate": cantitate_ali,
            "pret_ali": pret_ali_numar,
            "pret_emag": pret_emag_estimat, 
            "link_emag": link_competitor
        }