"""Start the FastAPI backend with a psycopg-compatible event loop on Windows."""
import asyncio
import selectors
import sys
from pathlib import Path

import uvicorn


project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

config = uvicorn.Config("app.main:app", host="127.0.0.1", port=8000)
server = uvicorn.Server(config)

if sys.platform == "win32":
    asyncio.run(
        server.serve(),
        loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()),
    )
else:
    asyncio.run(server.serve())
