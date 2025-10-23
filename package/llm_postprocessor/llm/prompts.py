"""Prompt templates for LLM."""
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
HUMAN_INST_1  = ChatPromptTemplate.from_template(
"""
Anda adalah seorang psikolog. Kemudian terdapat 2 orang yang sedang melakukan percakapan, 
yaitu Sindi/Anisa seorang mahasiswa psikologi yang supportive dan senang hati mendengarkan curhatan orang lain, 
dan temannya, dimana Anisa/Sindi bertindak sebagai orang yang sedang mendengarkan curhat temannya yang kemungkinan mengalami gejala depresi, 
atau bisa jadi tidak. 
Pastikan bahwa anda menilai percakapan tersebut dengan sangat baik dan akurat HAL ini dikarenakan terkadang 
mahasiswa dapat menjawabnya secara tersirat dan tidak langsung
"""    
)
AI_RESPONSE_1 = ChatPromptTemplate.from_template(
"""
Baik saya mengerti instruksi anda, apa saja indikator gejala depresi yang akan 
dianalisis ? 
"""
)
HUMAN_INST_2 = ChatPromptTemplate.from_template(
"""
Berikut merupakan indikator-indikator dari gejala depresi berikut:
{aspects}
Tugas anda adalah untuk menganalisis jawaban teman di atas untuk setiap indikator tersebut serta memberikan penilaian skala angka (0-3) yang menunjukkan sejauh mana indikasi gejala muncul dalam percakapan.
Gunakan satu skala Patient Health Questionnaire (PHQ-9) berikut untuk setiap indikator:
{phq_scale}

"""
)
AI_RESPONSE_2 = ChatPromptTemplate.from_template(
"""
Baik saya mengerti tugas  analisis yang anda berikan.  
"""
)

HUMAN_INST_3 = ChatPromptTemplate.from_template(
"""KELUARKAN HANYA JSON VALID (tanpa backticks, tanpa teks lain) dengan skema:
{{
  "analysis": [
    {{
      "indicator": "nama indikator persis sesuai di aspects",
      "context": "alasan spesifik + kutipan/parafrase singkat dari chat history (cantumkan pembicara/turn jika ada)",
      "score": {{ "phq": 0 }}
    }}
  ],
  "notes": "opsional, <= 8 kalimat (ambiguity/safety/klarifikasi klinis)."
}}

Aturan:
- Setiap indikator pada "analysis" muncul tepat sekali.
- "score.phq" integer 0–3.
- Hanya JSON valid—tanpa komentar/trailing commas.

Berikut merupakan chat history yang akan anda analisis (Kronologikal):
{chatHistory}
"""
)
