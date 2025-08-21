## Architecture overview

### Domains
- **analysis**: text/OCR processing, interactive HTML, API
- **users**: auth, profile, save vocabulary
- **vocab**: models, recall updates, global translations
- **billing**: subscriptions, admin tooling
- **webext**: browser extension

### Analysis core (lego pipeline)
- `analysis/core/config.py`: `get_limits(_) -> { max_words }`
- `analysis/core/input_normalize.py`: `normalize_input(payload) -> text`
- `analysis/core/sentences.py`: `split_text(text) -> sentences`
- `analysis/core/mecab.py`: `analyze(text) -> tokens`
- `analysis/core/interactive_rules.py`: `interactive(pos) -> bool`
- `analysis/core/vocab_service.py`:
  - `get_user_vocab(user) -> dict`
  - `get_vocab_words(user) -> set`
  - `add_words({ user, words, meta }) -> { added }`
  - `batch_update_recalls({ user, interactions }) -> { updated }`
- `analysis/core/translate_service.py`:
  - `translate_word(word) -> str`
  - `translate_sentence(sentence) -> str`
- `analysis/core/interactive_build.py`:
  - `build_html({ sentence, results, vocab_words }) -> html`
  - `build_words_json({ results, vocab_map }) -> list`
- `analysis/core/pipeline.py`:
  - `analyze({ user, text }) -> { html, words }`
  - `finish({ user, text, meta }) -> { added_count, words_added }`

### Analysis app
- `analysis/api.py`: unified endpoints calling pipeline
  - `POST /analysis/api/analyze`
  - `POST /analysis/api/finish`
  - `POST /analysis/api/batch-recall`
  - `POST /analysis/api/translate-word`
  - `POST /analysis/api/translate-sentence`
- `analysis/views.py`: page views, image upload, hover tracking
- `analysis/urls.py`: routes
- `analysis/mecab_utils.py`: MeCab integration, interactive HTML, caching helpers
- `analysis/ocr_processing.py`, `analysis/image_handling.py`: OCR utilities
- `analysis/static/analysis/js/interactive/*`: frontend interaction modules

### Users, Vocab, Billing
- `users/views.py`: profile rendering, save vocabulary
- `vocab/models.py`: `Vocabulary`, `GlobalTranslation`, recall fields
- `vocab/bayesian_recall.py`: recall updates
- `billing/*`: subscription models, views, admin tooling

### Web extension
- `webext/background.js`: calls unified API, relays results to content script
- `webext/content.js`: renders interactive overlays in-page
- `webext/popup.*`: login, annotate actions

### Common tasks map
- Change max words cap: `analysis/core/config.py`
- Change interactive POS: `analysis/core/interactive_rules.py`
- Change HTML building: `analysis/mecab_utils.py`
- Add vocab side effects: `analysis/core/vocab_service.py`
- Translation behavior: `analysis/core/translate_service.py`
- API surface: `analysis/api.py`, `analysis/urls.py`
- Frontend behavior: `analysis/static/analysis/js/interactive/*.js`
- Extension calls: `webext/background.js`, `webext/content.js`

### Tests
- `analysis/tests.py`: pipeline smoke tests

### Conventions
- Small functions, one input/one output
- Single source of truth for JS under `analysis/static/analysis/js`
- Unified `/analysis/api/*` endpoints for clients
