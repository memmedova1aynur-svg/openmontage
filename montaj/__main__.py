"""İşə salma: python -m montaj [--host 0.0.0.0] [--port 4760]"""

from __future__ import annotations

import argparse


def main() -> None:
    ap = argparse.ArgumentParser(prog="python -m montaj", description="Montaj panelini işə sal")
    ap.add_argument("--host", default="127.0.0.1",
                    help="0.0.0.0 — eyni şəbəkədəki telefondan açmaq üçün")
    ap.add_argument("--port", type=int, default=4760)
    args = ap.parse_args()
    import uvicorn

    print(f"Montaj paneli: http://{'localhost' if args.host in ('127.0.0.1', '0.0.0.0') else args.host}:{args.port}/")
    uvicorn.run("montaj.server:app", host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
