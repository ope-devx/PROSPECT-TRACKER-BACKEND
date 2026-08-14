from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

import requests
import json

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://prospect-tracker-tawny.vercel.app",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_conn():
    if not DATABASE_URL:
        raise HTTPException(
            status_code=500,
            detail="DATABASE_URL is not set. Add it to BACKEND/.env",
        )
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prospects (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            niche TEXT,
            handle TEXT,
            link TEXT,
            followers INTEGER,
            engagement TEXT,
            website TEXT,
            status TEXT,
            contact TEXT,
            spending TEXT,
            pains TEXT,
            score INTEGER,
            notes TEXT,
            date TEXT,
            last_message TEXT
        )
    """)
    conn.commit()
    conn.close()


if DATABASE_URL:
    init_db()


def row_to_dict(row):
    return {
        "id": row[0],
        "name": row[1],
        "niche": row[2],
        "handle": row[3],
        "link": row[4],
        "followers": row[5],
        "engagement": row[6],
        "website": row[7],
        "status": row[8],
        "contact": row[9],
        "spending": row[10],
        "pains": row[11].split(",") if row[11] else [],
        "score": row[12],
        "notes": row[13],
        "date": row[14],
        "last_message": row[15],
    }


@app.get("/prospects")
def get_prospects():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM prospects ORDER BY id")
    rows = cursor.fetchall()
    conn.close()

    return [row_to_dict(row) for row in rows]


class ProspectInput(BaseModel):
    name: str
    niche: str
    handle: str
    link: str
    followers: int
    engagement: str
    website: str
    status: str
    contact: str
    spending: str
    pains: List[str]
    score: int
    notes: str


@app.post("/prospects", status_code=201)
def add_prospect(prospect: ProspectInput):
    allowed = ["new", "contacted", "follow_up", "meeting_booked", "closed", "lost"]
    if prospect.status not in allowed:
        raise HTTPException(
            status_code=400, detail=f"Invalid status: {prospect.status}"
        )

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id FROM prospects WHERE LOWER(name) = LOWER(%s)
        """,
        (prospect.name,),
    )
    existing_prospect = cursor.fetchone()

    if existing_prospect:
        conn.close()
        raise HTTPException(
            status_code=400, detail=f"Prospect with name {prospect.name} already exists"
        )

    cursor.execute(
        """
        INSERT INTO prospects (name, niche, handle, link, followers, engagement, website, status, contact, spending, pains, score, notes, date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *
        """,
        (
            prospect.name,
            prospect.niche,
            prospect.handle,
            prospect.link,
            prospect.followers,
            prospect.engagement,
            prospect.website,
            prospect.status,
            prospect.contact,
            prospect.spending,
            ",".join(prospect.pains),
            prospect.score,
            prospect.notes,
            datetime.now().strftime("%d/%m/%Y"),
        ),
    )
    row = cursor.fetchone()
    conn.commit()
    conn.close()

    return row_to_dict(row)


