import argparse
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from prestes_os.audio.audio_service import AudioService
from prestes_os.services.ai_service import AIService
from prestes_os.services.calendar_service import CalendarService
from prestes_os.services.config_service import ConfigService
from prestes_os.services.database_service import DatabaseService
from prestes_os.services.event_bus import EventBus
from prestes_os.services.gmail_service import GmailService
from prestes_os.services.log_service import LogService
from prestes_os.services.notebooklm_service import NotebookLMService
from prestes_os.services.platform_service import PlatformService
from prestes_os.services.search_service import SearchService
from prestes_os.services.sync_service import SyncService
from prestes_os.services.transcription_service import TranscriptionService

console = Console()


def build_parser():
    parser = argparse.ArgumentParser(prog="prestes", add_help=True)
    subparsers = parser.add_subparsers(dest="command")

    record_parser = subparsers.add_parser("gravar", help="Inicia uma gravacao de audio.")
    record_parser.add_argument(
        "--tipo",
        default="Outro",
        choices=["Aula", "Reuniao", "Conversa", "Outro"],
        help="Tipo da gravacao.",
    )
    record_parser.add_argument("--titulo", default=None, help="Titulo da gravacao.")
    subparsers.add_parser("transcrever", help="Prepara a gravacao mais recente para transcricao.")
    ai_parser = subparsers.add_parser("resumir", help="Gera resumo da transcricao mais recente.")
    ai_parser.add_argument(
        "--tipo",
        default=None,
        choices=["Aula", "Reuniao", "Conversa", "Outro"],
        help="Tipo de resumo a gerar.",
    )
    search_parser = subparsers.add_parser("buscar", help="Busca textual nos conteudos indexados.")
    search_parser.add_argument("consulta", help="Texto a buscar.")
    semantic_parser = subparsers.add_parser("buscar-semantico", help="Busca semantica local nos conteudos indexados.")
    semantic_parser.add_argument("consulta", help="Ideia ou conceito a buscar.")
    subparsers.add_parser("status", help="Exibe um diagnostico consolidado da plataforma.")
    subparsers.add_parser("gmail-status", help="Exibe o preparo local da integracao com Gmail.")
    subparsers.add_parser("calendar-status", help="Exibe o preparo local da integracao com Google Calendar.")
    subparsers.add_parser("notebooklm-status", help="Exibe o preparo local da integracao com NotebookLM.")
    subparsers.add_parser("sincronizar", help="Gera manifesto local para sincronizacao futura.")
    subparsers.add_parser("historico-sync", help="Exibe o historico local de sincronizacao.")
    subparsers.add_parser("falhas-sync", help="Exibe falhas recentes de sincronizacao.")
    subparsers.add_parser("resumo-sync", help="Exibe resumo por execucao de sincronizacao.")
    return parser


def mostrar_eventos(db):
    rows = db.last_events(10)

    table = Table(title="Ultimos eventos")
    table.add_column("ID")
    table.add_column("Tipo")
    table.add_column("Origem")
    table.add_column("Descricao")
    table.add_column("Criado em")

    for row in rows:
        table.add_row(str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]))

    console.print(table)


def selecionar_tipo():
    console.print(
        Panel.fit(
            "Tipo de gravacao\n\n"
            "1 Aula\n"
            "2 Reuniao\n"
            "3 Conversa\n"
            "4 Outro",
            border_style="cyan",
        )
    )
    option = console.input("Escolha: ").strip()
    return {"1": "Aula", "2": "Reuniao", "3": "Conversa", "4": "Outro"}.get(option, "Outro")


def executar_gravacao_direta(tipo="Outro", titulo=None):
    AudioService().record(tipo=tipo, titulo=titulo)


def executar_preparacao_transcricao():
    result = TranscriptionService().transcribe_latest_recording()
    console.print(f"[green]Pasta de saida:[/green] {result.output_folder}")
    console.print(f"[green]Transcricao consolidada:[/green] {result.consolidated_file}")
    for artifact in result.artifacts:
        console.print(f"- {artifact.txt_file}")


