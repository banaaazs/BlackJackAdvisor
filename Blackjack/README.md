# 🃏 Blackjack Strategy Advisor

Két különálló eszköz — használhatod bármelyiket:

---

## 1. `blackjack_advisor.html` — Standalone böngésző app

Egyszerűen nyisd meg dupla kattintással. Semmi telepítés nem kell.

**Funkciók:**
- Lapkiválasztó kártyával (kattintható)
- Azonnali stratégia javaslat: Hit / Stand / Double / Split / Surrender
- Kemény, puha és pár-kezek teljes stratégiája
- Hi-Lo kártyaszámlálás (running count + true count)
- Döntési napló
- Teljes referencia táblázat (kiemelve az aktuális szituáció)
- Billentyűparancsok: `P` = saját lap, `D` = dealer, `N` = új kéz, `R` = reset, `Enter` = rögzít

---

## 2. `blackjack_overlay.py` — Python overlay (mindig felül)

Valós idejű, átlátszó ablak ami mindig a többi ablak felett marad. Manuális és automatikus (OCR) módban is működik.

### Telepítés

**1. Python 3.8+ szükséges**

```bash
pip install -r requirements.txt
```

**2. Tesseract OCR (opcionális, auto módhoz)**

| Platform | Parancs |
|----------|---------|
| macOS    | `brew install tesseract` |
| Ubuntu   | `sudo apt install tesseract-ocr` |
| Windows  | [Letöltés](https://github.com/UB-Mannheim/tesseract/wiki) |

### Indítás

```bash
python3 blackjack_overlay.py
```

Windows:
```bash
python blackjack_overlay.py
```

### Billentyűparancsok

| Gomb | Funkció |
|------|---------|
| `N`  | Új kéz (lapok törlése) |
| `R`  | Teljes reset (count is) |
| `Q` / `Esc` | Kilépés |

### Manuális mód (mindig elérhető)

1. Válaszd a **"Saját lap"** vagy **"Dealer"** rádiógombot
2. Kattints a lapokra alul (A, 2–9, 10, J, Q, K)
3. A stratégia azonnal megjelenik felül

### Auto mód (Tesseract szükséges)

Ha a Tesseract telepítve van, megjelenik az **"Auto OFF"** gomb.
Kattints rá → **"Auto ON"** — a program 2 másodpercenként figyeli a képernyőt
és automatikusan frissíti a stratégiát.

> ⚠️ **Megjegyzés:** Az auto mód legjobban online kaszinó szoftvereken működik
> ahol a lapok számai tisztán láthatóak a képernyőn. A pontosság függ a
> kaszinó grafikai stílusától.

---

## Stratégia magyarázat

Az alkalmazás a **Las Vegas Strip alapstratégiát** használja (6 pakli, dealer S17).

| Jelzés | Magyar | Leírás |
|--------|--------|--------|
| **H** | Hit | Húzz még egy lapot |
| **S** | Stand | Megállsz |
| **D** | Double Down | Duplázd a tétet, pontosan 1 lap |
| **P** | Split | Osztd ketté a párt |
| **R** | Surrender | Add fel — kapsz vissza a tét felét |

### Hi-Lo kártyaszámlálás

| Lapok | Érték |
|-------|-------|
| 2–6   | +1    |
| 7–9   | 0     |
| 10–A  | −1    |

- **Running count** = eddig látott lapok összege
- **True count** = Running count / maradék pakliszám
- Magas pozitív true count → játékosnak kedvez

---

## Felelős játék

Ez az eszköz kizárólag **oktatási és szórakoztatási célra** készült.
Az alapstratégia csökkenti a house edge-t ~0.5%-ra, de nem garantál nyereményt.
Kérjük, felelősen játssz. 🙏
