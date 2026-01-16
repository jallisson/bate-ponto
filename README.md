# 🕐 Bate Ponto - Ponto Automático

Script Python para registro automático de ponto no sistema [Central do Funcionário (Secullum)](https://centraldofuncionario.com.br).

## ✨ Funcionalidades

- ✅ Registro automático dos 4 pontos diários
- ✅ **Compensação inteligente de horas** - calcula a saída para completar 8h
- ✅ **Variação aleatória nos horários** - simula comportamento humano 🎲
- ✅ Respeita 1 hora de almoço (configurável)
- ✅ Verificação a cada 5 minutos
- ✅ Ignora feriados e fins de semana
- ✅ Logs detalhados de todas as operações
- ✅ Geolocalização configurável
- ✅ **Inicia automaticamente com o Windows** (roda em background)

## 🎲 Variação Aleatória

Para parecer mais natural, o sistema adiciona uma variação aleatória em cada ponto:

| Ponto | Variação | Exemplo |
|-------|----------|---------|
| Entrada | +0 a 10 min | 09:00 → 09:07 |
| Saída almoço | +0 a 5 min | 12:00 → 12:03 |
| Retorno | +0 a 10 min | 13:00 → 13:08 |
| Saída | +0 a 10 min | 18:20 → 18:26 |

> 💡 Os valores são sorteados **uma vez por dia** e permanecem fixos até o dia seguinte.

## 🧠 Lógica Inteligente de Compensação

O script calcula automaticamente os horários baseado na sua jornada:

| Situação | Exemplo | Ação |
|----------|---------|------|
| Entrada normal | 09:00 | Saída às 18:00 |
| Entrada atrasada | 09:20 | Saída às 18:20 (compensa 20min) |
| Entrada adiantada | 08:45 | Saída às 17:45 (sai 15min antes) |

### Exemplo de cálculo:
```
Entrada: 09:07 (com variação +7min)
Saída almoço: 12:03
Horas manhã: 2h56min

Retorno almoço: 13:08 (almoço de 1h05)
Horas que faltam: 8h - 2h56min = 5h04min

Saída base: 13:08 + 5h04min = 18:12
Variação: +4min
>>> Saída final: 18:16
```

---

# 🚀 Instalação

## Parte 1: Configurar o WSL

### 1.1 Abrir o WSL (Ubuntu)
```bash
wsl
```

### 1.2 Atualizar o sistema
```bash
sudo apt update && sudo apt upgrade -y
```

### 1.3 Instalar dependências do sistema
```bash
sudo apt install -y python3 python3-venv python3-full wget curl unzip git
```

### 1.4 Instalar o Google Chrome
```bash
cd ~
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt --fix-broken install -y
rm google-chrome-stable_current_amd64.deb
```

Verificar instalação:
```bash
google-chrome --version
```

---

## Parte 2: Configurar o Script

### 2.1 Clonar o repositório
```bash
cd ~
git clone https://github.com/jallisson/bate-ponto.git ponto
cd ~/ponto
```

### 2.2 Criar ambiente virtual Python
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2.3 Instalar bibliotecas Python
```bash
pip install --upgrade pip
pip install selenium schedule webdriver-manager python-dotenv
```

### 2.4 Configurar credenciais (arquivo .env)

Copie o arquivo de exemplo:
```bash
cp .env.example .env
```

Edite com seus dados:
```bash
nano .env
```

Preencha suas informações:
```env
# Credenciais
USUARIO=SEU_NUMERO_FOLHA
SENHA=SUA_SENHA
URL_BASE=https://centraldofuncionario.com.br/CODIGO_EMPRESA

# Localização
LATITUDE=-5.5292
LONGITUDE=-47.4916

# Configurações de tempo
TEMPO_ALMOCO_MINUTOS=60
CARGA_HORARIA_DIARIA=8

# Variação aleatória (minutos)
VARIACAO_ENTRADA=10
VARIACAO_SAIDA_ALMOCO=5
VARIACAO_RETORNO=10
VARIACAO_SAIDA=10
```

> 💡 **Dica:** Use o Google Maps para encontrar as coordenadas. Clique com botão direito no local e copie.

> ⚠️ **IMPORTANTE:** O arquivo `.env` contém suas credenciais e **nunca deve ser compartilhado!**

### 2.5 Dar permissão ao script de inicialização
```bash
chmod +x ~/ponto/iniciar.sh
```

### 2.6 Configurar inicialização automática no WSL
```bash
echo '' >> ~/.bashrc
echo '# Iniciar ponto automático' >> ~/.bashrc
echo '~/ponto/iniciar.sh' >> ~/.bashrc
```

### 2.7 Testar o script
```bash
cd ~/ponto
source venv/bin/activate
python ponto.py verificar
```

Se funcionar, deve mostrar seus pontos e as variações do dia:
```
=== VERIFICAÇÃO ===
Data: 16/01/2026
Hora: 10:30
Pontos: ['09:07']
Qtd: 1

🎲 Variações de hoje:
   Entrada: +7 min
   Saída almoço: +3 min
   Retorno: +8 min
   Saída: +4 min
```

---

## Parte 3: Configurar Inicialização Automática no Windows

Para o script rodar automaticamente quando você ligar o computador:

### 3.1 Criar pasta de scripts no Windows

Abra o **PowerShell** e execute:
```powershell
New-Item -ItemType Directory -Force -Path "C:\Scripts"
```

### 3.2 Criar o script BAT

Substitua `SEU_USUARIO_UBUNTU` pelo seu usuário do Ubuntu:
```powershell
@'
wsl -d Ubuntu-24.04 -u SEU_USUARIO_UBUNTU -- bash -c "~/ponto/iniciar.sh && sleep 5"
'@ | Out-File -FilePath "C:\Scripts\ponto_wsl.bat" -Encoding ASCII
```

> 💡 Para descobrir seu usuário do Ubuntu: `wsl whoami`

### 3.3 Testar o script BAT
```powershell
C:\Scripts\ponto_wsl.bat
```

Verificar se o WSL está rodando:
```powershell
wsl -l -v
```

Deve mostrar `Running`.

### 3.4 Criar tarefa agendada

Abra o **PowerShell como Administrador** e execute:

Substitua `SEU_USUARIO_UBUNTU` e `SEU_USUARIO_WINDOWS`:
```powershell
$action = New-ScheduledTaskAction -Execute "wsl.exe" -Argument "-d Ubuntu-24.04 -u SEU_USUARIO_UBUNTU -- bash -c '~/ponto/iniciar.sh && sleep 5'"
$trigger = New-ScheduledTaskTrigger -AtLogon -User "SEU_USUARIO_WINDOWS"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId "SEU_USUARIO_WINDOWS" -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName "PontoAutomaticoWSL" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Ponto Automatico WSL"
```

### 3.5 Testar

Reinicie o computador e verifique no PowerShell:
```powershell
wsl -l -v
```

Deve mostrar `Running` automaticamente! 🎉

---

## 🎮 Uso

### Verificar pontos e variações do dia
```bash
cd ~/ponto && source venv/bin/activate
python ponto.py verificar
```

### Forçar registro de ponto
```bash
python ponto.py agora
```

### Ver logs em tempo real
```bash
tail -f ~/ponto/ponto_automatico.log
```

### Verificar se está rodando
```bash
ps aux | grep ponto.py
```

### Parar o script
```bash
pkill -f ponto.py
```

### Reiniciar
```bash
pkill -f ponto.py
~/ponto/iniciar.sh
```

---

## ⚙️ Configuração

### Horários dos pontos

| Horário | Pontos | Ação |
|---------|--------|------|
| 08:00 - 11:59 | 0 | Registra entrada (+ variação) |
| 12:00 - 12:59 | 1 | Registra saída almoço (+ variação) |
| Após almoço + variação | 2 | Registra retorno |
| Horário calculado + variação | 3 | Registra saída |

### Variações aleatórias

Você pode ajustar as variações no arquivo `.env`:
```env
VARIACAO_ENTRADA=10      # 0 a 10 minutos após 09:00
VARIACAO_SAIDA_ALMOCO=5  # 0 a 5 minutos após 12:00
VARIACAO_RETORNO=10      # 0 a 10 minutos extras de almoço
VARIACAO_SAIDA=10        # 0 a 10 minutos após horário calculado
```

### Feriados

Edite a lista `feriados` no arquivo `ponto.py`:
```python
feriados = [
    '2025-01-01',  # Ano Novo
    '2025-12-25',  # Natal
    # Adicione mais datas
]
```

---

## 📁 Estrutura de arquivos
```
~/ponto/
├── ponto.py              # Script principal
├── iniciar.sh            # Script de inicialização
├── .env                  # Suas credenciais (NÃO compartilhar!)
├── .env.example          # Template de configuração
├── .gitignore            # Arquivos ignorados pelo Git
├── venv/                 # Ambiente virtual Python
├── ponto_automatico.log  # Logs do sistema
├── registros_ponto.json  # Histórico de registros
└── delay_hoje.json       # Variações sorteadas do dia
```

---

## 📊 Exemplo de Log
```
2026-01-16 09:00:00 - INFO - 🎲 Delays gerados para hoje: entrada +7min, saída almoço +3min, retorno +8min, saída +4min
2026-01-16 09:07:15 - INFO - 🎲 Entrada com variação: +7 min (horário: 09:07)
2026-01-16 09:07:32 - INFO - ✓ entrada_manha OK!
...
2026-01-16 12:03:45 - INFO - 🎲 Saída almoço com variação: +3 min (horário: 12:03)
2026-01-16 12:04:02 - INFO - ✓ saida_almoco OK!
...
2026-01-16 13:11:30 - INFO - 🎲 Retorno com variação: +8 min de almoço extra
2026-01-16 13:11:48 - INFO - ✓ retorno_almoco OK!
...
2026-01-16 18:16:05 - INFO - === CÁLCULO DE SAÍDA ===
2026-01-16 18:16:05 - INFO - Saída base: 18:12
2026-01-16 18:16:05 - INFO - 🎲 Variação: +4 min
2026-01-16 18:16:05 - INFO - >>> Saída final: 18:16
2026-01-16 18:16:32 - INFO - ✓ saida_tarde OK!
```

---

## 🔍 Solução de Problemas

### WSL para quando fecha o terminal

Verifique se a tarefa agendada existe:
1. Pressione `Win + R`
2. Digite `taskschd.msc`
3. Procure por "PontoAutomaticoWSL"

### Remover tarefa agendada

PowerShell como Admin:
```powershell
Unregister-ScheduledTask -TaskName "PontoAutomaticoWSL" -Confirm:$false
```

### Erro de ChromeDriver
```bash
rm -rf ~/.wdm
```

### Ver logs de erro
```bash
tail -100 ~/ponto/ponto_automatico.log
```

### Resetar variações do dia
```bash
rm ~/ponto/delay_hoje.json
```

---

## 📦 Bibliotecas Python
```bash
pip install selenium schedule webdriver-manager python-dotenv
```

| Biblioteca | Descrição |
|------------|-----------|
| selenium | Automação do navegador |
| schedule | Agendamento de tarefas |
| webdriver-manager | Gerencia ChromeDriver |
| python-dotenv | Carrega variáveis do .env |

---

## 🔄 Atualizações

### v3.0 - Variação Aleatória
- ✅ Variação aleatória nos horários (simula comportamento humano)
- ✅ Configuração de variações via .env
- ✅ Delays fixos por dia (sorteados uma vez)

### v2.0 - Compensação de Horas
- ✅ Cálculo inteligente do horário de saída
- ✅ Compensação automática de atrasos

### v1.0 - Versão Inicial
- ✅ Registro automático dos 4 pontos
- ✅ Respeita 1 hora de almoço

---

## ⚠️ Avisos

1. **Credenciais** - Nunca compartilhe seu arquivo `.env`
2. **Geolocalização** - Configure as coordenadas corretas
3. **Responsabilidade** - Use por sua conta e risco

---

## 📝 Licença

Uso pessoal. Use com responsabilidade.

---

**Desenvolvido com ❤️ para automatizar o dia a dia**
