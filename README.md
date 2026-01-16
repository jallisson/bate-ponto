# 🕐 Bate Ponto - Ponto Automático

Script Python para registro automático de ponto no sistema [Central do Funcionário (Secullum)](https://centraldofuncionario.com.br).

## ✨ Funcionalidades

- ✅ Registro automático dos 4 pontos diários
- ✅ **Compensação inteligente de horas** - calcula a saída para completar 8h
- ✅ Respeita 1 hora de almoço (configurável)
- ✅ Verificação a cada 5 minutos
- ✅ Ignora feriados e fins de semana
- ✅ Logs detalhados de todas as operações
- ✅ Geolocalização configurável
- ✅ **Inicia automaticamente com o Windows** (roda em background)

## 🧠 Lógica Inteligente de Compensação

O script calcula automaticamente os horários baseado na sua jornada:

| Situação | Exemplo | Ação |
|----------|---------|------|
| Entrada normal | 09:00 | Saída às 18:00 |
| Entrada atrasada | 09:20 | Saída às 18:20 (compensa 20min) |
| Entrada adiantada | 08:45 | Saída às 17:45 (sai 15min antes) |

### Exemplo de cálculo:
```
Entrada: 09:20
Saída almoço: 12:00
Horas manhã: 2h40min

Retorno almoço: 13:00
Horas que faltam: 8h - 2h40min = 5h20min

>>> Saída calculada: 13:00 + 5h20min = 18:20
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
USUARIO=SEU_NUMERO_FOLHA
SENHA=SUA_SENHA
URL_BASE=https://centraldofuncionario.com.br/CODIGO_EMPRESA
LATITUDE=-5.5292
LONGITUDE=-47.4916
TEMPO_ALMOCO_MINUTOS=60
CARGA_HORARIA_DIARIA=8
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

Se funcionar, deve mostrar seus pontos do dia.

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

### Verificar pontos (sem registrar)
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
| 08:00 - 11:59 | 0 | Registra entrada |
| 12:00 - 12:59 | 1 | Registra saída almoço |
| Após 1h do almoço | 2 | Registra retorno |
| Horário calculado | 3 | Registra saída (completa 8h) |

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
└── ponto_automatico.log  # Logs do sistema
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

## ⚠️ Avisos

1. **Credenciais** - Nunca compartilhe seu arquivo `.env`
2. **Geolocalização** - Configure as coordenadas corretas
3. **Responsabilidade** - Use por sua conta e risco

---

## 📝 Licença

Uso pessoal. Use com responsabilidade.

---

**Desenvolvido com ❤️ para automatizar o dia a dia**
