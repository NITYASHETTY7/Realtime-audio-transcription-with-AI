
  

# Live AI Audio Transcription Assistant : Development Roadmap & Sprint Planning

## Project Overview

**Timeline:**  2 Weeks (4 sprints)
**Sprint Duration:**  4 Micro-Sprints (3–4 days each)
**Methodology:**  Agile (Parallel Execution Strategy)
**Team Composition:**  -   2 AI/Backend Intern

----------

## 🏃 Sprint 1: Real-Time Audio & Transcription 

**Duration:**  Days 1-3  
**Goal:** Build live microphone streaming and transcription system.
**Total Estimated Effort:** 2 Days

### [AI-01] Microphone Capture(PyAudio)
-   **Type:**  AI / Backend
-   **Priority:**  P0 (Blocker)
-   **Description:**
    - Implement local microphone capture using PyAudio
     -   Stream audio in small chunks (100–300ms)
    -   Ensure non-blocking audio loop
    -   Handle device permission errors
-   **Acceptance Criteria:**
    -    Audio stream captured continuously
    -   No audio buffer overflow
    -   CPU usage stable
    -   Works on Windows/Linux
 - **Estimated Delivery Date:** 14/02/2026
    
### [AI-02] Deepgram Streaming Integration

-   **Type:**  Backend / AI
-   **Priority:**  P0 (Blocker)
-   **Description:**
    -    Connect to Deepgram Streaming API
    -   Send audio chunks via WebSocket
    -   Receive:
        -   Live transcript
        -   Speaker labels
        -   Pause detection signals
       -   Implement transcript buffering logic
-   **Acceptance Criteria:**
    -  Transcript latency < 500ms
    -   Speaker labels visible
    -   Pause detection working
    -   No audio stored locally
 - **Estimated Delivery Date:** 16/02/2026


### [BE-01] Transcript Buffer & Console Monitoring, Persistence trigger

-   **Type:**  Backend
-   **Priority:**  P1
-   **Description:**
    -   Print transcript live in terminal
    -   Maintain rolling transcript window
    - Append most recent chunk
    -   Store temporary in-memory transcript buffer
    - Speech break appends newest text chunk to convo.txt with minimal latency.
-   **Acceptance Criteria:**
    -  Transcript updates instantly
    -   Buffer correctly stores last N seconds
    - No memory leaks
    -  Append on speech break, ensure file locking safety.
  - **Estimated Delivery Date:** 16/02/2026

----------

## 🏃 Sprint 2: Intelligence Layer (Gemini Flash)

**Duration:**  Days 4–6  
**Goal:**  Add real-time understanding of conversation.
**Total Estimated Effort:** 3 Days

### [AI-03] Sentiment Classification Engine
-   **Type:**  AI 
-   **Priority:**  P0 (Blocker)
-   **Description:**
    -   Send transcript chunks to Gemini Flash 3.0
    -   Classify sentiment:
           -   Positive
          -   Neutral
          -   Negative
         -   Agitated
      -   Return confidence score
    -   Optimize prompt for low latency
-   **Acceptance Criteria:**
    -   Sentiment updates within 300ms
    - ->85% accuracy on test samples
    -   No redundant API calls
  - **Estimated Delivery Date:** 17/02/2026


### [AI-04] Issue Categorization Engine

-   **Type:**  AI 
-   **Priority:**  P0 (Blocker)
-   **Description:**
    -  Classify transcript into:
          1.  Machine Operation Issues
         2.  Maintenance & Parts
         3.  Technical Troubleshooting
    -   Maintain confidence score
    -   Update dynamically during conversation
-   **Acceptance Criteria:**
    -   ->80% classification accuracy
    -   Latency < 400ms
  - **Estimated Delivery Date:** 18/02/2026


### [AI-05] Search Term Synthesizer (Pause Trigger)

-   **Type:**  AI 
-   **Priority:**  P0 (Blocker)
-   **Description:**
    - On speech break:
    -   Extract recent transcript chunk
    -   Generate optimized search query
    -   Add silence threshold logic
-   **Acceptance Criteria:**
    -   Query generated < 1 second
    -   No duplicate triggers
 - **Estimated Delivery Date:** 19/02/2026

