 # Plano de Implantação do Sistema de Avaliação (Integração de Notas)

 Data: 13/12/2025

 Objetivo: avaliar a viabilidade técnica e organizacional para integrar o módulo de notas ao Banco de Questões, migrar professores que usam cadernetas físicas e descrever os passos necessários para aceitação e implantação.

 ---

 ## 1. Resumo executivo

 O sistema atual já possui `avaliacoes` e uma interface `notas`, porém sem vínculo direto ao `banco_questoes`. É viável integrar correção e registro de notas, com esforço médio: modelagem de dados (DDL), serviços backend para respostas/correções, integração da UI e um programa de adoção (piloto + treinamento). Principais riscos: resistência de professores, necessidade de dispositivos/internet em algumas escolas, e qualidade dos dados migrados das cadernetas.

 ## 2. Requisitos mínimos técnicos
 - Servidor de aplicação com acesso ao banco (MySQL) e backups automáticos.
 - Tabelas para `avaliacoes_alunos` e `respostas_questoes` (DDL proposto abaixo).
 - Serviços backend: `RespostaService`, `AvaliacaoService` e `RelatorioService`.
 - Importador CSV/XLS para migrar dados das cadernetas físicas.
 - Interface de correção (UI) conectada à aba `notas`.
 - Autenticação e permissões (professor somente suas turmas; coordenador/administrador com mais privilégios).

 ## 3. DDL mínimo proposto (exemplo)

 ```sql
 CREATE TABLE avaliacoes_alunos (
   id INT AUTO_INCREMENT PRIMARY KEY,
   avaliacao_id INT NOT NULL,
   aluno_id INT NOT NULL,
   data_aplicacao DATETIME DEFAULT CURRENT_TIMESTAMP,
   nota_total DECIMAL(5,2) DEFAULT 0,
   status ENUM('pendente','corrigida','finalizada') DEFAULT 'pendente',
   created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
   updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
 );

 CREATE TABLE respostas_questoes (
   id INT AUTO_INCREMENT PRIMARY KEY,
   avaliacao_aluno_id INT NOT NULL,
   questao_id INT NOT NULL,
   alternativa_id INT NULL,
   resposta_texto TEXT NULL,
   pontuacao_obtida DECIMAL(5,2) DEFAULT 0,
   max_pontuacao DECIMAL(5,2) NOT NULL,
   corrigido_por INT NULL,
   corrigido_em DATETIME NULL,
   status ENUM('nao_corrigida','corrigida') DEFAULT 'nao_corrigida',
   comentario TEXT NULL,
   created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
   updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
 );
 ```

 ## 4. Fluxos de correção e registro de notas

 - Correção automática (objetivas): quando o professor registra uma resposta objetiva (alternativa_id), o `RespostaService` compara com o gabarito da questão e preenche `pontuacao_obtida` e `status='corrigida'`.
 - Correção manual (dissertativas): respostas de texto ficam com `status='nao_corrigida'` e entram na fila de correção do professor; o professor atribui `pontuacao_obtida`, adiciona comentário e marca como corrigida.
 - Atualização de nota total: soma das `pontuacao_obtida` por `avaliacao_aluno_id` e atualização de `avaliacoes_alunos.nota_total` e `status`.

 ## 5. Integração com a aba `notas` (UI)

 Passos técnicos:
 - Listar avaliações por turma/periodo na aba `notas`.
 - Ao selecionar uma avaliação, mostrar lista de alunos com coluna `status` e `nota_total`.
 - Ações: "Registrar Resposta" por aluno (formulário por questão), "Fila de Correção" (lista de respostas discursivas pendentes), "Auto-corrigir objetivas", "Importar notas (CSV/XLS)".
 - Painel de correção por questão: enunciado, resposta do aluno, campo número para pontuação, campo para comentário, salvar.

 ## 6. Processos organizacionais e aceitação pelos professores

 Fatores para aceitação:
 - Simplicidade e rapidez da interface para entrada de notas (reduzir cliques).
 - Possibilidade de continuar usando cadernetas inicialmente (dupla entrada durante transição).
 - Treinamento prático, vídeos curtos e suporte presencial nas primeiras turmas.
 - Piloto com 1-2 turmas voluntárias, com coleta de métricas e ajustes.
 - Importador de cadernetas para reduzir trabalho de entrada manual.

 Recomendações de implantação:
 1. Preparação: configurar infra, backups e criar templates de importação.
 2. Piloto de 4–6 semanas com 1 coordenador + 2 professores por disciplina.
 3. Reuniões semanais de feedback e ajustes rápidos na UI/fluxos.
 4. Treinamento amplo (sessões + material digital) antes do roll-out por série.
 5. Suporte inicial (SLA curto) e acompanhamento de adoção por métricas (tempo por lançamento, taxa de erro, % de uso).

 ## 7. Riscos e mitigação

 - Resistência cultural: mitigar com piloto, tutorias e co-autoria de professores no ajuste da UI.
 - Falta de dispositivos/internet: oferecer plan B (entrada em lote offline via CSV) e cronograma para uso em sala com dispositivos compartilhados.
 - Dados inconsistentes: validar importação e manter logs; permitir edição manual pós-importação.

 ## 8. Métricas de sucesso

 - % de professores usando sistema após 3 meses
 - Redução do tempo médio por avaliação registrada
 - Taxa de erros ao importar notas (meta < 2%)
 - Tempo médio até finalização da correção por avaliação

 ---

 ## Indagações a documentar / Perguntas para professores (a serem respondidas durante entrevistas/piloto)

 1. Como seriam feitas as correções das questões pelos professores?

 - Preferem corrigir por aluno (ficha por aluno) ou por questão (fila de correção)?
 - Quanto tempo, em média, levam para corrigir uma prova com X questões (mix objetiva/dissertativa)?
 - Há necessidade de comentários pedagógicos por questão que serão enviados ao aluno?
 - Precisam de um campo para justificar alteração de nota? Quem aprova revisão de nota?

 2. Como seriam inseridos no sistema os resultados de cada aluno?

 - Digitariam manualmente (por aluno) ou importariam planilhas preenchidas?
 - Existe um padrão de caderno/caderneta que possamos mapear para um template CSV/XLS?
 - Desejam que o sistema corrija automaticamente objetivas e mostre apenas discursivas para correção manual?
 - Precisam de impressão das respostas/boletins diretamente do sistema?

 ---

 ## Próximas ações sugeridas (curto prazo)

 1. ✅ **CONCLUÍDO:** DDL criado em `db/migrations/adicionar_tabelas_avaliacoes_respostas.sql`
 2. ✅ **CONCLUÍDO:** `RespostaService` implementado em `banco_questoes/resposta_service.py`
 3. 🔄 **EM ANDAMENTO:** Integração com `InterfaceCadastroEdicaoNotas.py` (ver `GUIA_INTEGRACAO_NOTAS_AVALIACOES.md`)
 4. ⏳ **PENDENTE:** Material de treinamento e template CSV/XLS
 5. ⏳ **PENDENTE:** Executar migração SQL no ambiente de teste
 6. ⏳ **PENDENTE:** Testes de integração (executar `testar_sistema_avaliacoes.py`)

 ---

 ## Arquivos criados nesta etapa

 ### Banco de dados
 - `db/migrations/adicionar_tabelas_avaliacoes_respostas.sql` - Migração completa com tabelas, views, procedures e triggers

 ### Backend
 - `banco_questoes/resposta_service.py` - Serviço completo para gerenciamento de respostas

 ### Documentação
 - `PLANO_IMPLANTACAO_AVALIACOES.md` - Este arquivo (análise de viabilidade)
 - `GUIA_INTEGRACAO_NOTAS_AVALIACOES.md` - Guia técnico de integração com interface de notas

 ### Testes
 - `testar_sistema_avaliacoes.py` - Script de validação da migração e serviços

 ---

 ## Como executar a migração

 ```powershell
 # 1. Fazer backup do banco atual
 mysqldump -u root -p redeescola > backup_pre_migracao_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql

 # 2. Executar migração
 mysql -u root -p redeescola < db/migrations/adicionar_tabelas_avaliacoes_respostas.sql

 # 3. Validar migração
 python testar_sistema_avaliacoes.py
 ```

 ---

 Arquivo gerado automaticamente por equipe técnica — pronto para revisão e para uso como checklist de implantação.
