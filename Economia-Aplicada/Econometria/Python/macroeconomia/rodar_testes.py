"""
Roda os testes de todas as pastas de macroeconomia (caminhos.PASTAS), uma de
cada vez. Rode a partir da pasta Econometria/:

    python Python/macroeconomia/rodar_testes.py
    python Python/macroeconomia/rodar_testes.py dsge abm2_sem_leiloeiro   # só algumas pastas
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import caminhos  # noqa: E402


def main(filtro) -> int:
    falhas = []
    for pasta in caminhos.PASTAS:
        if not list(pasta.glob("test_*.py")):
            continue
        nome = pasta.relative_to(caminhos.RAIZ)
        if filtro and not any(f in str(nome) for f in filtro):
            continue
        print(f"== {nome}", flush=True)
        resultado = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(pasta)])
        if resultado.returncode != 0:
            falhas.append(str(nome))
    print("\nTodos os testes passaram." if not falhas else f"\nFalharam: {', '.join(falhas)}")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
