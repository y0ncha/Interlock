# Running the Interlock MCP Server

## Quick Answer

**Yes, it's now a valid MCP server using FastMCP!** You can run it locally.

## Installation

1. **Install dependencies:**
   ```bash
   pip install -e .
   ```

   This installs:
   - `fastmcp` - The FastMCP library for building MCP servers
   - `pydantic` - For schema validation

## MCP configuration (agent runs the server)

The agent runs the Interlock server as an MCP. Configure the **command** and **args** in your MCP config file (`mcp.json` or `settings.json`) as a JSON object. The client will spawn the server process and connect via stdio.

### Config shape (JSON object)

```json
{
  "mcpServers": {
    "interlock": {
      "command": "python",
      "args": ["-m", "interlock.server"]
    }
  }
}
```

- **`command`** — Executable used to run the server (e.g. `python`, `py`, or full path to venv Python).
- **`args`** — Arguments list, typically `["-m", "interlock.server"]`.

Optional:

- **`cwd`** — Working directory (project root where `interlock` is installed).
- **`env`** — Optional environment variables (object).

### Example: `mcp.json`

Copy from the repo example and adjust paths if needed:

```json
{
  "mcpServers": {
    "interlock": {
      "command": "python",
      "args": ["-m", "interlock.server"]
    }
  }
}
```

With a virtualenv and fixed working directory:

```json
{
  "mcpServers": {
    "interlock": {
      "command": "/path/to/py/.venv/bin/python",
      "args": ["-m", "interlock.server"],
      "cwd": "/path/to/py"
    }
  }
}
```

### Where to put the config

- **Cursor** — Use Cursor settings → MCP, or the config file your IDE uses for MCP servers (often a JSON object with `mcpServers` or similar).
- **Claude Desktop** — e.g. `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS). Same `mcpServers` structure.
- **Other MCP clients** — Put the same JSON object in the `mcp.json` or `settings.json` location your client documents.

After saving the config, (re)start the client so the agent can use Interlock tools (`interlock_begin_run`, `interlock_submit_ticket`).

---

## Running Locally (manual)

If you want to run the server process yourself (e.g. for debugging):

```bash
python -m interlock.server
```

The server will communicate via STDIN/STDOUT. Normally the **agent runs the server** via the MCP config above; you don't need to start it manually.

### Option 2: HTTP Mode (for testing with HTTP clients)

You can also run it as an HTTP server:
```python
# In interlock/server.py, change the last line to:
if __name__ == "__main__":
    mcp.run(transport="http", host="localhost", port=8000)
```

Then access it at `http://localhost:8000`

## Testing the Server

### Test with a Simple Client Script

Create `test_client.py`:

```python
import asyncio
import json
from interlock.schemas.ticket import Ticket
from uuid import uuid4

async def test_server():
    from fastmcp import Client
    
    # Connect to the server (in-memory for testing)
    from interlock.server import mcp
    client = Client(mcp)
    
    # Begin a run and get clean ticket.json at fetch_ticket
    begin = await client.call_tool(
        "interlock_begin_run",
        {"ticket_id": "TEST-001", "run_id": str(uuid4())}
    )
    ticket = begin["updated_ticket"]

    # Fill required fields for fetch_ticket and submit
    ticket["payload"] = {
        "external_source": "jira",
        "external_ticket_id": "TEST-001",
        "title": "Test ticket",
        "description": "Example description"
    }
    result = await client.call_tool(
        "interlock_submit_ticket",
        {"ticket_json": json.dumps(ticket)}
    )
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(test_server())
```

Run it:
```bash
python test_client.py
```

### Test with Claude Desktop (or other MCP client)

1. Add the Interlock server to your MCP config (see **MCP configuration** above). For Claude Desktop on Mac, the config file is usually `~/Library/Application Support/Claude/claude_desktop_config.json`; use the same `mcpServers.interlock` JSON object with `command` and `args`.
2. Restart the client.
3. Use the tools — agent first calls `interlock_begin_run`, then loops with `interlock_submit_ticket` using returned `ticket.json`.

## What Changed

- ✅ **Converted to FastMCP** - Much simpler API with decorators
- ✅ **Cleaner code** - No manual tool registration, FastMCP handles it
- ✅ **Same functionality** - All the governance logic remains the same
- ✅ **Easier to test** - FastMCP supports in-memory testing

## Server Features

The server provides:

- **`interlock_begin_run`**:
  - Input: `ticket_id` and optional `run_id`
  - Output: clean `ticket.json` initialized at `fetch_ticket`
- **`interlock_submit_ticket`**:
  - Input: `ticket_json` (string)
  - Output: updated `ticket.json`, `next_state`, `next_role`, `gate_result`
- **`interlock_next_step`**:
  - Backward-compatible alias of `interlock_submit_ticket`

## Troubleshooting

### Import Errors
```bash
pip install -e .
```

### FastMCP Not Found
```bash
pip install fastmcp>=2.0.0
```

### Server Won't Start
- Check Python version: `python --version` (needs 3.11+)
- Check logs for errors
- Make sure you're in the project directory

## Next Steps

- The server is ready to use with any MCP-compatible client
- You can extend it by adding more tools using `@mcp.tool()` decorator
- For production, consider HTTP transport with authentication
