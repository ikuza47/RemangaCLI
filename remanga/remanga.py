from requests import Session


class Remanga:
    def __init__(self) -> None:
        self.api = "https://api.remanga.org/api"
        self.public_api = "https://remanga.org/api"
        self.user_id = None
        self.access_token = None
        self.session = Session()
        self.session.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/103.0.5060.114 Safari/537.36"
            )
        }

    def _post(self, endpoint: str, data: dict) -> dict:
        return self.session.post(f"{self.api}{endpoint}", json=data).json()

    def _get(self, endpoint: str, params: dict = None) -> dict:
        return self.session.get(endpoint, params=params).json()

    def login(self, username: str, password: str) -> dict:
        response = self._post("/users/login/", {
            "user": username,
            "password": password,
        })
        if "content" in response:
            content = response["content"]
            if "access_token" in content:
                self.user_id = content["id"]
                self.access_token = content["access_token"]
                self.session.headers["Authorization"] = f"Bearer {self.access_token}"
        return response

    def get_account_info(self) -> dict:
        return self._get(f"{self.api}/users/current/")

    def get_user_info(self, user_id: int) -> dict:
        return self._get(f"{self.api}/users/{user_id}/")

    def get_title_info(self, dir_slug: str) -> dict:
        return self._get(f"{self.api}/titles/{dir_slug}/")

    def get_title_chapters(self, branch_id: int, page: int = 1) -> dict:
        return self._get(
            f"{self.api}/titles/chapters/",
            params={"branch_id": branch_id, "page": page},
        )

    def mark_chapter_viewed(self, chapter_id: int) -> int:
        r = self.session.post(
            f"{self.api}/activity/views/",
            json={"chapter": chapter_id},
        )
        return r.status_code

    def like_chapters(self, chapter_ids: list[int]) -> dict:
        return self._post("/activity/votes/", {
            "chapter_ids": chapter_ids,
        })

    def send_comment(self, text: str, title_id: int) -> dict:
        return self._post("/v2/activity/comments/", {
            "text": text,
            "title": title_id,
        })

    def send_chapter_comment(self, text: str, chapter_id: int, page: int = -1) -> dict:
        return self._post("/v2/activity/comments/", {
            "text": text,
            "chapter": chapter_id,
            "page": page,
        })
