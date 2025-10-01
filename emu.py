import os
import socket
import argparse


def execute_command(cmd_input):
    parts = []
    for part in cmd_input.split():
        if part.startswith('$'):
            var_name = part[1:]
            parts.append(os.getenv(var_name, part))
        else:
            parts.append(part)

    if not parts:
        return

    cmd = parts[0]
    args = parts[1:]

    if cmd == "exit":
        return "exit"
    elif cmd == "ls":
        print(f"ls: {' '.join(args)}")
    elif cmd == "cd":
        if args:
            print(f"cd: {args[0]}")
        else:
            print("cd: ~")
    else:
        print(f"{cmd}: команда не найдена")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--vfs')
    parser.add_argument('--script')
    args = parser.parse_args()

    print(f"DEBUG: VFS={args.vfs}, SCRIPT={args.script}")

    if args.script:
        if os.path.exists(args.script):
            with open(args.script, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        user = os.getlogin()
                        hostname = socket.gethostname()
                        print(f"{user}@{hostname}$ {line}")

                        result = execute_command(line)
                        if result == "exit":
                            break
        else:
            print(f"Ошибка: скрипт {args.script} не найден")
            return

    while True:
        user = os.getlogin()
        hostname = socket.gethostname()
        print(f"{user}@{hostname}$ ", end="")
        cmd_input = input().strip()

        result = execute_command(cmd_input)
        if result == "exit":
            break


if __name__ == "__main__":
    main()