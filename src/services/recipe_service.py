
import logging
import re
from typing import Any, Dict, List, Optional

from src.capabilities.rag import RecipeRAG
from src.clients.recipe_api_client import (
    search_recipes_by_ingredient,
    get_recipe_details,
)

logger = logging.getLogger(__name__)
rag_client = RecipeRAG()


# Conservative ingredient screening, not an allergy certification.

ANIMAL_FLESH = {
    "meat", "beef", "pork", "chicken", "turkey", "bacon", "ham",
    "fish", "salmon", "tuna", "shrimp", "prawn", "anchovy",
    "seafood", "sausage", "gelatin", "gelatine", "lard",
    "pepperoni", "prosciutto", "chorizo", "oyster", "clam",
    "liha", "nauta", "sika", "kana", "broileri", "kalkkuna",
    "pekoni", "kinkku", "kala", "lohi", "tonnikala", "katkarapu",
    "makkara", "liivate",
}

ANIMAL_BROTH = {
    "chicken stock", "beef stock", "fish stock", "bone broth",
    "chicken broth", "beef broth", "fish sauce", "oyster sauce",
}

DAIRY = {
    "milk", "cream", "cheese", "butter", "yogurt", "yoghurt", "ghee",
    "parmesan", "cheddar", "mozzarella", "whey", "casein", "buttermilk",
    "sour cream", "condensed milk", "ice cream", "maito", "kerma",
    "juusto", "voi", "jogurtti", "kermaviili", "rahka",
}

EGGS = {
    "egg", "eggs", "egg white", "egg yolk", "mayonnaise",
    "kananmuna", "kananmunat", "muna",
}

OTHER_ANIMAL = {
    "honey", "hunaja",
}

GLUTEN = {
    "wheat", "wheat flour", "all purpose flour", "plain flour",
    "self raising flour", "flour", "pasta", "spaghetti", "macaroni",
    "bread", "breadcrumbs", "barley", "rye", "couscous", "semolina",
    "bulgur", "farro", "seitan", "pastry", "puff pastry", "beer",
    "soy sauce", "vehnä", "jauho", "spagetti", "makaroni", "leipä",
    "ohra", "ruis", "korppujauho", "taikina",
}

NUTS = {
    "nut", "nuts", "peanut", "almond", "walnut", "cashew",
    "hazelnut", "pecan", "pistachio",
    "pähkinä", "maapähkinä", "manteli",
}


# =========================================
# INGREDIENT NORMALIZATION
# =========================================

def normalize_ingredient(value: str) -> str:
    value = str(value or "").strip().lower()
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    return " ".join(value.split())


def singularize_word(word: str) -> str:
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"

    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]

    return word


def ingredient_words(value: str) -> List[str]:
    return [
        singularize_word(word)
        for word in normalize_ingredient(value).split()
    ]


def ingredient_matches(
    user_ingredient: str,
    recipe_ingredient: str,
) -> bool:
    user_words = ingredient_words(user_ingredient)
    recipe_words = ingredient_words(recipe_ingredient)

    return bool(
        user_words
        and recipe_words
        and all(word in recipe_words for word in user_words)
    )


def clean_recipe_name(name: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        str(name or ""),
    ).strip(" -,:;")


def get_recipe_ingredients(details: dict) -> List[str]:
    return [
        value.strip()
        for index in range(1, 21)
        if isinstance(
            (value := details.get(f"strIngredient{index}")),
            str,
        )
        and value.strip()
    ]


def contains_keyword(text: str, keywords: set) -> bool:
    """
    Match complete ingredient words and common English plurals.

    For example:
    - "Raw King Prawns" matches "prawn"
    - "Fresh Eggs" matches "egg"
    - "chamomile" does not match "ham"
    """
    text_words = ingredient_words(text)

    if not text_words:
        return False

    for keyword in keywords:
        keyword_words = ingredient_words(keyword)

        if not keyword_words:
            continue

        length = len(keyword_words)

        if any(
            text_words[start:start + length] == keyword_words
            for start in range(len(text_words) - length + 1)
        ):
            return True

    return False


# =========================================
# DIETARY FILTERING
# =========================================

def _ingredient_conflicts(
    ingredient: str,
    diet: str,
) -> bool:
    """
    Flags clear dietary conflicts.

    Ambiguous packaged ingredients still require
    manual checking.
    """

    value = normalize_ingredient(ingredient)

    if not value:
        return False

    plant_based = contains_keyword(
        value,
        {
            "soy milk",
            "soya milk",
            "almond milk",
            "oat milk",
            "coconut milk",
            "rice milk",
            "plant milk",
            "vegan cheese",
            "vegan butter",
            "vegan cream",
            "dairy free milk",
            "dairy free cheese",
            "dairy free cream",
            "dairy free butter",
            "plant based milk",
            "plant based cheese",
            "plant based butter",
            "plant based cream",
        },
    )

    lactose_free = (
        "lactose free" in value
        or "laktoositon" in value
    )

    dairy_conflict = (
        contains_keyword(value, DAIRY)
        and not plant_based
    )

    flesh_conflict = contains_keyword(
        value,
        ANIMAL_FLESH | ANIMAL_BROTH,
    )

    if diet == "vegetarian":
        return flesh_conflict

    if diet == "vegan":
        return (
            flesh_conflict
            or dairy_conflict
            or contains_keyword(
                value,
                EGGS | OTHER_ANIMAL,
            )
        )

    if diet == "gluten free":
        if (
            "gluten free" in value
            or "gluteeniton" in value
        ):
            return False

        return contains_keyword(value, GLUTEN)

    if diet == "lactose free":
        return dairy_conflict and not lactose_free

    if diet == "dairy free":
        return dairy_conflict

    if diet == "nut free":
        return contains_keyword(value, NUTS)

    return False


