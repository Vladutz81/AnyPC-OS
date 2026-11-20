import argparse
import os
import sys

from .server import App, serve


def main(argv=None):
    here = os.path.dirname(os.path.abspath(__file__))
    default_ui = os.environ.get("ANYPC_UI_DIR") or os.path.normpath(os.path.join(here, "..", "..", "ui"))
    p = argparse.ArgumentParser(prog="anypc-shelld", description="AnyPC OS shell service")
    p.add_argument("--port", type=int, default=int(os.environ.get("ANYPC_PORT", "7700")))
    p.add_argument("--ui", default=default_ui, help="directory with the shell UI")
    p.add_argument("--demo", action="store_true", help="sample games, no system changes")
    args = p.parse_args(argv)
    if not os.path.isdir(args.ui):
        print(f"anypc-shelld: UI directory not found: {args.ui}", file=sys.stderr)
        return 1
    app = App(args.ui, demo=args.demo, port=args.port)
    httpd = serve(app, "127.0.0.1", args.port)
    print(f"anypc-shelld listening on http://127.0.0.1:{args.port}/" + (" (demo)" if args.demo else ""),
          flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
