import schedule
import time
import datetime
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
import json
import os

# ============================================
# CONFIGURAÇÕES
# ============================================
usuario = '2965'
senha = '1234'

LATITUDE = -5.5292
LONGITUDE = -47.4916

TEMPO_ALMOCO_MINUTOS = 60
CARGA_HORARIA_DIARIA = 8  # horas

URL_BASE = 'https://centraldofuncionario.com.br/50911'
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
        """
        Calcula o horário de saída para completar 8 horas
        Retorna: (horario_saida, info_calculo)
        """
        try:
            agora = datetime.datetime.now()
            
            entrada = datetime.datetime.strptime(pontos_registrados[0], '%H:%M')
            saida_almoco = datetime.datetime.strptime(pontos_registrados[1], '%H:%M')
            retorno_almoco = datetime.datetime.strptime(pontos_registrados[2], '%H:%M')
            
            entrada_hoje = datetime.datetime.combine(agora.date(), entrada.time())
            saida_almoco_hoje = datetime.datetime.combine(agora.date(), saida_almoco.time())
            retorno_almoco_hoje = datetime.datetime.combine(agora.date(), retorno_almoco.time())
            
            # Horas trabalhadas na manhã
            horas_manha = (saida_almoco_hoje - entrada_hoje).total_seconds() / 3600
            
            # Horas que faltam para completar 8h
            horas_faltam_tarde = CARGA_HORARIA_DIARIA - horas_manha
            
            # Horário de saída = retorno + horas que faltam
            horario_saida = retorno_almoco_hoje + datetime.timedelta(hours=horas_faltam_tarde)
            
            info = {
                'entrada': pontos_registrados[0],
                'saida_almoco': pontos_registrados[1],
                'retorno_almoco': pontos_registrados[2],
                'horas_manha': horas_manha,
                'horas_faltam_tarde': horas_faltam_tarde,
                'horario_saida': horario_saida.strftime('%H:%M')
            }
            
            logging.info(f"=== CÁLCULO DE SAÍDA ===")
            logging.info(f"Entrada: {info['entrada']}")
            logging.info(f"Saída almoço: {info['saida_almoco']}")
            logging.info(f"Retorno almoço: {info['retorno_almoco']}")
            logging.info(f"Horas manhã: {horas_manha:.2f}h")
            logging.info(f"Horas faltam (tarde): {horas_faltam_tarde:.2f}h")
            logging.info(f">>> Saída calculada: {info['horario_saida']}")
            logging.info(f"========================")
            
            return horario_saida, info
            
        except Exception as e:
            logging.error(f"Erro ao calcular horário de saída: {e}")
            # Fallback: 18:00
            return datetime.datetime.combine(datetime.date.today(), datetime.time(18, 0)), None

    def determinar_ponto_necessario(hora_atual, pontos_registrados):
        """LÓGICA INTELIGENTE - compensa atraso na saída"""
        agora = datetime.datetime.now()
        hora = int(hora_atual.split(':')[0])
        qtd_pontos = len(pontos_registrados)
        
        logging.info(f"Análise: {hora_atual}, {qtd_pontos} ponto(s)")
        
        # ENTRADA (08:00 - 11:59): Se não tem nenhum ponto
        if 8 <= hora <= 11 and qtd_pontos == 0:
            return True, "entrada_manha"
        
        # SAÍDA ALMOÇO (12:00 - 12:59): Se tem 1 ponto
        if hora == 12 and qtd_pontos == 1:
            return True, "saida_almoco"
        
        # RETORNO ALMOÇO: Se tem 2 pontos, verificar se passou tempo de almoço
        if qtd_pontos == 2:
            try:
                saida_almoco_str = pontos_registrados[1]
                saida_almoco = datetime.datetime.strptime(saida_almoco_str, '%H:%M')
                saida_almoco_hoje = datetime.datetime.combine(agora.date(), saida_almoco.time())
                
                tempo_almoco = (agora - saida_almoco_hoje).total_seconds() / 60
                
                logging.info(f"Saída almoço: {saida_almoco_str} | Tempo de almoço: {tempo_almoco:.0f} min")
                
                if tempo_almoco >= TEMPO_ALMOCO_MINUTOS:
                    return True, "retorno_almoco"
                else:
                    minutos_restantes = TEMPO_ALMOCO_MINUTOS - tempo_almoco
                    logging.info(f"Aguardando almoço... Faltam {minutos_restantes:.0f} min")
                    return False, None
            except Exception as e:
                logging.warning(f"Erro ao calcular tempo de almoço: {e}")
                if 13 <= hora <= 17:
                    return True, "retorno_almoco"
        
        # SAÍDA: Se tem 3 pontos, calcular horário correto para completar 8h
        if qtd_pontos == 3:
            horario_saida, info = calcular_horario_saida(pontos_registrados)
            
            # Verificar se já chegou ou passou o horário de saída
            if agora >= horario_saida:
                return True, "saida_tarde"
            else:
                minutos_faltam = (horario_saida - agora).total_seconds() / 60
                logging.info(f"Aguardando horário de saída... Faltam {minutos_faltam:.0f} min para {horario_saida.strftime('%H:%M')}")
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
                
                # Mostrar previsões
                if len(pontos) == 2:
                    try:
                        agora = datetime.datetime.now()
                        saida_almoco = datetime.datetime.strptime(pontos[1], '%H:%M')
                        saida_almoco_hoje = datetime.datetime.combine(agora.date(), saida_almoco.time())
                        retorno_previsto = saida_almoco_hoje + datetime.timedelta(minutes=TEMPO_ALMOCO_MINUTOS)
                        print(f"Retorno previsto: {retorno_previsto.strftime('%H:%M')}")
                    except:
                        pass
                
                if len(pontos) == 3:
                    horario_saida, info = calcular_horario_saida(pontos)
                    print(f"Saída prevista: {horario_saida.strftime('%H:%M')} (para completar {CARGA_HORARIA_DIARIA}h)")
                
                driver.quit()
            except Exception as e:
                print(f"Erro: {e}")
            return
    
    agendar_tarefas()

if __name__ == '__main__':
    main()
