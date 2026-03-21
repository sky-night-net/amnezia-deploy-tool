#!/usr/bin/env python3
"""
 █▀▀█ █▀▄▀█ █▀▀▄ █▀▀ ▀▀█ ░▀░ █▀▀█    █▀▀ █   █
 █▄▄█ █ ▀ █ █  █ █▀▀   █  ▀█ █▄▄█    █   █   █
 ▀  ▀ ▀   ▀ ▀  ▀ ▀▀▀  ▀▀▀ ▀▀ ▀  ▀    ▀▀▀ ▀▀▀ ▀▀

Amnezia VPN Deployment & Management Suite
One-command deploy, diagnose, fix, clean — from any machine.
"""
import sys
import subprocess
import argparse
import time
import os

# ── Auto-install dependencies ──────────────────────────────────────
def ensure_deps():
    missing = []
    for pkg in ("paramiko", "bcrypt"):
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"[!] Installing missing packages: {', '.join(missing)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing, "-q"])
        print("[+] Done. Continuing...\n")

ensure_deps()

import paramiko
import bcrypt

# ── Constants ──────────────────────────────────────────────────────
IMAGE    = "ghcr.io/w0rng/amnezia-wg-easy"
VPN_PORT = "993"
WEB_PORT = "4466"
EXT_IP   = "95.85.116.86"

STEALTH = {
    "JC": "10", "JMIN": "100", "JMAX": "1000",
    "S1": "15",  "S2": "100",
    "H1": "1234567891", "H2": "1234567892",
    "H3": "1234567893", "H4": "1234567894",
}

# ── Colors ─────────────────────────────────────────────────────────
G = "\033[92m"; R = "\033[91m"; Y = "\033[93m"
B = "\033[94m"; C = "\033[96m"; W = "\033[0m"; BOLD = "\033[1m"; BC = "\033[44m"

def ok(msg):  print(f"{G}[✔]{W} {msg}")
def err(msg): print(f"{R}[✘]{W} {msg}")
def inf(msg): print(f"{C}[→]{W} {msg}")
def war(msg): print(f"{Y}[!]{W} {msg}")
def hdr(msg): print(f"\n{BOLD}{B}{'─'*45}\n  {msg}\n{'─'*45}{W}")

