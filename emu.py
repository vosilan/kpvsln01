import argparse
import sys
import os


def parse_arguments():
    parser = argparse.ArgumentParser(description='Визуализатор графа зависимостей')

    parser.add_argument('--package', required=True, help='имя анализируемого пакета')
    parser.add_argument('--source', required=True, help='url репозитория или путь к файлу тестового репозитория')
    parser.add_argument('--test-mode', choices=['on', 'off'], default='off',
                        help='режим работы с тестовым репозиторием')
    parser.add_argument('--version', help='версия пакета')
    parser.add_argument('--tree-output', choices=['on', 'off'], default='off',
                        help='режим вывода зависимостей в формате ascii-дерева')
    parser.add_argument('--max-depth', type=int, default=10, help='максимальная глубина анализа зависимостей')

    return parser.parse_args()


def validate_arguments(args):
    errors = []

    if not args.package or not args.package.strip():
        errors.append("имя пакета не может быть пустым")

    if not args.source or not args.source.strip():
        errors.append("источник не может быть пустым")

    if args.max_depth <= 0:
        errors.append("максимальная глубина должна быть положительным числом")

    if args.version and not args.version[0].isdigit():
        errors.append("версия должна начинаться с цифры")

    return errors


def main():
    try:
        args = parse_arguments()

        errors = validate_arguments(args)
        if errors:
            print("ошибки в параметрах:")
            for error in errors:
                print(f" - {error}")
            sys.exit(1)

        print("параметры конфигурации:")
        print(f"package: {args.package}")
        print(f"source: {args.source}")
        print(f"test-mode: {args.test_mode}")
        print(f"version: {args.version}")
        print(f"tree-output: {args.tree_output}")
        print(f"max-depth: {args.max_depth}")

    except Exception as e:
        print(f"критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()