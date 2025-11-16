import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from config_logs import get_logger

logger = get_logger(__name__)

# Configurar o WebDriver
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

# Abrir a página de login
driver.get('https://www.cartaoestudantilslz.com.br/login')

# Localizar os campos de entrada
username_input = driver.find_element(By.NAME, 'email')
password_input = driver.find_element(By.NAME, 'password')

# Obter as credenciais das variáveis de ambiente
username = os.getenv('alzirdias.lima@gmail.com')
password = os.getenv('nadir123')

# Verificar se as variáveis não são None antes de enviar
if username is None or password is None:
    logger.error("Erro: As variáveis de ambiente não estão definidas.")
else:
    username_input.send_keys(username)
    password_input.send_keys(password)

# Pausar para resolver o captcha manualmente
input("Por favor, resolva o captcha manualmente e pressione Enter para continuar...")

# Submeter o formulário
password_input.send_keys(Keys.RETURN)

# Fechar o navegador após algum tempo
import time
time.sleep(5)
driver.quit()