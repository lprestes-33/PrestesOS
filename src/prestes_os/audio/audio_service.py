from pathlib import Path
from datetime import datetime
import subprocess
import time
import signal
import sys
import unicodedata
import re

from prestes_os.services.config_service import ConfigService
from prestes_os.services.event_bus import EventBus

class AudioService:
    def __init__(self):
        self.config = ConfigService()
        self.bus = EventBus()
        self.running = True

    def slug(self, text):
        text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        text = re.sub(r"[^a-zA-Z0-9_-]+", "_", text).strip("_")
        return text or "gravacao"

    def stop(self, *_):
        self.running = False
        subprocess.run(["termux-microphone-record", "-q"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.bus.publish("recording.stopped", "audio", "Gravação finalizada pelo usuário")
        sys.exit(0)

    def record(self, tipo="Outro", titulo=None):
        signal.signal(signal.SIGINT, self.stop)

        duracao_min = int(self.config.get("audio.duracao_parte_minutos", 30))
        duracao_seg = duracao_min * 60
        gravacoes_dir = Path(self.config.get("audio.gravacoes_dir")).expanduser()

        now = datetime.now()
        dia = now.strftime("%d%m%Y")
        hora = now.strftime("%Hh%Mm%Ss")
        titulo = titulo or f"{tipo}_{dia}_{hora}"

        pasta = gravacoes_dir / dia / self.slug(titulo)
        pasta.mkdir(parents=True, exist_ok=True)

        metadata = pasta / "metadata.txt"
        metadata.write_text(
            f"tipo={tipo}\n"
            f"titulo={titulo}\n"
            f"inicio={now.isoformat()}\n"
            f"duracao_parte_minutos={duracao_min}\n",
            encoding="utf-8"
        )

        self.bus.publish("recording.started", "audio", f"Iniciada: {pasta}")

        parte = 1

        while self.running:
            inicio = datetime.now().strftime("%Hh%Mm%Ss")
            arquivo = pasta / f"{inicio}_parte{parte:02d}.opus"

            subprocess.run(["termux-microphone-record", "-q"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)

            self.bus.publish("recording.part.started", "audio", str(arquivo))

            subprocess.run([
                "termux-microphone-record",
                "-f", str(arquivo),
                "-l", str(duracao_seg)
            ])

            time.sleep(duracao_seg + 1)

            subprocess.run(["termux-microphone-record", "-q"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.bus.publish("recording.part.finished", "audio", str(arquivo))
            parte += 1
