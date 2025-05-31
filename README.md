## JeskoVPN Bot

JeskoVPN is a Telegram bot (@JeskoVPN_bot) designed to provide a seamless experience for purchasing and managing Outline VPN keys. Built with a robust FastAPI backend and powered by Aiogram and Fluentogram for localization, it supports payments via YooKassa, CryptoBot, and Telegram Stars. The bot includes a comprehensive admin panel, a referral system, and automated contests, all deployed effortlessly using Docker Compose.

### 🌟 Features

#### VPN Key Purchase: 
Buy Outline VPN keys for Android, TV, Apple, Mac, Windows, and routers with monthly subscriptions.
#### Payment Options: 
Supports YooKassa, CryptoBot, and Telegram Stars for secure and flexible payments.
#### Referral System: 
Invite a friend and both receive 50 RUB credited to your account.
#### Contests & Giveaways: 
Participate in automated contests and giveaways for exciting rewards.
#### Admin Panel: 
Manage users, VPN keys, servers, and finances with detailed logs of all admin actions.
#### Multilingual Support: 
Available in Russian and English via Fluentogram.
#### Deployment: 
Easy setup with Docker Compose, including bot, backend, and PostgreSQL database.

### 🛠️ Tech Stack

#### Bot: 
Python, Aiogram, Fluentogram (see bot/requirements.txt for details).
#### Backend: 
FastAPI, SQLAlchemy, PostgreSQL (see backend/requirements.txt for details).
#### External APIs: 
YooKassa, CryptoBot, Outline VPN.
#### Deployment: 
Docker Compose with services for bot, backend, and database.

### 📂 Project Structure
```
├── admin_actions.log           # Log file for admin actions
├── backend                     # FastAPI backend
│   ├── alembic                 # Database migrations
│   ├── app                     # Backend application code, endpoints
│   ├── config.yaml             # Backend configuration
│   ├── Dockerfile              # Docker configuration for backend
│   ├── init_migrations.py      # Database migration initialization
│   ├── requirements.txt        # Backend dependencies
├── bot                         # Telegram bot
│   ├── config.example.yaml     # Example configuration file
│   ├── config.py               # Configuration loader
│   ├── config.yaml             # Bot configuration
│   ├── Dockerfile              # Docker configuration for bot
│   ├── handlers                # Bot command and event handlers
│   ├── keyboards               # Custom Telegram keyboards
│   ├── locales                 # Localization files (Russian, English)
│   ├── __main__.py             # Bot entry point
│   ├── middlewares             # Bot middlewares - admin/blacklist
│   ├── requirements.txt        # Bot dependencies
│   ├── services                # Bot services and utilities
│   ├── utils                   # Helper utilities
├── docker-compose.yml          # Docker Compose configuration
```
### 🚀 Getting Started
#### Prerequisites

Docker and Docker Compose installed.
Python 3.8+ for local development (optional).
API keys for YooKassa, CryptoBot, and Outline VPN.
Access to a running Outline VPN server.

#### Configuration

config.yaml: Contains sensitive variables such as API keys and database credentials. Ensure this file is not committed to version control.
Payment Services: Configure YooKassa, CryptoBot, and Telegram Stars API keys in backend/config.yaml.
Outline VPN: Provide the Outline VPN API endpoint and credentials in backend/config.yaml.

### 🛡️ Admin Panel
The admin panel within the bot provides powerful tools to manage the service:

#### User Management: 
Block or promote users to admin status.
#### VPN Key Management: 
Create, block, or view key history.
#### Server Management: 
Add, remove, or monitor Outline VPN servers.
#### Financial Analytics: 
View daily, monthly, or all-time financial statistics.
#### Contests & Giveaways: 
Set up automated contests for users.
#### Action Logging: 
All admin actions are logged in admin_actions.log for transparency.

### 🤝 Contributing
Contributions are welcome! To get started:

Fork the repository.
Create a new branch (git checkout -b feature/your-feature).
Commit your changes (git commit -m "Add your feature").
Push to the branch (git push origin feature/your-feature).
Open a Pull Request.

Please ensure your code follows the project's style and includes appropriate tests.

#### 📜 License
This project is licensed under the MIT License. See the LICENSE file for details.

For support or inquiries, reach out via Telegram: @okolo_boga.

