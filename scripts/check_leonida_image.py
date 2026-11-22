"""Run the real native diagnostic job through HTTP inside a built OS image."""
import json
import os
import sys
import tempfile
import threading
import time
import urllib.request

sys.path.insert(0, "/usr/share/anypc/shell/daemon")
from anypc_shelld.leonida import CHECKS, REVISION
from anypc_shelld.server import App, make_handler, serve
from anypc_shelld.store import Store

with tempfile.TemporaryDirectory(prefix="anypc-image-check-") as config:
    app = App(None, store=Store(os.path.join(config, "state.json")), port=0)
    server = serve(app, "127.0.0.1", 0)
    app.port = server.server_address[1]
    server.RequestHandlerClass = make_handler(app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{app.port}/api/modules"
    try:
        with urllib.request.urlopen(url) as response:
            initial = json.load(response)
        if not initial["leonida"]["installed"] or initial["leonida"]["version"] != REVISION[:12]:
            raise RuntimeError("Native module is not installed at the expected revision")
        request = urllib.request.Request(url + "/leonida/check", data=b"{}",
                                         headers={"Content-Type": "application/json", "X-AnyPC": "1"})
        with urllib.request.urlopen(request) as response:
            if response.status != 202:
                raise RuntimeError("Diagnostic action was not accepted")
            json.load(response)
        deadline = time.monotonic() + 35
        while True:
            with urllib.request.urlopen(url) as response:
                result = json.load(response)["leonida"]
            if result["checks"]["state"] != "running":
                break
            if time.monotonic() >= deadline:
                raise RuntimeError("Diagnostic action did not complete")
            time.sleep(.05)
        checks = result["checks"]
        if (checks["state"] != "done" or checks["passed"] != len(CHECKS)
                or checks["failed"] or checks["simulated"] or len(checks["results"]) != len(CHECKS)):
            raise RuntimeError(json.dumps(result))
        print(json.dumps(result, indent=2))
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
