# Análise e Sugestões de Melhoria - Interface de Criação de Questões

**Arquivo analisado:** [banco_questoes/ui/principal.py](banco_questoes/ui/principal.py)  
**Data da análise:** 12 de dezembro de 2025

---

## 📋 Resumo Executivo

A interface de criação de questões para o banco de dados BNCC apresenta uma estrutura bem organizada e funcional, com suporte a múltiplos tipos de questões e integração com Google Drive. Esta análise identifica oportunidades de melhoria, com ênfase especial na **edição de imagens antes do upload**.

---

## ✅ Pontos Fortes Identificados

1. **Organização em abas** - Interface intuitiva com separação lógica de funcionalidades
2. **Suporte a múltiplos tipos de questão** - Múltipla escolha, dissertativa e verdadeiro/falso
3. **Integração BNCC** - Filtros por componente curricular e habilidades
4. **Upload de imagens** - Suporte a imagens no enunciado e alternativas
5. **Preview de imagens** - Visualização antes de salvar
6. **Backup duplo** - Armazenamento local + Google Drive
7. **Controle de permissões** - Baseado em perfis de usuário
8. **Posicionamento flexível** - Opções de posição da imagem (acima, abaixo, esquerda, direita, inline)

---

## 🔧 Sugestões de Melhorias Prioritárias

### 1. ⭐ **Editor de Imagens Integrado** (ALTA PRIORIDADE)

**Problema atual:**  
O usuário não pode editar imagens antes de salvá-las no banco de dados. Se precisar fazer ajustes (recortar, redimensionar, ajustar brilho, adicionar anotações), precisa usar um editor externo e selecionar a imagem novamente.

**Solução proposta:**  
Implementar um editor de imagens integrado que permita:

#### Funcionalidades do Editor:
- ✂️ **Recorte (crop)** - Selecionar área específica da imagem
- 🔄 **Rotação** - Girar imagem em 90°, 180°, 270°
- 📏 **Redimensionamento** - Ajustar largura/altura mantendo proporção
- 💡 **Ajustes de brilho/contraste** - Melhorar qualidade visual
- ✏️ **Anotações** - Desenhar, adicionar setas, círculos, texto
- 🎨 **Filtros básicos** - Preto e branco, sépia, realce
- ↩️ **Desfazer/Refazer** - Múltiplos níveis deundo/redo
- 💾 **Salvar como nova imagem** - Manter original intacta

#### Implementação sugerida:

```python
def abrir_editor_imagem(self, caminho_imagem: str, tipo: str = 'enunciado', letra_alt: str = None):
    """
    Abre o editor de imagens integrado.
    
    Args:
        caminho_imagem: Caminho da imagem a editar
        tipo: 'enunciado' ou 'alternativa'
        letra_alt: Letra da alternativa (se tipo='alternativa')
    """
    from banco_questoes.ui.editor_imagem import EditorImagem
    
    editor = EditorImagem(
        parent=self.janela,
        caminho_imagem=caminho_imagem,
        callback=lambda caminho_editado: self._aplicar_imagem_editada(
            caminho_editado, tipo, letra_alt
        )
    )
    editor.abrir()

def _aplicar_imagem_editada(self, caminho_editado: str, tipo: str, letra_alt: str = None):
    """Aplica a imagem editada ao campo apropriado."""
    if tipo == 'enunciado':
        self.imagem_enunciado_path = caminho_editado
        nome_arquivo = os.path.basename(caminho_editado)
        self.lbl_imagem_enunciado.config(text=f"✅ {nome_arquivo[:30]}... (editada)")
        self.mostrar_preview_imagem(caminho_editado, self.lbl_preview_enunciado, 150)
    elif tipo == 'alternativa' and letra_alt:
        self.imagens_alternativas[letra_alt] = caminho_editado
        nome_arquivo = os.path.basename(caminho_editado)
        self.labels_imagem_alt[letra_alt].config(text=f"✅ {nome_arquivo[:15]}... (ed)")
        self.mostrar_preview_imagem(caminho_editado, self.labels_preview_alt[letra_alt], 40)
```

#### Interface do Editor:

