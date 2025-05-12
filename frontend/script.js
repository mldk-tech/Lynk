document.addEventListener('DOMContentLoaded', () => {
    const chatLog = document.getElementById('chat-log');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const resetButton = document.getElementById('reset-button');

    const BACKEND_URL = 'http://localhost:8000'; // Adjust if your backend runs elsewhere

    function addMessage(text, sender, isYaml = false) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender === 'user' ? 'user-message' : 'bot-message');
        
        if (isYaml) {
            const pre = document.createElement('pre');
            pre.classList.add('yaml-block');
            pre.textContent = text;
            messageDiv.appendChild(pre);
        } else {
            messageDiv.textContent = text;
        }
        chatLog.appendChild(messageDiv);
        chatLog.scrollTop = chatLog.scrollHeight; // Auto-scroll
    }

    async function sendMessage() {
        const messageText = userInput.value.trim();
        if (!messageText) return;

        addMessage(messageText, 'user');
        userInput.value = '';

        try {
            const response = await fetch(`${BACKEND_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: messageText })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: "Unknown error occurred" }));
                addMessage(`Error: ${errorData.detail || response.statusText}`, 'bot');
                return;
            }

            const data = await response.json();
            if (data.reply) {
                addMessage(data.reply, 'bot');
            }
            if (data.yaml) {
                addMessage(data.yaml, 'bot', true);
            }

        } catch (error) {
            console.error("Send message error:", error);
            addMessage(`Network error or backend is down. Check console.`, 'bot');
        }
    }

    async function resetConversation() {
        addMessage("Resetting conversation...", 'user');
        try {
            const response = await fetch(`${BACKEND_URL}/reset`, { method: 'POST' });
            if (!response.ok) {
                addMessage(`Error resetting: ${response.statusText}`, 'bot');
                return;
            }
            const data = await response.json();
            addMessage(data.reply, 'bot');

        } catch (error) {
            console.error("Reset error:", error);
            addMessage(`Network error during reset. Check console.`, 'bot');
        }
    }


    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });
    resetButton.addEventListener('click', resetConversation);

    // Initial greeting from bot (or handled by backend on first /chat call if state is new)
    addMessage("Hello! What type of Lynk feature would you like to create (Metric, First-Last, Formula, or Field)? Or type 'reset' to start over.", 'bot');
});