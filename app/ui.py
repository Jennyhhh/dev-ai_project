
import html
import traceback
from pathlib import Path

import gradio as gr

from src.services.recipe_service import search_recipes
from src.services.ai_service import (
    recommend_recipes,
    chat_with_assistant,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSS_PATH = PROJECT_ROOT / "static" / "style.css"


def create_theme():
    """Luo sovelluksen väriteeman."""

    return gr.themes.Soft(
        primary_hue="orange",
        secondary_hue="stone",
        neutral_hue="stone",
    ).set(
        body_background_fill="#f7f3ed",
        body_text_color="#49372b",
        block_background_fill="#fffcf8",
        block_border_color="#e8ded2",
        input_background_fill="#ffffff",
        input_border_color="#e8ded2",
        input_placeholder_color="#998779",
        button_primary_background_fill="#c87542",
        button_primary_background_fill_hover="#ad6035",
        button_primary_text_color="#ffffff",
    )


def find_recipes(ingredients, diet, max_time):
    """Hakee reseptit ja palauttaa käyttöliittymän tulokset."""

    if not ingredients or not ingredients.strip():
        return (
            "",
            "Kirjoita ensin vähintään yksi ainesosa.",
            [],
            gr.update(choices=[], value=None),
            [],
        )

    try:
        recipes = search_recipes(ingredients)
    except Exception:
        traceback.print_exc()
        return (
            "",
            "Reseptien haku epäonnistui. Tarkista verkkoyhteys ja yritä uudelleen.",
            [],
            gr.update(choices=[], value=None),
            [],
        )

    if not recipes:
        return (
            "",
            "Reseptejä ei löytynyt. Kokeile muita aineksia.",
            [],
            gr.update(choices=[], value=None),
            [],
        )

    cards = []

    for recipe in recipes[:10]:
        name = html.escape(
            str(recipe.get("name") or "Nimetön resepti")
        )
        image_url = str(recipe.get("image") or "")
        matched = recipe.get("matched_ingredients", [])
        missing = recipe.get("missing_ingredients", [])
        instructions = str(recipe.get("instructions") or "")

        matched_html = ", ".join(
            html.escape(str(item)) for item in matched
        )
        missing_html = ", ".join(
            html.escape(str(item)) for item in missing
        )
        instructions_html = html.escape(instructions)

        image_html = ""

        if image_url.startswith(("https://", "http://")):
            safe_image_url = html.escape(image_url, quote=True)
            image_html = (
                f'<img class="recipe-image" src="{safe_image_url}" '
                f'alt="{name}" loading="lazy">'
            )

        cards.append(
            f"""
            <article class="recipe-card">
                {image_html}
                <h3>{name}</h3>

                <p>
                    <strong>Sinulta löytyvät:</strong><br>
                    {matched_html or "Ei tunnistettuja osumia"}
                </p>

                <p>
                    <strong>Mahdollisesti puuttuvat:</strong><br>
                    {missing_html or "Ei tunnistettuja puuttuvia aineksia"}
                </p>

                <details class="recipe-instructions-container">
                    <summary class="recipe-summary">
                        Avaa alkuperäinen valmistusohje
                    </summary>
                    <div class="recipe-instructions">
                        {instructions_html or "Valmistusohje puuttuu."}
                    </div>
                </details>
            </article>
            """
        )

    ai_html = ""
    status_message = (
        f"Haettiin {len(recipes)} reseptiä. "
        f"Näytetään enintään {min(len(recipes), 10)} reseptiä."
    )

    try:
        recommendation = recommend_recipes(
            ingredients=ingredients,
            recipes=recipes[:5],
            diet=diet,
        )

        recipes_by_name = {recipe.get("name"): recipe for recipe in recipes[:5]}

        picks_html = ""
        for pick in recommendation.picks:
            recipe = recipes_by_name.get(pick.recipe_name, {})
            matched = ", ".join(recipe.get("matched_ingredients", [])) or "-"
            picks_html += (
                f"<li><strong>{html.escape(pick.recipe_name)}</strong><br>"
                f"<small>Käyttää aineksiasi: {html.escape(matched)}</small><br>"
                f"{html.escape(pick.reason)}</li>"
            )

        list_html = f"<ol>{picks_html}</ol>" if picks_html else ""
        note_html = (
            f"<p><em>{html.escape(recommendation.note)}</em></p>"
            if recommendation.note
            else ""
        )

        ai_html = f"""
        <section class="ai-recommendations">
            <h2>🤖 Llama 3.2:n suositukset</h2>
            <p>
                Tekoäly valitsee löytyneistä resepteistä
                parhaiten aineksiisi sopivat.
            </p>
            {list_html}
            {note_html}
        </section>
        """

    except Exception:
        traceback.print_exc()
        status_message += (
            " AI-suosituksia ei saatu tällä kertaa, "
            "mutta reseptit näytetään normaalisti."
        )

    output = f"""
    <div class="recipe-results">
        {ai_html}
        <h2 class="results-heading">🍳 TheMealDB:n reseptit</h2>
        <div class="recipe-grid">
            {''.join(cards)}
        </div>
    </div>
    """

    available_recipes = recipes[:10]
    recipe_names = [
        str(recipe.get("name") or "Nimetön resepti")
        for recipe in available_recipes
    ]

    return (
        output,
        status_message,
        available_recipes,
        gr.update(
            choices=recipe_names,
            value=recipe_names[0] if recipe_names else None,
        ),
        [],
    )



def respond_to_chat(
    message,
    history,
    ingredients,
    diet,
    max_time,
    selected_recipe_name,
    recipes,
):
    """Käsittelee keskustelun Gradio 6.30:n viestimuodossa."""

    history = list(history or [])

    if not message or not message.strip():
        return history, ""

    message = message.strip()

    selected_recipe = next(
        (
            recipe
            for recipe in (recipes or [])
            if recipe.get("name") == selected_recipe_name
        ),
        None,
    )

    # Säilytetään vain kelvolliset keskusteluviestit.
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
            message=message,
            history=ai_history,
            ingredients=ingredients or "",
            diet=diet or "Ei erityisruokavaliota",
            max_time=int(max_time),
            selected_recipe=selected_recipe,
        )

        answer = str(answer or "").strip()

        if not answer:
            answer = "Tekoäly ei tällä kertaa tuottanut vastausta."

    except Exception:
        traceback.print_exc()
        answer = (
            "Viestin käsittely epäonnistui. Tarkista, että Ollama "
            "on käynnissä ja Llama 3.2 -malli on asennettu. "
            "Tarkempi virheilmoitus löytyy terminaalista."
        )

    history.append({
        "role": "user",
        "content": message,
    })
    history.append({
        "role": "assistant",
        "content": answer,
    })

    return history, ""


