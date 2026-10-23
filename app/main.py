
from pathlib import Path

from app.ui import create_ui, create_theme


# Projektin juurikansio
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# CSS-tiedoston sijainti
CSS_PATH = PROJECT_ROOT / "static" / "style.css"


def main():
    """Käynnistää AI-reseptisovelluksen."""

    if not CSS_PATH.is_file():
        raise FileNotFoundError(
            f"CSS-tiedostoa ei löytynyt: {CSS_PATH}"
        )

    # Luetaan ulkoasun tyylitiedosto.
    css = CSS_PATH.read_text(encoding="utf-8")

    # Luodaan käyttöliittymä.
    demo = create_ui()

    # Käynnistetään paikallinen palvelin.
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        css=css,
        theme=create_theme(),
    )


if __name__ == "__main__":
    main()
