"""Two-party PSI-cardinality smoke benchmark using OpenMined PSI.

Runs the ECDH-PSI based flow with ``reveal_intersection=False`` (the
client learns only the intersection *size*) and the exact ``RAW``
data structure (no configurable false positives, unlike GCS or
BloomFilter).

Measures wall-clock phases and serialized message sizes for
(|server items|, |client items|) configurations. Engineering
feasibility check only; results are run records, not paper results.
"""

from __future__ import annotations

import argparse
import json
import platform
import random
import time

import private_set_intersection.python as psi_lib


def run_once(server_size: int, client_size: int, overlap: int, seed: int) -> dict:
    rng = random.Random(seed)
    shared = [f"item-{rng.randrange(1 << 40)}" for _ in range(overlap)]
    server_items = shared + [f"s-{rng.randrange(1 << 40)}" for _ in range(server_size - overlap)]
    client_items = shared + [f"c-{rng.randrange(1 << 40)}" for _ in range(client_size - overlap)]

    server = psi_lib.server.CreateWithNewKey(False)
    client = psi_lib.client.CreateWithNewKey(False)

    t0 = time.perf_counter()
    request = client.CreateRequest(client_items)
    t_request = time.perf_counter() - t0
    req_bytes = len(request.SerializeToString())

    t0 = time.perf_counter()
    setup = server.CreateSetupMessage(
        1e-12, len(client_items), server_items, psi_lib.DataStructure.RAW
    )
    t_setup = time.perf_counter() - t0
    setup_bytes = len(setup.SerializeToString())

    t0 = time.perf_counter()
    response = server.ProcessRequest(request)
    t_process = time.perf_counter() - t0
    resp_bytes = len(response.SerializeToString())

    t0 = time.perf_counter()
    card = client.GetIntersectionSize(setup, response)
    t_decrypt = time.perf_counter() - t0

    return {
        "server_size": server_size,
        "client_size": client_size,
        "overlap": overlap,
        "seed": seed,
        "reported_cardinality": card,
        "correct": card == overlap,
        "seconds": {
            "client_request": t_request,
            "server_setup": t_setup,
            "server_process": t_process,
            "client_decrypt": t_decrypt,
            "total": t_request + t_setup + t_process + t_decrypt,
        },
        "bytes": {
            "request": req_bytes,
            "setup": setup_bytes,
            "response": resp_bytes,
            "total": req_bytes + setup_bytes + resp_bytes,
        },
        "data_structure": "RAW",
        "reveal_intersection": False,
        "library": f"openmined-psi {psi_lib.__version__}",
        "python": platform.python_version(),
        "machine": platform.machine(),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--server-size", type=int, default=100_000)
    ap.add_argument("--client-size", type=int, default=1_000)
    ap.add_argument("--overlap", type=int, default=100)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--out", type=str, default="")
    args = ap.parse_args()

    runs = [run_once(args.server_size, args.client_size, args.overlap, s) for s in range(args.repeats)]
    for r in runs:
        status = "OK" if r["correct"] else "WRONG CARDINALITY"
        print(
            f"server={r['server_size']} client={r['client_size']} overlap={r['overlap']} "
            f"card={r['reported_cardinality']} [{status}] total={r['seconds']['total']:.3f}s "
            f"comm={r['bytes']['total'] / 1e6:.1f}MB"
        )
    if not all(r["correct"] for r in runs):
        raise SystemExit("SMOKE FAILED: wrong cardinality")
    print("SMOKE OK")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(runs, fh, indent=2)


if __name__ == "__main__":
    main()
