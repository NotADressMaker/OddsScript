"""Unified VigScript CLI front door with legacy BetLang aliases."""

from __future__ import annotations

import argparse
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

from formatting import format_source
from interpreter import Interpreter, LanguageRuntimeError
from lexer import Lexer
from linting import lint_source
from parser import Parser, Program
from sportsbetlang.ingestion.config import DEFAULT_MARKETS, PipelineConfig, SourceConfig, Tooling
from sportsbetlang.ingestion.pipelines.runner import PipelineRunner
from sportsbetlang.lang.ir import build_ir, has_definitely_infinite_loop
from sportsbetlang.lang.limits import EXPERT_LIMITS, SAFE_LIMITS, resolve_runtime_limits
from sportsbetlang.lang.sandbox import HostCapabilities


def _add_runtime_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--mode", choices=("safe", "expert"), default="safe")
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--max-loop", type=int, default=None)
    parser.add_argument("--max-recursion", type=int, default=None)
    parser.add_argument(
        "--no-io", action="store_true", help="Disable host file/network functions (default deny)."
    )
    parser.add_argument(
        "--allow-read-dir",
        action="append",
        default=[],
        help="Allow host_read_text() access under this directory. Repeatable.",
    )
    parser.add_argument(
        "--allow-domain",
        action="append",
        default=[],
        help="Allow host_http_get() to this domain. Repeatable.",
    )
    parser.add_argument(
        "--audit-log", default=None, help="Write host capability audit events to this file."
    )


def _add_json_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--json", dest="as_json", action="store_true", help="Emit machine-readable JSON output."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vigscript",
        description=(
            "VigScript CLI for writing, testing, and explaining betting strategies as code. "
            "Formerly SportsBetLang."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run",
        help="Run a VigScript .vig file (.sportsodds is supported as legacy compatibility).",
    )
    run_parser.add_argument(
        "source", help="Path to a .vig VigScript program (.sportsodds legacy files still work)."
    )
    _add_runtime_flags(run_parser)
    _add_json_flag(run_parser)

    backtest_parser = subparsers.add_parser(
        "backtest", help="Backtest a VigScript .vig strategy file."
    )
    backtest_parser.add_argument(
        "source", help="Path to a .vig VigScript strategy (.sportsodds legacy files still work)."
    )
    _add_runtime_flags(backtest_parser)
    _add_json_flag(backtest_parser)

    repl_parser = subparsers.add_parser("repl", help="Start an interactive VigScript REPL.")
    _add_runtime_flags(repl_parser)
    _add_json_flag(repl_parser)

    test_parser = subparsers.add_parser("test", help="Run repository tests via pytest.")
    test_parser.add_argument("pytest_args", nargs="*", help="Additional pytest args.")
    _add_json_flag(test_parser)

    ingest_parser = subparsers.add_parser("ingest", help="Run ingestion pipelines (backfill/live).")
    ingest_parser.add_argument("mode", choices=("backfill", "live"))
    ingest_parser.add_argument("--sport", required=True)
    ingest_parser.add_argument("--start", dest="start_date", required=True)
    ingest_parser.add_argument("--end", dest="end_date", required=True)
    ingest_parser.add_argument("--markets", default=",".join(DEFAULT_MARKETS))
    _add_json_flag(ingest_parser)

    def add_research_options(research_command_parser: argparse.ArgumentParser) -> None:
        research_command_parser.add_argument("--sources", type=str, help="Path to seed URL list")
        research_command_parser.add_argument("--sitemaps", type=str, help="Path to sitemap list")
        research_command_parser.add_argument("--rss", type=str, help="Path to RSS feed list")
        research_command_parser.add_argument("--no-external-search", action="store_true")
        research_command_parser.add_argument("--max-results", type=int, default=8)
        research_command_parser.add_argument(
            "--cache-dir", type=str, default=".cache/web_research_agent"
        )
        research_command_parser.add_argument("--rate-limit", type=float, default=1.0)
        research_command_parser.add_argument(
            "--user-agent", type=str, default="WebResearchAgent/1.0 (+https://example.org/agent)"
        )

    research_parser = subparsers.add_parser("research", help="Run compliant web research agent.")
    research_parser.add_argument("query", help="Research query")
    add_research_options(research_parser)
    _add_json_flag(research_parser)

    research_terminal_parser = subparsers.add_parser(
        "research-terminal",
        aliases=["research-term"],
        help="Start an interactive terminal for repeated web research queries.",
    )
    add_research_options(research_terminal_parser)
    _add_json_flag(research_terminal_parser)

    format_parser = subparsers.add_parser(
        "format", help="Format a .vig VigScript program (.sportsodds remains compatible)."
    )
    format_parser.add_argument(
        "source", help="Path to a .vig VigScript program (.sportsodds legacy files still work)."
    )
    format_parser.add_argument(
        "--write", action="store_true", help="Write formatted output back to the source file."
    )
    _add_json_flag(format_parser)

    lint_parser = subparsers.add_parser(
        "lint", help="Lint a .vig VigScript program (.sportsodds remains compatible)."
    )
    lint_parser.add_argument(
        "source", help="Path to a .vig VigScript program (.sportsodds legacy files still work)."
    )
    _add_json_flag(lint_parser)

    ufc_parser = subparsers.add_parser(
        "ufc-dataset", help="Build a normalized UFC fight dataset CSV."
    )
    ufc_parser.add_argument("input", help="Input CSV with UFC fight rows.")
    ufc_parser.add_argument(
        "output", help="Output CSV path for normalized fighter-perspective rows."
    )
    _add_json_flag(ufc_parser)
    return parser