@app.put("/prospects/{prospect_id}")
def update_prospect(prospect_id: int, prospect: ProspectInput):
    allowed = ["new", "contacted", "follow_up", "meeting_booked", "closed", "lost"]
    if prospect.status not in allowed:
        raise HTTPException(
            status_code=400, detail=f"Invalid status: {prospect.status}"
        )

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE prospects
        SET name=%s, niche=%s, handle=%s, link=%s, followers=%s, engagement=%s,
            website=%s, status=%s, contact=%s, spending=%s, pains=%s, score=%s, notes=%s
        WHERE id=%s
        RETURNING *
        """,
        (
            prospect.name,
            prospect.niche,
            prospect.handle,
            prospect.link,
            prospect.followers,
            prospect.engagement,
            prospect.website,
            prospect.status,
            prospect.contact,
            prospect.spending,
            ",".join(prospect.pains),
            prospect.score,
            prospect.notes,
            prospect_id,
        ),
    )
    row = cursor.fetchone()

    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Prospect not found")

    conn.commit()
    conn.close()

    return row_to_dict(row)


@app.delete("/prospects/{prospect_id}")
def delete_prospect(prospect_id: int):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM prospects WHERE id=%s", (prospect_id,))

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Prospect not found")

    conn.commit()
    conn.close()
    return {"message": f"Prospect {prospect_id} deleted successfully"}


API_KEY = os.getenv("OPENROUTER_API_KEY")


@app.post("/prospects/{prospect_id}/cold-dm-generator")
def generate_cold_dm_message(prospect_id: int):
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM prospects WHERE id=%s", (prospect_id,))
        row = cursor.fetchone()

        if row == None:
            raise HTTPException(status_code=404, detail="Prospect not found")

        client = row_to_dict(row)

        # sytem prompt for if notes exist
        prompt1 = """
                You are a highly experienced sales professional   specializing in cold outreach.
                Write with a direct, conversational, value-first approach.
                Be confident without being pushy, friendly without sounding overly casual, and persuasive without using hype.
                Focus on the prospect's situation and potential benefit rather than talking excessively about the seller.
                Use simple, punchy, natural language and remove unnecessary words.

                You write warm, natural cold DMs to food business owners, as if you genuinely want to help them—not as a salesperson trying to make a quick pitch.

                Use the client's name and needs/details provided. Follow this exact 3-paragraph structure:

                "Hello/Hey/Hi [Name], I was scrolling through Instagram this afternoon and found [Business] — honestly [specific, genuine observation about their page, food, or content]."
                Explain naturally that I actually help food businesses get more orders and visibility by making it easier for customers to find them online, explore their menu and pricing, and order without having to reach out to you first.[you can change this line accoring to the notes provided, but do not invent any details about the business or its Instagram page, be flexible here and adapt to the notes provided, but do not invent any details about the business or its Instagram page.]
                End with: "But before I can tell if I can do the same for you, how do customers find you online and order from you right now? Walk me through that process, just so I understand better."

                Keep it friendly, warm, conversational, and human—like a genuine recommendation from a friend. Avoid corporate language, exaggerated compliments, generic praise, and hard-selling. Never invent details about the business that were not provided. Keep the message concise and preserve the meaning of the template.

                do not use hyphens, or —, or  quotation marks, or extra formatting; return only the finished DM with no explanation.
        """
        # sytem prompt for if notes deoesn't exist
        prompt2 = """
                You write cold DMs for a web designer reaching out to food businesses.
                Use the client's name and business name to personalize the message; never invent facts about the business or its Instagram page.
                Follow this exact structure:
                "Hey [Name], I was scrolling through Instagram this afternoon and found [Business] — honestly, your food looks really good and I wanted to reach out.
                I actually help food businesses get more orders and visibility by making it easy for customers to find you online, explore your menu and pricing, and order without messaging or calling first.
                Before I can tell if I can do the same for you, how do customers order from you right now? Walk me through that process, just so I understand."
                Replace only [Name] and [Business]; do not add, remove, or reorder the main sentences.
                Keep it natural, conversational, simple, and human; return only the finished DM with no explanation, hyphens, quotation marks, or extra formatting.
        """

        SYSTEM_PROMPT = prompt1
        if client["notes"] == None or client["notes"] == "":
            SYSTEM_PROMPT = prompt2

        message = f"Client Name: {client['name']}\n Notes: {client['notes']}\n"

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
            },
            data=json.dumps(
                {
                    "model": "nvidia/nemotron-3-ultra-550b-a55b:free",
                    "messages": [
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT,
                        },
                        {"role": "user", "content": message},
                    ],
                }
            ),
        )

        last_message = response.json()["choices"][0]["message"]["content"]

        cursor.execute(
            "UPDATE prospects SET last_message=%s WHERE id=%s",
            (
                last_message,
                prospect_id,
            ),
        )
        conn.commit()

        return last_message

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="AI request failed")

    finally:
        conn.close()


@app.post("/prospects/{prospect_id}/generate-follow-up-message")
def generate_follow_up_message(prospect_id: int):
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM prospects WHERE id=%s", (prospect_id,))
        row = cursor.fetchone()

        if row == None:
            raise HTTPException(status_code=404, detail="Prospect not found")

        client = row_to_dict(row)

        if client["last_message"] == None or client["last_message"] == "":
            raise HTTPException(status_code=400, detail="No last message!")

        SYSTEM_PROMPT = """
            You are an experienced sales professional who specializes in warm, natural follow-up messages.

            The client has already seen the first message but has not replied, and at least 24 hours have passed. Your job is to write a short follow-up that naturally reopens the conversation without sounding pushy, desperate, or automated.

            Review the first message, client name, and available notes. Do not repeat the first message word-for-word; instead, build naturally from it and use relevant client details when appropriate. Keep the tone warm, friendly, confident, and human, like someone genuinely trying to help. Use simple everyday language, avoid sales jargon, pressure, guilt, and exaggerated claims. Keep the message concise and no more than 3 lines. Return only the follow-up message, with no explanation or extra formatting, hyphnes or quotation mark.
        """

        message = f"Client Name: {client['name']}\n first message I sent: {client['last_message']}\n Notes: {client['notes']}\n"

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
            },
            data=json.dumps(
                {
                    "model": "openrouter/auto",
                    "messages": [
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT,
                        },
                        {"role": "user", "content": message},
                    ],
                }
            ),
        )

        return response.json()["choices"][0]["message"]["content"]

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="AI request failed")

    finally:
        conn.close()
