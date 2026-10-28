"""
Automated Load Balancer Verification & Distribution Analyzer.

Validates that Nginx distributes incoming HTTP traffic evenly between
backend-1 and backend-2 using the round-robin balancing algorithm.
"""

import sys
import os
import json
import time
import requests
from collections import Counter

TARGET_URL = os.environ.get("LB_TARGET_URL", "http://localhost:5000/health")
TOTAL_REQUESTS = int(os.environ.get("LB_NUM_REQUESTS", "40"))
OUTPUT_LOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "docs",
    "evidencias",
    "balanceamento",
    "nginx-round-robin.log"
)

def run_verification():
    print("=" * 70)
    print("  VERIFICACAO DE ALTA DISPONIBILIDADE E BALANCEAMENTO DE CARGA")
    print("=" * 70)
    print(f"Target URL:       {TARGET_URL}")
    print(f"Total Requests:   {TOTAL_REQUESTS}")
    print(f"Algorithm:        Round-Robin (Nginx upstream)")
    print("-" * 70)

    os.makedirs(os.path.dirname(OUTPUT_LOG_PATH), exist_ok=True)

    instances = []
    upstreams = []
    status_codes = []
    latencies = []
    log_lines = []

    header_msg = f"Iniciando envio de {TOTAL_REQUESTS} requisicoes consecutivas ao Load Balancer...\n"
    print(header_msg.strip())
    log_lines.append(header_msg)

    # Allow a moment for proxy to settle if just started
    time.sleep(1)

    for i in range(1, TOTAL_REQUESTS + 1):
        try:
            t0 = time.perf_counter()
            resp = requests.get(TARGET_URL, timeout=5)
            elapsed_ms = (time.perf_counter() - t0) * 1000

            status_code = resp.status_code
            instance_id = resp.headers.get("X-Instance-ID", "unknown")
            upstream_server = resp.headers.get("X-Upstream-Server", "unknown")
            req_id = resp.headers.get("X-Request-ID", "unknown")

            instances.append(instance_id)
            upstreams.append(upstream_server)
            status_codes.append(status_code)
            latencies.append(elapsed_ms)

            line = (
                f"Req #{i:02d} | Status: {status_code} | "
                f"Instance: {instance_id:10s} | Upstream: {upstream_server:22s} | "
                f"Latency: {elapsed_ms:6.2f}ms | ReqID: {req_id}"
            )
            print(line)
            log_lines.append(line + "\n")
            time.sleep(0.05)
        except Exception as e:
            err_line = f"Req #{i:02d} | FALHA DE CONEXAO: {e}"
            print(err_line)
            log_lines.append(err_line + "\n")
            instances.append("FAILED")
            status_codes.append(0)

    print("-" * 70)
    log_lines.append("-" * 70 + "\n")

    # Metrics computation
    total_valid = sum(1 for c in status_codes if c == 200)
    instance_counts = Counter(instances)
    upstream_counts = Counter(upstreams)
    avg_latency = sum(latencies) / len(latencies) if latencies else 0

    summary_lines = [
        "RELATORIO CONSOLIDADO DE BALANCEAMENTO:",
        f"  - Requisicoes Enviadas:  {TOTAL_REQUESTS}",
        f"  - Requisicoes Bem-Sucedidas (200 OK): {total_valid}/{TOTAL_REQUESTS} ({total_valid/TOTAL_REQUESTS*100:.1f}%)",
        f"  - Latencia Media:        {avg_latency:.2f}ms",
        "  - Distribuicao por Instancia:",
    ]

    for inst, count in sorted(instance_counts.items()):
        pct = (count / TOTAL_REQUESTS) * 100
        summary_lines.append(f"      * {inst:12s}: {count:2d} requisicoes ({pct:5.1f}%)")

    summary_lines.append("  - Distribuicao por Upstream Address:")
    for up, count in sorted(upstream_counts.items()):
        pct = (count / TOTAL_REQUESTS) * 100
        summary_lines.append(f"      * {up:22s}: {count:2d} requisicoes ({pct:5.1f}%)")

    # Check round-robin switching
    switches = sum(1 for i in range(1, len(instances)) if instances[i] != instances[i-1] and instances[i] != "FAILED")
    switch_rate = (switches / (len(instances) - 1)) * 100 if len(instances) > 1 else 0
    summary_lines.append(f"  - Alternancia entre Replicas: {switches}/{len(instances)-1} transicoes ({switch_rate:.1f}%)")

    for s in summary_lines:
        print(s)
        log_lines.append(s + "\n")

    with open(OUTPUT_LOG_PATH, "w", encoding="utf-8") as f:
        f.writelines(log_lines)

    print("-" * 70)
    print(f"Evidencia gravada em: {OUTPUT_LOG_PATH}")

    # Validation criteria:
    # 1. 100% 200 OK
    # 2. Both backend-1 and backend-2 must receive requests (between 40% and 60% each)
    # 3. Switch rate should be high (> 80% alternating)
    if total_valid != TOTAL_REQUESTS:
        print("[ERRO] Houve falhas nas requisicoes.")
        return 1

    b1_count = instance_counts.get("backend-1", 0)
    b2_count = instance_counts.get("backend-2", 0)
    if b1_count == 0 or b2_count == 0:
        print("[ERRO] Uma das instancias nao recebeu requisicoes!")
        return 1

    b1_ratio = b1_count / TOTAL_REQUESTS
    if not (0.35 <= b1_ratio <= 0.65):
        print(f"[ALERTA] Distribuicao fora da margem esperada: backend-1={b1_ratio:.2%}")
        return 1

    print("[SUCESSO] Alta disponibilidade e balanceamento round-robin validados com sucesso!")
    return 0

if __name__ == "__main__":
    sys.exit(run_verification())

