import csv
import json
from pathlib import Path

# Määritetään polut
DATA_DIR = Path("data")
INPUT_CSV = DATA_DIR / "raw_recipes.csv"  
OUTPUT_JSON = DATA_DIR / "recipes.json"

MAX_RECIPES = 200 

def parse_ingredients(raw_ingredients: str) -> list[str]:
    """Siistii Kagglen ainesosalistan."""
    if not raw_ingredients:
        return []
    cleaned = raw_ingredients.strip("[]\"'").replace("'", "")
    return [i.strip() for i in cleaned.split(",") if i.strip()]

def generate_tags(ingredients: list[str]) -> list[str]:
    """Luo automaattiset tagit ainesosien perusteella suodattimen testaamiseen."""
    ing_text = " ".join(ingredients).lower()
    tags = []
    
    if any(w in ing_text for w in ["chicken", "beef", "pork", "meat", "turkey"]):
        tags.append("liharuoka")
    else:
        tags.append("kasvisruoka")
        
    if not any(w in ing_text for w in ["wheat", "flour", "pasta", "bread", "rye", "barley"]):
        tags.append("gluteeniton")
        
    if not any(w in ing_text for w in ["milk", "cheese", "cream", "butter", "yogurt"]):
        tags.append("maidoton")
        
    if "kasvisruoka" in tags and "maidoton" in tags:
        tags.append("vegaaninen")
        
    return tags

def convert_csv_to_json():
    if not INPUT_CSV.exists():
        print(f"Virhe: Tiedostoa {INPUT_CSV} ei löydy.")
        return

    recipes = []
    with open(INPUT_CSV, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for idx, row in enumerate(reader):
            if len(recipes) >= MAX_RECIPES:
                break

            # Korjattu sarakehaku vastaamaan datasetin rakennetta:
            name = (
                row.get("recipe_name")   # Kagglen recipes.csv
                or row.get("Name")       # Kagglen test_recipes.csv
                or row.get("name")
                or "Nimetön resepti"
            )
            raw_ingredients = (
                row.get("ingredients")
                or row.get("Ingredients")
                or ""
            )
            instructions = (
                row.get("directions")
                or row.get("Directions")
                or row.get("instructions")
                or ""
            )

            ingredients_list = parse_ingredients(raw_ingredients)
            
            # Luodaan reseptejä vain jos nimi ja ainekset löytyivät
            if name != "Nimetön resepti" and ingredients_list:
                recipes.append(
                    {
                        "id": f"rag_{idx + 1}",
                        "name": name.strip(),
                        "ingredients": ingredients_list,
                        "instructions": instructions.strip(),
                        "tags": generate_tags(ingredients_list)
                    }
                )

    with open(OUTPUT_JSON, mode="w", encoding="utf-8") as f:
        json.dump(recipes, f, indent=2, ensure_ascii=False)

    print(f"Valmis! Muunnettu {len(recipes)} reseptiä tiedostoon: {OUTPUT_JSON}")

if __name__ == "__main__":
    convert_csv_to_json()