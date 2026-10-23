# Evaluation Results Summary

Document your team's evaluation results below.

## Summary Overview

- **Date of Evaluation:** 2026-10-21
- **Model Evaluated:** RecipeRAG paikallinen varajärjestelmä (`nomic-embed-text` / Jaccard-keyword -fallback)
- **Total Test Cases Executed:** 4
- **Passed:** 4
- **Failed:** 0
- **Pass Rate:** 100%

## Performance by Category

| Category | Total Cases | Passed | Failed | Pass Rate |
| :--- | :---: | :---: | :---: | :---: |
| Successful Cases | 1 | 1 | 0 | 100% |
| Difficult Cases | 1 | 1 | 0 | 100% |
| Failure / Edge Cases | 2 | 2 | 0 | 100% |

## Key Findings & Failure Analysis

### What worked well
- **API Fallback -siirtymä:** Järjestelmä nappaa tyylikkäästi kiinni `AttributeError`- tai verkkovirheistä ja siirtyy saumattomasti RAG-tietokannan käyttöön kaatumatta.
- **Deterministinen suodatus:** `filter_recipe_by_diets` -funktion kova koodaus (listat ja ehtolauseet) toimi 100 % tarkkuudella pudottaen maitoa ja voita sisältävät reseptit pois tuloksista.
- **Vikasietoisuus oudoilla syötteillä:** Vaikeat tai olemattomat ainesosat (esim. lohikäärmehedelmä) eivät riko logiikkaa, vaan palauttavat hallitusti tyhjän listan.

### Observed failure modes
- Suoranaisia virheitä ei esiintynyt itse logiikassa, mutta testivaiheessa huomattiin, että englanninkielinen Kaggle-datasetti vaatii toimiakseen englanninkieliset hakusanat, mikäli ei käytetä monikielistä embedding-mallia tai käännösrajapintaa välissä.

