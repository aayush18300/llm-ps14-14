<<<<<<< HEAD
# PS14 - Travel Planner Chatbot

**Problem statement:** Planning trips takes hours of searching. This app generates a day-wise
itinerary from destination, budget, number of days and interests, and lets the user refine it
through follow-up chat. The plan can be downloaded as TXT or PDF.

## Tech stack
- Python, Streamlit (UI)
- Google Gemini API (`gemini-2.5-flash`) via `google-genai`
- ReportLab (PDF download)

## How to run
```bash
pip install -r requirements.txt
cp .env.example .env        # then put your free Gemini key in .env
streamlit run app.py
```
Get a free key at https://aistudio.google.com/apikey. If no `.env` is present, the app asks for
the key in the sidebar.

## Features
- Form for destination, days, budget, currency, travellers and interests
- Day-wise table (morning / afternoon / evening) with estimated costs
- Budget breakdown that must stay within the budget
- Follow-up chat to refine ("make it cheaper", "add a beach day")
- Download as `.txt` or `.pdf`

## Screenshots
Add 1-2 screenshots here (e.g. `screenshots/output1.png`).

## Note
Costs are AI-generated estimates; verify before booking.
=======
# llm-ps14-14
>>>>>>> origin/main
