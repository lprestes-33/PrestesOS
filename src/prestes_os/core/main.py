import argparse
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from prestes_os.audio.audio_service import AudioService
from prestes_os.services.ai_service import AIService
from prestes_os.services.config_service import ConfigService
from prestes_os.services.database_service import DatabaseService
from prestes_os.services.event_bus import EventBus
from prestes_os.services.log_service import LogService
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
    subparsers.add_parser("sincronizar", help="Gera manifesto local para sincronizacao futura.")
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


def executar_preparacao_sync():
    result = SyncService().build_manifest()
    console.print(f"[green]Manifesto gerado:[/green] {result.manifest_file}")
    console.print(f"[green]Arquivos preparados:[/green] {len(result.items)}")


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
    table.add_row("10", "Sincronizar")
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
        executar_preparacao_sync()
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
    if args.command == "sincronizar":
        executar_preparacao_sync()
        return

    executar_menu()


if __name__ == "__main__":
    main(sys.argv[1:])
