
import re
import logging
from typing import Any, Dict, List, Optional

from src.capabilities.rag import RecipeRAG


from src.clients.recipe_api_client import (
    search_recipes_by_ingredient,
    get_recipe_details,
)

logger = logging.getLogger(__name__)

NON_VEGAN_KEYWORDS = {
    "meat", "beef", "pork", "chicken", "turkey", "bacon", "ham", "fish", "salmon",
    "tuna", "shrimp", "seafood", "egg", "eggs", "milk", "cream", "cheese",
    "butter", "yogurt", "liha", "nauta", "sika", "kana", "broileri", "kalkkuna",
    "pekoni", "kinkku", "kala", "lohi", "tonnikala", "katkarapu", "muna",
    "kananmuna", "maito", "kerma", "juusto", "voi", "jogurtti"
}

GLUTEN_KEYWORDS = {
    "wheat", "flour", "pasta", "spaghetti", "macaroni", "bread", "barley",
    "rye", "beer", "couscous", "semolina", "vehnä", "jauho", "pasta",
    "spagetti", "makaroni", "leipä", "ohra", "ruis", "korppujauho"
}

DAIRY_KEYWORDS = {
    "milk", "cream", "cheese", "butter", "yogurt", "sour cream", "parmesan",
    "cheddar", "mozzarella", "maito", "kerma", "juusto", "voi", "jogurtti",
    "kermaviili", "rahka"
}

NUT_KEYWORDS = {
    "nut", "nuts", "peanut", "peanuts", "almond", "almonds", "walnut", "walnuts",
    "cashew", "cashews", "hazelnut", "hazelnuts", "pähkinä", "maapähkinä",
    "manteli", "cashew"
}


def normalize_ingredient(value: str) -> str:
    """Yhtenäistää englanninkielisen ainesosan vertailua varten."""
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return " ".join(value.split())


def singularize_word(word: str) -> str:
    """Käsittelee tavallisimmat englannin monikkomuodot."""
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"

    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]

    return word


def ingredient_words(value: str) -> list[str]:
    """Muuttaa ainesosan vertailukelpoisiksi sanoiksi."""
    return [
        singularize_word(word)
        for word in normalize_ingredient(value).split()
    ]


def ingredient_matches(
    user_ingredient: str,
    recipe_ingredient: str,
) -> bool:
    """Vertaa ainesosia joustavasti ilman mielivaltaisia osumia."""
    user_words = ingredient_words(user_ingredient)
    recipe_words = ingredient_words(recipe_ingredient)

    if not user_words or not recipe_words:
        return False

    if user_words == recipe_words:
        return True

    if len(user_words) == 1 and user_words[0] in recipe_words:
        return True

    if len(recipe_words) == 1 and recipe_words[0] in user_words:
        return True

    return False


def clean_recipe_name(name: str) -> str:
    """Siistii reseptin nimen ylimääräisistä välilyönneistä."""
    name = re.sub(r"\s+", " ", name)
    return name.strip(" -,:;")


def get_recipe_ingredients(details: dict) -> list[str]:
    """Kerää reseptin ainesosat alkuperäisessä muodossa."""
    ingredients = []

    for index in range(1, 21):
        value = details.get(f"strIngredient{index}")

        if isinstance(value, str) and value.strip():
            ingredients.append(value.strip())

    return ingredients


