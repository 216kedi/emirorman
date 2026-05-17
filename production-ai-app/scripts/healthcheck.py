import sys
import urllib.request


def main(url: str = "http://localhost:8000/health") -> int:
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return 0 if resp.status == 200 else 1
    except Exception as e:
        print(f"healthcheck failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/health"))
