import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
os.environ["DATABASE_URL"] = f"sqlite:///{RAIZ / '.pytest_cache' / 'teste.db'}"
(RAIZ / ".pytest_cache").mkdir(exist_ok=True)
(RAIZ / ".pytest_cache" / "teste.db").unlink(missing_ok=True)
for k in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"):
    os.environ.pop(k, None)

EXEMPLOS = RAIZ / "exemplos"
