
from src.models.model_client import generate_response

from pydantic import ValidationError

from src.schemas.responses import RecipeRecommendation
from src.services.prompts import (
    RECOMMENDER_SYSTEM_PROMPT,
    build_recommendation_prompt,
)

import logging

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
Olet suomenkielinen ruoanlaittoassistentti, joka auttaa valmistamaan
tavallisia suomalaisia arkiruokia.

Tärkeimmät tehtäväsi:
- Auta käyttäjää keksimään ruokaa hänen aineksistaan.
- Suosi tuttuja ja käytännöllisiä arkiruokia.
- Keskustele käyttäjän kanssa ja vastaa jatkokysymyksiin.
- Anna tarvittaessa selkeitä, vaiheittaisia valmistusohjeita.
- Ehdota vaihtoehtoja, jos käyttäjältä puuttuu jokin ainesosa.

Säännöt:
- Vastaa aina suomeksi.
- Ole ystävällinen, selkeä ja käytännönläheinen.
- Älä suosittele erikoisia kansainvälisiä ruokia, ellei käyttäjä pyydä niitä.
- Älä väitä tietäväsi käyttäjän jääkaapin sisältöä.
- Kerro selvästi, mitkä ainekset ovat käyttäjän ilmoittamia ja mitä
  muita aineksia mahdollisesti tarvitaan.
- Voit ehdottaa tavallisia reseptejä ja valmistusohjeita.
- Älä väitä reseptiä TheMealDB:n reseptiksi, ellet saa sitä lähdetiedoista.
- Älä keksi tietoja ulkoisista resepteistä tai väitä tarkistaneesi niitä.
- Jos käyttäjä pyytää vaihtoehtoja, anna konkreettisia vaihtoehtoja.
- Jos käyttäjän pyyntö on epäselvä, kysy tarkentava kysymys.
- Säilytä keskustelun asiayhteys ja huomioi aiemmin ilmoitetut ainekset.
"""


def get_recipe_suggestions(
    ingredients: str,
    diet: str = "Ei erityisruokavaliota",
    max_time: int = 30,
) -> str:
    """Pyytää Llamalta arkiruokasuosituksia käyttäjän aineksista."""

    if not ingredients or not ingredients.strip():
        raise ValueError("Anna vähintään yksi ainesosa.")

    prompt = f"""
Keksi käyttäjälle kolme sopivaa arkiruokavaihtoehtoa.

Käyttäjän ilmoittamat ainekset:
{ingredients}

Ruokavalio:
{diet}

Enimmäisvalmistusaika:
{max_time} minuuttia

Suosi tavallisia suomalaisia arkiruokia.

Kerro jokaisesta vaihtoehdosta:
1. Ruoan nimi.
2. Miksi se sopii ilmoitettuihin aineksiin.
3. Mitä muita aineksia tarvitaan mahdollisesti.
4. Arvioitu valmistusaika vain, jos pystyt antamaan
   järkevän arvion. Kerro, että kyseessä on arvio.

Älä väitä, että ehdotukset ovat ulkoisesta reseptitietokannasta.
Huomioi ruokavalio ja valmistusaika.
Vastaa selkeällä suomen kielellä.
"""

    response = generate_response(prompt, SYSTEM_PROMPT)

    if not response or not response.strip():
        return "Tekoäly ei tuottanut suosituksia. Yritä uudelleen."

    return response.strip()


def chat_with_assistant(
    message: str,
    history: list[dict] | None = None,
    ingredients: str = "",
    diet: str = "Ei erityisruokavaliota",
    max_time: int = 30,
    selected_recipe: dict | None = None,
) -> str:
    """Vastaa käyttäjän jatkokysymykseen keskusteluhistorian avulla."""

    if not message or not message.strip():
        raise ValueError("Kirjoita ensin viesti.")

    history = history or []

    recipe_context = ""

    if selected_recipe:
        recipe_context = f"""
