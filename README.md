🤖 Calorie Bot
A Telegram bot designed to help users track calories, meals, body information, and nutrition-related goals directly through Telegram.
🍎 Overview
Calorie Bot is the Telegram component of the Calorie platform.
It allows users to interact with the calorie tracking system directly from Telegram without needing to open a website.
The bot works as a separate backend/service and is designed to complement the Calorie Site.
✨ Features
• 🍽️ Meal tracking
• 🔢 Calorie calculation
• 📊 Nutrition reports
• ⚖️ Body fat and body information
• 🎯 Personal nutrition goals
• 🏆 Challenges
• 👤 User registration
• 💾 Database storage
• 🤖 Telegram-based interaction
🏗️ Calorie Platform
The complete project consists of two connected components:
                 🍎 CALORIE PLATFORM
                         │
            ┌────────────┴────────────┐
            │                         │
       🌐 CALORIE SITE          🤖 CALORIE BOT
            │                         │
         Website                  Telegram
            │                         │
            └────────────┬────────────┘
                         │
                  Nutrition System
🌐 Calorie Site
The web application provides the visual interface of the platform.
Repository:
https://github.com/muxidinov/Calorie_site
🤖 Calorie Bot
This repository contains the Telegram bot.
Repository:
https://github.com/muxidinov/Calorie_bot
🛠️ Technologies
• Python
• Aiogram
• SQLAlchemy
• SQLite
• AioSQLite
• Anthropic API
• HTTPX
• Python-dotenv
📦 Installation
Clone the repository:
git clone https://github.com/muxidinov/Calorie_bot.git
Enter the project directory:
cd Calorie_bot
Create a virtual environment:
python -m venv .venv
Activate it on Windows:
.venv\Scripts\activate
Install dependencies:
pip install -r requirements.txt
🔐 Environment Variables
Create a .env file:
BOT_TOKEN=your_telegram_bot_token
ANTHROPIC_API_KEY=your_anthropic_api_key
Never upload .env to GitHub.
The project should keep .env inside .gitignore.
▶️ Run the Bot
Start the bot with:
python main.py
The bot will start polling Telegram and wait for user interactions.
📁 Project Structure
Calorie_bot/
├── handlers/
│   ├── registration.py
│   ├── meals.py
│   ├── reports.py
│   ├── bodyfat.py
│   └── challenge.py
├── utils/
├── config.py
├── database.py
├── main.py
├── states.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
🔗 Related Project
🌐 Calorie Site
https://github.com/muxidinov/Calorie_site
The website and Telegram bot are separate repositories but are developed as components of the same Calorie platform.
🎯 Project Goal
The goal of Calorie Bot is to make calorie and nutrition tracking simple and accessible through Telegram.
The bot provides a conversational interface for recording meals, calculating calories, viewing reports, and working toward nutrition goals.
🔒 Security
Never commit:
.env
• Telegram Bot Tokens
• API Keys
• Passwords
• Database credentials
• Other private credentials
Use .env.example to document required environment variables without exposing real secrets.
📌 Related Repositories
• 🌐 Calorie Site: https://github.com/muxidinov/Calorie_site
• 🤖 Calorie Bot: This repository
📄 License
This project is currently for educational and development purposes.
