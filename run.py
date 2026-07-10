"""
@file run.py
@brief Ponto de entrada da aplicacao Flask.

@details
Cria o cliente web configurado para usar os servidores TCP reais de AS, TGS e
Portal de Notas. O modo debug depende da variavel de ambiente `FLASK_DEBUG`.
"""

import os
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "src"))

from kerberos_notas.client.routes import create_app
from kerberos_notas.config import HOST_KERBEROS, PORTA_AS, PORTA_NOTAS, PORTA_TGS
from kerberos_notas.logs import log_ok

app = create_app(usar_rede=True)

if __name__ == "__main__":
    log_ok(
        "FLASK",
        "Cliente Web iniciado usando servidores Kerberos via TCP",
        {
            "host_kerberos": HOST_KERBEROS,
            "porta_as": PORTA_AS,
            "porta_tgs": PORTA_TGS,
            "porta_notas": PORTA_NOTAS,
            "usar_rede": True,
        },
    )
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
