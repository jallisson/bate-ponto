import schedule
import time
import datetime
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
import logging
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import json
import os

# Carregar variáveis do arquivo .env
load_dotenv()

# ============================================
# CONFIGURAÇÕES (carregadas do .env)
# ============================================
usuario = os.getenv('USUARIO')
senha = os.getenv('SENHA')
URL_BASE = os.getenv('URL_BASE', 'https://centraldofuncionario.com.br/50911')
LATITUDE = float(os.getenv('LATITUDE', -5.5292))
LONGITUDE = float(os.getenv('LONGITUDE', -47.4916))
TEMPO_ALMOCO_MINUTOS = int(os.getenv('TEMPO_ALMOCO_MINUTOS', 60))
CARGA_HORARIA_DIARIA = int(os.getenv('CARGA_HORARIA_DIARIA', 8))

# Variação aleatória em minutos (para parecer mais humano)
VARIACAO_ENTRADA = int(os.getenv('VARIACAO_ENTRADA', 10))        # 0-10 min
VARIACAO_SAIDA_ALMOCO = int(os.getenv('VARIACAO_SAIDA_ALMOCO', 5))  # 0-5 min
VARIACAO_RETORNO = int(os.getenv('VARIACAO_RETORNO', 10))        # 0-10 min
VARIACAO_SAIDA = int(os.getenv('VARIACAO_SAIDA', 10))            # 0-10 min

# Validar credenciais
if not usuario or not senha:
    raise ValueError("ERRO: Configure USUARIO e SENHA no arquivo .env")
# ============================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ponto_automatico.log"),
        logging.StreamHandler()
    ]
)

REGISTROS_FILE = "registros_ponto.json"
DELAY_FILE = "delay_hoje.json"