```python
# Novo arquivo: banco_questoes/ui/editor_imagem.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk, ImageDraw, ImageEnhance, ImageFilter
import os
from typing import Callable, Optional

class EditorImagem:
    """Editor de imagens integrado para o banco de questões."""
    
    def __init__(self, parent, caminho_imagem: str, callback: Callable[[str], None]):
        self.parent = parent
        self.caminho_original = caminho_imagem
        self.callback = callback
        
        # Carregar imagem
        self.imagem_original = Image.open(caminho_imagem)
        self.imagem_atual = self.imagem_original.copy()
        
        # Histórico para desfazer
        self.historico = [self.imagem_atual.copy()]
        self.indice_historico = 0
        
        # Estado do crop
        self.crop_ativo = False
        self.crop_coords = None
        
    def abrir(self):
        """Abre a janela do editor."""
        self.janela = tk.Toplevel(self.parent)
        self.janela.title("✏️ Editor de Imagens")
        self.janela.geometry("1000x700")
        self.janela.grab_set()
        
        self._criar_interface()
        
    def _criar_interface(self):
        """Cria a interface do editor."""
        # Barra de ferramentas
        frame_toolbar = tk.Frame(self.janela, bg="#333", height=60)
        frame_toolbar.pack(side="top", fill="x")
        
        # Botões de ferramentas
        botoes = [
            ("✂️ Recortar", self._ativar_crop),
            ("🔄 Rotacionar 90°", lambda: self._rotacionar(90)),
            ("↔️ Redimensionar", self._abrir_redimensionar),
            ("💡 Brilho/Contraste", self._abrir_ajustes),
            ("✏️ Desenhar", self._ativar_desenho),
            ("↩️ Desfazer", self._desfazer),
            ("↪️ Refazer", self._refazer),
            ("💾 Salvar", self._salvar),
            ("❌ Cancelar", self._cancelar)
        ]
        
        for texto, comando in botoes:
            btn = tk.Button(
                frame_toolbar, text=texto, command=comando,
                bg="#555", fg="white", padx=10, pady=5
            )
            btn.pack(side="left", padx=2, pady=5)
        
        # Canvas para exibir imagem
        self.canvas = tk.Canvas(self.janela, bg="#222")
        self.canvas.pack(fill="both", expand=True)
        
        # Atualizar display
        self._atualizar_display()
        
        # Bindings para crop
        self.canvas.bind("<Button-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
    
    def _atualizar_display(self):
        """Atualiza a exibição da imagem no canvas."""
        # Redimensionar para caber no canvas
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        
        if canvas_w <= 1:
            canvas_w = 800
        if canvas_h <= 1:
            canvas_h = 600
        
        img = self.imagem_atual.copy()
        img.thumbnail((canvas_w - 20, canvas_h - 20), Image.Resampling.LANCZOS)
        
        self.photo = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.create_image(
            canvas_w // 2, canvas_h // 2,
            image=self.photo, anchor="center", tags="imagem"
        )
    
    def _adicionar_ao_historico(self):
        """Adiciona estado atual ao histórico."""
        # Remover estados futuros se estamos no meio do histórico
        self.historico = self.historico[:self.indice_historico + 1]
        
        # Adicionar novo estado
        self.historico.append(self.imagem_atual.copy())
        self.indice_historico += 1
        
        # Limitar tamanho do histórico
        if len(self.historico) > 20:
            self.historico.pop(0)
            self.indice_historico -= 1
    
    def _desfazer(self):
        """Desfaz última ação."""
        if self.indice_historico > 0:
            self.indice_historico -= 1
            self.imagem_atual = self.historico[self.indice_historico].copy()
            self._atualizar_display()
    
    def _refazer(self):
        """Refaz ação desfeita."""
        if self.indice_historico < len(self.historico) - 1:
            self.indice_historico += 1
            self.imagem_atual = self.historico[self.indice_historico].copy()
            self._atualizar_display()
    
    def _rotacionar(self, graus: int):
        """Rotaciona a imagem."""
        self.imagem_atual = self.imagem_atual.rotate(-graus, expand=True)
        self._adicionar_ao_historico()
        self._atualizar_display()
    
    def _ativar_crop(self):
        """Ativa modo de recorte."""
        self.crop_ativo = True
        self.canvas.config(cursor="crosshair")
        messagebox.showinfo("Modo Recorte", "Clique e arraste para selecionar a área a recortar.")
    
    def _on_mouse_down(self, event):
        """Início do arrasto para crop."""
        if self.crop_ativo:
            self.crop_start = (event.x, event.y)
    
    def _on_mouse_drag(self, event):
        """Arrasto para crop."""
        if self.crop_ativo and hasattr(self, 'crop_start'):
            # Desenhar retângulo de seleção
            self.canvas.delete("crop_rect")
            self.canvas.create_rectangle(
                self.crop_start[0], self.crop_start[1],
                event.x, event.y,
                outline="red", width=2, tags="crop_rect"
            )
    
    def _on_mouse_up(self, event):
        """Fim do arrasto - executar crop."""
        if self.crop_ativo and hasattr(self, 'crop_start'):
            self.crop_end = (event.x, event.y)
            self._executar_crop()
            self.crop_ativo = False
            self.canvas.config(cursor="")
    
    def _executar_crop(self):
        """Executa o recorte da imagem."""
        if not hasattr(self, 'crop_start') or not hasattr(self, 'crop_end'):
            return
        
        # Converter coordenadas do canvas para coordenadas da imagem
        # (considerar que a imagem pode estar redimensionada no canvas)
        x1, y1 = min(self.crop_start[0], self.crop_end[0]), min(self.crop_start[1], self.crop_end[1])
        x2, y2 = max(self.crop_start[0], self.crop_end[0]), max(self.crop_start[1], self.crop_end[1])
        
        # Proporção de escala
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        img_display = self.imagem_atual.copy()
        img_display.thumbnail((canvas_w - 20, canvas_h - 20), Image.Resampling.LANCZOS)
        
        scale_x = self.imagem_atual.width / img_display.width
        scale_y = self.imagem_atual.height / img_display.height
        
        # Calcular offset (imagem centralizada)
        offset_x = (canvas_w - img_display.width) // 2
        offset_y = (canvas_h - img_display.height) // 2
        
        # Converter para coordenadas da imagem original
        img_x1 = int((x1 - offset_x) * scale_x)
        img_y1 = int((y1 - offset_y) * scale_y)
        img_x2 = int((x2 - offset_x) * scale_x)
        img_y2 = int((y2 - offset_y) * scale_y)
        
        # Validar coordenadas
        img_x1 = max(0, min(img_x1, self.imagem_atual.width))
        img_y1 = max(0, min(img_y1, self.imagem_atual.height))
        img_x2 = max(0, min(img_x2, self.imagem_atual.width))
        img_y2 = max(0, min(img_y2, self.imagem_atual.height))
        
        if img_x2 > img_x1 and img_y2 > img_y1:
            self.imagem_atual = self.imagem_atual.crop((img_x1, img_y1, img_x2, img_y2))
            self._adicionar_ao_historico()
            self._atualizar_display()
            self.canvas.delete("crop_rect")
    
    def _abrir_redimensionar(self):
        """Abre diálogo para redimensionar."""
        dialog = tk.Toplevel(self.janela)
        dialog.title("Redimensionar Imagem")
        dialog.geometry("400x200")
        dialog.grab_set()
        
        tk.Label(dialog, text="Nova Largura:").grid(row=0, column=0, padx=10, pady=10)
        entry_w = ttk.Entry(dialog, width=10)
        entry_w.insert(0, str(self.imagem_atual.width))
        entry_w.grid(row=0, column=1, padx=10, pady=10)
        
        tk.Label(dialog, text="Nova Altura:").grid(row=1, column=0, padx=10, pady=10)
        entry_h = ttk.Entry(dialog, width=10)
        entry_h.insert(0, str(self.imagem_atual.height))
        entry_h.grid(row=1, column=1, padx=10, pady=10)
        
        var_proporcao = tk.BooleanVar(value=True)
        tk.Checkbutton(
            dialog, text="Manter proporção",
            variable=var_proporcao
        ).grid(row=2, column=0, columnspan=2, pady=10)
        
        def aplicar_redimensionamento():
            try:
                nova_w = int(entry_w.get())
                nova_h = int(entry_h.get())
                
                if var_proporcao.get():
                    # Calcular altura proporcional
                    ratio = nova_w / self.imagem_atual.width
                    nova_h = int(self.imagem_atual.height * ratio)
                
                self.imagem_atual = self.imagem_atual.resize(
                    (nova_w, nova_h), Image.Resampling.LANCZOS
                )
                self._adicionar_ao_historico()
                self._atualizar_display()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Erro", "Digite valores numéricos válidos.")
        
        tk.Button(dialog, text="Aplicar", command=aplicar_redimensionamento).grid(
            row=3, column=0, columnspan=2, pady=20
        )
    
    def _abrir_ajustes(self):
        """Abre diálogo para ajustar brilho e contraste."""
        dialog = tk.Toplevel(self.janela)
        dialog.title("Ajustar Brilho e Contraste")
        dialog.geometry("400x250")
        dialog.grab_set()
        
        tk.Label(dialog, text="Brilho:").grid(row=0, column=0, padx=10, pady=10)
        scale_brilho = ttk.Scale(dialog, from_=0.1, to=2.0, orient="horizontal", length=200)
        scale_brilho.set(1.0)
        scale_brilho.grid(row=0, column=1, padx=10, pady=10)
        
        tk.Label(dialog, text="Contraste:").grid(row=1, column=0, padx=10, pady=10)
        scale_contraste = ttk.Scale(dialog, from_=0.1, to=2.0, orient="horizontal", length=200)
        scale_contraste.set(1.0)
        scale_contraste.grid(row=1, column=1, padx=10, pady=10)
        
        # Preview em tempo real
        preview_label = tk.Label(dialog)
        preview_label.grid(row=2, column=0, columnspan=2, pady=10)
        
        def atualizar_preview(event=None):
            img_temp = self.imagem_atual.copy()
            
            # Aplicar brilho
            enhancer = ImageEnhance.Brightness(img_temp)
            img_temp = enhancer.enhance(scale_brilho.get())
            
            # Aplicar contraste
            enhancer = ImageEnhance.Contrast(img_temp)
            img_temp = enhancer.enhance(scale_contraste.get())
            
            # Mostrar preview pequeno
            img_temp.thumbnail((150, 150), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img_temp)
            preview_label.config(image=photo)
            preview_label.image = photo  # Manter referência
        
        scale_brilho.config(command=atualizar_preview)
        scale_contraste.config(command=atualizar_preview)
        atualizar_preview()
        
        def aplicar_ajustes():
            # Aplicar brilho
            enhancer = ImageEnhance.Brightness(self.imagem_atual)
            self.imagem_atual = enhancer.enhance(scale_brilho.get())
            
            # Aplicar contraste
            enhancer = ImageEnhance.Contrast(self.imagem_atual)
            self.imagem_atual = enhancer.enhance(scale_contraste.get())
            
            self._adicionar_ao_historico()
            self._atualizar_display()
            dialog.destroy()
        
        tk.Button(dialog, text="Aplicar", command=aplicar_ajustes).grid(
            row=3, column=0, columnspan=2, pady=20
        )
    
    def _ativar_desenho(self):
        """Ativa modo de desenho (anotações)."""
        messagebox.showinfo(
            "Modo Desenho",
            "Funcionalidade de desenho será implementada em versão futura.\n"
            "Permitirá adicionar setas, círculos, texto e anotações."
        )
    
    def _salvar(self):
        """Salva a imagem editada."""
        # Criar nome para imagem editada
        nome_base = os.path.splitext(os.path.basename(self.caminho_original))[0]
        extensao = os.path.splitext(self.caminho_original)[1]
        
        # Salvar temporariamente
        diretorio = os.path.dirname(self.caminho_original)
        caminho_editado = os.path.join(diretorio, f"{nome_base}_editado{extensao}")
        
        # Se já existe, adicionar número
        contador = 1
        while os.path.exists(caminho_editado):
            caminho_editado = os.path.join(diretorio, f"{nome_base}_editado_{contador}{extensao}")
            contador += 1
        
        try:
            self.imagem_atual.save(caminho_editado)
            
            # Chamar callback com caminho da imagem editada
            self.callback(caminho_editado)
            
            messagebox.showinfo("Sucesso", "Imagem editada e aplicada com sucesso!")
            self.janela.destroy()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar imagem: {e}")
    
    def _cancelar(self):
        """Cancela edição."""
        if messagebox.askyesno("Confirmar", "Descartar alterações?"):
            self.janela.destroy()
```

