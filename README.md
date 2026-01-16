# 🕐 Bate Ponto - Ponto Automático

Script Python para registro automático de ponto no sistema Central do Funcionário (Secullum).

## Funcionalidades

- ✅ Registro automático dos 4 pontos diários
- ✅ Compensação inteligente de horas (calcula saída para completar 8h)
- ✅ Respeita 1 hora de almoço (configurável)
- ✅ Verificação a cada 5 minutos
- ✅ Ignora feriados e fins de semana
- ✅ Inicia automaticamente com o Windows (WSL)

## Instalação

### 1. Instalar dependências no WSL (Ubuntu)
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-full wget curl unzip

# Instalar Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt --fix-broken install -y
```

### 2. Configurar o projeto
```bash
mkdir -p ~/ponto
cd ~/ponto
python3 -m venv venv
source venv/bin/activate
pip install selenium schedule webdriver-manager python-dotenv
```

### 3. Configurar credenciais

Copie o arquivo de exemplo e edite com seus dados:
```bash
cp .env.example .env
nano .env
```

### 4. Executar
```bash
# Verificar pontos (sem registrar)
python ponto.py verificar

# Registrar ponto agora
python ponto.py agora

# Iniciar em background
./iniciar.sh
```

## Configuração Windows (iniciar automaticamente)

Veja instruções completas no arquivo de documentação.

## Arquivos

- `ponto.py` - Script principal
- `iniciar.sh` - Script de inicialização
- `.env.example` - Template de configuração
- `.env` - Suas credenciais (não compartilhar!)

## Licença

Uso pessoal. Use com responsabilidade.
