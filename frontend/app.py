import streamlit as st
import requests

# === BEÁLLÍTÁSOK ===
BACKEND_URL = "http://backend:8000"
st.set_page_config(page_title="AI Termékazonosító", page_icon="🤖", layout="wide")

st.title("🤖 AI Termékazonosító és Készletkezelő")
st.sidebar.title("📌 Menü")

menu_options = [
    "📥 Készlet Importálása", 
    "🖼️ Kép Hozzárendelése", 
    "🔍 AI Kép Alapú Keresés",
    "📦 Készlet & Megrendelés"
]
selected_menu = st.sidebar.radio("Válassz funkciót:", menu_options)


# === 1. KÉSZLET IMPORTÁLÁSA ===
if selected_menu == "📥 Készlet Importálása":
    st.header("📥 Készlet Importálása (Excel)")
    uploaded_file = st.file_uploader("Válassz egy Excel fájlt (.xlsx)", type=["xlsx", "xls"])
    
    if st.button("Feltöltés és Feldolgozás", type="primary"):
        if uploaded_file:
            with st.spinner("Mentés az adatbázisba..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                    response = requests.post(f"{BACKEND_URL}/import-excel", files=files)
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"Sikeres importálás! {data['imported_products']} termék frissítve.")
                    else:
                        st.error(f"Hiba: {response.text}")
                except Exception as e:
                    st.error(f"Hálózati hiba: {str(e)}")
        else:
            st.warning("Kérlek, válassz ki egy fájlt!")


# === 2. KÉP HOZZÁRENDELÉSE (VEKTORIZÁLÁS) ===
elif selected_menu == "🖼️ Kép Hozzárendelése":
    st.header("🖼️ Kép Hozzárendelése Termékhez (AI Tanítás)")
    st.write("Tölts fel egy fotót egy meglévő termékhez, hogy az AI felismerje a jövőben.")
    
    product_id = st.number_input("Termék Adatbázis ID (pl. 1, 2, 3...)", min_value=1, step=1)
    uploaded_image = st.file_uploader("Termékfotó feltöltése", type=["png", "jpg", "jpeg"])
    
    if st.button("Kép feltöltése és Vektorizálás", type="primary"):
        if uploaded_image:
            with st.spinner("AI Vektor (Embedding) generálása folyamatban... Ez eltarthat pár másodpercig."):
                try:
                    files = {"file": (uploaded_image.name, uploaded_image.getvalue())}
                    response = requests.post(f"{BACKEND_URL}/upload-image/{product_id}", files=files)
                    if response.status_code == 200:
                        st.success("✅ A kép sikeresen feltöltve, az AI megtanulta a terméket!")
                    else:
                        st.error(f"Hiba: {response.json().get('detail')}")
                except Exception as e:
                    st.error(f"Hálózati hiba: {str(e)}")
        else:
            st.warning("Kérlek, válassz ki egy képet!")


# === 3. AI KÉP ALAPÚ KERESÉS (EXTRÁKKAL) ===
elif selected_menu == "🔍 AI Kép Alapú Keresés":
    st.header("🔍 Termék Azonosítása Kép Alapján")
    search_image = st.file_uploader("Mit keresel? Tölts fel egy fotót!", type=["png", "jpg", "jpeg"])
    
    if st.button("AI Keresés Indítása", type="primary"):
        if search_image:
            with st.spinner("A mesterséges intelligencia elemzi a képet..."):
                try:
                    files = {"file": (search_image.name, search_image.getvalue())}
                    response = requests.post(f"{BACKEND_URL}/identify-product", files=files)
                    
                    if response.status_code == 200:
                        result = response.json()
                        best_match = result.get("best_match")
                        
                        if best_match:
                            st.subheader("🎉 Legjobb találat:")
                            st.success(f"**{best_match['name_hu']}** (Cikkszám: {best_match['vendor_serial_number']})")
                            st.progress(best_match['confidence_score'] / 100)
                            st.write(f"Biztonsági pontszám: **{best_match['confidence_score']}%**")
                            
                            # Gombok a fordításhoz és webshophoz egy sorban
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("🌐 Fordítás angolra és lengyelre"):
                                    res = requests.post(f"{BACKEND_URL}/translate-product/{best_match['id']}").json()
                                    st.info(f"EN: {res.get('name_en')} | PL: {res.get('name_pl')}")
                            with col2:
                                if st.button("🛒 Keresés az interneten (Webshop)"):
                                    res = requests.get(f"{BACKEND_URL}/search-webshop/{best_match['id']}").json()
                                    if res.get("webshop_url"):
                                        st.markdown(f"[🔗 Kattints ide a webshophoz]({res['webshop_url']})")
                                    else:
                                        st.warning("Sajnos nem találtunk webshopot.")
                        else:
                            st.warning("Sajnos az AI nem talált hasonlót az adatbázisban.")
                except Exception as e:
                    st.error(f"Hálózati hiba: {str(e)}")
        else:
            st.warning("Kérlek, tölts fel egy képet a kereséshez!")


# === 4. KÉSZLET EXPORT ÉS MEGRENDELÉS ===
elif selected_menu == "📦 Készlet & Megrendelés":
    st.header("📦 Exportálás és Megrendelőlap Készítése")
    
    tab1, tab2 = st.tabs(["📊 Készlet Letöltése (Excel)", "🛒 Megrendelőlap Generálása"])
    
    with tab1:
        st.write("A teljes, vagy szűrt adatbázis letöltése Excel formátumban.")
        search_query = st.text_input("Szűrés (Opcionális - pl. kategória, név):")
        if st.button("Készlet Exportálása"):
            url = f"{BACKEND_URL}/export-excel"
            if search_query:
                url += f"?search={search_query}"
            res = requests.get(url)
            if res.status_code == 200:
                st.download_button(label="📥 Excel Fájl Letöltése", data=res.content, file_name="keszlet.xlsx")
            else:
                st.error("Hiba az exportálás során.")
                
    with tab2:
        st.write("Adj meg termék ID-kat vesszővel elválasztva egy hivatalos megrendelőlap generálásához!")
        ids_input = st.text_input("Termék ID-k (pl: 1, 5, 12, 44)")
        
        if st.button("Megrendelőlap Generálása", type="primary"):
            if ids_input:
                # Szöveg átalakítása számok listájává
                id_list = [int(x.strip()) for x in ids_input.split(",") if x.strip().isdigit()]
                
                if id_list:
                    res = requests.post(f"{BACKEND_URL}/export-order", json={"product_ids": id_list})
                    if res.status_code == 200:
                        st.download_button(label="📝 Megrendelőlap Letöltése", data=res.content, file_name="megrendeles.xlsx")
                    else:
                        st.error("Hiba a generálás során.")
                else:
                    st.warning("Kérlek, valós számokat adj meg!")
            else:
                st.warning("Nem adtad meg a termékek azonosítóit!")