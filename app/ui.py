
import html
import logging

import gradio as gr

from src.services.recipe_service import search_recipes
from src.services.ai_service import recommend_recipes, chat_with_assistant
from src.capabilities.memory import (
    UserPreferences,
    load_preferences,
    save_preferences,
    parse_staples,
    remove_pantry_staples,
)


logger = logging.getLogger(__name__)

DIET_CHOICES = [
    "No dietary restrictions",
    "Vegetarian",
    "Vegan",
    "Gluten-free",
    "Lactose-free",
]

DIET_TRANSLATIONS = {
    "Ei erityisruokavaliota": "No dietary restrictions",
    "Kasvisruoka": "Vegetarian",
    "Vegaaninen": "Vegan",
    "Gluteeniton": "Gluten-free",
    "Laktoositon": "Lactose-free",
}

NO_RECIPE_SELECTED = "No recipe selected"


def create_theme():
    return gr.themes.Soft(
        primary_hue="orange",
        secondary_hue="stone",
        neutral_hue="stone",
    )


def safe_text(value):
    return html.escape(str(value or ""), quote=True)


def create_recipe_card(recipe):
    name = safe_text(recipe.get("name", "Unnamed recipe"))
    image_url = str(recipe.get("image") or "")

    image_html = ""
    if image_url.startswith(("https://", "http://")):
        image_html = (
            f'<img class="recipe-image" '
            f'src="{safe_text(image_url)}" '
            f'alt="{name}" loading="lazy">'
        )

    matched = recipe.get("matched_ingredients") or []
    missing = recipe.get("missing_ingredients") or []
    ingredients = recipe.get("ingredients") or []

    matched_text = (
        ", ".join(safe_text(x) for x in matched)
        or "No matching ingredients identified"
    )

    missing_text = (
        ", ".join(safe_text(x) for x in missing)
        or "No additional ingredients identified"
    )

    ingredients_text = (
        ", ".join(safe_text(x) for x in ingredients)
        or "Ingredient information unavailable"
    )

    instructions = safe_text(
        recipe.get("instructions")
        or "Cooking instructions are unavailable."
    )

    source = recipe.get("source", "")
    source_name = {
        "api": "TheMealDB",
        "rag": "Local recipe collection",
    }.get(source, "Recipe collection")

    return f"""
    <article class="recipe-card">
        {image_html}
        <h3>{name}</h3>
        <p class="recipe-source">{safe_text(source_name)}</p>

        <div class="recipe-detail">
            <strong>Ingredients you have:</strong>
            <p>{matched_text}</p>
        </div>

        <div class="recipe-detail">
            <strong>Additional ingredients needed:</strong>
            <p>{missing_text}</p>
        </div>

        <details class="recipe-instructions-container">
            <summary class="recipe-summary">
                View cooking instructions
            </summary>

            <div class="recipe-instructions">
                <strong>Recipe ingredients:</strong>
                <p>{ingredients_text}</p>

                <strong>Instructions:</strong>
                <p>{instructions}</p>
            </div>
        </details>
    </article>
    """


def create_recommendations_html(recommendation, recipes):
    if recommendation is None:
        return ""

    known_names = {
        str(recipe.get("name", "")).casefold()
        for recipe in recipes
    }

    items = []

    for pick in recommendation.picks:
        name = str(pick.recipe_name)

        if name.casefold() not in known_names:
            continue

        items.append(
            "<li>"
            f"<strong>{safe_text(name)}</strong>"
            f"<p>{safe_text(pick.reason)}</p>"
            "</li>"
        )

    items_html = (
        "<ol>" + "".join(items) + "</ol>"
        if items
        else "<p>No specific recommendations were available.</p>"
    )

    note = safe_text(recommendation.note)
    note_html = (
        f"<p class='ai-note'>{note}</p>"
        if note
        else ""
    )

    return f"""
    <section class="ai-recommendations">
        <h2>🤖 Llama 3.2 Recommendations</h2>
        {items_html}
        {note_html}
    </section>
    """