def main():
    logging.info('Programa iniciado')

    feriados = [
        '2025-01-01', '2025-03-03', '2025-03-04', '2025-03-05',
        '2025-04-17', '2025-04-18', '2025-04-21', '2025-05-01',
        '2025-06-19', '2025-06-20', '2025-09-07', '2025-10-12',
        '2025-11-02', '2025-11-15', '2025-12-25', '2026-01-01',
    ]

    if not os.path.exists(REGISTROS_FILE):
        with open(REGISTROS_FILE, 'w') as f:
            json.dump({}, f)

    def carregar_registros():
        try:
            with open(REGISTROS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}

    def salvar_registro(hora_tipo):
        registros = carregar_registros()
        hoje = datetime.date.today().strftime('%Y-%m-%d')
        if hoje not in registros:
            registros[hoje] = []
        hora_atual = datetime.datetime.now().strftime('%H:%M:%S')
        registros[hoje].append({"hora": hora_atual, "tipo": hora_tipo})
        with open(REGISTROS_FILE, 'w') as f:
            json.dump(registros, f, indent=2)

    def obter_delay_do_dia(tipo_ponto):
        """
        Gera ou recupera o delay aleatório do dia para cada tipo de ponto.
        O delay é fixo por dia para evitar que mude a cada verificação.
        """
        hoje = datetime.date.today().strftime('%Y-%m-%d')
        
        # Carregar delays salvos
        try:
            with open(DELAY_FILE, 'r') as f:
                delays = json.load(f)
        except:
            delays = {}
        
        # Se não é do dia de hoje, limpar e gerar novos
        if delays.get('data') != hoje:
            delays = {
                'data': hoje,
                'entrada_manha': random.randint(0, VARIACAO_ENTRADA),
                'saida_almoco': random.randint(0, VARIACAO_SAIDA_ALMOCO),
                'retorno_almoco': random.randint(0, VARIACAO_RETORNO),
                'saida_tarde': random.randint(0, VARIACAO_SAIDA)
            }
            with open(DELAY_FILE, 'w') as f:
                json.dump(delays, f, indent=2)
            logging.info(f"🎲 Delays gerados para hoje: entrada +{delays['entrada_manha']}min, " +
                        f"saída almoço +{delays['saida_almoco']}min, " +
                        f"retorno +{delays['retorno_almoco']}min, " +
                        f"saída +{delays['saida_tarde']}min")
        
        return delays.get(tipo_ponto, 0)

    def chrome_driver(headless=True):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--log-level=3")
        
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.geolocation": 1,
            "profile.default_content_settings.popups": 0,
            "profile.default_content_setting_values.notifications": 1
        })
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        logging.info("ChromeDriver iniciado")
        driver.implicitly_wait(10)
        driver.set_page_load_timeout(30)
        
        driver.execute_cdp_cmd("Emulation.setGeolocationOverride", {
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "accuracy": 100
        })
        logging.info(f"Geolocalização configurada: {LATITUDE}, {LONGITUDE}")
        
        return driver

    def verificar_pontos_site(driver):
        try:
            driver.get(f'{URL_BASE}/cartao-ponto')
            time.sleep(5)
            hoje = datetime.date.today().strftime('%d/%m')
            logging.info(f"Procurando registros para: {hoje}")
            elementos_data = driver.find_elements(By.XPATH, f"//div[contains(text(), '{hoje}')]")
            pontos_hoje = []
            for elem_data in elementos_data:
                try:
                    elemento_pai = elem_data.find_element(By.XPATH, "./..")
                    elementos_hora = elemento_pai.find_elements(By.XPATH, ".//div[contains(text(), ':')]")
                    for elem_hora in elementos_hora:
                        texto_hora = elem_hora.text.strip()
                        if texto_hora and ":" in texto_hora and texto_hora != hoje:
                            pontos_hoje.append(texto_hora)
                    if pontos_hoje:
                        break
                except:
                    pass
            logging.info(f"Pontos encontrados: {pontos_hoje}")
            return pontos_hoje
        except Exception as e:
            logging.error(f"Erro ao verificar pontos: {e}")
            return []

    def calcular_horario_saida(pontos_registrados):
        """Calcula o horário de saída para completar a carga horária"""
        try:
            agora = datetime.datetime.now()
            
            entrada = datetime.datetime.strptime(pontos_registrados[0], '%H:%M')
            saida_almoco = datetime.datetime.strptime(pontos_registrados[1], '%H:%M')
            retorno_almoco = datetime.datetime.strptime(pontos_registrados[2], '%H:%M')
            
            entrada_hoje = datetime.datetime.combine(agora.date(), entrada.time())
            saida_almoco_hoje = datetime.datetime.combine(agora.date(), saida_almoco.time())
            retorno_almoco_hoje = datetime.datetime.combine(agora.date(), retorno_almoco.time())
            
            horas_manha = (saida_almoco_hoje - entrada_hoje).total_seconds() / 3600
            horas_faltam_tarde = CARGA_HORARIA_DIARIA - horas_manha
            horario_saida = retorno_almoco_hoje + datetime.timedelta(hours=horas_faltam_tarde)
            
            # Adicionar variação aleatória do dia
            delay_saida = obter_delay_do_dia('saida_tarde')
            horario_saida_com_variacao = horario_saida + datetime.timedelta(minutes=delay_saida)
            
            logging.info(f"=== CÁLCULO DE SAÍDA ===")
            logging.info(f"Entrada: {pontos_registrados[0]}")
            logging.info(f"Saída almoço: {pontos_registrados[1]}")
            logging.info(f"Retorno almoço: {pontos_registrados[2]}")
            logging.info(f"Horas manhã: {horas_manha:.2f}h")
            logging.info(f"Horas faltam (tarde): {horas_faltam_tarde:.2f}h")
            logging.info(f"Saída base: {horario_saida.strftime('%H:%M')}")
            logging.info(f"🎲 Variação: +{delay_saida} min")
            logging.info(f">>> Saída final: {horario_saida_com_variacao.strftime('%H:%M')}")
            logging.info(f"========================")
            
            return horario_saida_com_variacao, {'horas_manha': horas_manha, 'delay': delay_saida}
            
        except Exception as e:
            logging.error(f"Erro ao calcular horário de saída: {e}")
            return datetime.datetime.combine(datetime.date.today(), datetime.time(18, 0)), None

    def determinar_ponto_necessario(hora_atual, pontos_registrados):
        """LÓGICA INTELIGENTE com variação aleatória"""
        agora = datetime.datetime.now()
        hora = int(hora_atual.split(':')[0])
        minuto = int(hora_atual.split(':')[1])
        qtd_pontos = len(pontos_registrados)
        
        logging.info(f"Análise: {hora_atual}, {qtd_pontos} ponto(s)")
        
        # ENTRADA (08:00 - 11:59): Se não tem nenhum ponto
        if 8 <= hora <= 11 and qtd_pontos == 0:
            delay = obter_delay_do_dia('entrada_manha')
            # Verificar se já passou do horário base + delay
            horario_bater = datetime.datetime.combine(agora.date(), datetime.time(9, 0)) + datetime.timedelta(minutes=delay)
            if agora >= horario_bater:
                logging.info(f"🎲 Entrada com variação: +{delay} min (horário: {horario_bater.strftime('%H:%M')})")
                return True, "entrada_manha"
            else:
                minutos_faltam = (horario_bater - agora).total_seconds() / 60
                logging.info(f"⏳ Aguardando variação da entrada... Faltam {minutos_faltam:.0f} min para {horario_bater.strftime('%H:%M')}")
                return False, None
        
        # SAÍDA ALMOÇO (12:00 - 12:59): Se tem 1 ponto
        if hora == 12 and qtd_pontos == 1:
            delay = obter_delay_do_dia('saida_almoco')
            horario_bater = datetime.datetime.combine(agora.date(), datetime.time(12, 0)) + datetime.timedelta(minutes=delay)
            if agora >= horario_bater:
                logging.info(f"🎲 Saída almoço com variação: +{delay} min (horário: {horario_bater.strftime('%H:%M')})")
                return True, "saida_almoco"
            else:
                minutos_faltam = (horario_bater - agora).total_seconds() / 60
                logging.info(f"⏳ Aguardando variação da saída almoço... Faltam {minutos_faltam:.0f} min para {horario_bater.strftime('%H:%M')}")
                return False, None
        
        # RETORNO ALMOÇO: Se tem 2 pontos
        if qtd_pontos == 2:
            try:
                saida_almoco_str = pontos_registrados[1]
                saida_almoco = datetime.datetime.strptime(saida_almoco_str, '%H:%M')
                saida_almoco_hoje = datetime.datetime.combine(agora.date(), saida_almoco.time())
                
                # Tempo de almoço + variação
                delay = obter_delay_do_dia('retorno_almoco')
                tempo_almoco_total = TEMPO_ALMOCO_MINUTOS + delay
                
                tempo_almoco = (agora - saida_almoco_hoje).total_seconds() / 60
                
                logging.info(f"Saída almoço: {saida_almoco_str} | Tempo de almoço: {tempo_almoco:.0f} min | 🎲 Almoço total: {tempo_almoco_total} min")
                
                if tempo_almoco >= tempo_almoco_total:
                    logging.info(f"🎲 Retorno com variação: +{delay} min de almoço extra")
                    return True, "retorno_almoco"
                else:
                    minutos_restantes = tempo_almoco_total - tempo_almoco
                    logging.info(f"⏳ Aguardando almoço... Faltam {minutos_restantes:.0f} min")
                    return False, None
            except Exception as e:
                logging.warning(f"Erro ao calcular tempo de almoço: {e}")
                if 13 <= hora <= 17:
                    return True, "retorno_almoco"
        
        # SAÍDA: Se tem 3 pontos
        if qtd_pontos == 3:
            horario_saida, info = calcular_horario_saida(pontos_registrados)
            
            if agora >= horario_saida:
                return True, "saida_tarde"
            else:
                minutos_faltam = (horario_saida - agora).total_seconds() / 60
                logging.info(f"⏳ Aguardando saída... Faltam {minutos_faltam:.0f} min para {horario_saida.strftime('%H:%M')}")
                return False, None
        
        # Casos de atraso
        if hora >= 13 and qtd_pontos == 1:
            logging.warning("ATENÇÃO: Falta saída do almoço!")
            return True, "saida_almoco"
        
        if hora >= 18 and qtd_pontos == 2:
            logging.warning("ATENÇÃO: Falta retorno do almoço!")
            return True, "retorno_almoco"
        
        return False, None

    def registrar_ponto(driver, pontos_hoje, tipo_ponto):
        try:
            driver.get(f'{URL_BASE}/incluir-ponto')
            time.sleep(8)
            
            driver.save_screenshot(f"incluir_ponto_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            
            driver.execute_cdp_cmd("Emulation.setGeolocationOverride", {
                "latitude": LATITUDE,
                "longitude": LONGITUDE,
                "accuracy": 100
            })
            
            time.sleep(3)
            
            logging.info("Procurando botão de incluir ponto...")
            
            try:
                driver.execute_script("""
                    var btn = document.getElementById('localizacao-incluir-ponto');
                    if (btn) {
                        btn.click();
                    }
                """)
                logging.info("Clique via JavaScript executado")
            except Exception as e:
                logging.warning(f"Erro no clique JS: {e}")
                botao = driver.find_element(By.ID, 'localizacao-incluir-ponto')
                botao.click()
                logging.info("Clique normal executado")
            
            logging.info("Aguardando processamento...")
            time.sleep(25)
            
            driver.save_screenshot(f"apos_clique_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            
            confirmado = False
            
            try:
                sucesso = driver.find_element(By.XPATH, "//*[contains(text(), 'sucesso') or contains(text(), 'Sucesso') or contains(text(), 'registrado')]")
                if sucesso:
                    logging.info(f"✓ Mensagem de sucesso: {sucesso.text}")
                    confirmado = True
            except:
                pass
            
            if not confirmado:
                try:
                    hoje_fmt = datetime.date.today().strftime('%m/%d')
                    registros = driver.find_elements(By.XPATH, f"//div[contains(text(), '{hoje_fmt}')]")
                    hora_agora = datetime.datetime.now().strftime('%H:%M')
                    for r in registros:
                        if hora_agora[:2] in r.text:
                            logging.info(f"✓ Novo registro encontrado: {r.text}")
                            confirmado = True
                            break
                except:
                    pass
            
            if not confirmado:
                logging.info("Verificando por contagem...")
                time.sleep(10)
                pontos_apos = verificar_pontos_site(driver)
                if len(pontos_apos) > len(pontos_hoje):
                    logging.info(f"✓ Confirmado: {len(pontos_hoje)} -> {len(pontos_apos)} pontos")
                    confirmado = True
            
            if confirmado:
                salvar_registro(tipo_ponto)
                logging.info(f"✓ Ponto {tipo_ponto} registrado!")
                return True
            else:
                logging.error("FALHA ao confirmar registro")
                driver.save_screenshot(f"falha_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                return False
                
        except Exception as e:
            logging.error(f"Erro ao registrar: {e}")
            driver.save_screenshot(f"erro_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            return False

    def verificar_e_bater_ponto():
        hoje = datetime.date.today().strftime('%Y-%m-%d')
        if hoje in feriados:
            logging.info(f"Feriado ({hoje})")
            return
        
        dia_semana = datetime.date.today().weekday()
        if dia_semana >= 5:
            logging.info("Fim de semana")
            return

        driver = None
        try:
            driver = chrome_driver(headless=True)
            driver.get(URL_BASE)
            driver.maximize_window()
            time.sleep(10)

            login_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="login-numero-folha"]'))
            )
            login_field.send_keys(usuario)
            senha_field = driver.find_element(By.XPATH, '//*[@id="login-senha"]')
            senha_field.send_keys(senha)
            
            try:
                enter_button = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[1]/div/div[3]/div[9]')
                enter_button.click()
            except:
                senha_field.send_keys(Keys.ENTER)

            time.sleep(5)
            logging.info('Login realizado')

            pontos_hoje = verificar_pontos_site(driver)
            hora_atual = datetime.datetime.now().strftime('%H:%M')
            deve_bater, tipo_ponto = determinar_ponto_necessario(hora_atual, pontos_hoje)
            
            logging.info(f"Hora: {hora_atual} | Pontos: {pontos_hoje} | Bater: {deve_bater} | Tipo: {tipo_ponto}")
            
            if deve_bater and tipo_ponto:
                logging.info(f">>> Registrando: {tipo_ponto}")
                sucesso = registrar_ponto(driver, pontos_hoje, tipo_ponto)
                if sucesso:
                    logging.info(f"✓ {tipo_ponto} OK!")
                else:
                    logging.error(f"✗ Falha em {tipo_ponto}")
            else:
                logging.info("Nenhum ponto pendente.")
            
        except Exception as e:
            logging.error(f"Erro: {e}")
        finally:
            if driver:
                time.sleep(3)
                driver.quit()
            logging.info("Finalizado.")

    def agendar_tarefas():
        schedule.every(5).minutes.do(verificar_e_bater_ponto)
        
        logging.info("=== PONTO AUTOMÁTICO ===")
        logging.info("Verificação a cada 5 min")
        logging.info(f"Tempo de almoço: {TEMPO_ALMOCO_MINUTOS} min")
        logging.info(f"Carga horária: {CARGA_HORARIA_DIARIA}h")
        logging.info("Compensação: NA SAÍDA")
        logging.info(f"🎲 Variações: entrada ±{VARIACAO_ENTRADA}min, saída almoço ±{VARIACAO_SAIDA_ALMOCO}min, retorno ±{VARIACAO_RETORNO}min, saída ±{VARIACAO_SAIDA}min")
        logging.info("========================")
        
        verificar_e_bater_ponto()
        
        while True:
            schedule.run_pending()
            time.sleep(30)

    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "agora":
            verificar_e_bater_ponto()
            return
        elif sys.argv[1] == "verificar":
            try:
                driver = chrome_driver(headless=True)
                driver.get(URL_BASE)
                time.sleep(10)
                
                login_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="login-numero-folha"]'))
                )
                login_field.send_keys(usuario)
                senha_field = driver.find_element(By.XPATH, '//*[@id="login-senha"]')
                senha_field.send_keys(senha)
                senha_field.send_keys(Keys.ENTER)
                time.sleep(5)
                
                pontos = verificar_pontos_site(driver)
                hora_atual = datetime.datetime.now().strftime('%H:%M')
                deve_bater, tipo_ponto = determinar_ponto_necessario(hora_atual, pontos)
                
                print("=== VERIFICAÇÃO ===")
                print(f"Data: {datetime.date.today().strftime('%d/%m/%Y')}")
                print(f"Hora: {hora_atual}")
                print(f"Pontos: {pontos}")
                print(f"Qtd: {len(pontos)}")
                print(f"Bater agora: {'SIM' if deve_bater else 'NÃO'}")
                print(f"Próximo: {tipo_ponto if tipo_ponto else 'Aguardando...'}")
                
                # Mostrar delays do dia
                print(f"\n🎲 Variações de hoje:")
                print(f"   Entrada: +{obter_delay_do_dia('entrada_manha')} min")
                print(f"   Saída almoço: +{obter_delay_do_dia('saida_almoco')} min")
                print(f"   Retorno: +{obter_delay_do_dia('retorno_almoco')} min")
                print(f"   Saída: +{obter_delay_do_dia('saida_tarde')} min")
                
                if len(pontos) == 2:
                    try:
                        agora = datetime.datetime.now()
                        saida_almoco = datetime.datetime.strptime(pontos[1], '%H:%M')
                        saida_almoco_hoje = datetime.datetime.combine(agora.date(), saida_almoco.time())
                        delay_retorno = obter_delay_do_dia('retorno_almoco')
                        retorno_previsto = saida_almoco_hoje + datetime.timedelta(minutes=TEMPO_ALMOCO_MINUTOS + delay_retorno)
                        print(f"\nRetorno previsto: {retorno_previsto.strftime('%H:%M')} (almoço + {delay_retorno}min variação)")
                    except:
                        pass
                
                if len(pontos) == 3:
                    horario_saida, info = calcular_horario_saida(pontos)
                    print(f"\nSaída prevista: {horario_saida.strftime('%H:%M')} (para completar {CARGA_HORARIA_DIARIA}h)")
                
                driver.quit()
            except Exception as e:
                print(f"Erro: {e}")
            return
    
    agendar_tarefas()

if __name__ == '__main__':
    main()
