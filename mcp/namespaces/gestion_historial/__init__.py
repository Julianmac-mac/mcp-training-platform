from .handlers import historial_cursos_namespace
from .config import NAMESPACE_CONFIG

# ffmcp discovers namespaces by directory name. The namespace instance must
# be available as <directory_name>_namespace.
gestion_historial_namespace = historial_cursos_namespace

__all__ = ["historial_cursos_namespace", "gestion_historial_namespace", "NAMESPACE_CONFIG"]
