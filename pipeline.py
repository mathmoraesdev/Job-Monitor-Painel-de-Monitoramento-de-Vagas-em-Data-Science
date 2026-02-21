"""
pipeline.py
Orquestra todo o fluxo: scraping → banco → IA → exportação.
Execute este arquivo para rodar o projeto completo.
"""

from scraper import run_scraper
from database import create_tables, insert_vagas, query_vagas, stats
from ai_categorizer import categorize_jobs
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def run_pipeline():
    print("\n" + "="*50)
    print("🚀 INICIANDO PIPELINE - Job Monitor")
    print("="*50 + "\n")

    # 1. Garante schema do banco
    print("📦 [1/4] Configurando banco de dados...")
    create_tables()

    # 2. Scraping
    print("\n🕷️  [2/4] Coletando vagas...")
    df_raw = run_scraper()

    if df_raw.empty:
        print("⚠️  Nenhuma vaga coletada. Verifique sua conexão.")
        return

    # 3. Enriquecer com IA
    print(f"\n🤖 [3/4] Categorizando {len(df_raw)} vagas com IA...")
    df_enriched = categorize_jobs(df_raw.head(20))

    # 4. Salvar no banco e exportar
    print("\n💾 [4/4] Salvando resultados...")
    insert_vagas(df_enriched)

    # Exporta CSV para análise no Power BI
    csv_path = OUTPUT_DIR / "vagas_processadas.csv"
    df_enriched.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"  → CSV exportado: {csv_path}")

    # Relatório de estatísticas
    s = stats()
    print(f"\n📊 RESUMO FINAL")
    print(f"  Total no banco : {s['total']} vagas")
    print(f"\n  Por categoria:")
    print(s["por_categoria"].to_string(index=False))

    print("\n✅ Pipeline concluído com sucesso!\n")


if __name__ == "__main__":
    run_pipeline()
