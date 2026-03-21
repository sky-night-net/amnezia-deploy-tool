#!/usr/bin/env python3
import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print("[*] Connecting to 10.101.50.101...")
ssh.connect("10.101.50.101", username="root", password="1q2w3e!@571", timeout=15)
print("[+] Connected!")

def run(cmd):
    print(f"  > {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print(f"    {out}")
    if err and "Warning" not in err: print(f"    ERR: {err}")
    return out, err

print("\n[1] Kill old container instantly...")
run("docker kill amnezia-wg-easy 2>/dev/null || true")
run("docker rm -f amnezia-wg-easy 2>/dev/null || true")
run("fuser -k 993/udp || true")
run("fuser -k 4466/tcp || true")
time.sleep(2)

print("\n[2] Redeploy with 0.0.0.0 binding...")
cmd = (
    "docker run -d --name=amnezia-wg-easy "
    "-e WG_HOST=95.85.116.86 "
    "-e PORT=4466 -e WG_PORT=993 "
    "-e EXPERIMENTAL_AWG=true "
    "-e JC=10 -e JMIN=100 -e JMAX=1000 "
    "-e S1=15 -e S2=100 "
    "-e H1=1234567891 -e H2=1234567892 -e H3=1234567893 -e H4=1234567894 "
    "-v ~/.amnezia-wg-easy:/etc/wireguard "
    "-p 4466:4466/tcp "
    "-p 993:993/udp "
    "--cap-add=NET_ADMIN --cap-add=SYS_MODULE "
    "--sysctl='net.ipv4.conf.all.src_valid_mark=1' --sysctl='net.ipv4.ip_forward=1' "
    "--device=/dev/net/tun:/dev/net/tun --restart unless-stopped "
    "ghcr.io/w0rng/amnezia-wg-easy"
)
run(cmd)

print("\n[3] Verify:")
run("docker ps --filter name=amnezia-wg-easy --format '{{.Names}} {{.Status}} {{.Ports}}'")
ssh.close()
print("\n[+] DONE!")
