from src.capabilities.rag import RecipeRAG
from src.services.recipe_service import RecipeService, filter_recipe_by_diets


def test_standalone_rag():
    print("--- 1. TESTATAAN RAG-HAKUA ---")
    rag = RecipeRAG()
    results = rag.query_recipes(["chicken", "pasta"], top_k=2)

    if not results:
        print("Huom: RAG ei palauttanut tuloksia. Onko data/recipes.json luotu?")
    for res in results:
        print(f"Löydetty: {res.get('name')} (Lähde: {res.get('source')})")
        print(f"Ainekset: {res.get('ingredients')[:4]}...\n")


def test_filters():
    print("--- 2. TESTATAAN RUOKAVALIOSUODATUSTA ---")
    test_recipe_meat = {
        "name": "Kanakastike",
        "ingredients": ["chicken", "cream", "curry"],
    }
    test_recipe_vegan = {
        "name": "Tomaattipasta",
        "ingredients": ["pasta", "tomato", "basil"],
    }

    print("Kanakastike vegaanisena (pitäisi olla False):", filter_recipe_by_diets(test_recipe_meat, ["vegan"]))
    print("Kanakastike maidottomana (pitäisi olla False):", filter_recipe_by_diets(test_recipe_meat, ["dairy-free"]))
    print("Tomaattipasta gluteenittomana (pitäisi olla False):", filter_recipe_by_diets(test_recipe_vegan, ["gluten-free"]))
    print("Tomaattipasta vegaanisena (pitäisi olla True):", filter_recipe_by_diets(test_recipe_vegan, ["vegan"]))
    print()


def test_service_fallback():
    print("--- 3. TESTATAAN PALVELUN VARAJÄRJESTELMÄÄ (FALLBACK) ---")
    # Koska API-client on vielä tyhjä runko tai ei vastaa,
    # RecipeService kääntyy automaattisesti RAGin puoleen
    service = RecipeService()
    results = service.search_recipes(
        ingredients=["tomato"],
        diet_preferences=["vegan"],
        limit=2
    )

    print(f"Palautettuja tuloksia: {len(results)}")
    for res in results:
        print(f"- {res.get('name')} | Lähde: {res.get('source')}")


if __name__ == "__main__":
    test_standalone_rag()
    test_filters()
    test_service_fallback()