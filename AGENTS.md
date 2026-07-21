**English Practice Application for Windows Desktop**

This app will feature:
- Typing practice
- Reading practice

**How each works:**
YH
**Typing practice:**
Two text boxes: one contains the original text to be typed, the other contains the user's input. As the user types, words on the **original text side** are highlighted: red for misspelled/incorrect words, green for correctly typed words, until the user finishes typing the full text. After finishing, display metrics: typing speed, accuracy, and time taken.

The user's input text box receives correction highlighting only upon user request (not automatic/real-time).

Typing can also have a sound mode: the user does not see the original text and instead hears it via a text-to-speech model. The user types based on what he hears, and the system checks his writing and gives him feedback.

**Reading practice:**
The user reads a passage taken from the provided context. An AI model generates one question with variants — MCQ, word matching/pairing, a simple question, or fill-in-the-blank. Metric: correct answer rate.

**Context:**
The user must provide context for the practices. The app logic must extract paragraphs from it and use them in the practices. The user can provide PDF files only, and can select which practice(s) to include this context in.

**AI:**
The AI model is accessed via LangChain, using the `langchain_openrouter` package with `langchain`. This model is responsible for:
- Providing passages for the user
- Generating questions
- Rating user performance

**Rating system:**
While typing, mistakes are marked in real time on the original text side (red/green highlighting). Separately, when the user finishes typing a word, it is saved and the AI performs a spelling/grammar check; a short note (message bubble) appears on the word explaining the problem and how to fix it. The user can enable/disable this feature, or set it to run only after finishing.

**UI:**
3 tabs: Reading, Typing, Settings. Built with PyQt6.

**Persistent data:**
User data must be saved persistently in an SQLite database file named `Data.db`, located under a folder named after the app inside the Windows Documents folder. Database access must use an ORM (SQLAlchemy) — no raw SQL code inside the Python codebase.

**Project structure:**
Must follow OOP and SOLID principles strictly. Must have a clear folder structure with clear naming of files and classes. Must use Pydantic and declare each value object; using `Any` or leaving types undeclared is not allowed.

**Current layout (implemented):**
```
main.py                     # entry point
app/
  core/       config.py (paths, Data.db), database.py (engine/session), workers.py (TaskRunner), animations.py (fade_in/slide_in)
  domain/     models.py (Pydantic value objects), tables.py (SQLAlchemy ORM)
  services/   pdf_service, typing_engine (pure logic), ai_service (ChatOpenRouter), tts_service (Chatterbox)
  repositories/  document_repository, session_repository (settings + practice sessions)
  ui/         typing_tab, reading_tab, settings_tab, widgets/ (HighlightTextEdit, MessageBubble, BusyIndicator)
tests/        test_typing_engine.py
```

**Conventions:**
- DB access only inside `repositories/` (SQLAlchemy ORM, no raw SQL).
- Slow/blocking calls (AI, TTS) run via `TaskRunner` on worker threads; only GUI-thread callbacks touch widgets.
- `AIService` raises `ValueError` if the OpenRouter key is missing; UI surfaces it in a message box.
- TTS model loads lazily on first sound-mode use; WAVs cached in `Documents/EnglishPractice/tts_cache`.

**Commands:**
- Setup: `uv venv --python 3.12 && uv pip install -e .` (or `uv sync`)
- Run: `uv run python main.py`
- Tests: `$env:PYTHONPATH='.'; uv run python tests/test_typing_engine.py`
