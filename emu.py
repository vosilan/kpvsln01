import argparse
import sys
import urllib.request
import gzip
import re
from collections import deque, defaultdict
import subprocess
import os


def parse_arguments():
    parser = argparse.ArgumentParser(description='визуализатор графа зависимостей')

    parser.add_argument('--package', required=True, help='имя анализируемого пакета')
    parser.add_argument('--source', required=True, help='url репозитория или путь к файлу тестового репозитория')
    parser.add_argument('--test-mode', choices=['on', 'off'], default='off',
                        help='режим работы с тестового репозитория')
    parser.add_argument('--version', help='версия пакета')
    parser.add_argument('--tree-output', choices=['on', 'off'], default='off',
                        help='режим вывода зависимостей в формате ascii-дерева')
    parser.add_argument('--max-depth', type=int, default=10, help='максимальная глубина анализа зависимостей')
    parser.add_argument('--show-order', choices=['on', 'off'], default='off',
                        help='режим вывода порядка загрузки зависимостей')
    parser.add_argument('--graph-output', choices=['on', 'off'], default='off',
                        help='режим вывода графа в формате graphviz')

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


def parse_dependencies(package_data, package_name, version, test_mode):
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

            if test_mode == 'on':
                dependencies = re.split(r',\s*', depends_str)
            else:
                dependencies = re.split(r',\s*|\|\s*', depends_str)

            for dep in dependencies:
                if test_mode == 'on':
                    dep_name = dep.strip()
                else:
                    dep_name = re.split(r'\s*\(', dep)[0].strip()

                if dep_name and dep_name not in packages[current_package]['depends']:
                    packages[current_package]['depends'].append(dep_name)

    if package_name not in packages:
        raise Exception(f"пакет {package_name} не найден")

    if version:
        for pkg_name, pkg_info in packages.items():
            if pkg_name == package_name and pkg_info['version'] == version:
                return packages, pkg_info['depends']
        raise Exception(f"версия {version} для пакета {package_name} не найдена")
    else:
        return packages, packages[package_name]['depends']


def build_dependency_graph_bfs(packages, root_package, max_depth):
    graph = {}
    visited = set()
    cycles = []

    def bfs_recursive(current_package, current_depth, path):
        if current_depth > max_depth:
            return

        if current_package not in graph:
            graph[current_package] = []

        if current_package in path:
            cycle_start = path.index(current_package)
            cycle = path[cycle_start:] + [current_package]
            cycles.append(cycle)
            return

        current_path = path + [current_package]

        if current_package in packages:
            for dep in packages[current_package]['depends']:
                if dep not in visited:
                    visited.add(dep)
                    graph[current_package].append(dep)
                    bfs_recursive(dep, current_depth + 1, current_path)

    visited.add(root_package)
    bfs_recursive(root_package, 0, [])
    return graph, cycles


