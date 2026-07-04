from dataclasses import dataclass

from prestes_os.services.planning_service import PlanningService


@dataclass
class FakePlatformStatus:
    core_ready: bool


class FakePlatformService:
    def __init__(self, core_ready=True):
        self.core_ready = core_ready
        self.bus = None

    def status(self):
        return FakePlatformStatus(core_ready=self.core_ready)


def test_planning_service_returns_prioritized_cycle_when_foundations_are_ready():
    service = PlanningService(platform_service=FakePlatformService(core_ready=True))

    snapshot = service.snapshot()

    assert snapshot.cycle_name == "Ciclo pos-v1.0"
    assert snapshot.foundation_ready is True
    assert snapshot.summary.startswith("Base local pronta")
    assert [initiative.title for initiative in snapshot.initiatives] == [
        "Consolidar Kernel",
        "Plugin Manager",
        "ConfigService robusto",
        "DatabaseService robusto",
    ]


def test_planning_service_marks_foundation_warning_when_platform_is_not_ready():
    service = PlanningService(platform_service=FakePlatformService(core_ready=False))

    snapshot = service.snapshot()

    assert snapshot.foundation_ready is False
    assert snapshot.summary.startswith("Ainda existem pendencias")
