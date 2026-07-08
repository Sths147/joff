# joff

Get the latest updates of the french law with this personal summarizer of the french Journal Officiel

## POC — récupération du JO via l'API Légifrance (PISTE)

`dl_journal.py` récupère le sommaire du Journal Officiel (JORF) via l'API Légifrance de PISTE (production par défaut, `PISTE_ENV=sandbox` pour l'environnement de test).

### Prérequis

1. Un compte sur [piste.gouv.fr](https://piste.gouv.fr) avec une application souscrite à l'API **Légifrance**.
2. Copier `.env.example` en `.env` et y mettre le `client_id` / `client_secret` de l'application.
3. Python 3 avec `requests` (`pip install requests`).

### Usage

```bash
python3 dl_journal.py              # JO du jour
python3 dl_journal.py 2026-07-01   # JO d'une date donnée
python3 dl_journal.py --last       # dernier JO paru
```

Le script :
1. obtient un jeton OAuth2 (client credentials) sur `oauth.piste.gouv.fr` ;
2. appelle `POST /consult/jorfCont` (par date) ou `POST /consult/lastNJo` puis `jorfCont` (par id) sur `api.piste.gouv.fr/dila/legifrance/lf-engine-app` ;
3. affiche la liste des textes du sommaire (titre, nature, id `JORFTEXT...`) et sauvegarde la réponse brute dans `jo_raw.json`.

Note : le JO ne paraît pas tous les jours — si la date du jour ne renvoie rien, utiliser `--last`.

## Récupération du texte intégral et recherche sémantique

Prérequis supplémentaire : `pip install sentence-transformers` (installe PyTorch, ~2 Go ; le modèle d'embeddings `intfloat/multilingual-e5-small`, ~470 Mo, est téléchargé au premier lancement).

```bash
python3 fetch_texts.py             # texte intégral des textes du JO du jour → data/<date>/
python3 fetch_texts.py --last      # ou du dernier JO paru
python3 vectorize.py               # découpe + vectorise tout data/ → data/index/
python3 search.py "prix des médicaments remboursés"   # recherche sémantique (top 5)
```

- `fetch_texts.py` appelle `POST /consult/jorf` avec chaque `textCid` du sommaire et extrait le texte brut du HTML.
- `vectorize.py` découpe chaque texte en chunks (~1200 caractères), les vectorise localement et stocke l'index (numpy + jsonl) dans `data/index/`.
- `search.py` vectorise la requête et renvoie les chunks les plus proches (similarité cosinus).

## Résumé par LLM (API Mistral, gratuite)

Prérequis : une clé API Mistral (plan gratuit « Experiment ») créée sur [console.mistral.ai](https://console.mistral.ai), à mettre dans le `.env` (`MISTRAL_API_KEY=...`).

```bash
python3 summarize.py             # résumé thématique global du dernier JO téléchargé
python3 summarize.py "santé"     # résumé ciblé : recherche vectorielle puis résumé des extraits
```

- Sans argument : envoie les titres du sommaire à Mistral pour un résumé global par thèmes.
- Avec un sujet : sélectionne les chunks les plus proches dans l'index (`-k N`, défaut 10), et demande à Mistral de les résumer en citant les identifiants `JORFTEXT...` — c'est lui qui écarte les extraits hors sujet remontés par la recherche vectorielle.
- Modèle par défaut : `mistral-small-latest` (changeable via `MISTRAL_MODEL` dans le `.env`).
