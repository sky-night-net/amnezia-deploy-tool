# Amnezia VPN CLI
Complete tool for deployment, diagnostics, and management.

---

## Quick Start

### Run once (fix EOFError):
```bash
python3 <(curl -fsSL https://raw.githubusercontent.com/sky-night-net/amnezia-deploy-tool/main/amnezia-cli.py)
```

### Install as 'amnezia' command:
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/sky-night-net/amnezia-deploy-tool/main/install.sh)
```
After installation, just run: `amnezia`

---

## Key Features

### Peer Management
* List Peers * Add Peer
  * * Download Config (.conf)
   
    * ### Network Settings
    * * Change Tunnel Subnet
     
      * ### Diagnostics & Fixes
      * * Diagnose Docker, ports, firewall
        * * Fix Web UI access
          * * Fix UFW rules
           
            * ---
           
            * ## Menu Options
            * 1. Deploy new VPN server
              2. 2. Status / full info
                 3. 3. Diagnose problems
                    4. 4. Peers: List existing users
                       5. 5. Peers: Add NEW user
                          6. 6. Peers: Download config
                             7. 7. Network: Change Tunnel Subnet
                                8. 8. Fix: Web UI not accessible
                                   9. 9. Fix: Firewall
                                      10. 10. Restart container
                                          11. 11. Show container logs
                                              12. 12. Change Web UI password
                                                  13. 13. Update this script
                                                     
                                                      14. ---
                                                     
                                                      15. ## Recommended NTP Servers (for Turkmenistan)
                                                      16. 1. uk.pool.ntp.org
                                                          2. 2. time.nrc.ca
                                                             3. 3. nl.pool.ntp.org
                                                               
                                                                4. ## Requirements
                                                                5. - Python 3.7+
                                                                   - - Dependencies installed automatically.
                                                                     - 
