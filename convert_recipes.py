import csv
import json
from pathlib import Path

# Määritetään polut
DATA_DIR = Path("data")
INPUT_CSV = DATA_DIR / "raw_recipes.csv"  
OUTPUT_JSON = DATA_DIR / "recipes.json"

MAX_RECIPES = 200 


def parse_ingredients(raw_ingredients: str) -> list[str]:
    """Siistii Kagglen ainesosalistan (jos se on tallennettu merkkijonona/listana)."""
    if not raw_ingredients:
        return []

    cleaned = raw_ingredients.strip("[]\"'").replace("'", "")
    return [i.strip() for i in cleaned.split(",") if i.strip()]


def convert_csv_to_json():
    if not INPUT_CSV.exists():
        print(f"Virhe: Tiedostoa {INPUT_CSV} ei löydy. Laita Kaggle-tiedosto data/-kansioon.")
        return

    recipes = []
    with open(INPUT_CSV, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for idx, row in enumerate(reader):
            if len(recipes) >= MAX_RECIPES:
                break

            name = (
                row.get("name")
                or row.get("title")
                or row.get("RecipeName")
                or "Nimetön resepti"
            )
            raw_ingredients = (
                row.get("ingredients")
                or row.get("Ingredients")
                or row.get("recipe_ingredients")
                or ""
            )
            instructions = (
                row.get("instructions")
                or row.get("directions")
                or row.get("Directions")
                or ""
            )

            ingredients_list = parse_ingredients(raw_ingredients)

            if name and ingredients_list:
                recipes.append(
                    {
                        "id": f"rag_{idx + 1}",
                        "name": name.strip(),
                        "ingredients": ingredients_list,
                        "instructions": instructions.strip(),
                    }
                )

    with open(OUTPUT_JSON, mode="w", encoding="utf-8") as f:
        json.dump(recipes, f, indent=2, ensure_ascii=False)

    print(
        f"Valmis! Muunnettu {len(recipes)} reseptiä tiedostoon: {OUTPUT_JSON}"
    )


if __name__ == "__main__":
    convert_csv_to_json()