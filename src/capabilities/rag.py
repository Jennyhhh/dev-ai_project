import json
import logging
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)


class RecipeRAG:
    """Paikallinen RAG-haku reseptiarkistolle.

    Toimii varajärjestelmänä (fallback), jos ulkoinen API ei vastaa.
    """

    def __init__(
        self,
        data_path: str = "data/recipes.json",
        ollama_url: Optional[str] = None,
        embed_model: str = "nomic-embed-text",
    ):
        self.data_path = Path(data_path)
        self.ollama_url = ollama_url or os.getenv(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        )
        self.embed_model = embed_model
        self.recipes: List[Dict[str, Any]] = []
        self.recipe_embeddings: List[List[float]] = []

        self.load_data()

    def load_data(self) -> None:
        """Lataa reseptit data/recipes.json -tiedostosta muistiin."""
        if not self.data_path.exists():
            logger.warning(
                f"Reseptitiedostoa ei löytynyt polusta: {self.data_path}"
            )
            return

        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                self.recipes = json.load(f)
            logger.info(
                f"Ladattu {len(self.recipes)} reseptiä paikalliseen RAG-kantaan."
            )
        except Exception as e:
            logger.error(f"Virhe ladattaessa reseptejä tiedostosta: {e}")

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Hakee tekstin embedding-vektorin paikalliselta Ollama-palvelimelta."""
        url = f"{self.ollama_url}/api/embeddings"
        payload = json.dumps({"model": self.embed_model, "prompt": text}).encode(
            "utf-8"
        )

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=3.0) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("embedding")
        except Exception:
            # Jos Ollaman embedding-malli ei vastaa, käytetään sanapohjaista hakua
            return None

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Laskee kosinisamankaltaisuuden kahden vektorin välille."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm_a = math.sqrt(sum(a * a for a in vec1))
        norm_b = math.sqrt(sum(b * b for b in vec2))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    def _keyword_similarity(
        self, query_ingredients: List[str], recipe_ingredients: List[str]
    ) -> float:
        """Kevyt sanapohjainen osumatarkkuus (Jaccard-samankaltaisuus), jos embeddingejä ei ole saatavilla."""
        query_set = {i.lower().strip() for i in query_ingredients}
        recipe_text = " ".join(recipe_ingredients).lower()

        matches = sum(
            1 for q in query_set if any(q in ing for ing in recipe_ingredients)
        )
        return matches / max(len(query_set), 1)

    def query_recipes(
        self, ingredients: List[str], top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Etsii ja palauttaa osuvimmat reseptit annettujen raaka-aineiden perusteella.

        Tulokset merkitään lähteellä source="rag".
        """
        if not self.recipes:
            self.load_data()
            if not self.recipes:
                return []

        query_text = ", ".join(ingredients)
        query_vector = self._get_embedding(query_text)

        scored_recipes = []

        for idx, recipe in enumerate(self.recipes):
            rec_ingredients = recipe.get("ingredients", [])

            # 1. Jos embeddingit toimivat, lasketaan vektorivertailu
            if query_vector:
                # Luo embedding reseptin aineksille lennossa tai käytä tallennettua
                rec_text = (
                    f"{recipe.get('name', '')}: {', '.join(rec_ingredients)}"
                )
                rec_vector = self._get_embedding(rec_text)
                if rec_vector:
                    score = self._cosine_similarity(query_vector, rec_vector)
                else:
                    score = self._keyword_similarity(
                        ingredients, rec_ingredients
                    )
            else:
                # 2. Vararatkaisu: sanapohjainen osumatarkistus
                score = self._keyword_similarity(ingredients, rec_ingredients)

            scored_recipes.append((score, recipe))

        # Järjestetään pisteytyksen mukaan laskevasti
        scored_recipes.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, recipe in scored_recipes[:top_k]:
            if score > 0.05:  # Hylätään täysin epäoleelliset
                res = dict(recipe)
                res["source"] = "rag"
                res["similarity_score"] = round(score, 3)
                results.append(res)

        return results