# ── SSH helpers ────────────────────────────────────────────────────
def ssh_connect(ip, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    inf(f"Connecting to {ip} as root...")
    client.connect(ip, username="root", password=password, timeout=15)
    ok("SSH connection established.")
    return client

def run(ssh, cmd, label=None):
    if label:
        inf(label)
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    out = stdout.read().decode().strip()
    err_out = stderr.read().decode().strip()
    return out, err_out

def show(out, error=""):
    """Print command output nicely."""
    if out:
        for line in out.splitlines():
            print(f"       {line}")
    if error and "Warning" not in error and "warning" not in error:
        for line in error.splitlines():
            print(f"   {R}   {line}{W}")

# ── Actions ────────────────────────────────────────────────────────

def action_status(ssh):
    """Show full server status."""
    hdr("SERVER STATUS")

    out, _ = run(ssh, "docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'", "Running containers:")
    show(out)

    out, _ = run(ssh, "netstat -tulpn 2>/dev/null | grep -E '993|4466' || ss -tulpn | grep -E '993|4466' 2>/dev/null", "\nPort 993/4466 usage:")
    if out:
        show(out)
    else:
        ok("Ports 993 and 4466 are FREE.")

    out, _ = run(ssh, "docker inspect amnezia-wg-easy --format '{{range .HostConfig.PortBindings}}{{println .}}{{end}}' 2>/dev/null", "\nPort bindings:")
    if out:
        show(out)
    else:
        war("Container 'amnezia-wg-easy' not found.")

    out, _ = run(ssh, "ufw status", "\nUFW Firewall:")
    show(out)


def action_diagnose(ssh, vpn_port=VPN_PORT, web_port=WEB_PORT):
    """Diagnose potential problems."""
    hdr("DIAGNOSTICS")
    issues = 0

    inf("Checking Docker...")
    out, e = run(ssh, "docker info --format '{{.ServerVersion}}' 2>/dev/null")
    if out:
        ok(f"Docker version: {out}")
    else:
        err("Docker is NOT running!"); issues += 1

    inf("Checking container...")
    out, _ = run(ssh, "docker inspect amnezia-wg-easy --format '{{.State.Running}}' 2>/dev/null")
    if out == "true":
        ok("Container amnezia-wg-easy is RUNNING.")
    else:
        err("Container amnezia-wg-easy is NOT running."); issues += 1

    inf(f"Checking VPN port {vpn_port}/udp...")
    out, _ = run(ssh, f"ss -tulpn | grep {vpn_port} 2>/dev/null")
    if out:
        ok(f"Port {vpn_port} is listening.")
        show(out)
    else:
        err(f"Port {vpn_port} is NOT listening!"); issues += 1

    inf(f"Checking Web UI port {web_port}/tcp...")
    out, _ = run(ssh, f"ss -tulpn | grep {web_port} 2>/dev/null")
    if out:
        binding = out
        if "0.0.0.0" in binding or ":::" in binding:
            ok(f"Web UI port {web_port} is open on ALL interfaces (0.0.0.0). ✓")
        else:
            war(f"Web UI port {web_port} is bound to a specific IP — may not be accessible via VPN!")
        show(out)
    else:
        err(f"Web UI port {web_port} is NOT listening!"); issues += 1

    inf("Checking WireGuard interface...")
    out, _ = run(ssh, "ip link show awg0 2>/dev/null || ip link show wg0 2>/dev/null")
    if out:
        ok("WireGuard interface is UP.")
    else:
        war("WireGuard interface not found. May still be starting."); issues += 1

    inf("Checking UFW...")
    out, _ = run(ssh, f"ufw status | grep {vpn_port}")
    if out:
        ok(f"UFW: port {vpn_port} is allowed.")
    else:
        err(f"UFW: port {vpn_port} is NOT in allow rules!")
        war("Run 'Fix UFW' from the menu to correct this."); issues += 1

    print()
    if issues == 0:
        ok("All checks passed! Server looks healthy.")
    else:
        war(f"{issues} issue(s) found. Use the Fix options from the menu.")
    return issues


def action_cleanup(ssh, vpn_port=VPN_PORT, web_port=WEB_PORT):
    """Deep cleanup — stop containers, free ports, remove data."""
    hdr("DEEP CLEANUP")

    inf("Before state:")
    out, _ = run(ssh, "docker ps -a --format '  {{.Names}} — {{.Status}}'")
    show(out) if out else print("       (no containers)")

    inf("Killing any container starting with 'amnezia-'...")
    run(ssh, "docker ps -a --filter name=amnezia --format '{{.ID}}' | xargs -r docker stop 2>/dev/null || true")
    run(ssh, "docker ps -a --filter name=amnezia --format '{{.ID}}' | xargs -r docker rm -f 2>/dev/null || true")

    inf("Finding and killing any container using target ports...")
    for port in [vpn_port, web_port]:
        out, _ = run(ssh, f"docker ps -q --filter 'publish={port}'")
        if out:
            for cid in out.splitlines():
                war(f"Killing container {cid} using port {port}...")
                run(ssh, f"docker kill {cid} && docker rm -f {cid}")
            ok(f"Freed port {port}.")

    inf("Freeing ports via fuser (hard kill)...")
    run(ssh, f"fuser -k {vpn_port}/udp 2>/dev/null || true")
    run(ssh, f"fuser -k {web_port}/tcp 2>/dev/null || true")

    inf("Removing WireGuard config data...")
    run(ssh, "rm -rf ~/.amnezia-wg-easy")

    time.sleep(1)
    inf("After state:")
    out, _ = run(ssh, "docker ps -a --format '  {{.Names}} — {{.Status}}'")
    show(out) if out else ok("No containers running. Clean!")
    out, _ = run(ssh, f"ss -tulpn | grep -E '{vpn_port}|{web_port}' 2>/dev/null")
    if out:
        war(f"Some process still holding ports:\n{out}")
    else:
        ok("Ports are FREE.")


def action_deploy(ssh, ext_ip, password, vpn_port=VPN_PORT, web_port=WEB_PORT):
    """Deploy AmneziaWG container."""
    hdr("DEPLOYING AMNEZIA VPN")

    inf("Generating password hash...")
    salt = bcrypt.gensalt()
    pw_hash = bcrypt.hashpw(password.encode(), salt).decode()
    ok("Password hash generated.")

    inf("Running Docker container...")
    docker_cmd = (
        f"docker run -d --name=amnezia-wg-easy "
        f"-e WG_HOST={ext_ip} "
        f"-e PASSWORD_HASH='{pw_hash}' "
        f"-e PORT={web_port} -e WG_PORT={vpn_port} "
        f"-e EXPERIMENTAL_AWG=true "
        f"-e JC={STEALTH['JC']} -e JMIN={STEALTH['JMIN']} -e JMAX={STEALTH['JMAX']} "
        f"-e S1={STEALTH['S1']} -e S2={STEALTH['S2']} "
        f"-e H1={STEALTH['H1']} -e H2={STEALTH['H2']} "
        f"-e H3={STEALTH['H3']} -e H4={STEALTH['H4']} "
        f"-v ~/.amnezia-wg-easy:/etc/wireguard "
        f"-p {web_port}:{web_port}/tcp "
        f"-p {vpn_port}:{vpn_port}/udp "
        f"--cap-add=NET_ADMIN --cap-add=SYS_MODULE "
        f"--sysctl='net.ipv4.conf.all.src_valid_mark=1' "
        f"--sysctl='net.ipv4.ip_forward=1' "
        f"--device=/dev/net/tun:/dev/net/tun "
        f"--restart unless-stopped {IMAGE}"
    )
    out, e = run(ssh, docker_cmd)
    if e and "is already" not in e and "allocated" not in e:
        err(f"Deployment failed:\n{e}")
        return False
    ok(f"Container started. ID: {(out or '?')[:12]}")

    inf("Configuring UFW firewall...")
    run(ssh, "ufw allow 22/tcp")
    run(ssh, f"ufw allow {vpn_port}/udp")
    for sub in ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]:
        run(ssh, f"ufw allow from {sub} to any port {web_port} proto tcp")
    run(ssh, "echo 'y' | ufw enable")
    ok("Firewall rules applied.")

    time.sleep(2)
    out, _ = run(ssh, "docker ps --filter name=amnezia-wg-easy --format '{{.Status}}'")
    ok(f"Container status: {out}")

    print(f"\n{'═'*45}")
    print(f"{G}{BOLD}   ✔ AMNEZIA VPN DEPLOYED SUCCESSFULLY{W}")
    print(f"{'═'*45}")
    print(f"  Internal server IP : {ssh.get_transport().getpeername()[0]}")
    print(f"  External (public)  : {ext_ip}")
    print(f"  VPN Port           : {vpn_port}/UDP")
    print(f"  Web UI (LAN/VPN)   : http://{ssh.get_transport().getpeername()[0]}:{web_port}")
    print(f"  Web UI (via VPN)   : http://10.8.0.1:{web_port}")
    print(f"{'═'*45}\n")
    return True


