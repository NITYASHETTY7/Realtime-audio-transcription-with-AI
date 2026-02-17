import os
import re
import time
import json
import psycopg2
from datetime import date
from dotenv import load_dotenv
from google import genai
import fitz  # PyMuPDF

load_dotenv()
DATABASE_URL   = os.getenv("DATABASE_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env")
client = genai.Client(api_key=GEMINI_API_KEY)

PDF_PATH            = "xnc-1-2-manual-2.pdf"
START_PAGE          = 120          # 0-indexed
END_PAGE            = 170          # exclusive
MAX_WORDS_PER_CHUNK = 400
MIN_CHUNK_LENGTH    = 150
DELAY_SECONDS       = 1.5

# Quota guard — Gemini embedding-001 free tier: 1,500 requests/day
DAILY_QUOTA         = 1_500
QUOTA_SAFETY_BUFFER = 50                                            
QUOTA_FILE          = ".gemini_quota.json"                          
def load_quota() -> dict:
    """Load today's quota usage from disk. Resets automatically on a new day."""
    today = str(date.today())
    if os.path.exists(QUOTA_FILE):
        with open(QUOTA_FILE) as f:
            data = json.load(f)
        if data.get("date") == today:
            return data
    return {"date": today, "used": 0}
def save_quota(data: dict):
    with open(QUOTA_FILE, "w") as f:
        json.dump(data, f)
def quota_remaining(data: dict) -> int:
    return (DAILY_QUOTA - QUOTA_SAFETY_BUFFER) - data["used"]

# Matches lines that look like section headings, e.g.:
#   "3.2 Troubleshooting"  /  "CHAPTER 4"  /  "Error Codes"  /  "A. Safety"
HEADING_RE = re.compile(
    r"^("
    r"(?:\d+[\.\d]*\s+[A-Z].{3,})"       # numbered:  3.2 Some Title
    r"|(?:CHAPTER\s+\w+.*)"              # CHAPTER X
    r"|(?:[A-Z][A-Z\s]{4,})"             # ALL CAPS line (min 5 chars)
    r"|(?:[A-Z]\.\s+[A-Z].{3,})"         # A. Some Title
    r")$"
)
def is_heading(line: str) -> bool:
    return bool(HEADING_RE.match(line.strip()))

def clean_text(text: str) -> str:
    text = text.replace("\x00", "")          # strip NUL bytes — PostgreSQL rejects them
    text = re.sub(r"\.{3,}", " ", text)      # remove dotted TOC lines
    text = re.sub(r"\n\s*\n", "\n", text)    # remove extra blank lines
    text = re.sub(r"\s{2,}", " ", text)      # normalise whitespace
    return text.strip()

def extract_chunks_with_metadata(doc, start_page: int, end_page: int) -> list:
    """
    Returns a list of dicts with:
      - content      : chunk text
      - page_start   : first PDF page in the chunk (1-indexed for readability)
      - page_end     : last PDF page in the chunk
      - section      : nearest heading found at or before the chunk
    """
    chunks = []
    current_words = []
    current_pages = []
    current_section = "Unknown Section"

    def flush(words, pages, section):
        text = " ".join(words).strip()
        if len(text) >= MIN_CHUNK_LENGTH:
            chunks.append({
                "content":    text,
                "page_start": min(pages),
                "page_end":   max(pages),
                "section":    section,
            })

    for page_idx in range(start_page, end_page):
        page     = doc[page_idx]
        page_num = page_idx + 1          # convert to 1-indexed
        raw      = page.get_text("text")
        cleaned  = clean_text(raw)
        for line in cleaned.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Update running section heading when we spot one
            if is_heading(line):
                # Flush existing chunk before starting a new section
                if current_words:
                    flush(current_words, current_pages, current_section)
                    current_words = []
                    current_pages = []
                current_section = line

            words = line.split()
            if len(current_words) + len(words) >= MAX_WORDS_PER_CHUNK:
                flush(current_words, current_pages, current_section)
                current_words = []
                current_pages = []
            current_words.extend(words)
            current_pages.append(page_num)
    # Flush any remaining content
    if current_words:
        flush(current_words, current_pages, current_section)
    return chunks

def get_embedding(text: str) -> list:
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
    )
    return response.embeddings[0].values

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS manual_embeddings (
    id          SERIAL PRIMARY KEY,
    content     TEXT        NOT NULL,
    embedding   VECTOR(3072),
    page_start  INTEGER,
    page_end    INTEGER,
    section     TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
"""

def ensure_schema(cur):
    """Create the table with metadata columns if it doesn't already exist."""
    cur.execute(SCHEMA_SQL)

def main():
    quota     = load_quota()
    remaining = quota_remaining(quota)
    print(f"Gemini quota today: {quota['used']} used / {DAILY_QUOTA} limit  "
          f"({remaining} requests available before safety buffer)\n")
    if remaining <= 0:
        print("Daily quota limit reached. Re-run tomorrow.")
        return

    conn = psycopg2.connect(DATABASE_URL)
    cur  = conn.cursor()
    ensure_schema(cur)
    conn.commit()

    print("Clearing existing rows from manual_embeddings...")
    cur.execute("DELETE FROM manual_embeddings;")
    conn.commit()
    print("Table cleared. Starting fresh.\n")

    print(f"Opening PDF: {PDF_PATH}")
    doc    = fitz.open(PDF_PATH)
    print(f"Extracting pages {START_PAGE + 1} to {END_PAGE} (1-indexed PDF page numbers)...\n")
    chunks = extract_chunks_with_metadata(doc, START_PAGE, END_PAGE)
    doc.close()
    print(f"Total chunks ready to embed: {len(chunks)}")

    if len(chunks) > remaining:
        print(f"WARNING: Only {remaining} quota requests available — "
              f"will embed first {remaining} chunks and stop.\n"
              f"Re-run tomorrow to embed the remaining {len(chunks) - remaining} chunks.\n")
        chunks = chunks[:remaining]
    else:
        print(f"All {len(chunks)} chunks fit within today's quota.\n")

   
    inserted = 0
    skipped  = 0
    for i, chunk in enumerate(chunks, start=1):
        section_label = chunk['section'][:60]
        label = (f"Chunk {i}/{len(chunks)} | "
                 f"Pages {chunk['page_start']}-{chunk['page_end']} | "
                 f"Section: {section_label}")
        print(f"  Embedding {label}...", end=" ", flush=True)
        try:
            embedding = get_embedding(chunk["content"])
            cur.execute(
                """
                INSERT INTO manual_embeddings (content, embedding, page_start, page_end, section)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    chunk["content"],
                    embedding,
                    chunk["page_start"],
                    chunk["page_end"],
                    chunk["section"],
                ),
            )
            conn.commit()
            # Update quota counter after every successful call
            quota["used"] += 1
            save_quota(quota)
            inserted += 1
            print("OK")
        except Exception as e:
            conn.rollback()
            skipped += 1
            print(f"SKIPPED -- {e}")
        time.sleep(DELAY_SECONDS)

    print(f"\nDone!  Inserted: {inserted}  |  Skipped: {skipped}  |  "
          f"Total chunks processed: {len(chunks)}")
    print(f"Gemini quota used today: {quota['used']} / {DAILY_QUOTA}")
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()