#### Modificações na interface principal:

```python
# Adicionar botões de edição ao lado dos botões de seleção de imagem

# No método criar_aba_cadastro(), modificar a seção de imagem do enunciado:

tk.Button(
    frame_btn_img, text="✏️ Editar Imagem",
    command=self.editar_imagem_enunciado,
    bg="#FF9800", fg="white"
).pack(side="left", padx=5)

# E adicionar o método:
def editar_imagem_enunciado(self):
    """Abre editor para editar imagem do enunciado."""
    if not self.imagem_enunciado_path:
        messagebox.showinfo("Aviso", "Selecione uma imagem primeiro.")
        return
    
    if not os.path.exists(self.imagem_enunciado_path):
        messagebox.showerror("Erro", "Arquivo de imagem não encontrado.")
        return
    
    self.abrir_editor_imagem(self.imagem_enunciado_path, tipo='enunciado')

# Similar para alternativas:
def editar_imagem_alternativa(self, letra: str):
    """Abre editor para editar imagem de uma alternativa."""
    caminho = self.imagens_alternativas.get(letra)
    if not caminho:
        messagebox.showinfo("Aviso", f"Selecione uma imagem para a alternativa {letra} primeiro.")
        return
    
    if not os.path.exists(caminho):
        messagebox.showerror("Erro", "Arquivo de imagem não encontrado.")
        return
    
    self.abrir_editor_imagem(caminho, tipo='alternativa', letra_alt=letra)
```