def action_fix_webui(ssh, web_port=WEB_PORT, vpn_port=VPN_PORT, ext_ip=EXT_IP):
    """Rebind web port to 0.0.0.0 so it's accessible from VPN."""
    hdr("FIX: WEB UI ACCESS FROM VPN")
    war("Recreating container with 0.0.0.0 port binding...")

    inf("Getting current config...")
    out, _ = run(ssh, "docker inspect amnezia-wg-easy --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null")
    env_lines = out.splitlines()
    env = {}
    for line in env_lines:
        if "=" in line:
            k, v = line.split("=", 1)
            env[k] = v

    pw_hash = env.get("PASSWORD_HASH", "")
    ext_ip  = env.get("WG_HOST", ext_ip)

    inf("Killing old container...")
    run(ssh, "docker stop amnezia-wg-easy 2>/dev/null || true")
    run(ssh, "docker rm -f amnezia-wg-easy 2>/dev/null || true")
    run(ssh, f"fuser -k {web_port}/tcp 2>/dev/null || true")
    time.sleep(1)

    inf("Starting with 0.0.0.0 binding...")
    pw_env = f"-e PASSWORD_HASH='{pw_hash}' " if pw_hash else ""
    docker_cmd = (
        f"docker run -d --name=amnezia-wg-easy "
        f"-e WG_HOST={ext_ip} "
        f"{pw_env}"
        f"-e PORT={web_port} -e WG_PORT={vpn_port} "
        f"-e EXPERIMENTAL_AWG=true "
        f"-e JC=10 -e JMIN=100 -e JMAX=1000 "
        f"-e S1=15 -e S2=100 "
        f"-e H1=1234567891 -e H2=1234567892 -e H3=1234567893 -e H4=1234567894 "
        f"-v ~/.amnezia-wg-easy:/etc/wireguard "
        f"-p {web_port}:{web_port}/tcp "
        f"-p {vpn_port}:{vpn_port}/udp "
        f"--cap-add=NET_ADMIN --cap-add=SYS_MODULE "
        f"--sysctl='net.ipv4.conf.all.src_valid_mark=1' "
        f"--sysctl='net.ipv4.ip_forward=1' "
        f"--device=/dev/net/tun:/dev/net/tun "
        f"--restart unless-stopped {IMAGE}"
    )

    out, e = run(ssh, docker_cmd)
    if e and "allocated" not in e and "already" not in e:
        err(f"Failed: {e}")
        return

    inf("Setting UFW rules (Private subnets only)...")
    for sub in ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]:
        run(ssh, f"ufw allow from {sub} to any port {web_port} proto tcp")
    run(ssh, "echo 'y' | ufw enable")
    ok("UFW updated.")
    
    time.sleep(2)
    out2, _ = run(ssh, f"ss -tulpn | grep {web_port} 2>/dev/null")
    show(out2)
    if "0.0.0.0" in out2 or ":::" in out2:
        ok("Web UI is now accessible from ALL interfaces (0.0.0.0)")
        ok("While on VPN: http://10.8.0.1:4466")
    else:
        war("Binding not confirmed yet — container may still be starting.")


