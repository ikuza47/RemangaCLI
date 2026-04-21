from getpass import getpass

from remanga import Remanga


def _login_with_2fa(client: Remanga, username: str, password: str, methods: list[dict]) -> bool:
    print("\nВключена двухфакторная аутентификация.")
    print("Доступные методы:")
    for i, m in enumerate(methods, 1):
        print(f"  {i}. {m['name']} ({m['type']})")

    choice = input("Выберите метод (номер): ").strip()
    try:
        idx = int(choice) - 1
        method = methods[idx]["type"]
    except (ValueError, IndexError):
        print("Неверный выбор.")
        return False

    resp = client._post("/users/login/", {
        "user": username,
        "password": password,
        "method": method,
    })
    content = resp.get("content", resp)
    msg = content.get("msg", resp.get("msg", ""))
    if "отправлен" not in msg.lower() and "sent" not in msg.lower():
        print(f"\nОшибка: {msg}")
        return False

    print(f"\n{msg}")

    for attempt in range(3):
        code = input("Код из почты: ").strip()
        if not code:
            print("Код не может быть пустым.")
            continue

        resp = client._post("/users/login/", {
            "user": username,
            "password": password,
            "method": method,
            "code": code,
        })
        content = resp.get("content", {})
        if "access_token" in content:
            client.user_id = content["id"]
            client.access_token = content["access_token"]
            client.session.headers["Authorization"] = f"Bearer {client.access_token}"
            return True

        err_msg = resp.get("msg", content.get("msg", "Неверный код"))
        print(f"\nОшибка: {err_msg}")
        if attempt < 2:
            print("Попробуйте ещё раз.")

    print("Превышено число попыток.")
    return False


def login(client: Remanga) -> bool:
    username = input("Логин: ").strip()
    if not username:
        print("Логин не может быть пустым.")
        return False
    password = getpass("Пароль: ")
    if not password:
        print("Пароль не может быть пустым.")
        return False

    response = client.login(username, password)
    content = response.get("content", {})

    if content.get("two_factor_auth"):
        return _login_with_2fa(client, username, password, content.get("methods", []))

    if "access_token" not in content:
        msg = response.get("msg", content.get("msg", "Неизвестная ошибка"))
        print(f"\nОшибка входа: {msg}")
        return False

    return True
