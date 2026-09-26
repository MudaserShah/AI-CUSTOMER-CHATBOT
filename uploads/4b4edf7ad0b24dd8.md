# Loom Video Script — LangGraph Agentic Researcher
**Total length target: ~4-6 minutes**

---

## 1. Intro (0:00 – 0:30)

"Hey, main Mudaser — is video mein main aapko apna ek project dikhaunga jo maine LangGraph use karke banaya hai: ek **Agentic Research Assistant**.

Ye ek autonomous AI system hai jo koi bhi research topic leta hai, use validate karta hai, phir khud sub-questions banata hai, web se information gather karta hai, aur end mein ek professional structured report generate kar deta hai — bilkul jaise ek human researcher karta hai, lekin fully automated."

---

## 2. Problem Statement (0:30 – 1:00)

"Idea ye tha ke normal chatbots ek shot mein answer de dete hain — lekin real research is tarah nahi hoti. Real research mein pehle topic samajhna hota hai, phir uske multiple angles nikalne hote hain, phir un sab ko search karna hota hai, aur phir sab findings ko ek coherent report mein combine karna hota hai.

Ye project exactly wahi multi-step reasoning workflow simulate karta hai — using an **agentic architecture** jahan har step ek dependent node hai, aur agent khud decide karta hai next step kya lena hai."

---

## 3. Tech Stack Overview (1:00 – 1:45)

"Chaliye quickly tech stack dekh lete hain:

- **LangGraph** — poora orchestration aur state management isi se hota hai
- **LangChain** — LLM aur tool integration ke liye
- **Hugging Face Inference** — LLM calls ke liye, chat-completions endpoint use kar raha hoon
- **Tavily API** — real-time web search ke liye
- **Qdrant Cloud** — optional knowledge base, vector search ke liye agar documents already upload kiye hon
- **FastAPI** — backend API, with **Server-Sent Events (SSE)** for real-time progress streaming
- **SQLite** — research history save karne ke liye
- **React + Vite** — frontend

Backend aur frontend dono separate hain — clean architecture, easy to scale."

*(Screen: show repo folder structure — backend/, frontend/)*

---

## 4. Architecture Walkthrough (1:45 – 2:45)

"Ab main aapko workflow ka core dikhata hoon — ye `agent.py` file hai jahan poora LangGraph state machine define hai.

Six main nodes hain:

1. **validate_topic** — pehle LLM check karta hai ke user ka diya hua topic ek valid research topic hai ya nahi
2. **analyze_query** — agar valid hai, to LLM us topic ko 3 focused sub-questions mein break karta hai, aur decide karta hai search strategy — web-only ya web plus knowledge base
3. **decide_search_strategy** — confirm karta hai plan
4. **web_search** — Tavily API se har sub-question ke liye real-time results fetch karta hai, max 20 URLs ka cap hai
5. **kb_search** — agar Qdrant configured hai, to local knowledge base se bhi relevant chunks nikalta hai
6. **synthesize** — sab collected data ko combine karke ek final structured report banata hai — Executive Summary, Background, Findings, Analysis, Conclusion, aur Sources ke sath

Har node ke beech state pass hoti hai — LangGraph ka `StateGraph` isko handle karta hai, aur agar topic invalid ho to graph directly end ho jata hai, warna pura pipeline chalta hai."

*(Screen: scroll through `agent.py` — show the node functions and `workflow.add_conditional_edges`)*

---

## 5. Live Demo (2:45 – 4:15)

"Ab live demo dekhte hain.

Frontend open karta hoon... yahan main ek research topic type karta hoon, jaise — 'Impact of AI Agents in Healthcare'.

Submit karte hi backend real-time progress stream kar raha hai SSE ke zariye — dekhiye, ye thinking steps live update ho rahe hain:
- Topic validate ho raha hai
- Sub-questions ban rahe hain
- Web search chal raha hai — sources collect ho rahe hain
- Aur ab final report synthesize ho raha hai

*(wait for the demo to complete)*

Aur ye lijiye — final structured report. Executive summary, background, findings, analysis, conclusion, aur niche actual sources bhi listed hain jo web search se aaye.

Main history tab bhi dikhata hoon — pichle saare research reports SQLite mein save hote hain, aur yahan se PDF download bhi kar sakte hain."

*(Screen: show /history page, then download a PDF report)*

---

## 6. Code Highlights (4:15 – 5:00)

"Kuch cheezein jo mujhe is project mein particularly likhne mein maza aaya:

- **Structured output parsing** — LLM se JSON response nikalna, kyunke open-source models kabhi kabhi markdown fences ya extra text add kar dete hain, to maine ek safe `_parse_json_response` helper likha hai jo ye handle karta hai
- **Graceful fallbacks** — agar LLM validation fail ho jaye, to system crash nahi hota, ek local fallback logic se continue karta hai
- **URL capping and per-query limits** — taake rate limits aur costs control mein rahein
- **SSE streaming** — real user experience ke liye, taake user ko pata chale agent abhi kya kar raha hai, instead of a blank loading screen"

*(Screen: show `_parse_json_response` function and the SSE event_generator in api.py)*

---

## 7. Challenges & Learnings (5:00 – 5:30)

"Ek interesting challenge jo maine face kiya — Hugging Face ke inference providers models ko drop ya add karte rehte hain, to model availability ka dynamically check karna zaroori hai. Maine iske liye configurable `LLM_MODEL` env variable rakha hai, taake kisi bhi supported chat model ko easily swap kar sakoon without changing code.

Isse mujhe agentic systems ke real-world deployment challenges samajhne mein kaafi help mili — jaise provider dependency, graceful degradation, aur streaming architecture."

---

## 8. Closing (5:30 – 6:00)

"To ye tha mera LangGraph Agentic Researcher project — poora code GitHub par available hai, link description mein de raha hoon.

Agar aapko ye project pasand aaya ho, GitHub par ek star zaroor de dena, aur agar koi suggestion ya feedback ho to comments mein bata dena.

Thanks for watching!"

---

## Notes for Recording
- Keep terminal + browser + code editor pre-arranged in tabs before recording, taake switching smooth rahe.
- Run one research query *before* recording to warm up models/caches (avoids long dead-air during demo).
- Have a short, fast-resolving example topic ready to keep the demo section under 90 seconds.
- Optional: add captions/text overlays for tech stack list (Section 3) since it's a fast list.
