from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules

hiddenimports = collect_submodules('PyQt6')
binaries = collect_dynamic_libs('PyQt6')

# 添加Qt6核心库
binaries += [
    ('C:\\Qt\\6.5.2\\mingw_64\\bin\\Qt6Core.dll', '.'),
    ('C:\\Qt\\6.5.2\\mingw_64\\bin\\Qt6Gui.dll', '.'),
    ('C:\\Qt\\6.5.2\\mingw_64\\bin\\Qt6Widgets.dll', '.')
] 