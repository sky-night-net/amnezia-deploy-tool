# Amnezia VPN CLI — Deployment & Management Suite

Полный инструмент для развёртывания, диагностики и управления Amnezia VPN с любого ПК — за одну команду.

---

## ⚡ Быстрый старт

### Разовый запуск:
```bash
python3 <(curl -fsSL https://raw.githubusercontent.com/sky-night-net/amnezia-deploy-tool/main/amnezia-cli.py)
```

### Установить как постоянную команду `amnezia`:
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/sky-night-net/amnezia-deploy-tool/main/install.sh)
```
После этого запускай просто: `amnezia`

---

## 🚀 Основные возможности

### 👤 Управление пользователями (Пиры)
Теперь не нужно заходить в Web UI, чтобы создать нового пользователя:
*   **List Peers**: Просмотр всех существующих клиентов.
*   **Add Peer**: Мгновенное создание нового клиента.
*   **Download Config**: Автоматическое скачивание `.conf` файла прямо на ваш компьютер.

### 🌐 Сетевые настройки
*   **Change Subnet**: Смена внутренней подсети туннеля (например, на `10.10.0.x`) за одно действие. Контейнер будет автоматически перезапущен с новыми параметрами.

### 🛠️ Лечение и диагностика
*   **Diagnose**: Проверка Docker, портов, интерфейсов и фаервола.
*   **Fix Web UI**: Проброс порта 4466 на 0.0.0.0 для доступа через VPN.
*   **Fix UFW**: Автоматическая настройка правил фаервола.

---

## 📋 Меню скрипта

1.  **Deploy new VPN server** — Чистая установка.
2.  **Status / full info** — Состояние системы.
3.  **Diagnose problems** — Поиск неисправностей.
4.  **Peers: List existing users** — Список клиентов.
5.  **Peers: Add NEW user** — Добавить клиента.
6.  **Peers: Download config** — Скачать конфиг на ПК.
7.  **Network: Change Tunnel Subnet** — Смена подсети.
8.  **Fix: Web UI not accessible** — Починить вход в панель.
9.  **Fix: Firewall** — Настройка доступа (Private/Public).
10. **Restart container** — Перезапуск.
11. **Show container logs** — Просмотр логов.
12. **Change Web UI password** — Смена пароля панели.
13. **Update this script** — Самообновление из GitHub.

---

## 🔄 Обновление
Просто выберите пункт **13** в меню скрипта, или выполните:
```bash
amnezia --update  # (если установлено через install.sh)
```

## ⏱️ Рекомендуемые NTP Серверы (для Туркменистана)
Для стабильной работы AmneziaWG на Keenetic и других роутерах важна синхронизация времени. Вот самые быстрые серверы по результатам бенчмарка:
1. `uk.pool.ntp.org`
2. `time.nrc.ca`
3. `nl.pool.ntp.org`

## Требования
- Python 3.7+
- Зависимости (`paramiko`, `bcrypt`) устанавливаются автоматически при первом запуске.

> [!IMPORTANT]
> Для корректной работы AmneziaWG на роутерах Keenetic, убедитесь, что время на роутере синхронизировано, а параметры Stealth в конфиге совпадают с серверными.