---

### 2. 📊 **Validação de Tamanho de Arquivo**

**Problema:**  
Não há verificação de tamanho máximo de arquivo, podendo causar problemas de armazenamento.

**Solução:**
```python
def validar_tamanho_imagem(self, caminho: str, tamanho_max_mb: int = 5) -> bool:
    """
    Valida se a imagem não excede o tamanho máximo.
    
    Args:
        caminho: Caminho do arquivo
        tamanho_max_mb: Tamanho máximo em MB
        
    Returns:
        bool: True se válido, False caso contrário
    """
    try:
        tamanho_bytes = os.path.getsize(caminho)
        tamanho_mb = tamanho_bytes / (1024 * 1024)
        
        if tamanho_mb > tamanho_max_mb:
            resposta = messagebox.askyesno(
                "Arquivo Grande",
                f"A imagem tem {tamanho_mb:.1f}MB (máximo recomendado: {tamanho_max_mb}MB).\n\n"
                "Deseja redimensionar automaticamente?",
                icon='warning'
            )
            
            if resposta:
                return self._redimensionar_automatico(caminho, tamanho_max_mb)
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao validar tamanho: {e}")
        return False

def _redimensionar_automatico(self, caminho: str, tamanho_max_mb: int) -> bool:
    """Redimensiona imagem automaticamente para não exceder tamanho máximo."""
    try:
        from PIL import Image
        
        img = Image.open(caminho)
        
        # Reduzir qualidade/tamanho progressivamente
        qualidade = 85
        largura_atual = img.width
        
        while True:
            # Salvar temporariamente
            temp_path = caminho + ".temp.jpg"
            
            if largura_atual < img.width:
                ratio = largura_atual / img.width
                nova_altura = int(img.height * ratio)
                img_redim = img.resize((largura_atual, nova_altura), Image.Resampling.LANCZOS)
            else:
                img_redim = img
            
            img_redim.save(temp_path, "JPEG", quality=qualidade, optimize=True)
            
            # Verificar tamanho
            tamanho_mb = os.path.getsize(temp_path) / (1024 * 1024)
            
            if tamanho_mb <= tamanho_max_mb:
                # Substituir original
                os.replace(temp_path, caminho)
                messagebox.showinfo(
                    "Redimensionamento",
                    f"Imagem redimensionada para {tamanho_mb:.1f}MB"
                )
                return True
            
            # Reduzir mais
            qualidade -= 10
            largura_atual = int(largura_atual * 0.8)
            
            if qualidade < 30 or largura_atual < 200:
                os.remove(temp_path)
                messagebox.showerror(
                    "Erro",
                    "Não foi possível reduzir o tamanho da imagem adequadamente."
                )
                return False
        
    except Exception as e:
        logger.error(f"Erro ao redimensionar: {e}")
        return False
```

