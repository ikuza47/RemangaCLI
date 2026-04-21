from app.auth import login
from app.session import load_session, save_session, remove_session, restore_client
from app.commands import (
    select_title, read_cmd, like_cmd, about, cmd_status,
    originalcomment, customcomment,
    originalchaptercomment, customchaptercomment,
    suggest_command,
)
from app.display import (
    show_banner, show_help, styled_input,
    print_error, print_warning, print_success, print_dim,
    print_session_expired, print_relogin, print_login_ok,
    print_logout, print_goodbye,
)

from remanga import Remanga


SELECTED: dict | None = None
PREV_SLUG: str | None = None
DEFAULT_DELAY_MS = 200


def create_client() -> Remanga | None:
    session = load_session()
    if session:
        client = restore_client(session)
        info = client.get_account_info()
        if "content" in info:
            save_session(client)
            return client
        remove_session()
        print_session_expired()

    client = Remanga()
    if not login(client):
        return None

    save_session(client)
    print_login_ok()
    return client


def ensure_client(client: Remanga) -> Remanga | None:
    info = client.get_account_info()
    if "content" in info:
        save_session(client)
        return client
    print_relogin()
    return create_client()


def _no_selection() -> None:
    print_warning("Сначала выберите тайтл: select <URL или slug>")


def main() -> None:
    global SELECTED, PREV_SLUG, DEFAULT_DELAY_MS

    show_banner()

    client = create_client()
    if client is None:
        return

    while True:
        try:
            raw = styled_input(SELECTED)
        except (EOFError, KeyboardInterrupt):
            print_goodbye()
            break

        if not raw:
            continue

        parts = raw.split(maxsplit=2)
        cmd = parts[0].lower()

        if cmd in ("exit", "quit", "q"):
            print_goodbye()
            break
        elif cmd == "help":
            show_help()
        elif cmd == "about":
            client = ensure_client(client)
            if client is None:
                return
            about(client)
        elif cmd == "status":
            cmd_status(SELECTED, DEFAULT_DELAY_MS)
        elif cmd in ("originalcomment", "oc"):
            if SELECTED is None:
                _no_selection()
                continue
            if len(parts) < 2:
                print_warning("Использование: oc <текст>")
                continue
            client = ensure_client(client)
            if client is None:
                return
            originalcomment(client, SELECTED, " ".join(parts[1:]))
        elif cmd in ("customcomment", "cc"):
            if SELECTED is None:
                _no_selection()
                continue
            if len(parts) < 2:
                print_warning("Использование: cc <текст>")
                continue
            client = ensure_client(client)
            if client is None:
                return
            customcomment(client, SELECTED, " ".join(parts[1:]))
        elif cmd in ("originalchaptercomment", "och"):
            if SELECTED is None:
                _no_selection()
                continue
            if len(parts) < 3:
                print_warning("Использование: och <номер_главы> <текст>")
                continue
            client = ensure_client(client)
            if client is None:
                return
            originalchaptercomment(client, SELECTED, parts[1], -1, parts[2])
        elif cmd in ("customchaptercomment", "cch"):
            if SELECTED is None:
                _no_selection()
                continue
            if len(parts) < 3:
                print_warning("Использование: cch <номер_главы> <текст>")
                continue
            client = ensure_client(client)
            if client is None:
                return
            customchaptercomment(client, SELECTED, parts[1], -1, parts[2])
        elif cmd == "select":
            if len(parts) < 2:
                print_warning("Использование: select <URL или slug>")
                print_dim("Пример: select https://remanga.org/title/the-pick-me-up_")
                print_dim("         select the-pick-me-up_")
                continue
            arg = " ".join(parts[1:]).strip()
            if arg.lower() == "last" and PREV_SLUG:
                arg = PREV_SLUG
                print_dim(f"Повторный выбор: {arg}")
            elif arg.lower() == "last" and not PREV_SLUG:
                print_warning("Нет предыдущего тайтла.")
                continue
            client = ensure_client(client)
            if client is None:
                return
            result = select_title(client, arg)
            if result:
                if SELECTED:
                    PREV_SLUG = SELECTED["slug"]
                SELECTED = result
        elif cmd == "read":
            if SELECTED is None:
                _no_selection()
                continue
            if len(parts) < 2:
                print_warning("Использование: read <+N> | read <N> | read <от> <до> | read all")
                continue
            client = ensure_client(client)
            if client is None:
                return
            args = parts[1].split() if len(parts) == 2 else parts[1:]
            read_cmd(client, SELECTED, args, DEFAULT_DELAY_MS)
        elif cmd == "like":
            if SELECTED is None:
                _no_selection()
                continue
            if len(parts) < 2:
                print_warning("Использование: like <+N> | like <N> | like <от> <до> | like all")
                continue
            args = parts[1].split() if len(parts) == 2 else parts[1:]
            like_cmd(client, SELECTED, args)
        elif cmd == "delay":
            if len(parts) < 2:
                print_success(f"Текущая задержка: {DEFAULT_DELAY_MS}ms")
                continue
            try:
                DEFAULT_DELAY_MS = int(parts[1])
                print_success(f"Задержка: {DEFAULT_DELAY_MS}ms")
            except ValueError:
                print_error(f"Неверное значение: {parts[1]}")
        elif cmd == "logout":
            remove_session()
            SELECTED = None
            PREV_SLUG = None
            print_logout()
            client = create_client()
            if client is None:
                return
        else:
            suggestion = suggest_command(cmd)
            msg = f"Неизвестная команда: {cmd}"
            if suggestion:
                msg += f" (может [cyan]{suggestion}[/]?)"
            print_error(msg)


if __name__ == "__main__":
    main()
