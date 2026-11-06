# Sage – Portfolio Chatbot (Flask + OpenRouter)

1. Open this folder in VS Code and make sure Python 3.11.9 is selected.
2. Terminal: `python -m venv venv` then `venv\Scripts\activate` (Windows) or `source venv/bin/activate`
3. `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and paste your OpenRouter key (https://openrouter.ai/keys).
5. Edit `portfolio.json` with your real details.
6. `python app.py` and open http://127.0.0.1:5000

Match your portfolio: edit the colour/font variables at the top of `static/style.css`.
Change the model in `.env` (`OPENROUTER_MODEL`), e.g. `meta-llama/llama-3.3-70b-instruct:free`.