def executar_resumo_ia(tipo=None):
    result = AIService().summarize_latest_transcription(summary_type=tipo)
    console.print(f"[green]Resumo gerado:[/green] {result.output_file}")
    console.print(f"[green]Tipo:[/green] {result.summary_type}")


def executar_busca_textual(consulta):
    service = SearchService()
    indexed = service.reindex_documents()
    results = service.search(consulta)
    console.print(f"[green]Documentos indexados:[/green] {indexed}")
    if not results:
        console.print("[yellow]Nenhum resultado encontrado.[/yellow]")
        return
    for result in results:
        console.print(f"[bold]{result.title}[/bold]")
        console.print(f"{result.source_path}")
        console.print(result.snippet)


def executar_busca_semantica(consulta):
    service = SearchService()
    indexed = service.reindex_documents()
    results = service.semantic_search(consulta)
    console.print(f"[green]Documentos indexados:[/green] {indexed}")
    if not results:
        console.print("[yellow]Nenhum resultado semantico encontrado.[/yellow]")
        return
    for result in results:
        console.print(f"[bold]{result.title}[/bold] ({result.score:.2f})")
        console.print(f"{result.source_path}")
        console.print(result.snippet)


def executar_status_gmail():
    status = GmailService().status()
    auth_status = "sim" if status.auth.access_token else "nao"
    console.print(f"[green]Provider:[/green] {status.provider}")
    console.print(f"[green]Autenticado:[/green] {auth_status}")
    console.print(f"[green]Origem do token:[/green] {status.auth.source}")
    console.print(f"[green]Arquivo de credenciais:[/green] {status.auth.credentials_path}")
    console.print(f"[green]Consulta padrao:[/green] {status.default_query}")
    console.print(f"[green]Maximo de resultados:[/green] {status.max_results}")
    console.print(f"[yellow]{status.auth.message}[/yellow]")


def executar_status_calendar():
    status = CalendarService().status()
    auth_status = "sim" if status.auth.access_token else "nao"
    console.print(f"[green]Provider:[/green] {status.provider}")
    console.print(f"[green]Autenticado:[/green] {auth_status}")
    console.print(f"[green]Origem do token:[/green] {status.auth.source}")
    console.print(f"[green]Arquivo de credenciais:[/green] {status.auth.credentials_path}")
    console.print(f"[green]Calendar padrao:[/green] {status.default_calendar_id}")
    console.print(f"[green]Dias a frente:[/green] {status.days_ahead}")
    console.print(f"[yellow]{status.auth.message}[/yellow]")


def executar_status_notebooklm():
    status = NotebookLMService().status()
    auth_status = "sim" if status.auth.access_token else "nao"
    console.print(f"[green]Provider:[/green] {status.provider}")
    console.print(f"[green]Autenticado:[/green] {auth_status}")
    console.print(f"[green]Origem do token:[/green] {status.auth.source}")
    console.print(f"[green]Arquivo de credenciais:[/green] {status.auth.credentials_path}")
    console.print(f"[green]Notebook padrao:[/green] {status.default_notebook}")
    console.print(f"[green]Maximo de fontes:[/green] {status.max_sources}")
    console.print(f"[yellow]{status.auth.message}[/yellow]")


def executar_status_plataforma():
    report = PlatformService().status()
    core_status = "sim" if report.core_ready else "nao"
    console.print(f"[green]Alvo:[/green] {report.target_version}")
    console.print(f"[green]Core pronto:[/green] {core_status}")

    table = Table(title="Diagnostico da plataforma")
    table.add_column("Area")
    table.add_column("Status")
    table.add_column("Mensagem")

    for check in report.checks:
        status_label = "ok" if check.status == "ok" else "aviso"
        table.add_row(check.title, status_label, check.message)

    console.print(table)


