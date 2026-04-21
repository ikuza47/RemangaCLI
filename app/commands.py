import sys
import time
import difflib
from urllib.parse import urlparse

from remanga import Remanga
from app.cache import fetch_all_chapters
from app.display import (
    console,
    show_title_info, show_about, show_status, show_help,
    read_progress, print_error, print_warning, print_success,
    print_dim, print_result, print_comment_result, print_like_result,
)


ALL_COMMANDS = [
    "select", "read", "like", "about", "status",
    "originalcomment", "oc", "customcomment", "cc",
    "och", "cch", "delay", "help", "logout", "exit",
]


def suggest_command(typo: str) -> str | None:
    matches = difflib.get_close_matches(typo, ALL_COMMANDS, n=1, cutoff=0.6)
    return matches[0] if matches else None


def _extract_slug(raw: str) -> str:
    raw = raw.strip().strip("\"'")
    if raw.startswith("http"):
        parts = urlparse(raw).path.strip("/").split("/")
        if parts and parts[-1] == "chapters":
            parts = parts[:-1]
        for i, p in enumerate(parts):
            if p in ("title", "manga") and i + 1 < len(parts):
                return parts[i + 1]
        return parts[-1] if parts else raw
    return raw


def _comment_original(message: str) -> str:
    return f'<p dir="ltr"><span style="white-space: pre-wrap;">{message}</span></p>'


def originalcomment(client: Remanga, selected: dict, message: str) -> None:
    text = _comment_original(message)
    title_id = selected["title_id"]
    try:
        resp = client.send_comment(text, title_id)
        print_comment_result(selected["rus_name"], "", resp)
    except Exception as e:
        print_error(f"Ошибка: {e}")


def customcomment(client: Remanga, selected: dict, text: str) -> None:
    title_id = selected["title_id"]
    try:
        resp = client.send_comment(text, title_id)
        print_comment_result(selected["rus_name"], "", resp)
    except Exception as e:
        print_error(f"Ошибка: {e}")


def _find_chapter(chapters: list[dict], chapter_ref: str) -> dict | None:
    for ch in chapters:
        if str(ch.get("chapter", "")) == chapter_ref:
            return ch
    return None


def originalchaptercomment(client: Remanga, selected: dict, chapter_ref: str, page: int, message: str) -> None:
    ch = _find_chapter(selected["chapters"], chapter_ref)
    if ch is None:
        print_error(f"Глава {chapter_ref} не найдена.")
        return
    text = _comment_original(message)
    ch_num = ch.get("chapter", ch["id"])
    try:
        resp = client.send_chapter_comment(text, ch["id"], page)
        print_comment_result(selected["rus_name"], f"гл. {ch_num}", resp)
    except Exception as e:
        print_error(f"Ошибка: {e}")


def customchaptercomment(client: Remanga, selected: dict, chapter_ref: str, page: int, text: str) -> None:
    ch = _find_chapter(selected["chapters"], chapter_ref)
    if ch is None:
        print_error(f"Глава {chapter_ref} не найдена.")
        return
    ch_num = ch.get("chapter", ch["id"])
    try:
        resp = client.send_chapter_comment(text, ch["id"], page)
        print_comment_result(selected["rus_name"], f"гл. {ch_num}", resp)
    except Exception as e:
        print_error(f"Ошибка: {e}")


def about(client: Remanga) -> None:
    info = client.get_account_info()
    content = info.get("content", info)

    if "id" not in content:
        print_error("Не удалось получить информацию об аккаунте.")
        return

    user_id = content.get("id", "—")
    username = content.get("username", "—")
    balance = content.get("balance", "0")
    ticket_balance = content.get("ticket_balance", 0)
    is_premium = content.get("is_premium", False)
    is_superuser = content.get("is_superuser", False)
    is_staff = content.get("is_staff", False)
    count_notifications = content.get("count_notifications", 0)

    detail = client.get_user_info(user_id)
    d = detail.get("content", detail)

    show_about(
        username=username, user_id=user_id,
        level=d.get("level", "—"),
        exp=d.get("exp", "—"),
        read_chapters=d.get("read_chapters", d.get("count_chapters", "—")),
        count_comments=d.get("count_comments", "—"),
        count_ratings=d.get("count_ratings", "—"),
        count_friends=d.get("count_friends", "—"),
        count_bookmarks=d.get("count_bookmarks", "—"),
        balance=balance, ticket_balance=ticket_balance,
        is_premium=is_premium,
        avatar=content.get("avatar", ""),
        count_notifications=count_notifications,
        is_superuser=is_superuser, is_staff=is_staff,
        publishers=content.get("publishers", []),
    )


def cmd_status(selected: dict | None, delay_ms: int) -> None:
    show_status(selected, delay_ms)


