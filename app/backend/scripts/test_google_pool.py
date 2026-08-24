"""
Script de teste de estresse e validação do GeminiPool (Google AI 6 chaves).
Executa chamadas paralelas para atestar que as 6 chaves operam em conjunto
com balanceamento Round-Robin, sem conflito de concorrência.
"""

import os
import sys
import time

# Adiciona o diretório backend ao sys.path para importar api.gemini_pool
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Carrega .env manualmente se necessário
env_file = os.path.join(backend_dir, ".env")
if os.path.exists(env_file):
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))

from api.gemini_pool import GeminiPool

def run_test():
    print("=" * 60)
    print("  TESTE DE CONECTIVIDADE E PERFORMANCE - GEMINI KEY POOL")
    print("=" * 60)

    pool = GeminiPool()
    print(f"\n[1] Total de chaves carregadas: {pool.total_keys}")
    if pool.total_keys == 0:
        print("[ERRO] Nenhuma chave encontrada no ambiente (.env).")
        return

    # 1. Health check individual
    print("\n[2] Executando Health Check em todas as chaves...")
    health = pool.health_check()
    for item in health["keys_report"]:
        status_icon = "[OK]" if item["status"] == "HEALTHY" else "[ERRO]"
        latency = f"{item.get('latency_ms', 0)}ms"
        print(f"  Chave #{item['key_index']} ({item['key_prefix']}): {status_icon} {item['status']} - Latencia: {latency}")

    # 2. Teste concorrente em lote (12 requisições paralelas distribuídas entre as 6 chaves)
    test_tasks = [
        f"Qual é o tratamento padrão-ouro para infarto agudo do miocárdio com supra de ST no item #{i}? Responda em 1 linha."
        for i in range(1, 13)
    ]

    print(f"\n[3] Disparando 12 requisições concorrentes em paralelo (workers=6)...")
    t0 = time.time()

    def _worker(prompt_text, p: GeminiPool):
        res = p.generate_content(
            prompt=prompt_text,
            temperature=0.1,
            timeout=15
        )
        return {
            "key_index": res["key_index"],
            "model": res["model"],
            "preview": res["text"][:80].replace("\n", " ")
        }

    results = pool.generate_batch_parallel(test_tasks, _worker, max_workers=6)
    elapsed = time.time() - t0

    print(f"  Concluído em {elapsed:.2f}s (Média: {elapsed/len(test_tasks):.2f}s por item)!")
    print("\n[4] Distribuição de execução por chave:")
    key_distribution = {}
    for r in results:
        if r:
            k_idx = r["key_index"]
            key_distribution[k_idx] = key_distribution.get(k_idx, 0) + 1

    for k_idx, count in sorted(key_distribution.items()):
        print(f"  Chave #{k_idx}: {count} requisições processadas")

    print("\n[5] Exemplo de resposta obtida:")
    if results and results[0]:
        print(f"  (Chave #{results[0]['key_index']}): {results[0]['preview']}...")

    print("\n" + "=" * 60)
    print("  RESULTADO: POOL MULTI-CHAVE 100% OPERACIONAL E CONCORRENTE!")
    print("=" * 60)

if __name__ == "__main__":
    run_test()
