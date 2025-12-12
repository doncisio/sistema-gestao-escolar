"""
Editor de Imagens Integrado para o Banco de Questões.

Permite editar imagens antes de salvá-las no banco de dados, incluindo:
- Recorte (crop)
- Rotação
- Redimensionamento
- Ajustes de brilho e contraste
- Histórico (desfazer/refazer)
"""

from config_logs import get_logger
logger = get_logger(__name__)

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk, ImageEnhance, ImageFilter
import os
from typing import Callable, Optional, Tuple


class EditorImagem:
    """Editor de imagens integrado para o banco de questões."""
    
    def __init__(self, parent, caminho_imagem: str, callback: Callable[[str], None]):
        """
        Inicializa o editor de imagens.
        
        Args:
            parent: Janela pai
            caminho_imagem: Caminho da imagem a editar
            callback: Função a chamar com o caminho da imagem editada
        """
        self.parent = parent
        self.caminho_original = caminho_imagem
        self.callback = callback
        
        # Carregar imagem
        try:
            self.imagem_original = Image.open(caminho_imagem)
            self.imagem_atual = self.imagem_original.copy()
        except Exception as e:
            logger.error(f"Erro ao carregar imagem: {e}")
            messagebox.showerror("Erro", f"Não foi possível carregar a imagem:\n{e}")
            return
        
        # Histórico para desfazer
        self.historico = [self.imagem_atual.copy()]
        self.indice_historico = 0
        
        # Estado do crop
        self.crop_ativo = False
        self.crop_start = None
        self.crop_end = None
        self.crop_rect_id = None
        
        # PhotoImage atual (para canvas)
        self.photo = None
        
        # Janela
        self.janela = None
    
    def abrir(self):
        """Abre a janela do editor."""
        self.janela = tk.Toplevel(self.parent)
        self.janela.title("✏️ Editor de Imagens")
        self.janela.geometry("1000x700")
        self.janela.grab_set()
        
        self._criar_interface()
        self._atualizar_display()
    
    def _criar_interface(self):
        """Cria a interface do editor."""
        # Barra de ferramentas
        frame_toolbar = tk.Frame(self.janela, bg="#333", height=60)
        frame_toolbar.pack(side="top", fill="x")
        
        # Botões de ferramentas
        botoes = [
            ("✂️ Recortar", self._ativar_crop),
            ("🔄 Girar 90°", lambda: self._rotacionar(90)),
            ("↔️ Redimensionar", self._abrir_redimensionar),
            ("💡 Brilho/Contraste", self._abrir_ajustes),
            ("↩️ Desfazer", self._desfazer),
            ("↪️ Refazer", self._refazer),
            ("💾 Salvar", self._salvar),
            ("❌ Cancelar", self._cancelar)
        ]
        
        for texto, comando in botoes:
            btn = tk.Button(
                frame_toolbar, text=texto, command=comando,
                bg="#555", fg="white", padx=10, pady=5,
                relief="raised", borderwidth=2
            )
            btn.pack(side="left", padx=2, pady=5)
        
        # Canvas para exibir imagem
        self.canvas = tk.Canvas(self.janela, bg="#222", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Bindings para crop
        self.canvas.bind("<Button-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        
        # Label de status
        self.lbl_status = tk.Label(
            self.janela, text=f"Imagem: {os.path.basename(self.caminho_original)} | "
                              f"{self.imagem_atual.width}x{self.imagem_atual.height}px",
            bg="#f0f0f0", anchor="w", padx=10
        )
        self.lbl_status.pack(side="bottom", fill="x")
    
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
        
        # Atualizar status
        self.lbl_status.config(
            text=f"Imagem: {os.path.basename(self.caminho_original)} | "
                 f"{self.imagem_atual.width}x{self.imagem_atual.height}px"
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
        else:
            messagebox.showinfo("Aviso", "Não há ações para desfazer.")
    
    def _refazer(self):
        """Refaz ação desfeita."""
        if self.indice_historico < len(self.historico) - 1:
            self.indice_historico += 1
            self.imagem_atual = self.historico[self.indice_historico].copy()
            self._atualizar_display()
        else:
            messagebox.showinfo("Aviso", "Não há ações para refazer.")
    
    def _rotacionar(self, graus: int):
        """Rotaciona a imagem."""
        self.imagem_atual = self.imagem_atual.rotate(-graus, expand=True)
        self._adicionar_ao_historico()
        self._atualizar_display()
    
    def _ativar_crop(self):
        """Ativa modo de recorte."""
        self.crop_ativo = True
        self.canvas.config(cursor="crosshair")
        messagebox.showinfo(
            "Modo Recorte",
            "Clique e arraste sobre a imagem para selecionar a área a recortar."
        )
    
    def _on_mouse_down(self, event):
        """Início do arrasto para crop."""
        if self.crop_ativo:
            self.crop_start = (event.x, event.y)
            self.crop_end = None
            # Remover retângulo anterior se existir
            if self.crop_rect_id:
                self.canvas.delete(self.crop_rect_id)
                self.crop_rect_id = None
    
    def _on_mouse_drag(self, event):
        """Arrasto para crop."""
        if self.crop_ativo and self.crop_start:
            # Remover retângulo anterior
            if self.crop_rect_id:
                self.canvas.delete(self.crop_rect_id)
            
            # Desenhar novo retângulo de seleção
            self.crop_rect_id = self.canvas.create_rectangle(
                self.crop_start[0], self.crop_start[1],
                event.x, event.y,
                outline="red", width=2, tags="crop_rect"
            )
    
    def _on_mouse_up(self, event):
        """Fim do arrasto - executar crop."""
        if self.crop_ativo and self.crop_start:
            self.crop_end = (event.x, event.y)
            self._executar_crop()
            self.crop_ativo = False
            self.canvas.config(cursor="")
            if self.crop_rect_id:
                self.canvas.delete(self.crop_rect_id)
                self.crop_rect_id = None
    
    def _executar_crop(self):
        """Executa o recorte da imagem."""
        if not self.crop_start or not self.crop_end:
            return
        
        try:
            # Converter coordenadas do canvas para coordenadas da imagem
            canvas_w = self.canvas.winfo_width()
            canvas_h = self.canvas.winfo_height()
            
            # Calcular escala da imagem no canvas
            img_display = self.imagem_atual.copy()
            img_display.thumbnail((canvas_w - 20, canvas_h - 20), Image.Resampling.LANCZOS)
            
            scale_x = self.imagem_atual.width / img_display.width
            scale_y = self.imagem_atual.height / img_display.height
            
            # Calcular offset (imagem centralizada)
            offset_x = (canvas_w - img_display.width) // 2
            offset_y = (canvas_h - img_display.height) // 2
            
            # Coordenadas do retângulo de seleção
            x1, y1 = min(self.crop_start[0], self.crop_end[0]), min(self.crop_start[1], self.crop_end[1])
            x2, y2 = max(self.crop_start[0], self.crop_end[0]), max(self.crop_start[1], self.crop_end[1])
            
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
            else:
                messagebox.showwarning("Aviso", "Área de seleção inválida.")
                
        except Exception as e:
            logger.error(f"Erro ao executar crop: {e}")
            messagebox.showerror("Erro", f"Erro ao recortar imagem:\n{e}")
    
    def _abrir_redimensionar(self):
        """Abre diálogo para redimensionar."""
        dialog = tk.Toplevel(self.janela)
        dialog.title("Redimensionar Imagem")
        dialog.geometry("400x250")
        dialog.grab_set()
        
        tk.Label(
            dialog, text="Nova Largura (pixels):", anchor="w"
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        entry_w = ttk.Entry(dialog, width=15)
        entry_w.insert(0, str(self.imagem_atual.width))
        entry_w.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        tk.Label(
            dialog, text="Nova Altura (pixels):", anchor="w"
        ).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        entry_h = ttk.Entry(dialog, width=15)
        entry_h.insert(0, str(self.imagem_atual.height))
        entry_h.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        
        var_proporcao = tk.BooleanVar(value=True)
        chk = tk.Checkbutton(
            dialog, text="Manter proporção",
            variable=var_proporcao
        )
        chk.grid(row=2, column=0, columnspan=2, pady=10)
        
        def atualizar_altura(event=None):
            """Atualiza altura ao mudar largura (se manter proporção)."""
            if var_proporcao.get():
                try:
                    nova_w = int(entry_w.get())
                    ratio = nova_w / self.imagem_atual.width
                    nova_h = int(self.imagem_atual.height * ratio)
                    entry_h.delete(0, tk.END)
                    entry_h.insert(0, str(nova_h))
                except ValueError:
                    pass
        
        def atualizar_largura(event=None):
            """Atualiza largura ao mudar altura (se manter proporção)."""
            if var_proporcao.get():
                try:
                    nova_h = int(entry_h.get())
                    ratio = nova_h / self.imagem_atual.height
                    nova_w = int(self.imagem_atual.width * ratio)
                    entry_w.delete(0, tk.END)
                    entry_w.insert(0, str(nova_w))
                except ValueError:
                    pass
        
        entry_w.bind("<KeyRelease>", atualizar_altura)
        entry_h.bind("<KeyRelease>", atualizar_largura)
        
        def aplicar_redimensionamento():
            try:
                nova_w = int(entry_w.get())
                nova_h = int(entry_h.get())
                
                if nova_w <= 0 or nova_h <= 0:
                    messagebox.showerror("Erro", "Dimensões devem ser positivas.")
                    return
                
                if nova_w > 10000 or nova_h > 10000:
                    messagebox.showerror("Erro", "Dimensões muito grandes (máximo 10000px).")
                    return
                
                self.imagem_atual = self.imagem_atual.resize(
                    (nova_w, nova_h), Image.Resampling.LANCZOS
                )
                self._adicionar_ao_historico()
                self._atualizar_display()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Erro", "Digite valores numéricos válidos.")
        
        frame_btns = tk.Frame(dialog)
        frame_btns.grid(row=3, column=0, columnspan=2, pady=20)
        
        tk.Button(
            frame_btns, text="Aplicar", command=aplicar_redimensionamento,
            bg="#4A86E8", fg="white", padx=20
        ).pack(side="left", padx=5)
        
        tk.Button(
            frame_btns, text="Cancelar", command=dialog.destroy,
            bg="#999", fg="white", padx=20
        ).pack(side="left", padx=5)
    
    def _abrir_ajustes(self):
        """Abre diálogo para ajustar brilho e contraste."""
        dialog = tk.Toplevel(self.janela)
        dialog.title("Ajustar Brilho e Contraste")
        dialog.geometry("450x350")
        dialog.grab_set()
        
        # Brilho
        tk.Label(dialog, text="Brilho:", anchor="w").grid(
            row=0, column=0, padx=10, pady=10, sticky="w"
        )
        scale_brilho = ttk.Scale(
            dialog, from_=0.1, to=2.0, orient="horizontal", length=250
        )
        scale_brilho.set(1.0)
        scale_brilho.grid(row=0, column=1, padx=10, pady=10)
        lbl_brilho = tk.Label(dialog, text="1.0")
        lbl_brilho.grid(row=0, column=2, padx=5)
        
        # Contraste
        tk.Label(dialog, text="Contraste:", anchor="w").grid(
            row=1, column=0, padx=10, pady=10, sticky="w"
        )
        scale_contraste = ttk.Scale(
            dialog, from_=0.1, to=2.0, orient="horizontal", length=250
        )
        scale_contraste.set(1.0)
        scale_contraste.grid(row=1, column=1, padx=10, pady=10)
        lbl_contraste = tk.Label(dialog, text="1.0")
        lbl_contraste.grid(row=1, column=2, padx=5)
        
        # Preview
        frame_preview = tk.Frame(dialog, relief="sunken", borderwidth=2)
        frame_preview.grid(row=2, column=0, columnspan=3, padx=10, pady=10)
        
        preview_label = tk.Label(frame_preview)
        preview_label.pack(padx=5, pady=5)
        
        def atualizar_preview(event=None):
            try:
                img_temp = self.imagem_atual.copy()
                
                # Aplicar brilho
                brilho_val = scale_brilho.get()
                lbl_brilho.config(text=f"{brilho_val:.2f}")
                enhancer = ImageEnhance.Brightness(img_temp)
                img_temp = enhancer.enhance(brilho_val)
                
                # Aplicar contraste
                contraste_val = scale_contraste.get()
                lbl_contraste.config(text=f"{contraste_val:.2f}")
                enhancer = ImageEnhance.Contrast(img_temp)
                img_temp = enhancer.enhance(contraste_val)
                
                # Mostrar preview pequeno
                img_temp.thumbnail((200, 200), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img_temp)
                preview_label.config(image=photo)
                preview_label.image = photo  # Manter referência
            except Exception as e:
                logger.error(f"Erro ao atualizar preview: {e}")
        
        scale_brilho.config(command=atualizar_preview)
        scale_contraste.config(command=atualizar_preview)
        atualizar_preview()
        
        def aplicar_ajustes():
            try:
                # Aplicar brilho
                enhancer = ImageEnhance.Brightness(self.imagem_atual)
                self.imagem_atual = enhancer.enhance(scale_brilho.get())
                
                # Aplicar contraste
                enhancer = ImageEnhance.Contrast(self.imagem_atual)
                self.imagem_atual = enhancer.enhance(scale_contraste.get())
                
                self._adicionar_ao_historico()
                self._atualizar_display()
                dialog.destroy()
            except Exception as e:
                logger.error(f"Erro ao aplicar ajustes: {e}")
                messagebox.showerror("Erro", f"Erro ao aplicar ajustes:\n{e}")
        
        frame_btns = tk.Frame(dialog)
        frame_btns.grid(row=3, column=0, columnspan=3, pady=20)
        
        tk.Button(
            frame_btns, text="Aplicar", command=aplicar_ajustes,
            bg="#4A86E8", fg="white", padx=20
        ).pack(side="left", padx=5)
        
        tk.Button(
            frame_btns, text="Cancelar", command=dialog.destroy,
            bg="#999", fg="white", padx=20
        ).pack(side="left", padx=5)
    
    def _salvar(self):
        """Salva a imagem editada."""
        try:
            # Criar nome para imagem editada
            nome_base = os.path.splitext(os.path.basename(self.caminho_original))[0]
            extensao = os.path.splitext(self.caminho_original)[1]
            
            # Salvar temporariamente
            diretorio = os.path.dirname(self.caminho_original)
            caminho_editado = os.path.join(diretorio, f"{nome_base}_editado{extensao}")
            
            # Se já existe, adicionar número
            contador = 1
            while os.path.exists(caminho_editado):
                caminho_editado = os.path.join(
                    diretorio, f"{nome_base}_editado_{contador}{extensao}"
                )
                contador += 1
            
            # Salvar imagem
            self.imagem_atual.save(caminho_editado, quality=95, optimize=True)
            
            # Chamar callback com caminho da imagem editada
            self.callback(caminho_editado)
            
            messagebox.showinfo("Sucesso", "Imagem editada e aplicada com sucesso!")
            self.janela.destroy()
            
        except Exception as e:
            logger.error(f"Erro ao salvar imagem: {e}")
            messagebox.showerror("Erro", f"Erro ao salvar imagem:\n{e}")
    
    def _cancelar(self):
        """Cancela edição."""
        if self.indice_historico > 0:
            resposta = messagebox.askyesno(
                "Confirmar",
                "Descartar todas as alterações?"
            )
            if not resposta:
                return
        
        self.janela.destroy()
