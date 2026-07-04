from dataclasses import dataclass

from prestes_os.services.event_bus import EventBus
from prestes_os.services.platform_service import PlatformService


@dataclass
class PlanningInitiative:
    """Responsabilidade: representar uma frente priorizada do ciclo pos-v1.0."""

    title: str
    focus: str
    outcomes: list[str]


@dataclass
class PlanningSnapshot:
    """Responsabilidade: agrupar a recomendacao de planejamento do proximo ciclo."""

    cycle_name: str
    foundation_ready: bool
    summary: str
    initiatives: list[PlanningInitiative]


class PlanningService:
    """Responsabilidade: transformar o roadmap pos-v1.0 em um plano consultavel pela plataforma."""

    def __init__(
        self,
        platform_service: PlatformService | None = None,
        event_bus: EventBus | None = None,
    ):
        self.platform_service = platform_service or PlatformService()
        self.bus = event_bus or getattr(self.platform_service, "bus", None)

    def _initiatives(self) -> list[PlanningInitiative]:
        return [
            PlanningInitiative(
                title="Consolidar Kernel",
                focus="Fortalecer o nucleo operacional e a observabilidade do Prestes Kernel.",
                outcomes=[
                    "padronizar eventos centrais e contratos do EventBus",
                    "reforcar diagnosticos e trilhas de auditoria",
                    "reduzir acoplamentos residuais entre fluxos principais",
                ],
            ),
            PlanningInitiative(
                title="Plugin Manager",
                focus="Abrir caminho para extensoes futuras sem quebrar a base atual.",
                outcomes=[
                    "definir descoberta e registro de plugins",
                    "separar extensoes opcionais do nucleo estavel",
                    "preparar integracoes futuras como modulos acoplados por eventos",
                ],
            ),
            PlanningInitiative(
                title="ConfigService robusto",
                focus="Tornar a configuracao mais segura, validavel e amigavel ao uso diario.",
                outcomes=[
                    "melhorar validacoes e mensagens de configuracao",
                    "padronizar defaults e migracoes simples",
                    "facilitar operacao local no Termux e Linux",
                ],
            ),
            PlanningInitiative(
                title="DatabaseService robusto",
                focus="Fortalecer persistencia e consultas para o crescimento da plataforma.",
                outcomes=[
                    "ampliar operacoes de leitura com metodos dedicados",
                    "preparar evolucao de esquema com baixo risco",
                    "manter SQLite como base confiavel do conhecimento pessoal",
                ],
            ),
        ]

    def snapshot(self) -> PlanningSnapshot:
        platform_status = self.platform_service.status()
        foundation_ready = platform_status.core_ready
        summary = (
            "Base local pronta para iniciar o ciclo pos-v1.0 com foco em consolidacao do nucleo."
            if foundation_ready
            else "Ainda existem pendencias na base local antes de acelerar o ciclo pos-v1.0."
        )
        snapshot = PlanningSnapshot(
            cycle_name="Ciclo pos-v1.0",
            foundation_ready=foundation_ready,
            summary=summary,
            initiatives=self._initiatives(),
        )
        if self.bus is not None:
            self.bus.publish(
                "planning.snapshot.generated",
                "planning",
                snapshot.cycle_name,
                payload={
                    "foundation_ready": snapshot.foundation_ready,
                    "initiatives": len(snapshot.initiatives),
                },
            )
        return snapshot
