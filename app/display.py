import sys
import time

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.prompt import Prompt
from rich.style import Style
from rich.box import ROUNDED

console = Console()

BANNER = Text.from_markup("""[bold magenta]
   ____      _                          ____ _     _
  |  _ \\ ___| |__  _ __ ___   ___      | __ ) _   _| |_
  | |_) / _ \\ '_ \\| '_ ` _ \\ / _ \\     |  _ \\| | | | __|
  |  _ <  __/ |_) | | | | | |  __/     | |_) | |_| | |_
  |_| \\_\\___|_.__/|_| |_| |_|\\___|     |____/ \\__,_|\\__|[/]""")


def show_banner() -> None:
    console.print(BANNER)
    console.print()


def show_panel(title: str, rows: list[tuple[str, str]], subtitle: str = "", border_style: str = "magenta") -> None:
    table = Table.grid(padding=(0, 1), expand=False)
    table.add_column(style="dim", width=18, justify="right")
    table.add_column()
    for key, value in rows:
        table.add_row(key + ":", value)
    panel = Panel(
        table,
        title=f"[bold]{title}[/]",
        subtitle=subtitle or None,
        border_style=border_style,
        box=ROUNDED,
        padding=(0, 2),
    )
    console.print(panel)


def show_title_info(rus_name: str, en_name: str, total: int, free: int, paid: int,
                    viewed: int, rated: int, is_licensed: bool, branch_id: int,
                    total_in_branch: int) -> None:
    rows = [
        ("Название", f"[bold]{rus_name}[/]"),
        ("Всего глав", str(total)),
        ("Бесплатных", str(free)),
        ("Платных", str(paid)),
        ("Прочитано", f"[green]{viewed}[/]/{total}"),
        ("Лайкнуто", f"[yellow]{rated}[/]/{total}"),
        ("Лицензия", "[green]Да[/]" if is_licensed else "[dim]Нет[/]"),
        ("Ветка", f"branch_id={branch_id} ({total_in_branch} гл.)"),
    ]
    if en_name and en_name != rus_name:
        rows.insert(1, ("Англ. название", en_name))
    show_panel("Тайтл", rows, border_style="cyan")


def show_about(
    username: str, user_id: int, level, exp, read_chapters, count_comments,
    count_ratings, count_friends, count_bookmarks, balance, ticket_balance,
    is_premium: bool, avatar: str, count_notifications: int,
    is_superuser: bool, is_staff: bool, publishers: list,
) -> None:
    rows = [
        ("Ник", f"[bold]{username}[/]"),
        ("ID", str(user_id)),
        ("Уровень", str(level)),
        ("EXP", str(exp)),
        ("Прочитано глав", str(read_chapters)),
        ("Комментарии", str(count_comments)),
        ("Оценки", str(count_ratings)),
        ("Друзья", str(count_friends)),
        ("В закладках", str(count_bookmarks)),
        ("Баланс", str(balance)),
        ("Тикеты", str(ticket_balance)),
        ("Премиум", "[green]Да[/]" if is_premium else "[dim]Нет[/]"),
    ]
    if avatar:
        rows.append(("Аватар", f"https://remanga.org{avatar}"))
    rows.append(("Уведомления", str(count_notifications)))
    if is_superuser:
        rows.append(("Админ", "[red]Да[/]"))
    if is_staff:
        rows.append(("Модератор", "[yellow]Да[/]"))
    if publishers:
        rows.append(("Издательства", ""))
        for p in publishers:
            name = p.get("name", "—")
            pid = p.get("id", "—")
            rows.append(("", f"  [dim]-[/] {name} [dim](id: {pid})[/]"))
    show_panel("Аккаунт", rows, border_style="magenta")


def show_status(selected: dict | None, delay_ms: int) -> None:
    rows = [("Задержка", f"{delay_ms}ms")]
    if selected:
        ch = selected["chapters"]
        total = len(ch)
        viewed = sum(1 for c in ch if c.get("viewed"))
        rated = sum(1 for c in ch if c.get("rated"))
        paid = sum(1 for c in ch if c.get("is_paid"))
        rows += [
            ("Тайтл", f"[bold]{selected['rus_name']}[/]"),
            ("Slug", selected["slug"]),
            ("Всего глав", str(total)),
            ("Прочитано", f"[green]{viewed}[/]/{total}"),
            ("Лайкнуто", f"[yellow]{rated}[/]/{total}"),
            ("Платных", str(paid)),
            ("Лицензия", "[green]Да[/]" if selected["is_licensed"] else "[dim]Нет[/]"),
        ]
    else:
        rows.append(("Тайтл", "[dim]не выбран[/]"))
    show_panel("Статус", rows, border_style="blue")


