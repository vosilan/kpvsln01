import os
import socket


def get_username():
    """Получаем имя пользователя разными способами"""
    try:
        # Попробуем разные методы
        return os.getlogin()
    except (OSError, AttributeError):
        try:
            return os.environ.get('USER') or os.environ.get('USERNAME') or 'unknown'
        except:
            return 'unknown'


def get_hostname():
    """Получаем имя хоста"""
    try:
        return socket.gethostname()
    except:
        return 'localhost'


def get_current_dir():
    """Получаем текущую директорию с заменой домашней на ~"""
    try:
        current_dir = os.getcwd()
        home_dir = os.path.expanduser("~")

        if current_dir == home_dir:
            return "~"
        elif current_dir.startswith(home_dir + os.sep):
            return "~" + current_dir[len(home_dir):]
        else:
            return current_dir
    except:
        return "?"


def get_console_prompt():
    """Формируем приглашение консоли"""
    username = get_username()
    hostname = get_hostname()
    current_dir = get_current_dir()

    return f"{username}@{hostname}:{current_dir}$ "


# Использование
if __name__ == "__main__":
    prompt = get_console_prompt()
    print(prompt)