def find_recipes(ingredients, diet, pantry_text):
    empty_selection = gr.update(
        choices=[NO_RECIPE_SELECTED],
        value=NO_RECIPE_SELECTED,
    )

    if not ingredients or not ingredients.strip():
        return (
            "",
            "Please enter at least one ingredient.",
            [],
            empty_selection,
            [],
        )

    try:
        staples = parse_staples(pantry_text or "")
    except Exception:
        logger.exception("Could not parse pantry staples")
        staples = []

    try:
        save_preferences(
            UserPreferences(
                diet=diet,
                pantry_staples=staples,
            )
        )
    except Exception:
        logger.exception("Could not save preferences")

    diet_preferences = (
        []
        if diet == "No dietary restrictions"
        else [diet]
    )

    try:
        recipes = search_recipes(
            ingredients_text=ingredients.strip(),
            diet_preferences=diet_preferences,
            limit=10,
        )
    except Exception:
        logger.exception("Recipe search failed")
        return (
            "",
            "Recipe search failed. Check the terminal for details.",
            [],
            empty_selection,
            [],
        )

    if not recipes:
        return (
            "",
            "No recipes found. Try other ingredients or "
            "a different dietary preference.",
            [],
            empty_selection,
            [],
        )

    try:
        recipes = remove_pantry_staples(recipes, staples)
    except Exception:
        logger.exception("Could not process pantry staples")

    recipes = recipes[:10]

    cards_html = "".join(
        create_recipe_card(recipe)
        for recipe in recipes
    )

    recommendation_html = ""
    status = f"Found {len(recipes)} recipes."

    try:
        recommendation = recommend_recipes(
            ingredients=ingredients,
            recipes=recipes[:5],
            diet=diet,
        )

        recommendation_html = create_recommendations_html(
            recommendation,
            recipes[:5],
        )
    except Exception:
        logger.exception("AI recommendations failed")
        status += (
            " AI recommendations are currently unavailable, "
            "but the recipe search succeeded."
        )

    results_html = f"""
    <div class="recipe-results">
        {recommendation_html}

        <h2 class="results-heading">🍳 Found Recipes</h2>

        <div class="recipe-grid">
            {cards_html}
        </div>
    </div>
    """

    recipe_names = [
        str(recipe.get("name") or "Unnamed recipe")
        for recipe in recipes
    ]

    recipe_choices = [
        NO_RECIPE_SELECTED,
        *recipe_names,
    ]

    return (
        results_html,
        status,
        recipes,
        gr.update(
            choices=recipe_choices,
            value=NO_RECIPE_SELECTED,
        ),
        [],
    )


def respond_to_chat(
    message,
    history,
    ingredients,
    diet,
    selected_recipe_name,
    recipes,
):
    history = list(history or [])

    if not message or not message.strip():
        return history, ""

    user_message = message.strip()

    selected_recipe = None

    if (
        selected_recipe_name
        and selected_recipe_name != NO_RECIPE_SELECTED
    ):
        selected_recipe = next(
            (
                recipe
                for recipe in (recipes or [])
                if recipe.get("name") == selected_recipe_name
            ),
            None,
        )

    ai_history = [
        {
            "role": item["role"],
            "content": item["content"],
        }
        for item in history
        if isinstance(item, dict)
        and item.get("role") in ("user", "assistant")
        and isinstance(item.get("content"), str)
    ]

    try:
        answer = chat_with_assistant(
            message=user_message,
            history=ai_history,
            ingredients=ingredients or "",
            diet=diet or "No dietary restrictions",
            selected_recipe=selected_recipe,
        )

        answer = str(answer or "").strip()

        if not answer:
            answer = "The AI did not generate a response."

    except Exception:
        logger.exception("Chatbot response failed")
        answer = (
            "I couldn't generate a response. "
            "Please check that Ollama is running and try again."
        )

    history.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    history.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )

    return history, ""


def clear_chat():
    return []


def load_saved_preferences():
    try:
        preferences = load_preferences()

        diet = DIET_TRANSLATIONS.get(
            preferences.diet,
            preferences.diet,
        )

        if diet not in DIET_CHOICES:
            diet = "No dietary restrictions"

        staples = ", ".join(
            str(item)
            for item in (preferences.pantry_staples or [])
        )

        return diet, staples

    except Exception:
        logger.exception("Could not load saved preferences")
        return "No dietary restrictions", ""


