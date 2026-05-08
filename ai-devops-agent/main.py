"""
Entry point: starts the AI DevOps Agent.

What this file does:
  - Creates the agent "runner" (the object that runs the incident workflow).
  - Creates the ServiceNow poller (watches for new incidents and triggers the agent).
  - Starts the poller in a background thread (so it keeps running while the API runs).
  - Creates the FastAPI app (health, ready, trigger, etc.) and runs the HTTP server on port 8080.

Why two things (poller + API)?
  - The API lets you trigger incidents manually and check status.
  - The poller automatically picks up new incidents from ServiceNow so you don't have to trigger every one by hand.

No AI/ML knowledge needed: this is just "start a background watcher + start a web server."
"""

import threading

import uvicorn

from agent.runner import AgentRunner
from watcher.poller import SNOWPoller
from api.server import create_app


def main():
    # Runner runs the agent graph (fetch incident → RAG → logs → diagnose → fix/escalate) for one incident.
    runner = AgentRunner()
    # Poller periodically fetches open incidents from ServiceNow and calls runner for each new one.
    poller = SNOWPoller(runner)

    # Run the poller in a daemon thread so it doesn't block the main thread. When main exits, this thread stops.
    poller_thread = threading.Thread(target=poller.run_forever, daemon=True)
    poller_thread.start()

    # Build the FastAPI app (it needs runner and poller to handle /trigger and optional stats).
    app = create_app(runner=runner, poller=poller)
    # Bind to 0.0.0.0 so the server is reachable from other machines (e.g. Kubernetes probes).
    uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