Käyttäjän tarkastelema resepti:
Nimi: {selected_recipe.get("name", "Tuntematon")}
Ainekset: {selected_recipe.get("ingredients", [])}
Puuttuvat ainekset: {selected_recipe.get("missing_ingredients", [])}
Valmistusohje: {selected_recipe.get("instructions", "")}
"""

    prompt_parts = [
        f"Käyttäjän käytettävissä olevat ainekset: {ingredients or 'Ei ilmoitettu'}",
        f"Ruokavalio: {diet}",
        f"Enimmäisvalmistusaika: {max_time} minuuttia",
        recipe_context,
        "Keskusteluhistoria:",
    ]

    for item in history[-10:]:
        if not isinstance(item, dict):
            continue

        role = item.get("role")
        content = item.get("content", "")

        if role in ("user", "assistant") and isinstance(content, str):
            label = "Käyttäjä" if role == "user" else "Assistentti"
            prompt_parts.append(f"{label}: {content}")

    prompt_parts.append(f"Käyttäjän uusi viesti: {message.strip()}")
    prompt_parts.append(
        "Vastaa käyttäjän kysymykseen suomeksi. "
        "Huomioi aiempi keskustelu. "
        "Anna konkreettinen vastaus tai vaihtoehtoja tarpeen mukaan."
    )

    prompt = "\n\n".join(prompt_parts)

    response = generate_response(prompt, SYSTEM_PROMPT)

    if not response or not response.strip():
        return "En saanut muodostettua vastausta. Kokeile uudelleen."

    return response.strip()


def format_api_recipes(
    ingredients: str,
    recipes: list[dict],
    diet: str = "Ei erityisruokavaliota",
    max_time: int = 30,
) -> str:
    """Vertaa API:sta saatuja reseptejä käyttäjän tarpeisiin."""

    if not recipes:
        return "Reseptihakusi ei tuottanut sopivia tuloksia."

    recipe_data = []

    for recipe in recipes[:5]:
        recipe_data.append({
            "name": recipe.get("name", "Nimetön resepti"),
            "ingredients": recipe.get("ingredients", []),
            "missing_ingredients": recipe.get(
                "missing_ingredients", []
            ),
        })

    prompt = f"""
Arvioi, sopivatko nämä reseptit käyttäjälle.

Käyttäjän ainekset:
{ingredients}

Ruokavalio:
{diet}

Enimmäisvalmistusaika:
{max_time} minuuttia

Löydetyt reseptit:
{recipe_data}

Suosi reseptejä, jotka sopivat mahdollisimman hyvin käyttäjän aineksiin.
Älä suosittele reseptiä vain siksi, että siinä on yksi yhteinen ainesosa.
Jos yksikään resepti ei vaikuta sopivalta arkiruoalta, kerro se rehellisesti.

Älä keksi lähdetiedoista puuttuvia faktoja.
Älä väitä valmistusaikaa tunnetuksi, jos sitä ei ole annettu.
Vastaa lyhyesti suomeksi.
"""

    response = generate_response(prompt, SYSTEM_PROMPT)

    if not response or not response.strip():
        return "Tekoäly ei tuottanut suositusta."

    return response.strip()

def _keep_known_recipes(
    result: RecipeRecommendation,
    recipes: list[dict],
) -> RecipeRecommendation:
    """Removes picks that are not in the retrieved recipe list (hallucinated recipes)."""

    known = {
        str(recipe.get("name", "")).strip().lower(): recipe.get("name", "")
        for recipe in recipes
    }

    valid_picks = []
    for pick in result.picks:
        exact_name = known.get(pick.recipe_name.strip().lower())
        if exact_name:
            valid_picks.append(pick.model_copy(update={"recipe_name": exact_name}))
        else:
            logger.warning("Removed recipe not in search results: %s", pick.recipe_name)

    if not valid_picks and not result.note:
        return RecipeRecommendation(
            picks=[],
            note="The AI could not recommend any of the recipes found.",
        )

    return RecipeRecommendation(picks=valid_picks, note=result.note)


def recommend_recipes(
    ingredients: str,
    recipes: list[dict],
    diet: str = "Ei erityisruokavaliota",
    max_retries: int = 1,
) -> RecipeRecommendation:
    """Asks the model to choose the best recipes and returns a validated result."""

    if not recipes:
        return RecipeRecommendation(picks=[], note="No recipes were found.")

    recipes = recipes[:5]
    prompt = build_recommendation_prompt(ingredients, diet, recipes)
    schema = RecipeRecommendation.model_json_schema()

    last_error = None

    for _ in range(max_retries + 1):
        raw = generate_response(
            prompt,
            RECOMMENDER_SYSTEM_PROMPT,
            json_schema=schema,
            num_predict=600,
        )

        try:
            result = RecipeRecommendation.model_validate_json(raw)
        except ValidationError as error:
            logger.warning("Invalid model output: %s", raw)
            last_error = error
            continue

        return _keep_known_recipes(result, recipes)

    raise ValueError(f"The model returned invalid output: {last_error}")