----------

## 🏃 Sprint 3: RAG Foundation (GCS + pgvector)

**Duration:**  Days 7–10 
**Goal:** Implement document ingestion and semantic retrieval
**Total Estimated Effort:** 4 Days

### [DATA-01] Manual Collection & Storage (GCS)

-   **Type:**  Data Engineering
-   **Priority:**  P0 (Blocker)
-   **Description:**
    -   Collect minimum 10 machine manuals (PDF format)
    -   Upload to Google Cloud Storage
    -   Maintain structured folder hierarchy
    -   Create metadata registry (machine model, version, document type)
 -   **Acceptance Criteria:**
     -   Minimum 10 manuals uploaded to GCS
     -  Folder structure logically organized
     -   Metadata file created and verified
     -   Files accessible from backend
  - **Estimated Delivery Date:** 20/02/2026


### [DATA-02] Embedding Pipeline (text-embedding-004)

-   **Type:**  AI / Data
-   **Priority:**  P0 (Blocker)
-   **Description:**
    -  Extract PDF text 
    -   Clean & normalize text
    -   Chunk into 500–800 tokens
    -   Generate embeddings using `text-embedding-004`
    -   Store vectors in PostgreSQL (pgvector)
    -   Attach metadata:
        -   Page number
        -   Section title
        -   Machine model
-   **Acceptance Criteria:**
    - All manuals successfully processed
    -   Embeddings stored in pgvector table
    -   Metadata attached correctly
    -   Cosine similarity query returns relevant results
    -   Vector search latency < 500ms
  - **Estimated Delivery Date:** 21/02/2026


### [BE-02] Semantic Retrieval Engine

- **Type:** Backend  
- **Priority:** P0 (Blocker)
-  **Description**:
     -   Embed search query generated from Gemini
     -   Perform similarity search using pgvector
    -   Retrieve Top 2–3 relevant sections
    -   Rank by cosine similarity score
    -   Format structured JSON response
- **Acceptance Criteria** :
   -   Top 2–3 relevant manual sections returned
    -   Results match expected troubleshooting sections
    -   Retrieval latency < 2 seconds (end-to-end)
    -   No database connection issues under basic load
   - **Estimated Delivery Date:** 24/02/2026



----------

## 🏃 Sprint 4: UI & Cloud Deployment

**Duration:**  Days 11–13
**Goal:**  Build dashboard and deploy to Cloud Run.
**Total Estimated Effort:** 4 Days

### [FE-01] Basic Dashboard (React)

-   **Type:**  Frontend
-   **Priority:**  P1
-   **Description:**
    -    Display:
         -   Live transcript
         -   Sentiment indicator (color-coded)
         -   Category badge
         -   2–3 solution cards
  -   Auto-update on pause trigger
 -   Maintain clean, minimal UI
-   **Acceptance Criteria:**
 -   Transcript updates in real-time
 -   Sentiment indicator updates dynamically
 -   Category badge reflects classification
  -   Solution cards appear after pause trigger
   -   UI responsive on desktop browser
  - **Estimated Delivery Date:** 25/02/2026


### [OPS-01] Dockerization
- **Type:** DevOps  
- **Priority:** P0 (Blocker)
- **Description:**
   -   Create Dockerfile
    -   Install dependencies
    -   Configure environment variables
    -   Test container locally
 - **Acceptance Criteria:**
    -   Docker image builds successfully
    -   Application runs inside container
    -   No dependency errors
    -   Environment variables properly loaded
   - **Estimated Delivery Date:** 27/02/2026


###  [OPS-02] Cloud Run Deployment

-   **Type:**  DevOps
-   **Priority:**  P0 (Blocker)
-   **Description:**
    -  Deploy Docker image to Cloud Run
    -   Connect to Cloud SQL (PostgreSQL)
    -   Connect to GCS
    -   Enable HTTPS
    -   Configure autoscalin
-   **Acceptance Criteria:**
    -   Service publicly accessible
    -   PostgreSQL connection stable
    -   GCS accessible from Cloud Run
    -   Autoscaling verified
    -   End-to-end system works in cloud
   - **Estimated Delivery Date:** 28/02/2026



----------





