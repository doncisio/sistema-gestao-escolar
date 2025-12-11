import tkinter as tk
from ui.button_factory import ButtonFactory

root = tk.Tk()
root.withdraw()

bf = ButtonFactory()

icons = [
    'icon/plus.png',
    'icon/video-conference.png',
    'icon/notebook.png',
    'icon/learning.png',
    'icon/book.png',
    'icon/update.png'
]

print("Testando carregamento de ícones:")
print("-" * 50)
for icon in icons:
    img = bf._load_image(icon)
    status = "✓ OK" if img is not None else "✗ FALHOU"
    print(f"{icon:30} {status}")

print("-" * 50)
print("\nTeste concluído!")

root.destroy()
