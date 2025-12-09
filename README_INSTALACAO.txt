================================================================================
          SISTEMA DE GESTÃO ESCOLAR - GUIA DE INSTALAÇÃO
================================================================================

REQUISITOS DO SISTEMA:
----------------------
- Windows 7 ou superior (64-bit recomendado)
- MySQL Server 5.7 ou superior
- 4 GB de RAM (mínimo)
- 500 MB de espaço em disco

INSTALAÇÃO AUTOMÁTICA:
---------------------
O instalador inclui um Assistente de Configuração que irá:
  ✓ Verificar se MySQL está instalado
  ✓ Ajudar a baixar e instalar MySQL (se necessário)
  ✓ Criar banco de dados automaticamente
  ✓ Configurar usuário e permissões
  ✓ Configurar integração com Google Drive (opcional)

NOTA: Se MySQL não estiver instalado, o assistente irá:
  • Detectar automaticamente a ausência do MySQL
  • Oferecer opções de download (MySQL Community ou XAMPP)
  • Guiá-lo pelo processo de instalação
  • Após instalar MySQL, basta reiniciar o assistente

CONFIGURAÇÃO MANUAL (AVANÇADO):
-------------------------------
Se preferir configurar manualmente:

1. Instale MySQL Server 5.7+ manualmente
2. Acesse: C:\Program Files\Sistema de Gestão Escolar
3. Edite o arquivo .env:
   
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=seu_usuario
   DB_PASSWORD=sua_senha
   DB_NAME=gestao_escolar
   ESCOLA_ID=1
   ESCOLA_NOME=Nome da Sua Escola
   GESTAO_TEST_MODE=False

INTEGRAÇÃO GOOGLE DRIVE:
------------------------
O assistente permite configurar Google Drive durante a instalação:
  • Selecione o arquivo credentials.json quando solicitado
  • Na primeira execução do sistema, autorize o acesso
  • Ou configure manualmente depois copiando credentials.json para a pasta de instalação

PRIMEIRA EXECUÇÃO:
-----------------
1. Execute o Sistema de Gestão Escolar pelo menu Iniciar ou ícone da área de trabalho
2. O sistema criará as tabelas necessárias no banco de dados automaticamente
3. Configure os perfis de usuários (se habilitado)

SOLUÇÃO DE PROBLEMAS:
--------------------
- Se o programa não iniciar, verifique:
  • MySQL Server está rodando
  • Configurações do .env estão corretas
  • Arquivo de log em: C:\Program Files\Sistema de Gestão Escolar\logs

- Para suporte técnico:
  • Consulte a documentação completa no GitHub
  • Abra uma issue em: https://github.com/doncisio/sistema-gestao-escolar/issues

BACKUP E SEGURANÇA:
------------------
- O sistema realiza backups automáticos (configurável)
- Backups são salvos em: C:\Program Files\Sistema de Gestão Escolar\backup
- Recomenda-se backup regular dos dados em local externo

DESINSTALAÇÃO:
-------------
Use o desinstalador pelo Painel de Controle do Windows ou pelo menu Iniciar.

================================================================================
Copyright (c) 2025 - Sistema de Gestão Escolar
================================================================================
