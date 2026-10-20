# Reseptiaineisto (RAG Local Fallback Dataset)

Tämä aineisto toimii sovelluksen paikallisena RAG-tietokantana ja varajärjestelmänä (fallbackina), jos ulkoinen resepti-API ei vastaa tai sen kiintiö ylittyy.

## Aineiston tiedot ja lähde

* **Aineiston nimi:** Better Recipes for a Better Life (Recipes Dataset)
* **Lähde:** Kaggle ([https://www.kaggle.com/datasets/thedevastator/better-recipes-for-a-better-life](https://www.kaggle.com/datasets/thedevastator/better-recipes-for-a-better-life))
* **Lisenssi:** **CC0: Public Domain** (Creative Commons Zero 1.0 Universal)
* **Käyttöoikeus:** Aineisto on luovutettu vapaaseen julkiseen käyttöön ilman tekijänoikeusrajoituksia.

## Käsitellyt tiedostot

* `recipes.json`: Alkuperäisestä yli 100 000 reseptin aineistosta poimittu noin 200 reseptin edustava otos.
  * Otoksen rajaus tehtiin suorituskykysyistä ja versionhallinnan tiedostokokorajoitusten vuoksi.
  * Reseptit on jäsennelty muotoon: `id`, `name`, `ingredients` (lista) ja `instructions`.