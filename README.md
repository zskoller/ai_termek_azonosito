# Mesterséges intelligencia alapú termékazonosító és beszerzéstámogató webalkalmazás

**Szakdolgozati prototípus**  
**Szerző:** Koller Zsolt (OPWDH3)  
**Verzió:** `v1.0.0`

## 1. Projekt áttekintése
Ez a repozitórium egy elszigetelt (Docker Sandbox) környezetben futó, mikroszolgáltatás-alapú webalkalmazás forráskódját tartalmazza. A rendszer célja a sérült vagy hiányzó azonosítójú (vonalkód nélküli) kereskedelmi (COTS) hardverek képalapú, referenciaalapú vizuális azonosítása, valamint a többnyelvű (lengyel–angol) beszerzési dokumentáció automatizálása.

### Főbb funkciók
* **Referenciaalapú vizuális keresés:** Az OpenAI CLIP (`clip-ViT-B-32`, eredeti OpenAI súlyokkal) modell segítségével 512 dimenziós vektorok generálása és koszinusz-távolság alapú keresés PostgreSQL (`pgvector`) adatbázisban.
* **Hibrid izoláció (On-Premise AI):** A képfeldolgozás és a vektoros keresés 100%-ban helyben fut; a képek nem hagyják el a belső hálózatot.
* **Hibatűrő web-scraping (Fallback):** Opcionális lengyel webshop-kereső modul (`duckduckgo-search`), amely hálózati hiba vagy offline (air-gapped) mód esetén is engedi a folyamat befejezését (*Graceful Degradation*).
* **Tömeges adatimport és export:** Készletbetöltés Excel (`.xlsx`) fájlból szigorú Pydantic típusvalidációval, valamint egykattintásos angol nyelvű Excel megrendelőlap generálása.
* **Biztonság:** Állapotmentes JWT hitelesítés és szerepkör alapú hozzáférés-vezérlés (RBAC: `operator` / `admin`).

---

## 2. Technológiák és függőségek
A reprodukálhatóság érdekében a prototípus az alábbi főbb verziókkal lett tesztelve (dedikált GPU nélkül, Intel Core i5 / 16 GB RAM környezetben):

* **Python:** `3.10`
* **Backend:** `FastAPI 0.103`, `SQLAlchemy`, `Pydantic`, `Pandas`
* **AI / Embedding:** `sentence-transformers 2.2.2` (`clip-ViT-B-32`)
* **Frontend:** `Streamlit`
* **Adatbázis:** `PostgreSQL 16` + `pgvector 0.5.1` (`ankane/pgvector` Docker image)
* **Tesztelés & CI/CD:** `pytest`, `httpx`, `flake8`, `GitHub Actions`

A teljes Python függőségi lista a `requirements.txt` fájlban található.

---

## 3. Rendszerarchitektúra (Docker Compose)
A rendszer három elkülönített konténerből áll egy belső Docker Bridge hálózaton:
1. **`db_service` (Port: `5432`, csak belső hálózaton):** PostgreSQL + `pgvector` adatbázis perzisztens `pgdata` kötettel.
2. **`backend_service` (Port: `8000`):** Aszinkron FastAPI REST API és a memóriában (Singleton) betöltött CLIP modell.
3. **`frontend_service` (Port: `8501`):** Streamlit alapú grafikus felhasználói felület.

---

## 4. Telepítés és futtatás

### Előfeltételek
* Telepített **Docker** és **Docker Compose** (pl. Docker Desktop)
* Legalább 4 GB szabad RAM (az AI modell memóriába töltéséhez)

### Indítás lépésről lépésre
1. **Repozitórium klónozása:**
   ```bash
   git clone [https://github.com/](https://github.com/)zskoller/ai_termek_azonosito.git
   cd ai_termek_azonosito
   git checkout v1.0.0

   
