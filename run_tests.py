from src.services.recipe_service import RecipeService
from src.capabilities.rag import RecipeRAG

def run_my_tests():
    # Alustetaan RAG käyttämään uutta Kaggle-dataa
    rag = RecipeRAG(data_path="data/recipes.json")
    
    # Tehdään tyhjä mock-luokka estämään häiritsevä API-virhetuloste (valinnainen)
    class DummyAPI:
        def search_by_ingredients(self, ingredients):
            return []
            
    service = RecipeService(rag_client=rag)
    service.api_client = DummyAPI() # Vaiennetaan AttributeError

    # 1. RAG-onnistuminen (Etsitään omenoita ja kanelia)
    print("--- Testi 1: RAG Onnistuminen ---")
    res1 = service.search_recipes(ingredients=["apple", "cinnamon", "sugar"])
    print(f"Löytyi {len(res1)} reseptiä. Osuvin: {res1[0]['name'] if res1 else 'Ei osumia'}\n")

    # 2. RAG-rajoite (Etsitään jotain täysin datasetin ulkopuolelta)
    print("--- Testi 2: Vaikea tapaus ---")
    res2 = service.search_recipes(ingredients=["dragonfruit", "saffron", "truffle oil"])
    print(f"Löytyi {len(res2)} reseptiä.\n")

    # 3. Ruokavaliosuodatus (Etsitään omenoita, voita ja maitoa -> suodatetaan maidottomaksi)
    print("--- Testi 3: Maidoton suodatus ---")
    
    # Ilman suodatusta:
    res3_all = service.search_recipes(ingredients=["apple", "butter", "milk"])
    print(f"Ilman suodatusta löytyi: {len(res3_all)} reseptiä.")
    
    # Maidoton suodatus:
    res3_filtered = service.search_recipes(ingredients=["apple", "butter", "milk"], diet_preferences=["dairy-free"])
    print(f"Maidottomalla suodatuksella löytyi: {len(res3_filtered)} reseptiä.\n")

if __name__ == "__main__":
    run_my_tests()