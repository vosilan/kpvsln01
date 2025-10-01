import os
import socket


def main():
    while True:
        user = os.getlogin()
        hostname = socket.gethostname()

        print(f"{user}@{hostname}$ ", end="")
        cmd_input = input().strip()

        # Парсер: раскрываем переменные окружения
        parts = []
        for part in cmd_input.split():
            if part.startswith('$'):
                var_name = part[1:]
                parts.append(os.getenv(var_name, part))
            else:
                parts.append(part)

        if not parts:
            continue

        cmd = parts[0]
        args = parts[1:]

        if cmd == "exit":
            break
        elif cmd == "ls":
            print(f"ls: {' '.join(args)}")
        elif cmd == "cd":
            if args:
                print(f"cd: {args[0]}")
            else:
                print("cd: ~")
        else:
            print(f"{cmd}: команда не найдена")


if __name__ == "__main__":
    main()