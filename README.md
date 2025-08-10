# Port Change Watcher

Port Change Watcher is a Python script that scans open ports on a target host and sends notifications about port changes to your own Telegram account using **your own Telegram bot**.

---

## How to Set Up and Use

### 1. Create Your Telegram Bot and Get Token

1. Open Telegram and chat with [@BotFather](https://t.me/BotFather).  
2. Send `/newbot` and follow instructions to create your bot.  
3. Copy the **bot token** (a string like `123456789:ABCDEF...`).

### 2. Get Your Telegram Chat ID

1. Start your bot by sending any message to it in Telegram.  
2. Open this URL( https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates ) in your browser (replace `<YOUR_BOT_TOKEN>` with your bot token)
3. 3. Look for `"chat":{"id":123456789,...}` in the JSON response.  
   That number is your **chat ID**.

---

### 3. Insert Your Token and Chat ID in the Script

Open `port_change_watcher.py` in a text editor and replace these lines:

  port_change_watcher.py:
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE" 

4.INSTALLATION🚀
wget https://raw.githubusercontent.com/arsenii12012/PortChangeWatcher/refs/heads/main/port_change_watcher.py

5. Install Required Python Package:
 Make sure you have Python 3 installed, then install the requests library:

pip install requests

6. Run the Script

   python3 port_change_watcher.py

📌 Usage
Scan example.com ports 22, 80, 443 every 60 seconds:

python3 port_change_watcher.py example.com --ports 22,80,443 --interval 60

Scan ports 1-1024 with Telegram notifications (token and chat ID are set inside the script):

python3 port_change_watcher.py example.com --ports 1-1024 --interval 60
