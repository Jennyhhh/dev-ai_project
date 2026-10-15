
from pathlib import Path

from app.ui import create_ui


def main():
    css_path = Path(__file__).resolve().parent.parent / "static" / "style.css"
    css = css_path.read_text(encoding="utf-8")

    demo = create_ui()
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        css=css,
    )


if __name__ == "__main__":
    main()
