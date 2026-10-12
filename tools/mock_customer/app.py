"""Mock customer webhook receiver.

A tiny standalone FastAPI app that receives {{APP_NAME}} webhooks and shows a
dashboard of what it got. Its behavior is configurable to simulate customer-side
failures — this is how we demo the integration problem space (auth rejection,
5xx, timeouts, bad signatures) the agent will diagnose.

Run:
    cd tools/mock_customer
    MOCK_MODE=ok uvicorn app:app --port 9100

MOCK_MODE (env or ?mode= query on /hook): ok | 401 | 403 | 500 | timeout | badsig
"""
import hashlib
import hmac
import os
import time
from datetime import datetime, timezone

from fastapi import FastAPI, Header, Request
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(title="Mock Customer Receiver")

# In-memory log of received hooks.
RECEIVED: list[dict] = []
# Optional shared secret for signature verification in "ok"/"badsig" modes.
SECRET = os.environ.get("MOCK_WEBHOOK_SECRET", "demo-secret")


def _mode(request: Request) -> str:
    return request.query_params.get("mode") or os.environ.get("MOCK_MODE", "ok")


@app.post("/hook")
async def hook(request: Request, x_signature: str | None = Header(default=None)):
    mode = _mode(request)
    body = await request.body()
    payload_text = body.decode("utf-8", errors="replace")

    expected = "sha256=" + hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
    sig_ok = (x_signature == expected)

    RECEIVED.insert(0, {
        "at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "signature_ok": sig_ok,
        "body": payload_text[:1000],
    })
    del RECEIVED[200:]

    if mode == "401":
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    if mode == "403":
        return JSONResponse({"error": "forbidden"}, status_code=403)
    if mode == "500":
        return JSONResponse({"error": "server error"}, status_code=500)
    if mode == "timeout":
        time.sleep(30)  # exceed the sender's timeout
        return JSONResponse({"ok": True})
    if mode == "badsig" and not sig_ok:
        return JSONResponse({"error": "bad signature"}, status_code=400)

    return JSONResponse({"ok": True})


@app.get("/", response_class=HTMLResponse)
def dashboard():
    rows = "".join(
        f"<tr><td>{r['at']}</td><td>{r['mode']}</td>"
        f"<td>{'✓' if r['signature_ok'] else '✗'}</td>"
        f"<td><code>{r['body'][:200]}</code></td></tr>"
        for r in RECEIVED
    )
    return f"""
    <html><head><title>Mock Customer Receiver</title></head>
    <body style="font-family:system-ui;margin:2rem">
      <h1>Mock Customer Receiver</h1>
      <p>Mode: <strong>{os.environ.get('MOCK_MODE', 'ok')}</strong> · received {len(RECEIVED)} hook(s)</p>
      <table border="1" cellpadding="6" cellspacing="0">
        <tr><th>At</th><th>Mode</th><th>Sig</th><th>Body</th></tr>
        {rows or '<tr><td colspan="4">Nothing yet</td></tr>'}
      </table>
    </body></html>
    """


@app.get("/received")
def received():
    return {"count": len(RECEIVED), "items": RECEIVED}
