"""
Cria backup com timestamp do banco de dados SQLite.
Mantém os 30 backups mais recentes e remove os demais.

Uso:
    python backup.py
"""
import os
import shutil
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'inoutvehicle.db')
BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'backups')


def run():
    if not os.path.exists(DB_PATH):
        print('[BACKUP] Banco de dados não encontrado — nada a fazer.')
        return

    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = os.path.join(BACKUP_DIR, f'backup_{ts}.db')
    shutil.copy2(DB_PATH, dest)
    print(f'[BACKUP] Cópia criada: {dest}')

    # Remove backups mais antigos, mantendo os 30 mais recentes
    backups = sorted(
        f for f in os.listdir(BACKUP_DIR) if f.startswith('backup_') and f.endswith('.db')
    )
    while len(backups) > 30:
        old = os.path.join(BACKUP_DIR, backups.pop(0))
        os.remove(old)
        print(f'[BACKUP] Backup antigo removido: {old}')


if __name__ == '__main__':
    run()