def create_ui():
    with gr.Blocks(
        title="What Should I Cook Today?",
        theme=create_theme(),
    ) as demo:

        gr.Markdown(
            """
            # 🍳 What Should I Cook Today?
            Discover recipes using ingredients you already have.
            """,
            elem_id="app-header",
        )

        recipes_state = gr.State([])

        # Recipe search panel
        with gr.Column(elem_id="search-panel-column"):
            with gr.Column(elem_id="search-panel"):

                ingredients = gr.Textbox(
                    label="What ingredients do you have?",
                    placeholder="e.g. chicken, rice, tomato",
                    lines=2,
                    elem_id="ingredients-input",
                )

                diet = gr.Dropdown(
                    choices=DIET_CHOICES,
                    value="No dietary restrictions",
                    label="Dietary preference",
                    elem_id="diet-select",
                )

                pantry = gr.Textbox(
                    label="Pantry staples you always have",
                    info=(
                        "These ingredients will not appear in "
                        "the missing ingredients list. "
                        "Preferences are saved when searching."
                    ),
                    placeholder="e.g. salt, pepper, olive oil",
                    lines=1,
                    elem_id="pantry-input",
                )

                search_button = gr.Button(
                    "🔎 Find Recipes",
                    variant="primary",
                    elem_id="search-button",
                )

        status = gr.Markdown(
            "Your recipe suggestions will appear here.",
            elem_id="status-message",
        )

        recipe_output = gr.HTML(
            elem_id="recipe-output",
        )

        gr.Markdown("---")

        gr.Markdown(
            """
            ## 💬 Ask the AI Cooking Assistant

            Ask general cooking questions, get ingredient
            substitution ideas, or discuss a specific recipe.

            You can start chatting without searching for
            or selecting a recipe.
            """,
            elem_id="chat-header",
        )

        selected_recipe = gr.Dropdown(
            choices=[NO_RECIPE_SELECTED],
            value=NO_RECIPE_SELECTED,
            label="Recipe to discuss (optional)",
            info=(
                "Leave this as 'No recipe selected' for "
                "general cooking questions. "
                "Choose a recipe after searching if you "
                "want recipe-specific help."
            ),
            interactive=True,
            elem_id="selected-recipe",
            )

        chatbot = gr.Chatbot(
            label="Chat with Llama 3.2",
            height=380,
            elem_id="chatbot-panel",
        )

        with gr.Row(elem_id="chat-input-row"):
            chat_message = gr.Textbox(
                label="Your message",
                placeholder=(
                    "e.g. What can I cook with potatoes and eggs?"
                ),
                lines=2,
                scale=5,
                elem_id="chat-message-input",
            )

            send_button = gr.Button(
                "Send",
                variant="primary",
                scale=1,
                elem_id="chat-send-button",
            )

        clear_button = gr.Button(
            "Clear conversation",
            elem_id="chat-clear-button",
        )

        search_button.click(
            fn=find_recipes,
            inputs=[
                ingredients,
                diet,
                pantry,
            ],
            outputs=[
                recipe_output,
                status,
                recipes_state,
                selected_recipe,
                chatbot,
            ],
        )

        chat_inputs = [
            chat_message,
            chatbot,
            ingredients,
            diet,
            selected_recipe,
            recipes_state,
        ]

        chat_outputs = [
            chatbot,
            chat_message,
        ]

        send_button.click(
            fn=respond_to_chat,
            inputs=chat_inputs,
            outputs=chat_outputs,
        )

        chat_message.submit(
            fn=respond_to_chat,
            inputs=chat_inputs,
            outputs=chat_outputs,
        )

        clear_button.click(
            fn=clear_chat,
            inputs=[],
            outputs=[chatbot],
        )

        demo.load(
            fn=load_saved_preferences,
            inputs=[],
            outputs=[diet, pantry],
        )

    return demo
