from src.core.config_logs import get_logger
logger = get_logger(__name__)
"""
Módulo para integrar o preenchimento automático na interface de notas
Adiciona botão para acionar preenchimento a partir do GEDUC
"""

import tkinter as tk
from tkinter import messagebox
import threading
from typing import Any, Dict, Optional, cast
from src.importadores.geduc import AutomacaoGEDUC
from preencher_notas_automatico import criar_preenchimento_automatico


class IntegradorPreenchimentoAutomatico:
    """
    Integra o preenchimento automático na interface de notas existente
    """
    
    def __init__(self, interface_notas):
        """
        Args:
            interface_notas: Instância da InterfaceCadastroEdicaoNotas
        """
        self.interface = interface_notas
        self.automacao: Optional[AutomacaoGEDUC] = None
        self.thread_preenchimento = None
        
    def adicionar_botao_preenchimento(self):
        """
        Adiciona botão de preenchimento automático na interface
        """
        # Adicionar botão no frame de botões
        if hasattr(self.interface, 'frame_botoes'):
            btn_preencher_auto = tk.Button(
                self.interface.frame_botoes,
                text="🔄 Preencher do GEDUC",
                command=self.iniciar_preenchimento_automatico,
                bg="#9C27B0",  # Roxo
                fg="white",
                font=("Arial", 10, "bold"),
                width=20,
                cursor="hand2"
            )
            btn_preencher_auto.pack(side="left", padx=5)
            
            logger.info("✓ Botão de preenchimento automático adicionado")
    
    def validar_selecoes_interface(self):
        """
        Valida se a interface tem turma, disciplina e bimestre selecionados
        
        Returns:
            dict com as seleções ou None se inválido
        """
        if not hasattr(self.interface, 'cb_serie') or not self.interface.cb_serie.get():
            messagebox.showerror("Erro", "Selecione uma série na interface!")
            return None
        
        if not hasattr(self.interface, 'cb_turma') or not self.interface.cb_turma.get():
            messagebox.showerror("Erro", "Selecione uma turma na interface!")
            return None
        
        if not hasattr(self.interface, 'cb_disciplina') or not self.interface.cb_disciplina.get():
            messagebox.showerror("Erro", "Selecione uma disciplina na interface!")
            return None
        
        if not hasattr(self.interface, 'cb_bimestre') or not self.interface.cb_bimestre.get():
            messagebox.showerror("Erro", "Selecione um bimestre na interface!")
            return None
        
        # Extrair série
        serie_nome = self.interface.cb_serie.get()
        
        # Extrair número do bimestre
        bimestre_texto = self.interface.cb_bimestre.get()
        bimestre_num = bimestre_texto.split('º')[0].strip()
        
        # Extrair turma e turno (formato: " - VESP" ou "A - VESP")
        turma_completa = self.interface.cb_turma.get()
        
        # Debug: verificar o que está vindo
        logger.info(f"\n[DEBUG] Série: '{serie_nome}'")
        logger.info(f"[DEBUG] Turma completa da interface: '{turma_completa}'")
        
        # Dividir por " - " para separar nome da turma e turno
        if ' - ' in turma_completa:
            partes = turma_completa.split(' - ')
            turma_nome = partes[0].strip()
            turma_turno = partes[1].strip() if len(partes) > 1 else ""
        else:
            turma_nome = turma_completa.strip()
            turma_turno = ""
        
        logger.info(f"[DEBUG] Turma nome (letra/identificador): '{turma_nome}'")
        logger.info(f"[DEBUG] Turno: '{turma_turno}'")
        
        # Construir nome completo para busca no GEDUC
        # Formato CORRETO: {SÉRIE} + {TURNO} + {TURMA}
        # Ex: "7º Ano" + "VESP" + "A" = "7º Ano VESP A" ou "7º Ano-VESP"
        if turma_nome:
            # Tem letra/identificador: Série + Turno + Turma
            # Ex: "7º Ano" + "VESP" + "A" = "7º Ano VESP A"
            nome_busca_geduc = f"{serie_nome} {turma_turno} {turma_nome}" if turma_turno else f"{serie_nome} {turma_nome}"
        else:
            # Sem letra/identificador: Série + Turno
            # Ex: "7º Ano" + "VESP" = "7º Ano VESP"
            nome_busca_geduc = f"{serie_nome} {turma_turno}" if turma_turno else serie_nome
        
        logger.info(f"[DEBUG] Nome para busca no GEDUC: '{nome_busca_geduc}'")
        logger.info(f"[DEBUG] Ordem: {{SÉRIE}} + {{TURNO}} + {{TURMA}}")
        
        return {
            'serie': serie_nome,
            'turma': turma_nome,
            'turno': turma_turno,
            'nome_completo_geduc': nome_busca_geduc,
            'turma_completa': turma_completa,
            'disciplina': self.interface.cb_disciplina.get(),
            'bimestre': bimestre_num
        }
    
    def solicitar_credenciais(self):
        """
        Abre janela para solicitar credenciais do GEDUC
        
        Returns:
            dict com 'usuario' e 'senha' ou None se cancelado
        """
        # Criar janela modal
        janela_cred = tk.Toplevel(self.interface.janela)
        janela_cred.title("Credenciais GEDUC")
        janela_cred.geometry("400x200")
        janela_cred.resizable(False, False)
        janela_cred.grab_set()
        
        # Centralizar
        janela_cred.update_idletasks()
        x = (janela_cred.winfo_screenwidth() // 2) - (400 // 2)
        y = (janela_cred.winfo_screenheight() // 2) - (200 // 2)
        janela_cred.geometry(f'400x200+{x}+{y}')
        
        # Variáveis com valores padrão preenchidos
        usuario_var = tk.StringVar(value="01813518386")
        senha_var = tk.StringVar(value="01813518386")
        resultado: Dict[str, Any] = {'confirmado': False}
        
        # Conteúdo
        tk.Label(
            janela_cred,
            text="Credenciais do GEDUC",
            font=("Arial", 14, "bold")
        ).pack(pady=10)
        
        tk.Label(
            janela_cred,
            text="⚠️ Você precisará resolver o reCAPTCHA no navegador",
            font=("Arial", 9, "italic"),
            fg="#E65100"
        ).pack(pady=5)
        
        # Campos
        frame_campos = tk.Frame(janela_cred)
        frame_campos.pack(pady=10, padx=20)
        
        tk.Label(frame_campos, text="Usuário:", width=10, anchor="w").grid(row=0, column=0, pady=5)
        entry_usuario = tk.Entry(frame_campos, textvariable=usuario_var, width=25)
        entry_usuario.grid(row=0, column=1, pady=5)
        
        tk.Label(frame_campos, text="Senha:", width=10, anchor="w").grid(row=1, column=0, pady=5)
        entry_senha = tk.Entry(frame_campos, textvariable=senha_var, width=25, show="*")
        entry_senha.grid(row=1, column=1, pady=5)
        
        # Botões
        frame_botoes = tk.Frame(janela_cred)
        frame_botoes.pack(pady=10)
        
        def confirmar():
            if not usuario_var.get() or not senha_var.get():
                messagebox.showerror("Erro", "Preencha usuário e senha!", parent=janela_cred)
                return
            resultado['confirmado'] = True
            resultado['usuario'] = usuario_var.get()
            resultado['senha'] = senha_var.get()
            janela_cred.destroy()
        
        def cancelar():
            resultado['confirmado'] = False
            janela_cred.destroy()
        
        tk.Button(
            frame_botoes,
            text="Confirmar",
            command=confirmar,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
            width=12
        ).pack(side="left", padx=5)
        
        tk.Button(
            frame_botoes,
            text="Cancelar",
            command=cancelar,
            bg="#F44336",
            fg="white",
            font=("Arial", 10, "bold"),
            width=12
        ).pack(side="left", padx=5)
        
        # Focar no campo de usuário
        entry_usuario.focus()
        
        # Aguardar fechamento
        janela_cred.wait_window()
        
        if resultado['confirmado']:
            return {
                'usuario': resultado['usuario'],
                'senha': resultado['senha']
            }
        return None
    
    def iniciar_preenchimento_automatico(self):
        """
        Inicia o processo de preenchimento automático do GEDUC
        """
        # Validar seleções
        selecoes = self.validar_selecoes_interface()
        if not selecoes:
            return
        
        # Solicitar credenciais
        credenciais = self.solicitar_credenciais()
        if not credenciais:
            return
        
        # Confirmar ação
        msg = (
            f"Preencher automaticamente do GEDUC?\n\n"
            f"Turma: {selecoes['turma']}\n"
            f"Disciplina: {selecoes['disciplina']}\n"
            f"Bimestre: {selecoes['bimestre']}º\n\n"
            f"Este processo irá:\n"
            f"1. Abrir navegador e fazer login no GEDUC\n"
            f"2. Navegar até a página de notas\n"
            f"3. Extrair as notas\n"
            f"4. Preencher automaticamente esta interface\n\n"
            f"Continuar?"
        )
        
        if not messagebox.askyesno("Confirmar", msg):
            return
        
        # Iniciar em thread separada
        self.thread_preenchimento = threading.Thread(
            target=self._executar_preenchimento,
            args=(credenciais, selecoes),
            daemon=True
        )
        self.thread_preenchimento.start()
    
    def _executar_preenchimento(self, credenciais, selecoes):
        """
        Executa o preenchimento automático (roda em thread separada)
        """
        try:
            # Criar instância da automação
            self.automacao = AutomacaoGEDUC(headless=False)
            
            # Iniciar navegador
            logger.info("\n→ Iniciando navegador...")
            if not self.automacao.iniciar_navegador():
                self.interface.janela.after(0, lambda: messagebox.showerror(
                    "Erro", "Falha ao iniciar navegador!"
                ))
                return
            
            # Fazer login
            logger.info("→ Fazendo login no GEDUC...")
            if not self.automacao.fazer_login(
                credenciais['usuario'],
                credenciais['senha'],
                timeout_recaptcha=120
            ):
                self.interface.janela.after(0, lambda: messagebox.showerror(
                    "Erro", "Falha no login! Verifique suas credenciais."
                ))
                return
            
            # Acessar registro de notas
            logger.info("→ Acessando registro de notas...")
            if not self.automacao.acessar_registro_notas():
                self.interface.janela.after(0, lambda: messagebox.showerror(
                    "Erro", "Falha ao acessar página de registro de notas!"
                ))
                return
            
            # Navegar até turma/disciplina/bimestre
            logger.info(f"→ Selecionando turma, disciplina e bimestre...")
            sucesso = self._navegar_geduc(selecoes)
            
            if not sucesso:
                self.interface.janela.after(0, lambda: messagebox.showerror(
                    "Erro", "Falha ao navegar no GEDUC!"
                ))
                return
            
            # Criar preenchedor automático
            preenchedor = criar_preenchimento_automatico(
                self.automacao.driver,
                self.interface
            )
            
            # Processar página (detectar período fechado e preencher)
            logger.info("→ Processando página de notas...")
            sucesso = preenchedor.processar_pagina_notas()
            
            if sucesso:
                logger.info("✓ Preenchimento concluído com sucesso!")
            
        except Exception as e:
            logger.error(f"✗ Erro: {e}")
            import traceback
            traceback.print_exc()
            self.interface.janela.after(0, lambda: messagebox.showerror(
                "Erro", f"Erro durante preenchimento:\n{str(e)}"
            ))
        
        finally:
            # Fechar navegador após 5 segundos
            if self.automacao:
                logger.info("\n→ Fechando navegador em 5 segundos...")
                import time
                time.sleep(5)
                self.automacao.fechar()
    
    def _navegar_geduc(self, selecoes):
        """
        Navega no GEDUC até a turma/disciplina/bimestre corretos
        
        Returns:
            True se sucesso, False se falha
        """
        try:
            import time
            
            # Verificar automação
            if self.automacao is None:
                logger.info("✗ Automação do GEDUC não inicializada")
                return False

            # Usar variável local tipada para acalmar o analisador estático
            automacao = cast(AutomacaoGEDUC, self.automacao)

            # Obter turmas disponíveis
            turmas = automacao.obter_opcoes_select('IDTURMA')
            
            logger.info(f"\n→ Procurando turma no GEDUC:")
            logger.info(f"  Série: {selecoes['serie']}")
            logger.info(f"  Turno: {selecoes['turno']}")
            logger.info(f"  Turma: {selecoes['turma']}")
            logger.info(f"  Nome completo para busca: {selecoes['nome_completo_geduc']}")
            logger.info(f"  Ordem: {{SÉRIE}} + {{TURNO}} + {{TURMA}}")
            
            logger.info(f"\n  Turmas disponíveis no GEDUC:")
            for t in turmas[:10]:  # Mostrar primeiras 10
                logger.info(f"    • {t['text']}")
            if len(turmas) > 10:
                logger.info(f"    ... e mais {len(turmas) - 10} turmas")
            
            # Normalizar busca
            def normalizar_para_busca(texto):
                """Remove acentos, símbolos, espaços extras e converte para maiúsculas"""
                import unicodedata
                import re
                
                # Remover acentuação
                texto = ''.join(c for c in unicodedata.normalize('NFD', texto) 
                               if unicodedata.category(c) != 'Mn')
                
                # Remover símbolos especiais como º, ª, etc
                texto = texto.replace('º', '').replace('ª', '')
                
                # Converter para maiúsculas e remover espaços extras
                texto = ' '.join(texto.upper().split())
                
                return texto
            
            # Preparar busca usando nome completo (série + turno + turma)
            nome_completo_norm = normalizar_para_busca(selecoes['nome_completo_geduc'])
            
            logger.info(f"\n  Valor normalizado para busca: '{nome_completo_norm}'")
            
            # Procurar turma correspondente
            turma_id = None
            turma_encontrada = None
            
            logger.info(f"\n  Comparando com cada turma:")
            
            for turma in turmas:
                turma_text = turma['text'].strip()
                turma_text_norm = normalizar_para_busca(turma_text)
                
                # Debug: mostrar cada comparação
                logger.info(f"    • '{turma_text}' → normalizado: '{turma_text_norm}'")
                
                # MÉTODO 1: Comparação EXATA
                if turma_text_norm == nome_completo_norm:
                    turma_id = turma['value']
                    turma_encontrada = turma_text
                    logger.info(f"      ✓✓ MATCH EXATO!")
                    break
                
                # MÉTODO 2: Tentar diferentes formatos com hífen
                # GEDUC usa formatos como: "7 ANO-VESP", "6 ANO-VESP - A", etc.
                # Nossa busca pode ser: "7 ANO VESP" ou "6 ANO VESP A"
                
                partes_busca = nome_completo_norm.split()
                
                if len(partes_busca) >= 2:
                    formatos_busca = []
                    
                    if len(partes_busca) == 3:
                        # Caso 1: "7 ANO VESP" → buscar "7 ANO-VESP"
                        formatos_busca.append(' '.join(partes_busca[:-1]) + '-' + partes_busca[-1])
                        formatos_busca.append(' '.join(partes_busca[:-1]) + ' - ' + partes_busca[-1])
                    
                    elif len(partes_busca) == 4:
                        # Caso 2: "6 ANO VESP A" → buscar "6 ANO-VESP - A"
                        # Formato: {SÉRIE ANO}-{TURNO} - {TURMA}
                        formatos_busca.append(f"{partes_busca[0]} {partes_busca[1]}-{partes_busca[2]} - {partes_busca[3]}")
                        # Também tentar sem espaço no hífen: "6 ANO-VESP-A"
                        formatos_busca.append(f"{partes_busca[0]} {partes_busca[1]}-{partes_busca[2]}-{partes_busca[3]}")
                    
                    for formato in formatos_busca:
                        if turma_text_norm == formato:
                            turma_id = turma['value']
                            turma_encontrada = turma_text
                            logger.info(f"      ✓✓ MATCH com formato '{formato}'!")
                            break
                
                if turma_id:
                    break
                
                # MÉTODO 3: Verificar se turma COMEÇA com o nome completo
                if turma_text_norm.startswith(nome_completo_norm):
                    turma_id = turma['value']
                    turma_encontrada = turma_text
                    logger.info(f"      ✓ MATCH: começa com '{nome_completo_norm}'")
                    break
            
            if not turma_id:
                logger.info(f"\n✗ Turma não encontrada no GEDUC")
                logger.info(f"  Série: '{selecoes['serie']}'")
                logger.info(f"  Turno: '{selecoes['turno']}'")
                logger.info(f"  Turma: '{selecoes['turma']}'")
                logger.info(f"  Nome completo buscado: '{selecoes['nome_completo_geduc']}' (normalizado: '{nome_completo_norm}')")
                logger.info(f"  Turma completa da interface: {selecoes.get('turma_completa', 'N/A')}")
                logger.info(f"\n  💡 DICA: Compare com as turmas disponíveis acima")
                logger.info(f"  Ordem GEDUC: {{SÉRIE}} + {{TURNO}} + {{TURMA}}")
                return False
            
            # Selecionar turma
            logger.info(f"\n✓ Turma encontrada: {turma_encontrada}")
            automacao.selecionar_opcao('IDTURMA', turma_id)
            time.sleep(1)
            
            # Obter disciplinas disponíveis
            disciplinas = automacao.obter_opcoes_select('IDTURMASDISP')
            
            # Procurar disciplina correspondente
            disciplina_id = None
            for disciplina in disciplinas:
                if selecoes['disciplina'] in disciplina['text']:
                    disciplina_id = disciplina['value']
                    break
            
            if not disciplina_id:
                logger.info(f"✗ Disciplina não encontrada no GEDUC: {selecoes['disciplina']}")
                return False
            
            # Selecionar disciplina
            logger.info(f"  → Selecionando disciplina: {selecoes['disciplina']}")
            automacao.selecionar_opcao('IDTURMASDISP', disciplina_id)
            time.sleep(1)
            
            # Selecionar bimestre
            logger.info(f"  → Selecionando bimestre: {selecoes['bimestre']}º")
            automacao.selecionar_bimestre(int(selecoes['bimestre']))
            time.sleep(1)
            
            # Clicar em exibir alunos
            logger.info("  → Carregando alunos...")
            automacao.clicar_exibir_alunos()
            time.sleep(2)
            
            logger.info("✓ Navegação concluída")
            return True
            
        except Exception as e:
            logger.error(f"✗ Erro ao navegar no GEDUC: {e}")
            import traceback
            traceback.print_exc()
            return False


def adicionar_preenchimento_automatico_na_interface(interface_notas):
    """
    Função auxiliar para adicionar o preenchimento automático
    em uma interface existente
    
    Args:
        interface_notas: Instância da InterfaceCadastroEdicaoNotas
    
    Returns:
        Instância do IntegradorPreenchimentoAutomatico
    """
    integrador = IntegradorPreenchimentoAutomatico(interface_notas)
    integrador.adicionar_botao_preenchimento()
    return integrador