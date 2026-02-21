"""
ai_categorizer.py
Usa a API do Google Gemini (gratuita) para categorizar e pontuar vagas.
Tecnologias: requests, AI Prompting, interação com APIs REST
"""

import requests
import json
import os
import pandas as pd
import time
import logging
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent.parent / ".env")

load_dotenv()
logger = logging.getLogger(__name__)

# ── Configuração ─────────────────────────────────────────────────────────────
# Obtenha sua chave gratuita em: https://console.groq.com
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

CATEGORIAS = [
    "Data Science",
    "Data Engineering",
    "Machine Learning / IA",
    "Analytics / BI",
    "Backend / Automação",
    "Outro",
]

def build_prompt(titulo: str, descricao: str) -> str:
    return f"""Você é um especialista em recrutamento de tecnologia.
Analise a vaga abaixo e retorne SOMENTE um JSON válido, sem markdown.

Vaga:
Título: {titulo}
Descrição: {descricao[:400]}

Categorias disponíveis: {CATEGORIAS}

Retorne exatamente neste formato:
{{
  "categoria": "<uma das categorias acima>",
  "score_relevancia": <número de 0 a 10 indicando relevância para um estudante de Ciência de Dados>,
  "palavras_chave": ["<palavra1>", "<palavra2>", "<palavra3>"],
  "resumo": "<resumo em 1 frase do que a vaga exige>"
}}"""


def call_groq(prompt: str) -> dict | None:
    """Chama a API do Groq e retorna o JSON parseado."""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 256,
    }
    try:
        resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"]
        return json.loads(text)
    except Exception as e:
        logger.error(f"Erro na API Groq: {e}")
        return None


def categorize_jobs(df: pd.DataFrame) -> pd.DataFrame:
    """Itera sobre o DataFrame e enriquece com dados da IA."""
    resultados = []
    for _, row in df.iterrows():
        prompt = build_prompt(row["titulo"], row.get("descricao", ""))
        result = call_groq(prompt)
        if result:
            row["categoria"]      = result.get("categoria", "Outro")
            row["score_ia"]       = result.get("score_relevancia", 0)
            row["palavras_chave"] = ", ".join(result.get("palavras_chave", []))
            row["resumo_ia"]      = result.get("resumo", "")
        else:
            row["categoria"]      = "Outro"
            row["score_ia"]       = 0
            row["palavras_chave"] = ""
            row["resumo_ia"]      = ""
        resultados.append(row)
        time.sleep(3)

    return pd.DataFrame(resultados)


if __name__ == "__main__":
    sample = pd.DataFrame([{
        "titulo": "Estágio em Data Science",
        "descricao": "Buscamos estagiário com Python, pandas e SQL para análise de dados.",
    }])
    df_enriched = categorize_jobs(sample)
    print(df_enriched[["titulo", "categoria", "score_ia", "resumo_ia"]])
