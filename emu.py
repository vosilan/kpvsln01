import os
import socket
import argparse


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
                        print(f"$ {line}")
                        parts = line.split()
                        cmd = parts[0]
                        args_cmd = parts[1:] if len(parts) > 1 else []

                        if cmd == "ls":
                            print(f"ls: {' '.join(args_cmd)}")
                        elif cmd == "cd":
                            print(f"cd: {' '.join(args_cmd)}")
                        elif cmd == "exit":
                            break
                        else:
                            print(f"{cmd}: команда не найдена")
        else:
            print(f"Ошибка: скрипт {args.script} не найден")
            return

    while True:
        user = os.getlogin()
        hostname = socket.gethostname()
        print(f"{user}@{hostname}$ ", end="")
        cmd_input = input().strip()

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