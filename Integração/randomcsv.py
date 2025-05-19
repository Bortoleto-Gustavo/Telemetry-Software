import csv
import random
import time
import os
import shutil

# Diretório do próprio script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Caminhos dos arquivos
arquivo_csv = os.path.join(script_dir, 'dados_aleatorios.csv')
arquivo_copia = os.path.join(script_dir, 'current.csv')
arquivo_estado = os.path.join(script_dir, 'estado_timestamp.txt')

# Inicializa o contador do timestamp
if os.path.exists(arquivo_estado):
    with open(arquivo_estado, 'r') as f:
        contador = float(f.read().strip())
else:
    contador = 0.0

# Cria o CSV se não existir
if not os.path.exists(arquivo_csv):
    with open(arquivo_csv, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'ax', 'ay', 'az'])

print(f"Atualizando o arquivo '{arquivo_csv}' com dados aleatórios. Pressione Ctrl+C para parar.")

try:
    while True:
        timestamp = round(contador, 1)
        ax = round(random.uniform(-2.0, 2.0), 3)
        ay = round(random.uniform(-2, 2), 3)
        az = round(random.uniform(0.0, 2.0), 3)

        with open(arquivo_csv, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, ax, ay, az])
            f.flush()
            os.fsync(f.fileno())

        # Copia para o arquivo "visível"
        shutil.copy(arquivo_csv, arquivo_copia)

        # Salva o estado do timestamp
        contador += 0.1
        with open(arquivo_estado, 'w') as f:
            f.write(str(contador))

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nAtualização interrompida pelo usuário.")