---

### 3. 🎨 **Melhorias na Visualização**

**Problema:**  
Preview das imagens pode não mostrar detalhes suficientes.

**Solução:**
```python
def ampliar_preview(self, caminho: str):
    """Abre janela com visualização ampliada da imagem."""
    janela_preview = tk.Toplevel(self.janela)
    janela_preview.title("📷 Visualização da Imagem")
    janela_preview.geometry("800x600")
    
    try:
        from PIL import Image, ImageTk
        
        img = Image.open(caminho)
        
        # Redimensionar para caber na janela
        img.thumbnail((780, 550), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        
        label = tk.Label(janela_preview, image=photo)
        label.image = photo  # Manter referência
        label.pack(expand=True)
        
        # Info da imagem
        info_text = f"Dimensões: {img.width}x{img.height} | Tamanho: {os.path.getsize(caminho) / 1024:.1f}KB"
        tk.Label(janela_preview, text=info_text).pack(pady=10)
        
        tk.Button(
            janela_preview, text="Fechar",
            command=janela_preview.destroy
        ).pack(pady=10)
        
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao visualizar imagem: {e}")
        janela_preview.destroy()

# Adicionar botão "🔍 Ampliar" ao lado dos previews
```

---

### 4. 📝 **Arrastar e Soltar (Drag & Drop)**

**Problema:**  
Usuário precisa sempre usar diálogo de arquivo.

**Solução:**
```python
def habilitar_drag_drop(self):
    """Habilita arrastar e soltar imagens."""
    try:
        from tkinterdnd2 import DND_FILES, TkinterDnD
        
        # Enunciado
        self.frame_preview_enunciado.drop_target_register(DND_FILES)
        self.frame_preview_enunciado.dnd_bind(
            '<<Drop>>',
            lambda e: self._processar_drop(e.data, 'enunciado')
        )
        
        # Alternativas
        for letra in ["A", "B", "C", "D", "E"]:
            self.labels_preview_alt[letra].drop_target_register(DND_FILES)
            self.labels_preview_alt[letra].dnd_bind(
                '<<Drop>>',
                lambda e, l=letra: self._processar_drop(e.data, 'alternativa', l)
            )
            
    except ImportError:
        logger.info("tkinterdnd2 não disponível - drag & drop desabilitado")

def _processar_drop(self, data: str, tipo: str, letra: str = None):
    """Processa arquivo arrastado."""
    # Limpar string do caminho
    caminho = data.strip('{}').strip()
    
    # Verificar se é imagem
    extensoes_validas = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
    if not any(caminho.lower().endswith(ext) for ext in extensoes_validas):
        messagebox.showwarning("Aviso", "Arraste apenas arquivos de imagem.")
        return
    
    if tipo == 'enunciado':
        self.imagem_enunciado_path = caminho
        nome_arquivo = os.path.basename(caminho)
        self.lbl_imagem_enunciado.config(text=f"✅ {nome_arquivo[:30]}...")
        self.mostrar_preview_imagem(caminho, self.lbl_preview_enunciado, 150)
    elif tipo == 'alternativa' and letra:
        self.imagens_alternativas[letra] = caminho
        nome_arquivo = os.path.basename(caminho)
        self.labels_imagem_alt[letra].config(text=f"✅ {nome_arquivo[:15]}...")
        self.mostrar_preview_imagem(caminho, self.labels_preview_alt[letra], 40)
```

---

### 5. 🔍 **Busca de Imagens Online**

**Problema:**  
Usuário precisa sair do sistema para buscar imagens.

**Solução:**
```python
def buscar_imagem_online(self):
    """Abre interface para buscar imagens online (Creative Commons)."""
    janela_busca = tk.Toplevel(self.janela)
    janela_busca.title("🔍 Buscar Imagens Online")
    janela_busca.geometry("900x700")
    
    # Campo de busca
    frame_busca = tk.Frame(janela_busca)
    frame_busca.pack(fill="x", padx=10, pady=10)
    
    tk.Label(frame_busca, text="Buscar:").pack(side="left", padx=5)
    entry_busca = ttk.Entry(frame_busca, width=40)
    entry_busca.pack(side="left", padx=5)
    
    tk.Button(
        frame_busca, text="🔍 Buscar",
        command=lambda: self._executar_busca_imagem(entry_busca.get(), frame_resultados)
    ).pack(side="left", padx=5)
    
    tk.Label(
        frame_busca,
        text="(Apenas imagens Creative Commons)",
        font=("Arial", 8, "italic")
    ).pack(side="left", padx=10)
    
    # Frame para resultados
    frame_resultados = tk.Frame(janela_busca)
    frame_resultados.pack(fill="both", expand=True, padx=10, pady=10)

def _executar_busca_imagem(self, termo: str, frame_resultados):
    """Executa busca de imagens."""
    # Implementar integração com APIs como:
    # - Unsplash API
    # - Pexels API
    # - Pixabay API
    # Todas oferecem imagens gratuitas via API
    
    messagebox.showinfo(
        "Em Desenvolvimento",
        "Funcionalidade de busca online será implementada em breve.\n\n"
        "Integrações planejadas:\n"
        "• Unsplash (fotos profissionais)\n"
        "• Pexels (vídeos e fotos)\n"
        "• Pixabay (ilustrações e fotos)\n\n"
        "Todas com licença gratuita para uso educacional."
    )
```

