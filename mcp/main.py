"""
Historial Cursos MCP server entrypoint.
"""

import logging
import os
import uvicorn
from ffmcp import create_mcp_app


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    app = create_mcp_app(
        title="Historial Cursos MCP",
        namespaces_dir="./namespaces",
        config_file="mcp.yaml",
    )

    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port_str = os.getenv("SERVER_PORT", "8000")
    try:
        port = int(port_str)
    except ValueError:
        port = 8000

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