def action_fix_ufw(ssh, mode="private", vpn_port=VPN_PORT, web_port=WEB_PORT):
    """Reset UFW to safe rules or open to public."""
    hdr(f"FIX: UFW FIREWALL RULES ({mode.upper()})")
    inf(f"Resetting UFW rules (Mode: {mode})...")
    
    # We don't reset everything to avoid breaking other services, 
    # but we ensure our core rules are there.
    run(ssh, "ufw allow 22/tcp")
    run(ssh, f"ufw allow {vpn_port}/udp")
    
    if mode == "public":
        run(ssh, f"ufw allow {web_port}/tcp")
        ok(f"Web UI ({web_port}/tcp) allowed from ANYWHERE.")
    else:
        # Remove any broad allow rule first if it exists (not easy in UFW via CLI, but we add specific ones)
        for sub in ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]:
            run(ssh, f"ufw allow from {sub} to any port {web_port} proto tcp")
        ok(f"Web UI ({web_port}/tcp) allowed from all private subnets.")
        
    run(ssh, "echo 'y' | ufw enable")
    out, _ = run(ssh, "ufw status")
    show(out)
    ok("UFW updated.")


def action_logs(ssh, lines=50):
    """Show container logs."""
    hdr(f"CONTAINER LOGS (last {lines} lines)")
    out, e = run(ssh, f"docker logs --tail={lines} amnezia-wg-easy 2>&1")
    if out:
        show(out)
    else:
        war("No logs found (container may not be running).")


