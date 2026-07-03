from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from prestes_os.services.database_service import DatabaseService
from prestes_os.services.event_bus import EventBus
from prestes_os.services.config_service import ConfigService
from prestes_os.services.log_service import LogService

console = Console()

def mostrar_eventos(db):
    rows = db.last_events(10)

    table = Table(title="Últimos eventos")
    table.add_column("ID")
    table.add_column("Tipo")
    table.add_column("Origem")
    table.add_column("Descrição")
    table.add_column("Criado em")

    for row in rows:
        table.add_row(str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]))

    console.print(table)

def selecionar_tipo():
    console.print(Panel.fit(
        "Tipo de gravação\n\n"
        "1 Aula\n"
        "2 Reunião\n"
        "3 Conversa\n"
        "4 Outro",
        border_style="cyan"
    ))
    op = console.input("Escolha: ").strip()
    return {"1": "Aula", "2": "Reuniao", "3": "Conversa", "4": "Outro"}.get(op, "Outro")

def main():
    db = DatabaseService()
    bus = EventBus()
    cfg = ConfigService()
    log = LogService()

    bus.publish("sistema.iniciado", "kernel", "PrestesOS iniciado")

    console.clear()
    console.print(Panel.fit(
        "[bold cyan]PRESTES OS v0.3[/bold cyan]\nPrestes Kernel • Plataforma Pessoal de Conhecimento",
        border_style="cyan"
    ))

    table = Table(show_header=False)
    table.add_row("1", "🎙 Gravar")
    table.add_row("2", "📝 Transcrever")
    table.add_row("3", "🗄 Banco de dados")
    table.add_row("4", "📜 Eventos")
    table.add_row("5", "⚙ Configuração")
    table.add_row("6", "📄 Logs")
    table.add_row("0", "Sair")
    console.print(table)

    op = console.input("\n[bold cyan]Escolha:[/bold cyan] ")

    if op == "1":
        from prestes_os.audio.audio_service import AudioService
        tipo = selecionar_tipo()
        titulo = console.input("Título ENTER para automático: ").strip() or None
        AudioService().record(tipo=tipo, titulo=titulo)

    elif op == "2":
        console.print("[yellow]TranscriptionService será implementado na próxima sprint.[/yellow]")

    elif op == "3":
        console.print("[green]Banco SQLite ativo em ~/PrestesOS/database/prestes.db[/green]")

    elif op == "4":
        mostrar_eventos(db)

    elif op == "5":
        console.print(cfg.load())

    elif op == "6":
        log_path = cfg.get("logs.path")
        console.print(f"[green]Log:[/green] {log_path}")
        import os
        os.system(f'tail -30 "{log_path}" 2>/dev/null')

    elif op == "0":
        bus.publish("sistema.encerrado", "kernel", "Usuário saiu do PrestesOS")
        return

    else:
        console.print("[yellow]Opção inválida.[/yellow]")

if __name__ == "__main__":
    main()
