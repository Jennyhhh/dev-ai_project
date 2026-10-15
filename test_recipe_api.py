from src.clients.recipe_api_client import search_recipes_by_ingredient

def main():
    recipes = search_recipes_by_ingredient("chicken")

    if not recipes:
        print("Reseptejä ei löytynyt.")
        return

    print(f"Löytyi {len(recipes)} reseptiä:\n")

    for recipe in recipes[:5]:
        print(f"- {recipe['strMeal']} (ID: {recipe['idMeal']})")


if __name__ == "__main__":
    main()