---

### 6. 💾 **Cache de Imagens**

**Problema:**  
Carregar previews repetidamente pode ser lento.

**Solução:**
```python
def __init__(self, root=None, janela_principal=None):
    # ... código existente ...
    
    # Cache para imagens já carregadas
    self._cache_imagens = {}  # {caminho: (Image, PhotoImage)}
    
def mostrar_preview_imagem(self, caminho: str, label: tk.Label, tamanho_max: int = 100):
    """Mostra preview de uma imagem (com cache)."""
    try:
        # Verificar cache
        cache_key = f"{caminho}_{tamanho_max}"
        if cache_key in self._cache_imagens:
            photo = self._cache_imagens[cache_key]
            label.config(image=photo)
            return
        
        from PIL import Image, ImageTk
        
        img = Image.open(caminho)
        
        # Redimensionar mantendo proporção
        ratio = min(tamanho_max / img.width, tamanho_max / img.height)
        novo_w = int(img.width * ratio)
        novo_h = int(img.height * ratio)
        
        img_resized = img.resize((novo_w, novo_h), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img_resized)
        
        # Armazenar no cache
        self._cache_imagens[cache_key] = photo
        
        label.config(image=photo)
        self._store_image_ref(photo)
        
    except Exception as e:
        logger.error(f"Erro ao mostrar preview: {e}")
        label.config(text="[Erro no preview]")
```

---

### 7. 📋 **Template de Questões**

**Problema:**  
Criar questões similares requer preencher tudo novamente.

**Solução:**
```python
def salvar_como_template(self):
    """Salva questão atual como template."""
    nome = tk.simpledialog.askstring(
        "Nome do Template",
        "Digite um nome para o template:"
    )
    
    if not nome:
        return
    
    try:
        template = {
            'nome': nome,
            'componente': self.cad_componente.get(),
            'ano': self.cad_ano.get(),
            'tipo': self.cad_tipo.get(),
            'dificuldade': self.cad_dificuldade.get(),
            'alternativas': {
                letra: entry.get()
                for letra, entry in self.cad_alternativas.items()
            }
        }
        
        # Salvar em arquivo JSON
        templates_dir = os.path.join("config", "templates_questoes")
        os.makedirs(templates_dir, exist_ok=True)
        
        arquivo = os.path.join(templates_dir, f"{nome}.json")
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        
        messagebox.showinfo("Sucesso", f"Template '{nome}' salvo!")
        
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar template: {e}")

def carregar_template(self):
    """Carrega um template salvo."""
    templates_dir = os.path.join("config", "templates_questoes")
    
    if not os.path.exists(templates_dir):
        messagebox.showinfo("Aviso", "Nenhum template encontrado.")
        return
    
    templates = [f[:-5] for f in os.listdir(templates_dir) if f.endswith('.json')]
    
    if not templates:
        messagebox.showinfo("Aviso", "Nenhum template encontrado.")
        return
    
    # Diálogo de seleção
    janela = tk.Toplevel(self.janela)
    janela.title("Carregar Template")
    janela.geometry("400x300")
    
    tk.Label(janela, text="Selecione um template:").pack(pady=10)
    
    listbox = tk.Listbox(janela, height=10)
    listbox.pack(fill="both", expand=True, padx=10, pady=10)
    
    for template in templates:
        listbox.insert(tk.END, template)
    
    def aplicar():
        seleção = listbox.curselection()
        if not seleção:
            return
        
        nome_template = listbox.get(seleção[0])
        self._aplicar_template(nome_template)
        janela.destroy()
    
    tk.Button(janela, text="Carregar", command=aplicar).pack(pady=10)

def _aplicar_template(self, nome: str):
    """Aplica um template aos campos."""
    try:
        arquivo = os.path.join("config", "templates_questoes", f"{nome}.json")
        with open(arquivo, 'r', encoding='utf-8') as f:
            template = json.load(f)
        
        # Aplicar valores
        if template.get('componente'):
            self.cad_componente.set(template['componente'])
        if template.get('ano'):
            self.cad_ano.set(template['ano'])
        if template.get('tipo'):
            self.cad_tipo.set(template['tipo'])
            self.atualizar_campos_tipo()
        if template.get('dificuldade'):
            self.cad_dificuldade.set(template['dificuldade'])
        
        # Alternativas
        if template.get('alternativas'):
            for letra, texto in template['alternativas'].items():
                if letra in self.cad_alternativas:
                    self.cad_alternativas[letra].delete(0, tk.END)
                    self.cad_alternativas[letra].insert(0, texto)
        
        messagebox.showinfo("Sucesso", f"Template '{nome}' aplicado!")
        
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao carregar template: {e}")
```

