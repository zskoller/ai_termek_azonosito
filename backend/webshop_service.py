from duckduckgo_search import DDGS

def search_product_link(product_name: str) -> str:
    """
    Rákeres a termék nevére az interneten, és visszaadja az első releváns weboldal linkjét.
    """
    if not product_name:
        return None
        
    try:
        query = f"{product_name} vásárlás OR webshop OR ár"
        
        # A biztonság kedvéért azonnal listává alakítjuk az eredményt
        results = list(DDGS().text(query, max_results=1))
        
        if results and len(results) > 0:
            return results[0].get("href")
            
        return None
    except Exception as e:
        # Ezt a hibát most már ki fogjuk írni a terminálba
        print(f"Hiba a DuckDuckGo keresés során: {str(e)}")
        return None