def select_title(client: Remanga, raw_url: str) -> dict | None:
    slug = _extract_slug(raw_url)
    print_dim(f"Загрузка {slug}...")

    info = client.get_title_info(slug)
    content = info.get("content", info)

    if "id" not in content:
        msg = info.get("msg", content.get("msg", ""))
        print_error(f"Тайтл не найден: {slug}" + (f" ({msg})" if msg else ""))
        return None

    rus_name = content.get("rus_name") or content.get("en_name") or slug
    en_name = content.get("en_name") or content.get("secondary_name", "")
    is_licensed = content.get("is_licensed", False)
    branches = content.get("branches", [])

    if not branches:
        print_error(f"У тайтла \"{rus_name}\" нет веток с главами.")
        return None

    branch_id = branches[0]["id"]
    total_in_branch = branches[0].get("count_chapters", 0)

    chapters = fetch_all_chapters(client, branch_id)
    total = len(chapters)
    free = sum(1 for ch in chapters if not ch.get("is_paid"))
    paid = total - free
    viewed = sum(1 for ch in chapters if ch.get("viewed"))
    rated = sum(1 for ch in chapters if ch.get("rated"))

    show_title_info(
        rus_name=rus_name, en_name=en_name, total=total, free=free, paid=paid,
        viewed=viewed, rated=rated, is_licensed=is_licensed,
        branch_id=branch_id, total_in_branch=total_in_branch,
    )

    return {
        "slug": slug,
        "title_id": content["id"],
        "rus_name": rus_name,
        "branch_id": branch_id,
        "chapters": chapters,
        "is_licensed": is_licensed,
    }


def _pick_n_unfiltered(chapters: list[dict], filter_fn, count: int) -> list[dict]:
    result = []
    for ch in chapters:
        if not filter_fn(ch):
            result.append(ch)
            if len(result) == count:
                break
    return result


def _parse_read_args(args: list[str], total_chapters: int, chapters: list[dict], filter_fn=None) -> list[dict]:
    if not args:
        print_warning("Использование: read <+N> | read <N> | read <от> <до> | read all")
        return []

    if args[0].lower() == "all":
        return chapters

    if len(args) == 1:
        raw = args[0]
        if raw.startswith("+"):
            try:
                count = int(raw[1:])
            except ValueError:
                print_error(f"Неверное число: {raw}")
                return []
            if count <= 0:
                print_error("Число должно быть положительным.")
                return []
            if filter_fn is None:
                return chapters[:count]
            return _pick_n_unfiltered(chapters, filter_fn, count)
        try:
            count = int(raw)
        except ValueError:
            print_error(f"Неверное число: {raw}")
            return []
        if count <= 0:
            print_error("Число должно быть положительным.")
            return []
        return chapters[:count]

    if len(args) >= 2:
        try:
            start = int(args[0])
            end = int(args[1])
        except ValueError:
            print_error(f"Неверные числа: {args[0]} {args[1]}")
            return []
        if start < 1 or end < start:
            print_error(f"Неверный диапазон: {start}-{end}")
            return []
        return chapters[start - 1:end]

    return []


def read_cmd(client: Remanga, selected: dict, args: list[str], delay_ms: int = 200) -> None:
    chapters = selected["chapters"]
    rus_name = selected["rus_name"]

    to_read = _parse_read_args(args, len(chapters), chapters, filter_fn=lambda ch: ch.get("viewed"))
    if not to_read:
        return

    unviewed = [ch for ch in to_read if not ch.get("viewed")]
    if not unviewed:
        print_dim("Все выбранные главы уже прочитаны.")
        return

    total = len(unviewed)
    console.print(f"  [bold cyan]Чтение:[/] {rus_name} — [dim]{total} гл. | {delay_ms}ms[/]")

    t_start = time.monotonic()
    ok, failed, interrupted = read_progress(
        unviewed, delay_ms, client.mark_chapter_viewed
    )
    elapsed = time.monotonic() - t_start

    print_result(ok, total, failed, interrupted, elapsed)


def like_cmd(client: Remanga, selected: dict, args: list[str]) -> None:
    chapters = selected["chapters"]
    rus_name = selected["rus_name"]

    to_like = _parse_read_args(args, len(chapters), chapters, filter_fn=lambda ch: ch.get("rated"))
    if not to_like:
        return

    unliked = [ch for ch in to_like if not ch.get("rated")]
    if not unliked:
        print_dim("Все выбранные главы уже лайкнуты.")
        return

    chapter_ids = [ch["id"] for ch in unliked]
    skipped = len(to_like) - len(unliked)

    try:
        resp = client.like_chapters(chapter_ids)
        print_like_result(rus_name, len(chapter_ids), skipped, resp)
    except Exception as e:
        print_error(f"Ошибка: {e}")
