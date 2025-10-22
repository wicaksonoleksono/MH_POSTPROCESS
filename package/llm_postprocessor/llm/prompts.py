"""Prompt templates for LLM."""
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
HUMAN_INST_1  = ChatPromptTemplate.from_template(
"""
Anda adalah seorang psikolog. Kemudian terdapat 2 orang yang sedang melakukan percakapan, 
yaitu Sindi/Anisa seorang mahasiswa psikologi yang supportive dan senang hati mendengarkan curhatan orang lain, 
dan temannya, dimana Anisa/Sindi bertindak sebagai orang yang sedang mendengarkan curhat temannya yang kemungkinan mengalami gejala depresi, 
atau bisa jadi tidak.
"""    
)
AI_RESPONSE_1 = ChatPromptTemplate.from_template(
"""
Baik saya mengerti instruksi anda, apa saja indikator gejala depresi yang akan 
dianalisis ? 
"""
)
# aspects is built from
HUMAN_INST_2 = ChatPromptTemplate.from_template(
"""
Berikut merupakan indikator-indikator dari gejala depresi berikut:
{aspects}
Tugas anda adalah untuk Menganalisa jawaban teman diatas untuk setiap indikator tersebut beserta penilaian skala 
angka (0-3) 
yang diberikan untuk menunjukkan sejauh mana indikasi gejala tersebut muncul dalam percakapan:
Dengan 2 penilaian yang pertama:
skala Patient Health Questionare:
{phq_scale}
dan Skala Operasional Untuk penilaian narasi dari wawancara: 
Skala operasional:
{operational_scale}

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
      "score": {{ "phq": 0, "operational": 0 }}
    }}
  ],
  "totals": {{ "phq_sum": 0, "operational_sum": 0 }},
  "notes": "opsional, <= 3 kalimat (ambiguity/safety/klarifikasi klinis)."
}}

Aturan:
- Setiap indikator pada "analysis" muncul tepat sekali.
- "score.phq" dan "score.operational" integer 0–3.
- Hanya JSON valid—tanpa komentar/trailing commas.

Berikut merupakan chat history yang akan anda analisis (Kronologikal):
{chatHistory}
"""
)
# sekarang buatkan human message dan aimesssage u