---

### 8. 🔄 **Importação em Lote**

**Problema:**  
Não é possível importar múltiplas questões de uma vez.

**Solução:**
```python
def importar_questoes_excel(self):
    """Importa questões de um arquivo Excel."""
    from tkinter import filedialog
    import openpyxl
    
    caminho = filedialog.askopenfilename(
        title="Selecionar arquivo Excel",
        filetypes=[("Excel", "*.xlsx *.xls"), ("Todos", "*.*")]
    )
    
    if not caminho:
        return
    
    try:
        wb = openpyxl.load_workbook(caminho)
        ws = wb.active
        
        # Formato esperado:
        # Colunas: Componente, Ano, Habilidade, Tipo, Dificuldade, Enunciado, 
        #          Alt_A, Alt_B, Alt_C, Alt_D, Alt_E, Gabarito, Caminho_Imagem
        
        questoes_importadas = 0
        erros = []
        
        for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            try:
                # Validar linha
                if not row[0]:  # Componente vazio
                    continue
                
                # Processar questão
                # ... implementar lógica de importação ...
                
                questoes_importadas += 1
                
            except Exception as e:
                erros.append(f"Linha {i}: {str(e)}")
        
        mensagem = f"✅ {questoes_importadas} questões importadas com sucesso!"
        if erros:
            mensagem += f"\n\n⚠️ {len(erros)} erros:\n" + "\n".join(erros[:5])
            if len(erros) > 5:
                mensagem += f"\n... e mais {len(erros) - 5} erros"
        
        messagebox.showinfo("Importação Concluída", mensagem)
        
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao importar: {e}")

def exportar_template_excel(self):
    """Exporta template Excel para importação."""
    from tkinter import filedialog
    import openpyxl
    
    caminho = filedialog.asksaveasfilename(
        title="Salvar template",
        defaultextension=".xlsx",
        filetypes=[("Excel", "*.xlsx")]
    )
    
    if not caminho:
        return
    
    try:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Questões"
        
        # Cabeçalhos
        headers = [
            "Componente", "Ano", "Habilidade_BNCC", "Tipo", "Dificuldade",
            "Enunciado", "Texto_Apoio", "Alt_A", "Alt_B", "Alt_C", "Alt_D", "Alt_E",
            "Gabarito", "Caminho_Imagem_Enunciado"
        ]
        
        for col, header in enumerate(headers, start=1):
            ws.cell(1, col, header)
        
        # Exemplo
        exemplo = [
            "Matemática", "5º ano", "EF05MA08", "multipla_escolha", "media",
            "Quanto é 2 + 2?", "", "3", "4", "5", "6", "",
            "B", ""
        ]
        
        for col, valor in enumerate(exemplo, start=1):
            ws.cell(2, col, valor)
        
        wb.save(caminho)
        
        messagebox.showinfo(
            "Sucesso",
            f"Template exportado!\n\n"
            f"Preencha as colunas seguindo o exemplo da linha 2."
        )
        
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao exportar template: {e}")
```

---

### 9. 🎯 **Prévia da Questão**

**Problema:**  
Não é possível ver como a questão ficará antes de salvar.

**Solução:**
```python
def visualizar_questao(self):
    """Abre preview de como a questão aparecerá para os alunos."""
    janela_preview = tk.Toplevel(self.janela)
    janela_preview.title("👁️ Prévia da Questão")
    janela_preview.geometry("800x600")
    
    # Frame com scroll
    canvas = tk.Canvas(janela_preview)
    scrollbar = ttk.Scrollbar(janela_preview, orient="vertical", command=canvas.yview)
    frame_preview = tk.Frame(canvas, bg="white")
    
    canvas.create_window((0, 0), window=frame_preview, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Renderizar questão
    # Enunciado
    enunciado = self.cad_enunciado.get("1.0", "end").strip()
    if enunciado:
        tk.Label(
            frame_preview, text=enunciado,
            font=("Arial", 11), wraplength=750,
            bg="white", justify="left"
        ).pack(anchor="w", padx=20, pady=10)
    
    # Imagem do enunciado
    if self.imagem_enunciado_path:
        posicao = self.var_posicao_img.get()
        # ... renderizar imagem conforme posição ...
    
    # Alternativas
    if self.cad_tipo.get() == "multipla_escolha":
        for letra, entry in self.cad_alternativas.items():
            texto = entry.get().strip()
            if texto:
                frame_alt = tk.Frame(frame_preview, bg="white")
                frame_alt.pack(anchor="w", padx=20, pady=5)
                
                tk.Label(
                    frame_alt, text=f"{letra})",
                    font=("Arial", 10, "bold"), bg="white"
                ).pack(side="left", padx=5)
                
                tk.Label(
                    frame_alt, text=texto,
                    font=("Arial", 10), bg="white"
                ).pack(side="left", padx=5)
                
                # Imagem da alternativa
                if self.imagens_alternativas.get(letra):
                    # ... renderizar imagem ...
                    pass
    
    frame_preview.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    
    tk.Button(
        janela_preview, text="Fechar",
        command=janela_preview.destroy
    ).pack(pady=10)
```

---