def action_restart(ssh):
    """Restart the container."""
    hdr("RESTART CONTAINER")
    out, e = run(ssh, "docker restart amnezia-wg-easy")
    if e:
        err(f"Error: {e}")
    else:
        ok("Container restarted.")
    time.sleep(2)
    out, _ = run(ssh, "docker ps --filter name=amnezia-wg-easy --format '{{.Status}}'")
    ok(f"Status: {out}")


def action_change_password(ssh):
    """Change Web UI password by recreating container with new hash."""
    hdr("CHANGE WEB UI PASSWORD")
    new_pw = input("  Enter NEW password for Web UI: ").strip()
    if not new_pw:
        err("Password cannot be empty.")
        return

    inf("Generating new hash...")
    salt = bcrypt.gensalt()
    pw_hash = bcrypt.hashpw(new_pw.encode(), salt).decode()

    inf("Getting current config...")
    out, _ = run(ssh, "docker inspect amnezia-wg-easy --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null")
    env = {}
    for line in out.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            env[k] = v

    ext_ip   = env.get("WG_HOST", EXT_IP)
    web_port = env.get("PORT", WEB_PORT)
    vpn_port = env.get("WG_PORT", VPN_PORT)

    inf("Recreating container with new password...")
    run(ssh, "docker stop amnezia-wg-easy 2>/dev/null || true")
    run(ssh, "docker rm -f amnezia-wg-easy 2>/dev/null || true")
    
    pw_env = f"-e PASSWORD_HASH='{pw_hash}' "
    docker_cmd = (
        f"docker run -d --name=amnezia-wg-easy "
        f"-e WG_HOST={ext_ip} "
        f"{pw_env}"
        f"-e PORT={web_port} -e WG_PORT={vpn_port} "
        f"-e EXPERIMENTAL_AWG=true "
        f"-e JC={STEALTH['JC']} -e JMIN={STEALTH['JMIN']} -e JMAX={STEALTH['JMAX']} "
        f"-e S1={STEALTH['S1']} -e S2={STEALTH['S2']} "
        f"-e H1={STEALTH['H1']} -e H2={STEALTH['H2']} "
        f"-e H3={STEALTH['H3']} -e H4={STEALTH['H4']} "
        f"-v ~/.amnezia-wg-easy:/etc/wireguard "
        f"-p {web_port}:{web_port}/tcp "
        f"-p {vpn_port}:{vpn_port}/udp "
        f"--cap-add=NET_ADMIN --cap-add=SYS_MODULE "
        f"--sysctl='net.ipv4.conf.all.src_valid_mark=1' "
        f"--sysctl='net.ipv4.ip_forward=1' "
        f"--device=/dev/net/tun:/dev/net/tun "
        f"--restart unless-stopped {IMAGE}"
    )
    run(ssh, docker_cmd)
    ok("Password changed! Container restarted with new credentials.")


# ── Interactive Wizard ─────────────────────────────────────────────
MENU = """
  1. Deploy new VPN server
  2. Status / full info
  3. Diagnose problems
  4. Deep cleanup (stop + free ports + remove data)
  5. Fix: Web UI not accessible via VPN
  6. Fix: Firewall (Private / Public Access)
  7. Restart container
  8. Show container logs
  9. Change Web UI password
  0. Change Server / Logout
  Q. Exit
"""

def inp(prompt, default=None):
    suffix = f" [{default}]" if default else ""
    val = input(f"  {prompt}{suffix}: ").strip()
    return val if val else default

