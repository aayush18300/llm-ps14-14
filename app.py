
"""PS14 - Travel Planner Chatbot (LLM mini project)

Generates a day-wise travel itinerary from destination, budget, number of days
and interests using the Google Gemini API, with a Streamlit UI.
Users can refine the plan through follow-up chat and download it as TXT or PDF.
"""

import os
from io import BytesIO
from xml.sax.saxutils import escape

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

load_dotenv()

MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = (
    "You are a friendly and practical travel planner. "
    "Create realistic day-wise itineraries that fit the user's budget. "
    "Always give estimated costs in the currency the user asks for. "
    "Costs are estimates only; remind the user to verify prices. "
    "Do not invent specific hotel phone numbers or booking links."
)

ITINERARY_PROMPT = """Plan a trip with these details:
- Destination: {destination}
- Number of days: {days}
- Total budget: {budget} {currency}
- Interests: {interests}
- Travelling as: {travellers}

Output format (Markdown):
1. A one-line trip overview.
2. A table with columns: Day | Morning | Afternoon | Evening | Est. Cost ({currency}).
   One row per day. Keep each cell short.
3. A "Budget Breakdown" table (Stay, Food, Local transport, Activities, Misc, Total).
   The total must not exceed the budget.
4. 3 practical tips (best season, local transport, safety).
5. One line: "Costs are approximate - please verify before booking."
"""


def get_client():
    api_key = os.getenv("GEMINI_API_KEY") or st.session_state.get("api_key")

    if not api_key:
        return None

    # FIX: Use Gemini API v1beta to support system instructions
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            api_version="v1beta"
        )
    )

    return client


def ask_llm(client, history):
    """history: list of {"role": "user"/"assistant", "content": str}"""

    contents = [
        types.Content(
            role="user" if m["role"] == "user" else "model",
            parts=[types.Part(text=m["content"])],
        )
        for m in history
    ]

    response = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.7
        ),
    )

    return response.text


def make_pdf(text):
    """Very simple Markdown-ish text to PDF."""

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    for line in text.splitlines():
        line = line.strip()

        if not line or set(line) <= set("|-: "):
            story.append(Spacer(1, 6))
            continue

        if line.startswith("#"):
            story.append(
                Paragraph(escape(line.lstrip("# ")), styles["Heading2"])
            )
        else:
            clean = escape(line.replace("**", "").replace("|", "  |  "))
            story.append(Paragraph(clean, styles["BodyText"]))

    doc.build(story)

    return buf.getvalue()


# ---------------- UI ----------------

st.set_page_config(
    page_title="Travel Planner Chatbot",
    page_icon="🧳"
)

st.title("🧳 Travel Planner Chatbot")

st.caption(
    "Day-wise itinerary with estimated costs, powered by Gemini."
)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:

    st.header("Trip details")

    if not os.getenv("GEMINI_API_KEY"):
        st.session_state.api_key = st.text_input(
            "Gemini API key",
            type="password"
        )

    destination = st.text_input(
        "Destination",
        "Goa, India"
    )

    days = st.number_input(
        "Number of days",
        1,
        14,
        3
    )

    budget = st.number_input(
        "Total budget",
        1000,
        1000000,
        15000,
        step=1000
    )

    currency = st.selectbox(
        "Currency",
        ["INR", "USD", "EUR"]
    )

    travellers = st.selectbox(
        "Travelling as",
        ["Solo", "Couple", "Friends", "Family with kids"]
    )

    interests = st.multiselect(
        "Interests",
        [
            "Beaches",
            "History",
            "Food",
            "Adventure",
            "Nature",
            "Shopping",
            "Temples",
            "Nightlife"
        ],
        default=["Beaches", "Food"]
    )

    generate = st.button(
        "Generate itinerary",
        type="primary"
    )

    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()


client = get_client()


if generate:

    if client is None:
        st.error("Please enter your Gemini API key in the sidebar.")

    elif not destination.strip():
        st.error("Please enter a destination.")

    else:

        prompt = ITINERARY_PROMPT.format(
            destination=destination.strip(),
            days=days,
            budget=budget,
            currency=currency,
            interests=", ".join(interests) or "general sightseeing",
            travellers=travellers,
        )

        st.session_state.messages = [
            {"role": "user", "content": prompt}
        ]

        try:
            with st.spinner("Planning your trip..."):

                reply = ask_llm(
                    client,
                    st.session_state.messages
                )

            st.session_state.messages.append(
                {"role": "assistant", "content": reply}
            )

        except Exception as e:

            st.session_state.messages = []

            st.error(f"API error: {e}")


# Show conversation (skip the first long prompt)

for i, m in enumerate(st.session_state.messages):

    if i == 0:
        continue

    with st.chat_message(m["role"]):
        st.markdown(m["content"])


# Follow-up chat to refine the plan

if len(st.session_state.messages) >= 2:

    followup = st.chat_input(
        "Refine the plan (e.g. 'make it cheaper', 'add a beach day')"
    )

    if followup and client:

        st.session_state.messages.append(
            {"role": "user", "content": followup}
        )

        try:
            with st.spinner("Updating..."):

                reply = ask_llm(
                    client,
                    st.session_state.messages
                )

            st.session_state.messages.append(
                {"role": "assistant", "content": reply}
            )

        except Exception as e:
            st.error(f"API error: {e}")

        st.rerun()

    latest = st.session_state.messages[-1]["content"]

    c1, c2 = st.columns(2)

    c1.download_button(
        "Download .txt",
        latest,
        "itinerary.txt",
        "text/plain"
    )

    c2.download_button(
        "Download .pdf",
        make_pdf(latest),
        "itinerary.pdf",
        "application/pdf"
    )

else:

    st.info(
        "Fill in the sidebar and click **Generate itinerary**."
    )