def filter_recipe_by_diets(
    recipe: Dict[str, Any],
    diet_preferences: Optional[List[str]] = None,
) -> bool:
    if not diet_preferences:
        return True

    ingredients = recipe.get("ingredients") or []

    if not ingredients:
        return False

    for preference in diet_preferences:
        pref = normalize_ingredient(preference)

        pref = {
            "kasvisruoka": "vegetarian",
            "vegaaninen": "vegan",
            "gluteeniton": "gluten free",
            "laktoositon": "lactose free",
            "maidoton": "dairy free",
            "pähkinätön": "nut free",
        }.get(pref, pref)

        if pref in (
            "",
            "no dietary restrictions",
            "ei erityisruokavaliota",
        ):
            continue

        if any(
            _ingredient_conflicts(str(item), pref)
            for item in ingredients
        ):
            return False

    return True


# =========================================
# RECIPE FORMATTING
# =========================================

def format_recipe(
    recipe_id: str,
    name: str,
    image: str,
    instructions: str,
    original_ingredients: List[str],
    user_ingredients: List[str],
    source: str,
) -> Dict[str, Any]:

    original_ingredients = [
        str(item)
        for item in (original_ingredients or [])
        if str(item).strip()
    ]

    matched = [
        ingredient
        for ingredient in user_ingredients
        if any(
            ingredient_matches(ingredient, item)
            for item in original_ingredients
        )
    ]

    missing = [
        item
        for item in original_ingredients
        if not any(
            ingredient_matches(user, item)
            for user in user_ingredients
        )
    ]

    return {
        "id": recipe_id,
        "name": clean_recipe_name(name) or "Unnamed recipe",
        "image": image or "",
        "instructions": instructions or "",
        "ingredients": original_ingredients,
        "matched_ingredients": matched,
        "missing_ingredients": missing,
        "match_count": len(matched),
        "total_user_ingredients": len(user_ingredients),
        "source": source,
    }


# =========================================
# RECIPE SEARCH
# =========================================

def search_recipes(
    ingredients_text: str,
    diet_preferences: Optional[List[str]] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Search TheMealDB first, then RAG if
    no suitable API results remain.
    """

    ingredients = list(
        dict.fromkeys(
            normalize_ingredient(item)
            for item in (ingredients_text or "").split(",")
            if item.strip()
        )
    )

    if not ingredients or limit <= 0:
        return []

    candidate_scores = {}

    # 1. Search TheMealDB
    for ingredient in ingredients:
        try:
            for recipe in (
                search_recipes_by_ingredient(ingredient) or []
            ):
                recipe_id = recipe.get("idMeal")

                if recipe_id:
                    candidate_scores[recipe_id] = (
                        candidate_scores.get(recipe_id, 0) + 1
                    )

        except Exception as error:
            logger.warning(
                "TheMealDB search failed: %s",
                error,
            )

    candidate_ids = sorted(
        candidate_scores,
        key=lambda key: candidate_scores[key],
        reverse=True,
    )[:40]

    results = []

    for recipe_id in candidate_ids:
        try:
            details = get_recipe_details(recipe_id)

            if not details:
                continue

            results.append(
                format_recipe(
                    recipe_id,
                    details.get("strMeal", ""),
                    details.get("strMealThumb", ""),
                    details.get("strInstructions", ""),
                    get_recipe_ingredients(details),
                    ingredients,
                    "api",
                )
            )

        except Exception as error:
            logger.warning(
                "Recipe details could not be loaded: %s",
                error,
            )

    # 2. Filter API results by diet
    results = [
        recipe
        for recipe in results
        if filter_recipe_by_diets(
            recipe,
            diet_preferences,
        )
    ]

    # 3. Use RAG when no suitable API results remain
    if not results:
        logger.info(
            "No suitable TheMealDB recipes; "
            "searching local RAG recipes."
        )

        try:
            rag_results = rag_client.query_recipes(
                ingredients,
                top_k=40,
            )

            for recipe in rag_results:
                formatted = format_recipe(
                    recipe.get("id", ""),
                    recipe.get("name", ""),
                    recipe.get("image", ""),
                    recipe.get("instructions", ""),
                    recipe.get("ingredients", []),
                    ingredients,
                    "rag",
                )

                if filter_recipe_by_diets(
                    formatted,
                    diet_preferences,
                ):
                    results.append(formatted)

        except Exception as error:
            logger.error(
                "RAG search failed: %s",
                error,
            )

    # 4. Sort results
    results.sort(
        key=lambda recipe: (
            -recipe["match_count"],
            len(recipe["missing_ingredients"]),
            recipe["name"].lower(),
        )
    )

    # 5. Remove duplicate recipe names
    unique_results = []
    seen_names = set()

    for recipe in results:
        key = recipe["name"].casefold()

        if key not in seen_names:
            seen_names.add(key)
            unique_results.append(recipe)

        if len(unique_results) >= limit:
            break

    return unique_results


# =========================================
# SERVICE CLASS
# =========================================

class RecipeService:
    """Compatibility wrapper for other modules."""

    def __init__(
        self,
        rag_client: Optional[RecipeRAG] = None,
    ):
        self.rag_client = (
            rag_client or globals()["rag_client"]
        )

    def search_recipes(
        self,
        ingredients: List[str],
        diet_preferences: Optional[List[str]] = None,
        limit: int = 3,
    ) -> List[Dict[str, Any]]:

        return search_recipes(
            ingredients_text=", ".join(ingredients),
            diet_preferences=diet_preferences,
            limit=limit,
        )
