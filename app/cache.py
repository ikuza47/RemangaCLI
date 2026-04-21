from remanga import Remanga


def fetch_all_chapters(client: Remanga, branch_id: int) -> list[dict]:
    all_chapters = []
    page = 1
    while True:
        resp = client.get_title_chapters(branch_id, page=page)
        content = resp.get("content", [])
        if not isinstance(content, list) or not content:
            break
        all_chapters.extend(content)
        if len(content) < 30:
            break
        page += 1
    all_chapters.reverse()
    return all_chapters