def search_recipes(ingredients_text: str) -> list[dict]:
    """Hakee reseptejä, vertailee ainesosia ja järjestää tulokset."""

    ingredients = list(dict.fromkeys(
        normalize_ingredient(item)
        for item in ingredients_text.split(",")
        if item.strip()
    ))

    if not ingredients:
        return []

    candidate_scores = {}

    for ingredient in ingredients:
        try:
            recipes = search_recipes_by_ingredient(ingredient)
        except Exception:
            continue

        for recipe in recipes or []:
            recipe_id = recipe.get("idMeal")

            if not recipe_id:
                continue

            candidate_scores[recipe_id] = (
                candidate_scores.get(recipe_id, 0) + 1
            )

    candidate_ids = sorted(
        candidate_scores,
        key=lambda recipe_id: candidate_scores[recipe_id],
        reverse=True,
    )[:40]

    results = []

    for recipe_id in candidate_ids:
        try:
            details = get_recipe_details(recipe_id)
        except Exception:
            continue

        if not details:
            continue

        original_ingredients = get_recipe_ingredients(details)

        matched = [
            ingredient
            for ingredient in ingredients
            if any(
                ingredient_matches(ingredient, recipe_ingredient)
                for recipe_ingredient in original_ingredients
            )
        ]

        missing = [
            ingredient
            for ingredient in original_ingredients
            if not any(
                ingredient_matches(user_ingredient, ingredient)
                for user_ingredient in ingredients
            )
        ]

        original_name = clean_recipe_name(
            details.get("strMeal") or "Nimetön resepti"
        )

        original_instructions = (
            details.get("strInstructions") or ""
        ).strip()

        results.append({
            "id": recipe_id,
            "name": original_name,
            "image": details.get("strMealThumb") or "",
            "instructions": original_instructions,
            "ingredients": original_ingredients,
            "matched_ingredients": matched,
            "missing_ingredients": missing,
            "match_count": len(matched),
            "total_user_ingredients": len(ingredients),
        })

    results.sort(
        key=lambda recipe: (
            -recipe["match_count"],
            len(recipe["missing_ingredients"]),
            recipe["name"].lower(),
        )
    )

    return results

def filter_recipe_by_diets (
        recipe: Dict[str, Any], diet_preferences: List[str]
) -> bool:
    if not diet_preferences:
        return True

    ingredient_text = " ".join(recipe.get("ingredients", [])).lower()
    recipe_name = recipe.get("name", "").lower()
    full_text = f"{recipe_name} {ingredient_text}"

    for pref in diet_preferences:
        pref_clean = pref.lower().strip()

        #1. vegaaninen
        if pref_clean in ["vegan", "vegaaninen"]:
            if any(word in full_text for word in NON_VEGAN_KEYWORDS):
                return False

        # 2. gluteeniton
        elif pref_clean in ["gluten-free", "gluteeniton"]:
            if any(word in full_text for word in GLUTEN_KEYWORDS):
                return False

        # 3. maidoton
        elif pref_clean in ["dairy-free", "maidoton"]:
            if any(word in full_text for word in DAIRY_KEYWORDS):
                return False

        # 4. pähkinätön
        elif pref_clean in ["nut-free", "pähkinätön"]:
            if any(word in full_text for word in NUT_KEYWORDS):
                return False

    return True

class RecipeService:

    def __init__(
            self,
            rag_client: Optional[RecipeRAG] = None,
    ):
        self.rag_client = rag_client or RecipeRAG()

    def search_recipes(
        self,
        ingredients: List[str],
        diet_preferences: Optional[List[str]] = None,
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        """Hakee reseptejä ensisijaisesti API:sta ja virhetilanteessa RAG-varajärjestelmästä.

        Suodattaa lopulliset tulokset deterministisesti käyttäjän ruokavaliotoiveiden mukaisesti.
        """
        diet_preferences = diet_preferences or []
        recipes: List[Dict[str, Any]] = []
        api_failed = False

        # 1. Ensisijainen haku: Ulkoinen API
        try:
            logger.info("Yritetään hakea reseptejä ulkoisesta API:sta...")
            api_results = self.api_client.search_by_ingredients(ingredients)
            if api_results:
                for r in api_results:
                    r["source"] = "api"
                recipes = api_results
            else:
                logger.info("API ei palauttanut tuloksia, siirrytään RAG-varajärjestelmään.")
                api_failed = True
        except Exception as e:
            logger.warning(f"API-haku epäonnistui ({e}), käytetään RAG-varajärjestelmää.")
            api_failed = True

        # 2. Varajärjestelmän (Fallback) logiikka: Jos API ei vastaa tai tuloksia ei saatu
        if api_failed or not recipes:
            logger.info("Haetaan reseptit paikallisesta RAG-tietokannasta...")
            recipes = self.rag_client.query_recipes(ingredients, top_k=limit * 2)

        # 3. Deterministinen ruokavaliosuodatus
        filtered_recipes = [
            r for r in recipes if filter_recipe_by_diets(r, diet_preferences)
        ]

        return filtered_recipes[:limit]
    