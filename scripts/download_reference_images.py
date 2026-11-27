import csv
import re
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

# --- BEÁLLÍTÁSOK ---
INPUT_EXCEL = Path("sample_data/inventory_500.xlsx")
IMAGE_DIR = Path("reference_images")
OUTPUT_CSV = Path("docs/image_sources.csv")
DELAY_SECONDS = 2.0  # szünet a kérések között, hogy ne korlátozzon a kereső


def slugify(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "_", str(text).strip().lower())
    return text.strip("_")[:60]


def get_domain(url: str) -> str:
    host = urlparse(url).netloc.lower()
    return host.removeprefix("www.")


def pick_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def download_first_valid_image(query: str, target_base: Path) -> tuple[str | None, str | None]:
    with DDGS() as ddgs:
        results = list(ddgs.images(query, max_results=5))

    headers = {"User-Agent": "Mozilla/5.0"}
    for item in results:
        img_url = item.get("image")
        page_url = item.get("url") or img_url
        if not img_url:
            continue
        try:
            resp = requests.get(img_url, headers=headers, timeout=10)
            content_type = resp.headers.get("Content-Type", "").lower()
            if resp.status_code == 200 and "image" in content_type and len(resp.content) > 5000:
                ext = ".png" if "png" in content_type else ".jpg"
                file_path = target_base.with_suffix(ext)
                file_path.write_bytes(resp.content)
                return file_path.name, get_domain(page_url)
        except requests.RequestException:
            continue

    return None, None


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    xls = pd.ExcelFile(INPUT_EXCEL)
    sheet = "Inventory" if "Inventory" in xls.sheet_names else xls.sheet_names[0]
    df = pd.read_excel(INPUT_EXCEL, sheet_name=sheet)

    col_name = pick_column(df, ["name_en", "Név"])
    col_sku = pick_column(df, ["serial_number", "Cikkszám"])
    col_cat = pick_column(df, ["category", "Kategória"])

    if not col_name:
        raise ValueError(f"Nem található terméknév oszlop. Elérhető oszlopok: {list(df.columns)}")

    # Folytathatóság: ha korábban megszakadt, a már letöltött sorokat átugorja
    already_done = set()
    file_exists = OUTPUT_CSV.exists()
    if file_exists:
        existing_df = pd.read_csv(OUTPUT_CSV)
        already_done = set(existing_df["product_name"].astype(str))

    today_str = date.today().isoformat()

    with OUTPUT_CSV.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["filename", "sku", "category", "product_name", "source_domain", "download_date"])

        for idx, row in df.iterrows():
            product = str(row[col_name]).strip()
            sku = str(row[col_sku]).strip() if col_sku and pd.notna(row[col_sku]) else ""
            category = str(row[col_cat]).strip() if col_cat and pd.notna(row[col_cat]) else ""

            if product in already_done:
                continue

            base_name = IMAGE_DIR / f"img_{idx + 1:03d}_{slugify(sku or product)}"
            query = f"{product} {sku} official product photo".strip()

            try:
                filename, domain = download_first_valid_image(query, base_name)
                if filename:
                    writer.writerow([filename, sku, category, product, domain, today_str])
                    f.flush()
                    print(f"[OK] {idx + 1}/{len(df)} -> {filename} ({domain})")
                else:
                    print(f"[HIBA] {idx + 1}/{len(df)} -> Nem sikerült képet letölteni: {product}")
            except Exception as exc:
                print(f"[FIGYELMEZTETÉS] {idx + 1}/{len(df)} | {product}: {exc}")

            time.sleep(DELAY_SECONDS)

    print(f"\nKész! Letöltött képek: {IMAGE_DIR} | Forráslista: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()