def _emit(args: argparse.Namespace, payload: dict, text: str | None = None) -> None:
    if getattr(args, "as_json", False):
        print(json.dumps(payload, indent=2, sort_keys=True))
    elif text:
        print(text)


def _runtime_limits(source: str, args: argparse.Namespace):
    return resolve_runtime_limits(
        source,
        base_limits=SAFE_LIMITS if args.mode == "safe" else EXPERT_LIMITS,
        max_steps=args.max_steps,
        max_loop=args.max_loop,
        max_recursion=args.max_recursion,
    )


def _run_file(args: argparse.Namespace) -> int:
    file_path = Path(args.source)
    if not file_path.exists():
        raise FileNotFoundError(f"File '{args.source}' not found")

    source = file_path.read_text(encoding="utf-8")
    limits = _runtime_limits(source, args)
    tokens = Lexer(source, limits=limits).tokenize()
    ast = Parser(tokens, source, limits=limits).parse()
    ir_program = build_ir(ast)
    if has_definitely_infinite_loop(ir_program):
        raise LanguageRuntimeError("Program contains a definitely-infinite while true loop")

    interpreter = Interpreter(
        limits=limits,
        source=source,
        capabilities=HostCapabilities(
            no_io=args.no_io,
            allow_read_dirs=args.allow_read_dir,
            allow_domains=args.allow_domain,
        ),
    )
    program_output = ""
    if args.as_json:
        stream = io.StringIO()
        with redirect_stdout(stream):
            interpreter.interpret(Program(statements=ir_program.statements))
        program_output = stream.getvalue()
    else:
        interpreter.interpret(Program(statements=ir_program.statements))

    if args.audit_log:
        Path(args.audit_log).write_text(
            "\n".join(interpreter.capabilities.snapshot_audit_log()) + "\n", encoding="utf-8"
        )

    payload = {"command": "run", "status": "ok", "source": str(file_path)}
    if args.as_json:
        payload["program_output"] = program_output
    _emit(args, payload)
    return 0


def _repl(args: argparse.Namespace) -> int:
    print("VigScript v1.0 - Sports Betting Strategy Language")
    print("Type 'exit' or 'quit' to exit, 'help' for help")
    print()

    limits = _runtime_limits("", args)
    interpreter = Interpreter(
        limits=limits,
        source="",
        capabilities=HostCapabilities(
            no_io=args.no_io,
            allow_read_dirs=args.allow_read_dir,
            allow_domains=args.allow_domain,
        ),
    )

    while True:
        try:
            line = input(">>> ")
            if line.strip() in ["exit", "quit"]:
                break
            if not line.strip():
                continue
            tokens = Lexer(line, limits=limits).tokenize()
            ast = Parser(tokens, line, limits=limits).parse()
            result = interpreter.interpret(ast)
            if result is not None:
                print(result)
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\nInterrupted")
            break
        except LanguageRuntimeError as exc:
            print(f"Error: {exc.format()}")
        except Exception as exc:
            print(f"Error: {exc}")

    _emit(args, {"command": "repl", "status": "ok"})
    return 0


