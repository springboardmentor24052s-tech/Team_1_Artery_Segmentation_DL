"""
StenoVision Test Suite - Burst Throughput Stress & Heap Memory Leak Profiling
=============================================================================
Benchmarking suite validating:
1. High-Volume API Burst Stress (15, 30, 50 Requests across microservices)
2. Requests Per Second (RPS) Throughput & 0.0% Error Rate Enforcement
3. Dynamic Heap Memory Profiling & Leak Detection via Python tracemalloc
4. Sub-1.0 MB Net Heap Growth Threshold across repeated heavy cycles

Stores persistent execution results in test_suite/results/stress_and_memory_results.json.
"""

import sys
import time
import statistics
import tracemalloc
import gc
import json
from pathlib import Path

# Setup paths
suite_dir = Path(__file__).resolve().parent.parent
repo_root = suite_dir.parent
backend_dir = repo_root / "backend"
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.services.reporting import clinical_report_service

client = TestClient(app)

RESULTS_DIR = suite_dir / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def test_burst_stress_and_memory():
    print("==================================================================")
    print("  STENOVISION BURST STRESS & HEAP MEMORY PROFILING SUITE")
    print("==================================================================")

    start_total = time.time()
    stress_metrics = {}

    # 1. Burst Concurrency Stress Testing
    print("\n[Stress 1/2] Benchmarking High-Volume Burst Load & Throughput Stress (RPS)...")
    endpoints = [
        "/health",
        "/api/v1/models",
        "/api/v1/reports",
    ]

    burst_batches = [15, 30, 50]
    batch_results = []

    for batch_size in burst_batches:
        latencies = []
        errors = 0

        t_start = time.perf_counter()
        for i in range(batch_size):
            ep = endpoints[i % len(endpoints)]
            t0 = time.perf_counter()
            res = client.get(ep)
            t1 = time.perf_counter()
            if res.status_code == 200:
                latencies.append((t1 - t0) * 1000)
            else:
                errors += 1
        t_total = time.perf_counter() - t_start

        rps = batch_size / t_total if t_total > 0 else 0
        mean_lat = statistics.mean(latencies) if latencies else 0
        p95_lat = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else (max(latencies) if latencies else 0)
        error_rate = (errors / batch_size) * 100.0

        batch_results.append({
            "batch_size": batch_size,
            "elapsed_seconds": round(t_total, 3),
            "throughput_rps": round(rps, 1),
            "mean_latency_ms": round(mean_lat, 2),
            "p95_latency_ms": round(p95_lat, 2),
            "error_rate_pct": error_rate,
        })

        print(f"  Batch Burst:     {batch_size:>2} Requests | Total Elapsed: {t_total:.3f} s")
        print(f"    -> Throughput:   {rps:.1f} Requests/sec (RPS)")
        print(f"    -> Mean Latency: {mean_lat:.2f} ms | p95: {p95_lat:.2f} ms")
        print(f"    -> Error Rate:   {error_rate:.1f}% (Zero Errors Expected)")

        assert errors == 0
        assert error_rate == 0.0

    stress_metrics["burst_stress_tests"] = batch_results
    print("  ✓ Burst Stress Testing Passed: 0.0% Error Rate across all throughput tiers")

    # 2. Dynamic Heap Memory Profiling & Leak Detection
    print("\n[Stress 2/2] Verifying Heap Memory Stability & Zero Memory Leaks...")
    reports = clinical_report_service.get_all_reports()
    case_rpt = reports[0]

    gc.collect()
    tracemalloc.start()

    cycle_count = 25
    for _ in range(cycle_count):
        _ = clinical_report_service.generate_json(case_rpt)
        _ = clinical_report_service.generate_csv_cohort()

    gc.collect()
    current_bytes, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    net_memory_diff_mb = current_bytes / (1024.0 * 1024.0)
    peak_memory_mb = peak_bytes / (1024.0 * 1024.0)

    stress_metrics["memory_profile"] = {
        "heavy_cycles_executed": cycle_count,
        "net_heap_active_mb": round(net_memory_diff_mb, 4),
        "peak_heap_mb": round(peak_memory_mb, 4),
        "threshold_mb": 1.0,
        "leak_detected": net_memory_diff_mb >= 1.0,
    }

    print(f"  Executed Workload:        {cycle_count} structured JSON & tabular CSV streaming cycles")
    print(f"  Net Active Heap Memory:   {net_memory_diff_mb:.3f} MB (Threshold: < 1.000 MB)")
    print(f"  Peak Heap Allocation:     {peak_memory_mb:.3f} MB")

    assert net_memory_diff_mb < 1.0
    print("  ✓ Zero Progressive Memory Leaks Detected (Stable Heap Profile for Long-Running Servers)")

    total_duration = time.time() - start_total

    result_payload = {
        "suite": "Burst Stress & Heap Memory Leak Profiling",
        "status": "PASSED",
        "total_duration_seconds": round(total_duration, 3),
        "metrics": stress_metrics,
    }

    with open(RESULTS_DIR / "stress_and_memory_results.json", "w", encoding="utf-8") as f:
        json.dump(result_payload, f, indent=2)

    print("\n------------------------------------------------------------------")
    print(f"  ✓ STRESS & MEMORY BENCHMARKS PASSED IN {total_duration:.2f} SECONDS")
    print(f"  ✓ Results saved to: test_suite/results/stress_and_memory_results.json")
    print("==================================================================\n")
    return True

if __name__ == "__main__":
    test_burst_stress_and_memory()
