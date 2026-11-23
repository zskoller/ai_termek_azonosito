from deep_translator import GoogleTranslator

def translate_product_names(hungarian_name: str):
    """
    Kapk egy magyar terméknevet, és visszaadja az angol és lengyel fordítást.
    """
    if not hungarian_name:
        return None, None
        
    try:
        # Angol fordítás
        en_name = GoogleTranslator(source='hu', target='en').translate(hungarian_name)
        # Lengyel fordítás
        pl_name = GoogleTranslator(source='hu', target='pl').translate(hungarian_name)
        
        return en_name, pl_name
    except Exception as e:
        print(f"Hiba a fordítás során: {str(e)}")
        return None, None