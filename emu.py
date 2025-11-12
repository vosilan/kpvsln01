import argparse
import sys
import urllib.request
import gzip
import re


def parse_arguments():
    parser = argparse.ArgumentParser(description='визуализатор графа зависимостей')

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


def download_packages_data(url):
    try:
        with urllib.request.urlopen(url) as response:
            if url.endswith('.gz'):
                return gzip.decompress(response.read()).decode('utf-8')
            else:
                return response.read().decode('utf-8')
    except Exception as e:
        raise Exception(f"ошибка загрузки данных из {url}: {e}")


def load_local_packages_data(file_path):
    try:
        if file_path.endswith('.gz'):
            with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                return f.read()
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        raise Exception(f"ошибка чтения файла {file_path}: {e}")


def parse_dependencies(package_data, package_name, version):
    packages = {}
    current_package = None

    for line in package_data.split('\n'):
        if line.startswith('Package:'):
            current_package = line.split(':', 1)[1].strip()
            packages[current_package] = {'version': '', 'depends': []}
        elif line.startswith('Version:') and current_package:
            packages[current_package]['version'] = line.split(':', 1)[1].strip()
        elif (line.startswith('Depends:') or line.startswith('Pre-Depends:')) and current_package:
            depends_str = line.split(':', 1)[1].strip()
            dependencies = re.split(r',\s*', depends_str)
            for dep in dependencies:
                dep_name = re.split(r'\s*\(', dep)[0].strip()
                if dep_name and dep_name not in packages[current_package]['depends']:
                    packages[current_package]['depends'].append(dep_name)

    if package_name not in packages:
        raise Exception(f"пакет {package_name} не найден")

    if version:
        for pkg_name, pkg_info in packages.items():
            if pkg_name == package_name and pkg_info['version'] == version:
                return pkg_info['depends']
        raise Exception(f"версия {version} для пакета {package_name} не найдена")
    else:
        return packages[package_name]['depends']


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
        print()

        if args.test_mode == 'on':
            package_data = load_local_packages_data(args.source)
        else:
            package_data = download_packages_data(args.source)

        dependencies = parse_dependencies(package_data, args.package, args.version)

        print(f"прямые зависимости пакета {args.package}{' версии ' + args.version if args.version else ''}:")
        for dep in dependencies:
            print(f" - {dep}")

    except Exception as e:
        print(f"ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()