def executar_preparacao_sync():
    service = SyncService()
    auth_state = service.resolve_google_drive_auth()
    result = service.execute_sync()
    console.print(f"[green]Execucao:[/green] {result.run_id}")
    console.print(f"[green]Manifesto gerado:[/green] {result.preparation.manifest.manifest_file}")
    console.print(f"[green]Arquivos preparados:[/green] {len(result.preparation.manifest.items)}")
    if result.preparation.upload_plan is not None:
        console.print(f"[green]Plano Google Drive:[/green] {result.preparation.upload_plan.plan_file}")
        status = "sim" if result.preparation.upload_plan.credentials_configured else "nao"
        console.print(f"[green]Credenciais configuradas:[/green] {status}")
        console.print(f"[green]Autenticacao:[/green] {auth_state.source}")
        console.print(f"[green]Arquivos ignorados:[/green] {len(result.preparation.upload_plan.skipped_items)}")
    if result.upload_result is not None:
        console.print(f"[green]Arquivos enviados:[/green] {result.upload_result.uploaded_count}")
        console.print(f"[green]Arquivos reaproveitados:[/green] {result.upload_result.skipped_count}")
    elif result.preparation.upload_plan is not None:
        console.print(f"[yellow]{auth_state.message}[/yellow]")


def executar_historico_sync():
    history = SyncService().read_sync_history()
    console.print(f"[green]Arquivo de estado:[/green] {history.state_file}")
    console.print(f"[green]Itens sincronizados:[/green] {history.total_items}")
    if not history.items:
        console.print("[yellow]Nenhum historico de sincronizacao encontrado.[/yellow]")
        return

    table = Table(title="Historico de sincronizacao")
    table.add_column("Sincronizado em")
    table.add_column("Arquivo local")
    table.add_column("Destino remoto")
    table.add_column("File ID")

    for item in history.items:
        table.add_row(item.synced_at, item.relative_path, item.remote_path, item.file_id)

    console.print(table)


def executar_falhas_sync():
    failures = SyncService().read_sync_failures()
    console.print(f"[green]Arquivo de falhas:[/green] {failures.failure_file}")
    console.print(f"[green]Falhas registradas:[/green] {failures.total_items}")
    if not failures.items:
        console.print("[yellow]Nenhuma falha recente de sincronizacao encontrada.[/yellow]")
        return

    table = Table(title="Falhas recentes de sincronizacao")
    table.add_column("Falhou em")
    table.add_column("Arquivo local")
    table.add_column("Destino remoto")
    table.add_column("Erro")

    for item in failures.items:
        table.add_row(item.failed_at, item.relative_path, item.remote_path, item.error_message)

    console.print(table)


def executar_resumo_sync():
    snapshot = SyncService().read_sync_runs()
    console.print(f"[green]Arquivo de resumo:[/green] {snapshot.summary_file}")
    console.print(f"[green]Execucoes registradas:[/green] {snapshot.total_items}")
    if not snapshot.items:
        console.print("[yellow]Nenhum resumo de sincronizacao encontrado.[/yellow]")
        return

    table = Table(title="Resumo por execucao de sincronizacao")
    table.add_column("Execucao")
    table.add_column("Quando")
    table.add_column("Provider")
    table.add_column("Preparados")
    table.add_column("Enviados")
    table.add_column("Ignorados")
    table.add_column("Falhos")

    for item in snapshot.items:
        table.add_row(
            item.run_id,
            item.executed_at,
            item.provider,
            str(item.prepared_count),
            str(item.uploaded_count),
            str(item.skipped_count),
            str(item.failed_count),
        )

    console.print(table)


