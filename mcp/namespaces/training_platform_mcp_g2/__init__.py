from .handlers import training_platform_mcp_g2_namespace
from .config import NAMESPACE_CONFIG

# ffmcp discovers namespaces by directory name. The namespace instance must
# be available as <directory_name>_namespace.

__all__ = ["training_platform_mcp_g2_namespace", "NAMESPACE_CONFIG"]