### 10. ⚙️ **Configurações de Qualidade**

**Problema:**  
Não há controle sobre qualidade/compressão das imagens salvas.

**Solução:**
```python
# Adicionar no config.py ou em janela de configurações

CONFIGURACOES_IMAGENS = {
    'qualidade_jpeg': 85,  # 1-100
    'formato_padrao': 'JPEG',  # JPEG, PNG, WEBP
    'max_largura': 1920,
    'max_altura': 1080,
    'tamanho_max_mb': 5,
    'otimizar_automaticamente': True
}

def otimizar_imagem_automaticamente(self, caminho: str) -> str:
    """Otimiza imagem automaticamente antes de salvar."""
    try:
        from PIL import Image
        
        img = Image.open(caminho)
        
        # Redimensionar se necessário
        if img.width > CONFIGURACOES_IMAGENS['max_largura'] or \
           img.height > CONFIGURACOES_IMAGENS['max_altura']:
            img.thumbnail(
                (CONFIGURACOES_IMAGENS['max_largura'], 
                 CONFIGURACOES_IMAGENS['max_altura']),
                Image.Resampling.LANCZOS
            )
        
        # Salvar com compressão
        caminho_otimizado = caminho + ".optimized.jpg"
        img.save(
            caminho_otimizado,
            'JPEG',
            quality=CONFIGURACOES_IMAGENS['qualidade_jpeg'],
            optimize=True
        )
        
        # Verificar se ficou menor
        if os.path.getsize(caminho_otimizado) < os.path.getsize(caminho):
            os.replace(caminho_otimizado, caminho)
        else:
            os.remove(caminho_otimizado)
        
        return caminho
        
    except Exception as e:
        logger.error(f"Erro ao otimizar: {e}")
        return caminho
```

---

## 📦 Dependências Necessárias

Para implementar as melhorias sugeridas, adicionar ao `requirements.txt`:

```txt
# Já existentes
Pillow>=10.0.0

# Novas dependências
tkinterdnd2>=0.3.0  # Para drag & drop
opencv-python>=4.8.0  # Para processamento avançado de imagens (opcional)
numpy>=1.24.0  # Para manipulação de arrays de imagens
openpyxl>=3.1.0  # Para importação/exportação Excel
requests>=2.31.0  # Para busca de imagens online
```

---

## 🎯 Priorização das Implementações

### Fase 1 - Crítico (Implementar primeiro):
1. ✏️ **Editor de imagens integrado** - Solução do problema principal relatado
2. 📊 **Validação de tamanho** - Evita problemas de armazenamento
3. 🎨 **Melhoria nos previews** - Experiência do usuário

### Fase 2 - Importante:
4. 📝 **Drag & drop** - Conveniência
5. 💾 **Cache de imagens** - Performance
6. 📋 **Templates** - Produtividade

### Fase 3 - Desejável:
7. 🔄 **Importação em lote** - Escala
8. 🎯 **Prévia da questão** - Qualidade
9. ⚙️ **Configurações** - Controle fino
10. 🔍 **Busca online** - Conveniência extra

---

## 🚀 Roteiro de Implementação

### Semana 1:
- Criar arquivo `banco_questoes/ui/editor_imagem.py`
- Implementar funcionalidades básicas (crop, rotação, redimensionamento)
- Integrar com interface principal

### Semana 2:
- Adicionar ajustes de brilho/contraste
- Implementar histórico (desfazer/refazer)
- Validação de tamanho de arquivo

### Semana 3:
- Melhorias nos previews
- Sistema de cache
- Drag & drop

### Semana 4:
- Templates de questões
- Prévia da questão
- Testes e refinamentos

---

## 📝 Observações Adicionais

### Segurança:
- Validar tipos de arquivo (evitar executáveis)
- Sanitizar nomes de arquivo
- Limitar tamanho máximo de upload
- Verificar integridade das imagens (detectar arquivos corrompidos)

### Performance:
- Processar imagens em thread separada para não travar interface
- Implementar lazy loading para previews
- Comprimir imagens antes de enviar ao Drive

### Acessibilidade:
- Adicionar textos alternativos (alt text) para imagens
- Suporte a leitores de tela
- Atalhos de teclado para funções comuns

### Backup:
- Manter versão original da imagem
- Histórico de edições
- Possibilidade de reverter para original

---

## 🎓 Conclusão

A interface de criação de questões já possui uma base sólida. As melhorias sugeridas, especialmente o **editor de imagens integrado**, transformarão significativamente a experiência do usuário, eliminando a necessidade de ferramentas externas e agilizando o processo de criação de questões.

O editor permitirá que professores ajustem rapidamente:
- Recortes de diagramas de livros
- Fotos tiradas com celular
- Imagens da internet que precisam ser redimensionadas
- Adição de anotações explicativas

Isso resultará em:
- ⚡ **Maior produtividade** - Menos passos para criar questões
- 🎯 **Melhor qualidade** - Imagens otimizadas e adequadas
- 😊 **Melhor experiência** - Tudo em um só lugar
- 💾 **Economia de espaço** - Imagens otimizadas automaticamente

---

**Desenvolvedor responsável:** Sistema de Gestão Escolar  
**Última atualização:** 12/12/2025
