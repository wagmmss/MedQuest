#!/usr/bin/env python3
"""
MedQuest - Script de Deploy Automatizado (Python)

Uso:
    python deploy.py
    python deploy.py "Minha mensagem de commit"
    python deploy.py --skip-git
    python deploy.py --skip-remote
"""

import argparse
import datetime
import os
import subprocess
import sys
import time

HOST_DEFAULT = os.environ.get("MEDQUEST_DEPLOY_HOST", "136.248.114.130")
USER_DEFAULT = os.environ.get("MEDQUEST_DEPLOY_USER", "ubuntu")
REMOTE_DIR_DEFAULT = os.environ.get("MEDQUEST_DEPLOY_DIR", "~/MedQuest")


def run_command(cmd, shell=False, check=True):
    try:
        result = subprocess.run(cmd, shell=shell, check=check)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"\n[ERRO] Falha ao executar comando: {cmd}")
        sys.exit(e.returncode)


def resolve_ssh_key(custom_key=None):
    if custom_key and os.path.exists(custom_key):
        return custom_key

    env_key = os.environ.get("MEDQUEST_DEPLOY_KEY")
    if env_key and os.path.exists(env_key):
        return env_key
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_key = os.path.join(script_dir, "sua-chave.key")
    if os.path.exists(local_key):
        return local_key
    
    home_ssh = os.path.expanduser("~/.ssh/id_rsa")
    if os.path.exists(home_ssh):
        return home_ssh
    
    return None


def main():
    parser = argparse.ArgumentParser(description="Deploy automatizado do MedQuest")
    parser.add_argument("message", nargs="?", help="Mensagem do commit")
    parser.add_argument("--host", default=HOST_DEFAULT, help="IP da VPS")
    parser.add_argument("--user", default=USER_DEFAULT, help="Usuario SSH")
    parser.add_argument("--key", default=None, help="Caminho da chave SSH")
    parser.add_argument("--skip-git", action="store_true", help="Pular commit e push local")
    parser.add_argument("--skip-remote", action="store_true", help="Pular execucao remota na VPS")

    args = parser.parse_args()
    start_time = time.time()

    print("\n" + "=" * 60)
    print("             MEDQUEST - DEPLOY AUTOMATIZADO                 ")
    print("=" * 60 + "\n")

    root_dir = os.path.dirname(os.path.abspath(__file__))
    if root_dir:
        os.chdir(root_dir)

    # 1. GIT LOCAL
    if not args.skip_git:
        print("[1/3] Processando alteracoes no repositorio local (Git)...")
        status_proc = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        has_changes = bool(status_proc.stdout.strip())

        if has_changes:
            msg = args.message
            if not msg:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                if sys.stdin.isatty():
                    user_input = input(f"  Digite a mensagem do commit (Enter para '[deploy] {timestamp}'): ").strip()
                    msg = user_input if user_input else f"[deploy] Atualizacao {timestamp}"
                else:
                    msg = f"[deploy] Atualizacao {timestamp}"
            
            print(f"  [i] Adicionando arquivos e realizando commit: '{msg}'")
            run_command(["git", "add", "-A"])
            run_command(["git", "commit", "-m", msg])
        else:
            print("  [i] Nenhuma alteracao pendente de commit local.")

        print("  [i] Enviando commits para origin main...")
        run_command(["git", "push", "origin", "main"])
        print("  [OK] Git push concluido com sucesso.\n")
    else:
        print("[1/3] Etapa Git local pulada (--skip-git).\n")

    # 2. DEPLOY REMOTO VIA SSH
    if not args.skip_remote:
        print(f"[2/3] Conectando a VPS ({args.user}@{args.host}) e executando deploy...")
        key_path = resolve_ssh_key(args.key)
        
        remote_script = (
            "set -e && "
            "echo '  [VPS 1/4] Atualizando codigo do MedQuest via Git...' && "
            "cd ~/MedQuest && git pull origin main && "
            "echo '  [VPS 2/4] Reconstruindo e subindo containers Docker...' && "
            "sudo docker-compose up -d --build --force-recreate && "
            "echo '  [VPS 3/4] Limpando imagens antigas...' && "
            "sudo docker image prune -f > /dev/null 2>&1 || true && "
            "echo '  [VPS 4/4] Status atual dos servicos:' && "
            "sudo docker-compose ps"
        )

        ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=15"]
        if key_path:
            print(f"  [i] Usando chave SSH: {key_path}")
            ssh_cmd.extend(["-i", key_path])
        
        ssh_cmd.append(f"{args.user}@{args.host}")
        ssh_cmd.append(remote_script)

        run_command(ssh_cmd)
        print("  [OK] Deploy remoto na VPS concluido com sucesso!\n")
    else:
        print("[2/3] Etapa remota pulada (--skip-remote).\n")

    elapsed = int(time.time() - start_time)
    minutes = elapsed // 60
    seconds = elapsed % 60

    print("=" * 60)
    print("              DEPLOY CONCLUIDO COM SUCESSO!                 ")
    print("=" * 60)
    print(f"Tempo total: {minutes}m {seconds}s")
    print(f"MedQuest esta online e atualizado no servidor ({args.host}).\n")


if __name__ == "__main__":
    main()
