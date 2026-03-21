# Amnezia VPN CLI — Deployment & Management Suite

Полный инструмент для развёртывания, диагностики и управления Amnezia VPN с любого ПК — за одну команду.

---

## ⚡ Быстрый старт (без клонирования)

### Разовый запуск (самый быстрый способ):
```bash
curl -fsSL https://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@raw.githubusercontent.com/sky-night-net/amnezia-deploy-tool/main/amnezia-cli.py | python3
```

### Установить как постоянную команду `amnezia`:
```bash
bash <(curl -fsSL https://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@raw.githubusercontent.com/sky-night-net/amnezia-deploy-tool/main/install.sh)
```
После этого запускай просто:
```bash
amnezia
```

### Обновить до последней версии:
```bash
bash <(curl -fsSL https://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@raw.githubusercontent.com/sky-night-net/amnezia-deploy-tool/main/install.sh)
```

---

## Меню скрипта

```
  1. Deploy new VPN server         — полный деплой с очисткой
  2. Status / full info            — контейнеры, порты, UFW
  3. Diagnose problems             — авто-проверка 6 пунктов
  4. Deep cleanup                  — убить всё, освободить порты
  5. Fix: Web UI not via VPN       — перебинд порта на 0.0.0.0
  6. Fix: UFW firewall rules       — починить правила фаервола
  7. Restart container             — перезапуск контейнера
  8. Show container logs           — последние N строк логов
  9. Exit
```

---

## Авто-режим (без меню)

```bash
amnezia --ip 10.101.50.101 --password YOUR_PASS --auto
amnezia --ip 10.101.50.101 --password YOUR_PASS --status
amnezia --ip 10.101.50.101 --password YOUR_PASS --diagnose
amnezia --ip 10.101.50.101 --password YOUR_PASS --cleanup
amnezia --ip 10.101.50.101 --password YOUR_PASS --fix-webui
amnezia --ip 10.101.50.101 --password YOUR_PASS --logs
```

---

## Требования

- Python 3.7+
- Зависимости устанавливаются **автоматически**: `paramiko`, `bcrypt`