def _test(args: argparse.Namespace) -> int:
    import pytest

    code = pytest.main(args.pytest_args)
    _emit(args, {"command": "test", "status": "ok" if code == 0 else "failed", "exit_code": code})
    return int(code)


def _ingest(args: argparse.Namespace) -> int:
    config = PipelineConfig(
        sport=args.sport,
        start_date=args.start_date,
        end_date=args.end_date,
        markets=[market.strip() for market in args.markets.split(",")],
        sources=SourceConfig(),
    )
    report = PipelineRunner(Tooling()).run(config, mode=args.mode)

    payload = {
        "command": "ingest",
        "status": "ok",
        "mode": args.mode,
        "counts": report.counts,
        "data_gaps": report.data_gaps,
        "feature_preview_sql": report.feature_preview_sql,
    }
    _emit(
        args,
        payload,
        text=(
            "Pipeline run complete\n"
            f"Counts: {report.counts}\n"
            f"Data gaps: {report.data_gaps}\n"
            f"Feature preview SQL: {report.feature_preview_sql}"
        ),
    )
    return 0


def _research(args: argparse.Namespace) -> int:
    from sportsbetlang.web_research_agent.cli import (
        DEFAULT_USER_AGENT,
        _confidence_score,
        _read_url_file,
    )
    from sportsbetlang.web_research_agent.extract import extract_facts
    from sportsbetlang.web_research_agent.fetch import FetchError, RobotsBlockedError, WebFetcher
    from sportsbetlang.web_research_agent.output import build_summary, format_json, format_markdown
    from sportsbetlang.web_research_agent.parse import is_soft_404, parse_html
    from sportsbetlang.web_research_agent.search import SearchConfig, Searcher
    from sportsbetlang.web_research_agent.verify import detect_contradictions, triangulate

    user_agent = args.user_agent or DEFAULT_USER_AGENT
    fetcher = WebFetcher(
        cache_dir=Path(args.cache_dir),
        user_agent=user_agent,
        rate_limit_per_domain=args.rate_limit,
    )
    try:
        config = SearchConfig(
            sitemaps=_read_url_file(args.sitemaps),
            rss_feeds=_read_url_file(args.rss),
            seed_urls=_read_url_file(args.sources),
            no_external_search=args.no_external_search,
        )
        searcher = Searcher(fetcher=fetcher, config=config)
        results = searcher.search(args.query, max_results=args.max_results)

        facts = []
        for result in results:
            try:
                fetched = fetcher.fetch(result.url)
            except (RobotsBlockedError, FetchError):
                continue
            if fetched.status_code in {401, 403}:
                continue
            document = parse_html(fetched.content, fetched.final_url)
            if is_soft_404(document):
                continue
            facts.extend(extract_facts(args.query, document, fetched.fetched_at))

        verification = triangulate(facts)
        contradictions = detect_contradictions(facts)
        confidence = _confidence_score(verification, contradictions)
        summary = build_summary(args.query, verification["confirmed"], verification["unconfirmed"])

        if args.as_json:
            print(format_json(args.query, summary, facts, contradictions, confidence))
        else:
            print(format_markdown(args.query, facts, contradictions, confidence))
        return 0
    finally:
        fetcher.close()



def _research_terminal(args: argparse.Namespace) -> int:
    print("VigScript Research Terminal")
    print("Enter a research query, or type :help, :quit, or :exit.")
    print()

    while True:
        try:
            query = input("research> ").strip()
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\nInterrupted")
            break

        if not query:
            continue
        if query in {":quit", ":exit", "quit", "exit"}:
            break
        if query in {":help", "help"}:
            print("Type any research question to run the compliant web research agent.")
            print("Use :quit or :exit to close the terminal.")
            continue

        query_args = argparse.Namespace(**vars(args))
        query_args.query = query
        code = _research(query_args)
        if code != 0:
            return code
        print()

    _emit(args, {"command": "research-terminal", "status": "ok"})
    return 0