def wizard():
    print(f"\n{BC}{BOLD}{C}   AMNEZIA VPN MANAGEMENT SUITE   {W}")
    
    current_ip = "10.101.50.101"
    
    while True:
        print(f"\n{BOLD}{B}── NEW SESSION ─────────────────────────────{W}")
        ip       = inp("Server IP", current_ip)
        password = inp("Root password")
        if not password:
            err("Password required.")
            val = inp("Try again? (y/n)", "y")
            if val.lower() != 'y': return
            continue

        try:
            ssh = ssh_connect(ip, password)
            current_ip = ip
        except Exception as e:
            err(f"Cannot connect to {ip}: {e}")
            val = inp("Try again? (y/n)", "y")
            if val.lower() != 'y': return
            continue

        try:
            while True:
                print(MENU)
                choice = inp("Choose action", "2")
                
                if choice.upper() == "Q":
                    sys.exit(0)
                elif choice == "0":
                    break # Back to IP selection
                
                try:
                    if choice == "1":
                        ext_ip   = inp("Public external IP", EXT_IP)
                        web_port = inp("Web UI port", WEB_PORT)
                        vpn_port = inp("VPN port (UDP)", VPN_PORT)
                        action_cleanup(ssh, vpn_port, web_port)
                        action_deploy(ssh, ext_ip, password, vpn_port, web_port)
                    elif choice == "2":
                        action_status(ssh)
                    elif choice == "3":
                        action_diagnose(ssh)
                    elif choice == "4":
                        vpn_port = inp("VPN port to free", VPN_PORT)
                        web_port = inp("Web port to free", WEB_PORT)
                        action_cleanup(ssh, vpn_port, web_port)
                    elif choice == "5":
                        action_fix_webui(ssh)
                    elif choice == "6":
                        m = inp("Access Mode (1: Private, 2: Public Anywhere)", "1")
                        mode = "public" if m == "2" else "private"
                        action_fix_ufw(ssh, mode=mode)
                    elif choice == "7":
                        action_restart(ssh)
                    elif choice == "8":
                        n = inp("How many log lines", "50")
                        action_logs(ssh, n)
                    elif choice == "9":
                        action_change_password(ssh)
                    else:
                        war("Unknown option.")
                except Exception as e:
                    err(f"Action failed: {e}")
                    
                input(f"\n{C}[→]{W} Press Enter to continue...")
        finally:
            ssh.close()
            print(f"\n{C}[→]{W} Connection to {ip} closed.\n")


# ── CLI mode ───────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Amnezia VPN Management Suite")
    parser.add_argument("--ip",        help="Server IP")
    parser.add_argument("--password",  help="Root password")
    parser.add_argument("--ext-ip",    default=EXT_IP, help="Public IP")
    parser.add_argument("--auto",      action="store_true", help="Full auto deploy")
    parser.add_argument("--cleanup",   action="store_true", help="cleanup only")
    parser.add_argument("--diagnose",  action="store_true", help="Diagnose server")
    parser.add_argument("--status",    action="store_true", help="Show status")
    parser.add_argument("--fix-webui", action="store_true", help="Fix web UI binding")
    parser.add_argument("--fix-ufw",   action="store_true", help="Fix UFW rules")
    parser.add_argument("--logs",      action="store_true", help="Show logs")
    args = parser.parse_args()

    if not any([args.auto, args.cleanup, args.diagnose, args.status,
                args.fix_webui, args.fix_ufw, args.logs]):
        wizard()
        return

    if not (args.ip and args.password):
        err("--ip and --password are required for non-interactive mode.")
        sys.exit(1)

    try:
        ssh = ssh_connect(args.ip, args.password)
    except Exception as e:
        err(f"Cannot connect: {e}")
        sys.exit(1)

    try:
        if args.status:    action_status(ssh)
        if args.diagnose:  action_diagnose(ssh)
        if args.cleanup:   action_cleanup(ssh)
        if args.fix_webui: action_fix_webui(ssh)
        if args.fix_ufw:   action_fix_ufw(ssh)
        if args.logs:      action_logs(ssh)
        if args.auto:
            action_cleanup(ssh)
            action_deploy(ssh, args.ext_ip, args.password)
    finally:
        ssh.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Y}[!]{W} Aborted by user.")
        sys.exit(0)
