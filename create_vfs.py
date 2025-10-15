import zipfile

with zipfile.ZipFile('test.vfs', 'w') as zipf:
    zipf.writestr('file1.txt', 'Hello from VFS!')
    zipf.writestr('docs/readme.txt', 'This is readme')
    zipf.writestr('docs/api.txt', 'API documentation')
    zipf.writestr('src/main.py', 'print("Hello World")')
    zipf.writestr('src/utils/helper.py', 'def help(): pass')
    zipf.writestr('src/utils/__init__.py', '')
    zipf.writestr('data/config.json', '{"version": 1}')
    zipf.writestr('data/users/admin.json', '{"role": "admin"}')