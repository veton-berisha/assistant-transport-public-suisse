document.getElementById('user-input').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Fonction pour générer un identifiant unique (par exemple, un UUID simple)
function generateSessionId() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        let r = Math.random() * 16 | 0,
            v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Générer un nouveau session_id à chaque chargement de page
let sessionId = generateSessionId();

async function sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value;
    if (!message) return;

    const chatBox = document.getElementById('chat-box');
    const spinner = document.getElementById('spinner');
    const sendButton = document.getElementById('send-button');

    // Afficher le spinner et désactiver les entrées utilisateur
    spinner.classList.remove('hidden');
    input.disabled = true;
    sendButton.disabled = true;
    sendButton.classList.add('cursor-not-allowed'); // Ajouter un curseur interdit

    const userMessage = document.createElement('div');
    userMessage.classList.add('message', 'user');
    userMessage.textContent = message;
    chatBox.appendChild(userMessage);
    input.value = '';
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        // Envoyer le message au serveur FastAPI
        const response = await fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: message, session_id: sessionId })
        });

        const data = await response.json();
        const botReply = document.createElement('div');
        botReply.classList.add('message', 'bot');
        
        botReply.innerHTML = marked.parse(data.gpt_answer);
        chatBox.appendChild(botReply);
        chatBox.scrollTop = chatBox.scrollHeight;
    } catch (error) {
        console.error('Error:', error);
        const botReply = document.createElement('div');
        botReply.classList.add('message', 'bot');
        botReply.textContent = "Une erreur s'est produite. Veuillez réessayer.";
        chatBox.appendChild(botReply);
        chatBox.scrollTop = chatBox.scrollHeight;
    } finally {
        // Cacher le spinner et réactiver les entrées utilisateur
        spinner.classList.add('hidden');
        input.disabled = false;
        sendButton.disabled = false;
        sendButton.classList.remove('cursor-not-allowed'); // Retirer le curseur interdit
        input.focus();
    }
}

// Activer les entrées utilisateur après le chargement de la page
window.onload = function() {
    document.getElementById('user-input').disabled = false;
    document.getElementById('send-button').disabled = false;
};

function toggleChat() {
    const chatWindow = document.getElementById('chat-window');
    chatWindow.style.display = chatWindow.style.display === 'none' || chatWindow.style.display === '' ? 'flex' : 'none';
}

async function fetchSuggestions() {
    const query = document.getElementById('search-input').value;

    if (query.length >= 3) {
        const response = await fetch(`/search_stops/?query=${encodeURIComponent(query)}`);
        const stops = await response.json();
        displaySuggestions(stops);
    } else {
        document.getElementById('suggestions').classList.add('hidden');
    }
}

function displaySuggestions(stops) {
    const suggestionsBox = document.getElementById('suggestions');
    suggestionsBox.innerHTML = '';

    if (stops.length === 0) {
        suggestionsBox.classList.add('hidden');
        return;
    }

    stops.forEach(stop => {
        const suggestionItem = document.createElement('div');
        suggestionItem.classList.add('suggestion-item');
        suggestionItem.innerHTML = `
            ${stop.stop_name} 
            <span class="copy-icon" onclick="copyToClipboard('${stop.stop_name}')">📋</span>
            <span class="copy-helper hidden">Copier cet arrêt</span>
            <span class="copied hidden">✓ Copié</span>`;
        suggestionItem.addEventListener('mouseenter', () => showHelper(suggestionItem));
        suggestionItem.addEventListener('mouseleave', () => hideHelper(suggestionItem));
        suggestionsBox.appendChild(suggestionItem);
    });

    suggestionsBox.classList.remove('hidden');
}

function showHelper(item) {
    item.querySelector('.copy-helper').classList.remove('hidden');
}

function hideHelper(item) {
    item.querySelector('.copy-helper').classList.add('hidden');
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        const item = document.querySelector(`.suggestion-item:contains('${text}')`);
        item.querySelector('.copy-icon').classList.add('hidden');
        item.querySelector('.copy-helper').classList.add('hidden');
        item.querySelector('.copied').classList.remove('hidden');
        setTimeout(() => {
            item.querySelector('.copied').classList.add('hidden');
            item.querySelector('.copy-icon').classList.remove('hidden');
        }, 3000);
    }).catch(err => {
        console.error('Erreur lors de la copie : ', err);
    });
}
