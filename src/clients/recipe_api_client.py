import requests

BASE_URL = "https://www.themealdb.com/api/json/v1/1"


def search_recipes_by_ingredient(ingredient: str) -> list[dict]:
    """Hakee reseptejä yhden ainesosan perusteella."""

    url = f"{BASE_URL}/filter.php"

    response = requests.get(
        url,
        params={"i": ingredient},
        timeout=10,
    )
    response.raise_for_status()

    data = response.json()
    return data.get("meals") or []


def get_recipe_details(meal_id: str) -> dict | None:
    """Hakee yksittäisen reseptin tarkat tiedot."""

    url = f"{BASE_URL}/lookup.php"

    response = requests.get(
        url,
        params={"i": meal_id},
        timeout=10,
    )
    response.raise_for_status()

    data = response.json()
    meals = data.get("meals") or []

    return meals[0] if meals else None