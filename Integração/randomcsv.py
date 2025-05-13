import csv
import random
import time
import os
import shutil

# Diretório do próprio script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Caminhos completos dos arquivos
arquivo_csv = os.path.join(script_dir, 'dados_aleatorios.csv')
arquivo_copia = os.path.join(script_dir, 'current.csv')

# Verifica se o arquivo existe; se não, cria com cabeçalho
if not os.path.exists(arquivo_csv):
    with open(arquivo_csv, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'valor1', 'valor2', 'valor3'])

print(f"Atualizando o arquivo '{arquivo_csv}' com dados aleatórios. Pressione Ctrl+C para parar.")

try:
    while True:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        valor1 = random.randint(0, 100)
        valor2 = random.uniform(0, 500)
        valor3 = random.choice(['A', 'B', 'C', 'D'])

        with open(arquivo_csv, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, valor1, f"{valor2:.2f}", valor3])
            shutil.copy(arquivo_csv, arquivo_copia)
            f.flush()
            os.fsync(f.fileno())

        time.sleep(0.1)  # Espera 1 segundo antes de adicionar uma nova linha

except KeyboardInterrupt:
    print("\nAtualização interrompida pelo usuário.")