def show_help() -> None:
    table = Table.grid(padding=(0, 2), expand=False)
    table.add_column(style="bold cyan", width=20)
    table.add_column(style="dim")
    table.add_row("Тайтлы", "")
    table.add_row("  select <URL>", "выбрать тайтл")
    table.add_row("  select last", "повторно выбрать прошлый")
    table.add_row("  status", "текущий выбор и статистика")
    table.add_row("", "")
    table.add_row("Чтение и лайки", "")
    table.add_row("  read <N>", "прочитать N глав")
    table.add_row("  read <+N>", "N непрочитанных глав")
    table.add_row("  read <от> <до>", "главы с N по M")
    table.add_row("  read all", "все главы")
    table.add_row("  like ...", "то же для лайков")
    table.add_row("", "")
    table.add_row("Комментарии", "")
    table.add_row("  oc <текст>", "к тайтлу (HTML-обёртка)")
    table.add_row("  cc <текст>", "к тайтлу (сырой текст)")
    table.add_row("  och <гл> <текст>", "к главе (HTML-обёртка)")
    table.add_row("  cch <гл> <текст>", "к главе (сырой текст)")
    table.add_row("", "")
    table.add_row("Аккаунт", "")
    table.add_row("  about", "информация об аккаунте")
    table.add_row("  delay <мс>", "установить задержку")
    table.add_row("  logout", "выйти из аккаунта")
    table.add_row("  exit", "закрыть CLI")
    panel = Panel(table, title="[bold]Команды[/]", border_style="green", box=ROUNDED, padding=(0, 2))
    console.print(panel)


def _fmt_eta(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}м {s}с" if m > 0 else f"{s}с"


def read_progress(unviewed: list[dict], delay_ms: int, mark_fn) -> tuple[int, int, bool]:
    ok = 0
    failed = 0
    interrupted = False

    total = len(unviewed)

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]Чтение[/]"),
        BarColumn(bar_width=30),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("{task.completed}/{task.total}"),
        TimeRemainingColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("", total=total)

        try:
            for ch in unviewed:
                ch_id = ch["id"]
                ch_num = ch.get("chapter", ch_id)
                try:
                    st = mark_fn(ch_id)
                    if st in (200, 201, 204):
                        ok += 1
                    else:
                        failed += 1
                        console.print(f"  [red]Гл. {ch_num}: ошибка {st}[/]")
                except Exception as e:
                    failed += 1
                    console.print(f"  [red]Гл. {ch_num}: {e}[/]")

                progress.advance(task)
                if progress.tasks[0].completed < total:
                    time.sleep(delay_ms / 1000.0)

        except KeyboardInterrupt:
            interrupted = True

    return ok, failed, interrupted


def styled_input(selected: dict | None) -> str:
    if selected:
        name = selected["rus_name"]
        if len(name) > 18:
            name = name[:16] + ".."
        prompt_text = f"[bold cyan]remanga[/] [dim][{name}][/] [bold]>[/] "
    else:
        prompt_text = "[bold cyan]remanga[/] [bold]>[/] "
    return Prompt.ask(prompt_text, console=console)


def print_error(msg: str) -> None:
    console.print(f"[red]  {msg}[/]")


def print_warning(msg: str) -> None:
    console.print(f"[yellow]  {msg}[/]")


def print_success(msg: str) -> None:
    console.print(f"[green]  {msg}[/]")


def print_dim(msg: str) -> None:
    console.print(f"[dim]  {msg}[/]")


def print_result(ok: int, total: int, failed: int, interrupted: bool, elapsed: float) -> None:
    eta = _fmt_eta(elapsed)
    if interrupted:
        console.print(f"  [yellow]Прервано! Успешно: {ok}/{total} | Неудачно: {failed} | Время: {eta}[/]")
    else:
        text = f"  [bold green]Готово! Успешно: {ok}/{total}[/]"
        if failed:
            text += f" [red]| Неудачно: {failed}[/]"
        text += f" [dim]({eta})[/]"
        console.print(text)


def print_login_ok() -> None:
    console.print("  [bold green]Вход выполнен успешно![/]")


def print_session_expired() -> None:
    console.print("  [yellow]Сессия устарела. Необходимо войти заново.[/]")


def print_relogin() -> None:
    console.print("  [yellow]Сессия устарела. Выполняю повторный вход...[/]")


def print_logout() -> None:
    console.print("  [dim]Вы вышли из аккаунта.[/]")


def print_goodbye() -> None:
    console.print("  [dim]Пока![/]")


def print_comment_result(rus_name: str, ch_info: str, resp: dict) -> None:
    label = f"[bold magenta]Комментарий к:[/] {rus_name}"
    if ch_info:
        label += f" — [cyan]{ch_info}[/]"
    console.print(f"  {label}")
    msg = resp.get("msg", "")
    if "content" in resp:
        console.print("  [green]Комментарий отправлен![/]")
    else:
        console.print(f"  [red]Ошибка: {msg or resp}[/]")


def print_like_result(rus_name: str, count: int, skipped: int, resp: dict) -> None:
    console.print(f"  [bold magenta]Лайки:[/] {rus_name}")
    extra = f" (пропущено: {skipped})" if skipped else ""
    console.print(f"  [dim]К лайку: {count}{extra}[/]")
    msg = resp.get("msg", "")
    if "content" in resp or resp.get("status"):
        console.print(f"  [green]Готово! Лайкнуто: {count}[/]")
    else:
        console.print(f"  [red]Ошибка: {msg or resp}[/]")
