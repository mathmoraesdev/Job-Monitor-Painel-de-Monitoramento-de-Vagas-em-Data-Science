"""
scraper.py
Coleta vagas de emprego de fontes públicas (RSS/HTML).
Tecnologias: requests, BeautifulSoup, lxml
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ── Fontes públicas via RSS ──────────────────────────────────────────────────

RSS_SOURCES = {
    "RemoteOK": "https://remoteok.com/remote-jobs.rss",
    "WeWorkRemotely": "https://weworkremotely.com/categories/remote-data-science-jobs.rss",
}


def fetch_rss(name: str, url: str) -> list[dict]:
    """Faz o parse de um feed RSS e retorna lista de vagas."""
    logger.info(f"Coletando RSS: {name}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "xml")
        items = soup.find_all("item")
        vagas = []
        for item in items:
            vagas.append({
                "titulo":    item.find("title").get_text(strip=True) if item.find("title") else "",
                "empresa":   item.find("author").get_text(strip=True) if item.find("author") else "N/A",
                "link":      item.find("link").get_text(strip=True) if item.find("link") else "",
                "descricao": item.find("description").get_text(strip=True)[:300] if item.find("description") else "",
                "fonte":     name,
                "coletado_em": datetime.now().strftime("%Y-%m-%d %H:%M"),
            })
        logger.info(f"  → {len(vagas)} vagas coletadas de {name}")
        return vagas
    except Exception as e:
        logger.error(f"Erro ao coletar {name}: {e}")
        return []


def run_scraper() -> pd.DataFrame:
    """Executa todos os scrapers e retorna DataFrame consolidado."""
    all_jobs = []
    for name, url in RSS_SOURCES.items():
        all_jobs.extend(fetch_rss(name, url))
        time.sleep(1)  # respeita o servidor

    df = pd.DataFrame(all_jobs)
    if not df.empty:
        df.drop_duplicates(subset=["titulo", "empresa"], inplace=True)
        df.reset_index(drop=True, inplace=True)
    logger.info(f"Total de vagas únicas: {len(df)}")
    return df


if __name__ == "__main__":
    df = run_scraper()
    df.to_csv("../data/vagas_raw.csv", index=False, encoding="utf-8")
    print(df.head())
