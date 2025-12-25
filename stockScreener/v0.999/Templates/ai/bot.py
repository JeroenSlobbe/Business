{% extends "base.html" %}

{% block content %}
<div class="content-box" id="ai">
    <h2>Ask the European based AI</h2>

    <!-- Chat Window -->
    <div id="chat-window" 
         style="border:1px solid #ccc; padding:10px; height:300px; 
                overflow-y:auto; background:#f9f9f9; margin-bottom:10px;">
        <!-- Messages will be appended here -->
    </div>

    <!-- Chat Input -->
    <form id="chat-form" style="display:flex; gap:10px;">
        <input type="text" id="user-input" 
               placeholder="Type your question..." 
               style="flex:1; padding:8px;" required>
        <button type="submit" style="padding:8px 16px;">Send</button>
    </form>
</div>

<script>
document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("chat-form");
    const input = document.getElementById("user-input");
    const chatWindow = document.getElementById("chat-window");

    function appendMessage(sender, text) {
        const msg = document.createElement("div");
        msg.innerHTML = `<strong>${sender}:</strong> ${text}`;
        msg.style.marginBottom = "8px";
        chatWindow.appendChild(msg);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    form.addEventListener("submit", async function (e) {
        e.preventDefault();
        const userText = input.value.trim();
        if (!userText) return;

        appendMessage("You", userText);
        input.value = "";

        try {
            const response = await fetch("/ai/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: userText })
            });

            const data = await response.json();
            appendMessage("AI", data.answer || "No response received.");
        } catch (err) {
            appendMessage("AI", "Error contacting the AI service.");
            console.error(err);
        }
    });
});
</script>
{% endblock %}