def _format(args: argparse.Namespace) -> int:
    file_path = Path(args.source)
    if not file_path.exists():
        raise FileNotFoundError(f"File '{args.source}' not found")
    source = file_path.read_text(encoding="utf-8")
    formatted = format_source(source)
    if args.write:
        file_path.write_text(formatted, encoding="utf-8")
    else:
        print(formatted, end="")
    _emit(
        args,
        {"command": "format", "status": "ok", "wrote": bool(args.write), "source": str(file_path)},
    )
    return 0


def _lint(args: argparse.Namespace) -> int:
    file_path = Path(args.source)
    if not file_path.exists():
        raise FileNotFoundError(f"File '{args.source}' not found")
    source = file_path.read_text(encoding="utf-8")
    issues = lint_source(source)
    if issues:
        if args.as_json:
            print(
                json.dumps(
                    {
                        "command": "lint",
                        "status": "failed",
                        "issues": [issue.format() for issue in issues],
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            for issue in issues:
                print(issue.format())
        return 1
    _emit(args, {"command": "lint", "status": "ok", "issues": []})
    return 0


def _ufc_dataset(args: argparse.Namespace) -> int:
    from sportsbetlang.data.ufc_dataset import build_ufc_dataset_file

    count = build_ufc_dataset_file(args.input, args.output)
    _emit(
        args,
        {"command": "ufc-dataset", "status": "ok", "rows": count, "output": args.output},
        text=f"Built UFC dataset with {count} rows at {args.output}",
    )
    return 0


def _normalize_argv(argv: list[str]) -> list[str]:
    """Support legacy invocations by translating them to subcommands."""
    if not argv:
        return ["repl"]

    known = {
        "run",
        "repl",
        "test",
        "ingest",
        "research",
        "research-terminal",
        "research-term",
        "format",
        "lint",
        "ufc-dataset",
        "backtest",
        "-h",
        "--help",
        "--version",
    }
    if argv[0] in known:
        return argv

    # Legacy form: `sportsbetlang <file> [runtime-flags]`
    if not argv[0].startswith("-"):
        return ["run", *argv]

    # Legacy formatter/linter forms: `sportsbetlang --format file` or `--lint file`
    if argv[0] in {"--format", "--lint"}:
        command = argv[0][2:]
        return [command, *argv[1:]]

    # Legacy runtime flags before file: `sportsbetlang --max-steps 100 file.sportsodds`
    runtime_flags = {
        "--mode",
        "--max-steps",
        "--max-loop",
        "--max-recursion",
        "--no-io",
        "--allow-read-dir",
        "--allow-domain",
        "--audit-log",
    }
    if argv[0] in runtime_flags and any(not token.startswith("-") for token in argv):
        return ["run", *argv]
    return argv


def main() -> int:
    parser = build_parser()
    args = parser.parse_args(_normalize_argv(sys.argv[1:]))

    try:
        if args.command in {"run", "backtest"}:
            return _run_file(args)
        if args.command == "repl":
            return _repl(args)
        if args.command == "test":
            return _test(args)
        if args.command == "ingest":
            return _ingest(args)
        if args.command == "research":
            return _research(args)
        if args.command in {"research-terminal", "research-term"}:
            return _research_terminal(args)
        if args.command == "format":
            return _format(args)
        if args.command == "lint":
            return _lint(args)
        if args.command == "ufc-dataset":
            return _ufc_dataset(args)
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        return 1
    except LanguageRuntimeError as exc:
        print(f"Runtime Error: {exc.format()}")
        return 1
    except SyntaxError as exc:
        print(f"Syntax Error: {exc}")
        return 1
    except ImportError as exc:
        print(f"Dependency Error: {exc}")
        return 1
    except Exception as exc:
        print(f"Unexpected Error: {exc}")
        return 1

    print("Unknown command. Use --help for usage.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