def calculate_install_order(graph, root_package):
    in_degree = defaultdict(int)

    for node in graph:
        in_degree[node] = 0

    for node, deps in graph.items():
        for dep in deps:
            in_degree[dep] += 1

    queue = deque()
    for node in graph:
        if in_degree[node] == 0:
            queue.append(node)

    install_order = []
    while queue:
        current = queue.popleft()
        install_order.append(current)

        for neighbor in graph.get(current, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return install_order


def get_apt_install_order(package_name):
    try:
        result = subprocess.run(['apt-cache', 'depends', package_name],
                                capture_output=True, text=True, check=True)
        lines = result.stdout.split('\n')

        deps = []
        for line in lines:
            if line.strip().startswith('Depends:'):
                dep = line.split(':', 1)[1].strip()
                deps.append(dep.split()[0])

        return deps
    except subprocess.CalledProcessError:
        return None
    except FileNotFoundError:
        return None


def print_ascii_tree(graph, root, prefix="", is_last=True):
    if not graph:
        return

    connectors = {"body": "├── ", "tail": "└── ", "space": "    ", "vert": "│   "}

    print(prefix + (connectors["tail"] if is_last else connectors["body"]) + root)

    if root not in graph:
        return

    children = graph[root]
    for i, child in enumerate(children):
        is_last_child = i == len(children) - 1
        new_prefix = prefix + (connectors["space"] if is_last else connectors["vert"])
        print_ascii_tree(graph, child, new_prefix, is_last_child)


def generate_graphviz_dot(graph, root_package, package_name):
    dot_lines = []
    dot_lines.append('digraph DependencyGraph {')
    dot_lines.append('    rankdir=TB;')
    dot_lines.append('    node [shape=box, style=filled, fillcolor=lightblue];')
    dot_lines.append(f'    "{root_package}" [fillcolor=orange];')

    visited_nodes = set()

    def add_edges(node):
        if node in visited_nodes:
            return
        visited_nodes.add(node)

        if node in graph:
            for dep in graph[node]:
                dot_lines.append(f'    "{node}" -> "{dep}";')
                add_edges(dep)

    add_edges(root_package)
    dot_lines.append('}')

    dot_content = '\n'.join(dot_lines)

    filename = f"{package_name}_dependencies.dot"
    with open(filename, 'w') as f:
        f.write(dot_content)

    return dot_content, filename


def generate_graph_image(dot_filename, output_format='png'):
    try:
        output_filename = dot_filename.replace('.dot', f'.{output_format}')
        subprocess.run(['dot', '-T', output_format, dot_filename, '-o', output_filename],
                       check=True, capture_output=True)
        return output_filename
    except subprocess.CalledProcessError as e:
        raise Exception(f"ошибка генерации изображения: {e}")
    except FileNotFoundError:
        raise Exception("graphviz не установлен. установите: sudo apt install graphviz")


def compare_with_apt_graph(package_name, our_graph):
    try:
        result = subprocess.run(['apt-cache', 'dotty', package_name],
                                capture_output=True, text=True, check=True)
        apt_dot_content = result.stdout

        apt_nodes = set()
        apt_edges = set()

        for line in apt_dot_content.split('\n'):
            if '->' in line:
                parts = line.split('->')
                if len(parts) == 2:
                    from_node = parts[0].strip().strip('"')
                    to_node = parts[1].strip().strip('"').rstrip(';')
                    apt_edges.add((from_node, to_node))
                    apt_nodes.add(from_node)
                    apt_nodes.add(to_node)

        our_nodes = set(our_graph.keys())
        for deps in our_graph.values():
            our_nodes.update(deps)

        our_edges = set()
        for node, deps in our_graph.items():
            for dep in deps:
                our_edges.add((node, dep))

        print("сравнение с apt-cache dotty:")
        print(f" - общие узлы: {len(our_nodes & apt_nodes)}")
        print(f" - общие ребра: {len(our_edges & apt_edges)}")
        print(f" - узлы только в нашем анализе: {len(our_nodes - apt_nodes)}")
        print(f" - узлы только в apt: {len(apt_nodes - our_nodes)}")
        print(f" - ребра только в нашем анализе: {len(our_edges - apt_edges)}")
        print(f" - ребра только в apt: {len(apt_edges - our_edges)}")

        if our_nodes != apt_nodes or our_edges != apt_edges:
            print("\nпричины расхождений:")
            print(" 1. apt-cache dotty показывает полный граф транзитивных зависимостей")
            print(" 2. наш анализ ограничен глубиной max-depth")
            print(" 3. apt учитывает архитектурно-зависимые пакеты")
            print(" 4. разные алгоритмы обработки альтернативных зависимостей")

    except subprocess.CalledProcessError:
        print("apt-cache dotty не доступен для сравнения")
    except FileNotFoundError:
        print("apt-cache не найден")


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
        print(f"show-order: {args.show_order}")
        print(f"graph-output: {args.graph_output}")
        print()

        if args.test_mode == 'on':
            package_data = load_local_packages_data(args.source)
        else:
            package_data = download_packages_data(args.source)

        all_packages, direct_deps = parse_dependencies(package_data, args.package, args.version, args.test_mode)

        print(f"прямые зависимости пакета {args.package}{' версии ' + args.version if args.version else ''}:")
        for dep in direct_deps:
            print(f" - {dep}")
        print()

        dependency_graph, cycles = build_dependency_graph_bfs(all_packages, args.package, args.max_depth)

        print(f"граф зависимостей (глубина {args.max_depth}):")
        for pkg, deps in dependency_graph.items():
            print(f" - {pkg} -> {deps}")
        print()

        if cycles:
            print("обнаружены циклические зависимости:")
            for i, cycle in enumerate(cycles, 1):
                print(f" {i}. {' -> '.join(cycle)}")
            print()
        else:
            print("циклические зависимости не обнаружены")
            print()

        if args.tree_output == 'on':
            print("дерево зависимостей в ascii-формате:")
            print_ascii_tree(dependency_graph, args.package)
            print()

        if args.show_order == 'on':
            print("=== РЕЖИМ ВЫВОДА ПОРЯДКА ЗАГРУЗКИ ===")

            if cycles:
                print("невозможно рассчитать порядок загрузки из-за циклических зависимостей")
            else:
                install_order = calculate_install_order(dependency_graph, args.package)
                print("порядок загрузки зависимостей:")
                for i, pkg in enumerate(install_order, 1):
                    print(f" {i:2d}. {pkg}")
                print()

                if args.test_mode == 'off':
                    apt_order = get_apt_install_order(args.package)
                    if apt_order:
                        print("порядок загрузки через apt-cache depends:")
                        for i, pkg in enumerate(apt_order, 1):
                            print(f" {i:2d}. {pkg}")

        if args.graph_output == 'on':
            print("=== ВИЗУАЛИЗАЦИЯ ГРАФА ЗАВИСИМОСТЕЙ ===")

            dot_content, dot_filename = generate_graphviz_dot(dependency_graph, args.package, args.package)
            print(f"dot-файл создан: {dot_filename}")

            try:
                image_filename = generate_graph_image(dot_filename)
                print(f"изображение графа создано: {image_filename}")
                print(f"для просмотра выполните: xdg-open {image_filename}")
            except Exception as e:
                print(f"{e}")

            if args.test_mode == 'off':
                compare_with_apt_graph(args.package, dependency_graph)

    except Exception as e:
        print(f"ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()