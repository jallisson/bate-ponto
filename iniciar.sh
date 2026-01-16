#!/bin/bash
cd ~/ponto

if pgrep -f "ponto.py" > /dev/null; then
    echo "$(date): Já está rodando"
else
    echo "$(date): Iniciando ponto automático"
    source ~/ponto/venv/bin/activate
    nohup python ponto.py >> ~/ponto/ponto.log 2>&1 &
    echo "$(date): Iniciado com PID $!"
fi