def executar_menu():
    db = DatabaseService()
    bus = EventBus()
    cfg = ConfigService()
    log = LogService()

    bus.publish("sistema.iniciado", "kernel", "PrestesOS iniciado")

    console.clear()
    console.print(
        Panel.fit(
            "[bold cyan]PRESTES OS v0.3[/bold cyan]\nPrestes Kernel • Plataforma Pessoal de Conhecimento",
            border_style="cyan",
        )
    )

    table = Table(show_header=False)
    table.add_row("1", "Gravar")
    table.add_row("2", "Transcrever")
    table.add_row("3", "Banco de dados")
    table.add_row("4", "Eventos")
    table.add_row("5", "Configuracao")
    table.add_row("6", "Logs")
    table.add_row("7", "Resumo IA")
    table.add_row("8", "Buscar")
    table.add_row("9", "Buscar Semantico")
    table.add_row("10", "Status Plataforma")
    table.add_row("11", "Gmail Status")
    table.add_row("12", "Calendar Status")
    table.add_row("13", "NotebookLM Status")
    table.add_row("14", "Sincronizar")
    table.add_row("15", "Historico Sync")
    table.add_row("16", "Falhas Sync")
    table.add_row("17", "Resumo Sync")
    table.add_row("0", "Sair")
    console.print(table)

    option = console.input("\n[bold cyan]Escolha:[/bold cyan] ")

    if option == "1":
        tipo = selecionar_tipo()
        titulo = console.input("Titulo ENTER para automatico: ").strip() or None
        executar_gravacao_direta(tipo=tipo, titulo=titulo)
    elif option == "2":
        executar_preparacao_transcricao()
    elif option == "3":
        console.print("[green]Banco SQLite ativo em ~/PrestesOS/database/prestes.db[/green]")
    elif option == "4":
        mostrar_eventos(db)
    elif option == "5":
        console.print(cfg.load())
    elif option == "6":
        log_path = cfg.get("logs.path")
        console.print(f"[green]Log:[/green] {log_path}")
    elif option == "7":
        tipo = selecionar_tipo()
        executar_resumo_ia(tipo=tipo)
    elif option == "8":
        consulta = console.input("Consulta: ").strip()
        executar_busca_textual(consulta)
    elif option == "9":
        consulta = console.input("Consulta semantica: ").strip()
        executar_busca_semantica(consulta)
    elif option == "10":
        executar_status_plataforma()
    elif option == "11":
        executar_status_gmail()
    elif option == "12":
        executar_status_calendar()
    elif option == "13":
        executar_status_notebooklm()
    elif option == "14":
        executar_preparacao_sync()
    elif option == "15":
        executar_historico_sync()
    elif option == "16":
        executar_falhas_sync()
    elif option == "17":
        executar_resumo_sync()
    elif option == "0":
        bus.publish("sistema.encerrado", "kernel", "Usuario saiu do PrestesOS")
    else:
        console.print("[yellow]Opcao invalida.[/yellow]")


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv or [])

    if args.command == "gravar":
        executar_gravacao_direta(tipo=args.tipo, titulo=args.titulo)
        return
    if args.command == "transcrever":
        executar_preparacao_transcricao()
        return
    if args.command == "resumir":
        executar_resumo_ia(tipo=args.tipo)
        return
    if args.command == "buscar":
        executar_busca_textual(args.consulta)
        return
    if args.command == "buscar-semantico":
        executar_busca_semantica(args.consulta)
        return
    if args.command == "status":
        executar_status_plataforma()
        return
    if args.command == "gmail-status":
        executar_status_gmail()
        return
    if args.command == "calendar-status":
        executar_status_calendar()
        return
    if args.command == "notebooklm-status":
        executar_status_notebooklm()
        return
    if args.command == "sincronizar":
        executar_preparacao_sync()
        return
    if args.command == "historico-sync":
        executar_historico_sync()
        return
    if args.command == "falhas-sync":
        executar_falhas_sync()
        return
    if args.command == "resumo-sync":
        executar_resumo_sync()
        return

    executar_menu()


if __name__ == "__main__":
    main(sys.argv[1:])