def clear_chat():
    """Tyhjentää keskusteluhistorian."""

    return []


def create_ui():
    """Rakentaa sovelluksen käyttöliittymän."""

    if not CSS_PATH.is_file():
        raise FileNotFoundError(
            f"CSS-tiedostoa ei löytynyt: {CSS_PATH}"
        )

    with gr.Blocks(
        title="Mitä tänään syötäisiin?"
    ) as demo:

        gr.Markdown(
            """
            # 🍳 Mitä tänään syötäisiin?
            ### Löydä ruokaideoita niistä aineksista, joita sinulla jo on.
            """,
            elem_id="app-header",
        )

        recipes_state = gr.State([])

        with gr.Row():
            with gr.Column(scale=1, min_width=0):
                pass

            with gr.Column(
                scale=10,
                min_width=0,
                elem_id="search-panel-column",
            ):
                with gr.Column(elem_id="search-panel"):
                    ingredients = gr.Textbox(
                        label="Mitä aineksia sinulla on?",
                        placeholder="Esim. chicken, rice, tomato",
                        lines=2,
                        elem_id="ingredients-input",
                    )

                    diet = gr.Dropdown(
                        choices=[
                            "Ei erityisruokavaliota",
                            "Kasvisruoka",
                            "Vegaaninen",
                            "Gluteeniton",
                            "Laktoositon",
                        ],
                        value="Ei erityisruokavaliota",
                        label="Ruokavalio",
                        elem_id="diet-select",
                    )

                    max_time = gr.Slider(
                        minimum=10,
                        maximum=120,
                        value=30,
                        step=10,
                        label="Enimmäisvalmistusaika (min)",
                        elem_id="time-slider",
                    )

                    search_button = gr.Button(
                        "🔎 Hae reseptejä",
                        variant="primary",
                        elem_id="search-button",
                    )

        status = gr.Markdown(
            "Reseptiehdotukset ilmestyvät tähän.",
            elem_id="status-message",
        )

        recipe_output = gr.HTML(elem_id="recipe-output")

        gr.Markdown("---")

        gr.Markdown(
            """
            ## 💬 Kysy lisää ruoka-assistentilta

            Kysy resepteistä, pyydä vaihtoehtoja tai tarkenna valmistusohjeita.
            """
        )

        selected_recipe = gr.Dropdown(
            choices=[],
            label="Resepti, josta haluat keskustella",
            info=(
                "Valitse resepti tai jätä valinta ennalleen "
                "yleisiä kysymyksiä varten."
            ),
            interactive=True,
        )

        chatbot = gr.Chatbot(
            label="Keskustelu Llama 3.2:n kanssa",
            height=380,
        )

        with gr.Row():
            chat_message = gr.Textbox(
                label="Viesti",
                placeholder="Esim. Millä voisin korvata kerman?",
                lines=2,
                scale=5,
            )

            send_button = gr.Button(
                "Lähetä",
                variant="primary",
                scale=1,
            )

        clear_button = gr.Button("Tyhjennä keskustelu")

        search_button.click(
            fn=find_recipes,
            inputs=[ingredients, diet, max_time],
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
            max_time,
            selected_recipe,
            recipes_state,
        ]

        chat_outputs = [chatbot, chat_message]

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

    return demo


if __name__ == "__main__":
    app = create_ui()
    css_content = CSS_PATH.read_text(encoding="utf-8")

    app.launch(
        css=css_content,
        theme=create_theme(),
    )
