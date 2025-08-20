from flask import Flask, render_template_string, request, jsonify
import sqlite3
import openai
import os

# Load OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

# Database file
DB_FILE = "chat_history.db"

# Initialize SQLite DB
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT,
            ai_response TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Health check endpoint for Render
@app.route("/healthz")
def healthz():
    return "OK", 200

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AI Chatbot</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        #chatbox { width: 100%; height: 400px; border: 1px solid #ccc; padding: 10px; overflow-y: scroll; }
        #user_input { width: 80%; padding: 10px; }
        #send { padding: 10px 20px; }
        .user { color: blue; }
        .ai { color: green; }
        .message { margin-bottom: 10px; }
    </style>
</head>
<body>
    <h2>AI Chatbot</h2>
    <div id="chatbox"></div>
    <input type="text" id="user_input" placeholder="Type your message..." autofocus>
    <button id="send">Send</button>

    <script>
        const chatbox = document.getElementById("chatbox");
        const userInput = document.getElementById("user_input");
        const sendButton = document.getElementById("send");

        function appendMessage(sender, text) {
            const div = document.createElement("div");
            div.className = "message " + sender;
            div.textContent = sender.toUpperCase() + ": " + text;
            chatbox.appendChild(div);
            chatbox.scrollTop = chatbox.scrollHeight;
        }

        sendButton.onclick = async () => {
            const message = userInput.value.trim();
            if(!message) return;
            appendMessage("user", message);
            userInput.value = "";

            const response = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message })
            });
            const data = await response.json();
            appendMessage("ai", data.reply);
        };

        userInput.addEventListener("keypress", function(e){
            if(e.key === "Enter") sendButton.click();
        });
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_msg}],
            temperature=0.7
        )
        ai_msg = response.choices[0].message.content.strip()
    except Exception as e:
        ai_msg = f"Error: {str(e)}"

    # Save to SQLite
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO chat (user_message, ai_response) VALUES (?, ?)", (user_msg, ai_msg))
    conn.commit()
    conn.close()

    return jsonify({"reply": ai_msg})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
