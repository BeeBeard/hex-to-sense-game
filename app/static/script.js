let gameId, playerId, ws;
let selectedCells = [];
let currentPlayerId;
let myPlayerId;
let creatorId;
let timerInterval;
let isGameStarted = false;
let rootPath = "/hex-to-sense";

window.onload = () => {
    console.log("Window loaded, checking URL");
    const url = new URL(window.location.href);
    const pathParts = url.pathname.split('/');
    if (pathParts[1] === 'join' && pathParts[2]) {
        console.log("Join URL detected, game_id:", pathParts[2]);
        document.getElementById("game-id").value = pathParts[2];
        showJoinForm();
    }
};

async function createGame() {
    console.log("Create Game button clicked");
    const playerName = document.getElementById("player-name").value || "";
    console.log("Creating game for:", playerName);
    try {
        const response = await fetch(rootPath + "/create", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ player_name: playerName })
        });
        console.log("Fetch response status:", response.status);
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP error! Status: ${response.status}, Message: ${errorText}`);
        }
        const data = await response.json();
        console.log("Create game response:", data);
        gameId = data.game_id;
        myPlayerId = data.player_id;
        creatorId = data.creator_id;
        console.log("Creator ID set:", creatorId, "My Player ID:", myPlayerId, "Match:", myPlayerId === creatorId);
        startWebSocket();
    } catch (error) {
        console.error("Error creating game:", error);
        document.getElementById("message").textContent = `Ошибка при создании игры: ${error.message}`;
    }
}

async function joinGame() {
    console.log("Join Game button clicked");
    const playerName = document.getElementById("player-name").value || "";
    const inputGameId = document.getElementById("game-id").value.trim();
    if (!inputGameId) {
        console.error("No game ID provided");
        document.getElementById("message").textContent = "Ошибка: введите код игры";
        return;
    }
    console.log("Joining game:", inputGameId, "as", playerName);
    try {
        const response = await fetch(rootPath + "/join", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ game_id: inputGameId, player_name: playerName })
        });
        console.log("Fetch response status:", response.status);
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP error! Status: ${response.status}, Message: ${errorText}`);
        }
        const data = await response.json();
        if (data.error) {
            console.error("Server error:", data.error);
            throw new Error(data.error);
        }
        console.log("Join game response:", data);
        gameId = data.game_id;
        myPlayerId = data.player_id;
        startWebSocket();
    } catch (error) {
        console.error("Error joining game:", error);
        document.getElementById("message").textContent = `Ошибка: ${error.message}`;
    }
}

function showJoinForm() {
    console.log("Show Join Form button clicked");
    document.getElementById("join-form").style.display = "block";
}

async function startGame() {
    console.log("Starting game, WebSocket state:", ws.readyState, "myPlayerId:", myPlayerId, "creatorId:", creatorId);
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: "start_game", player_id: myPlayerId }));
        document.getElementById("message").textContent = "Запуск игры...";
    } else {
        console.error("WebSocket is not open");
        document.getElementById("message").textContent = "Ошибка: соединение с сервером не установлено";
        reconnectWebSocket();
    }
}

function startWebSocket() {
    console.log("Starting WebSocket for game:", gameId, "player:", myPlayerId);
    document.getElementById("start-screen").style.display = "none";
    document.getElementById("game-screen").style.display = "flex";
    const wsUrl = `ws://${location.host}${rootPath}/ws/${gameId}/${myPlayerId}`;
    console.log("WebSocket URL:", wsUrl);
    ws = new WebSocket(wsUrl);
    ws.onmessage = handleMessage;
    ws.onopen = () => {
        console.log("WebSocket opened");
    };
    ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        document.getElementById("message").textContent = "Ошибка соединения с сервером";
    };
    ws.onclose = () => {
        console.log("WebSocket closed, attempting to reconnect");
        document.getElementById("message").textContent = "Соединение с сервером потеряно, пытаемся переподключиться...";
        reconnectWebSocket();
    };
    const shareButtonDiv = document.getElementById("share-button");
    shareButtonDiv.innerHTML = `
        <button onclick="shareGame()">Поделиться</button>
    `;
}

function reconnectWebSocket() {
    setTimeout(() => {
        if (!gameId || !myPlayerId) {
            console.error("Cannot reconnect: gameId or myPlayerId missing");
            document.getElementById("message").textContent = "Ошибка: невозможно переподключиться";
            return;
        }
        console.log("Reconnecting WebSocket for game:", gameId, "player:", myPlayerId);
        startWebSocket();
    }, 3000);
}

function shareGame() {
    console.log("Sharing game:", gameId);
    const shareUrl = `${window.location.origin}/join/${gameId}`;
    navigator.clipboard.writeText(shareUrl).then(() => {
        document.getElementById("message").textContent = "Ссылка скопирована!";
        setTimeout(() => document.getElementById("message").textContent = "", 2000);
    }).catch(err => {
        console.error("Error copying link:", err);
        document.getElementById("message").textContent = "Ошибка при копировании ссылки";
    });
}

function updateStartButton(playersCount) {
    const min_players = 2;
    const showStartButton = myPlayerId === creatorId && !isGameStarted && playersCount >= min_players;
    console.log("Updating start button:", showStartButton, "Conditions:", {
        isCreator: myPlayerId === creatorId,
        notStarted: !isGameStarted,
        enoughPlayers: playersCount >= min_players,
        playersCount,
        myPlayerId,
        creatorId
    });
    if (myPlayerId === creatorId) {
        if (!showStartButton) {
            let reason = "";
            if (isGameStarted) reason = "Игра уже началась";
            else if (playersCount < min_players) reason = "Недостаточно игроков";
            document.getElementById("message").textContent = reason ? `Кнопка "Начать игру" недоступна: ${reason}` : "";
        } else {
            document.getElementById("message").textContent = "Готово к началу игры";
        }
    } else {
        document.getElementById("message").textContent = isGameStarted ? "" : "Ожидание начала игры";
    }
    document.getElementById("start-game-button").style.display = showStartButton ? "block" : "none";
}

function showNotification(message) {
    const notification = document.getElementById("notification");
    notification.textContent = message;
    notification.classList.add("show");
    setTimeout(() => {
        notification.classList.remove("show");
        notification.textContent = "";
    }, 3000);
}

function handleMessage(event) {
    const data = JSON.parse(event.data);
    console.log("WebSocket message:", data);
    console.log("Current player name:", data.current_player_name);
    if (data.type === "init" || data.type === "update" || data.type === "start") {
        currentPlayerId = data.current_player;
        isGameStarted = data.is_started;
        console.log(`Current player: ${currentPlayerId}, My player: ${myPlayerId}, Game started: ${isGameStarted}, Players count: ${data.players.length}, Creator ID: ${creatorId}`);
        renderGrid(data.grid);
        renderPlayers(data.players);
        document.getElementById("word-input").style.display = currentPlayerId === myPlayerId && isGameStarted ? "block" : "none";
        updateStartButton(data.players.length);
        document.getElementById("current-player-info").textContent = isGameStarted && data.current_player_name ? `Сейчас ходит: ${data.current_player_name}` : isGameStarted ? "Игра началась" : "Ожидание начала игры";
        if (data.type === "start") {
            document.getElementById("message").textContent = data.message || "Игра началась!";
        } else if (data.type === "update") {
            selectedCells = [];
            document.getElementById("current-word").value = "";
            document.getElementById("message").textContent = data.message || data.result?.reason || "";
            if (data.result && data.result.word) {
                const message = data.result.valid ?
                    `Слово "${data.result.word}" принято!` :
                    `Слово "${data.result.word}" неверно: ${data.result.reason}`;
                showNotification(message);
            }
        }
        if (data.game_over) {
            clearInterval(timerInterval);
            document.getElementById("timer").style.display = "none";
            const winner = data.players.reduce((a, b) => a.score > b.score ? a : b);
            document.getElementById("message").textContent = `Игра окончена! Победитель: ${winner.name} с ${winner.score} очками`;
        } else {
            startTimer();
        }
    } else if (data.type === "click_update") {
        const cell = document.querySelector(`.hex[data-row="${data.row}"][data-col="${data.col}"]`);
        if (cell) {
            cell.querySelector(".clicks").textContent = data.clicks;
        }
    } else if (data.type === "info") {
        document.getElementById("message").textContent = data.message;
        renderPlayers(data.players || []);
        const playersCount = data.players ? data.players.length : document.getElementById("players-info").children.length;
        updateStartButton(playersCount);
    } else if (data.type === "error") {
        document.getElementById("message").textContent = `Ошибка: ${data.message}`;
        if (data.message.includes("Only the creator") || data.message.includes("two players")) {
            updateStartButton(data.players?.length || document.getElementById("players-info").children.length);
        }
    }
}

function renderGrid(grid) {
    const gridDiv = document.getElementById("grid");
    gridDiv.innerHTML = "";
    grid.forEach((row, r) => {
        const rowDiv = document.createElement("div");
        rowDiv.className = `row ${r % 2 === 0 ? "even" : "odd"}`;
        row.forEach((cell, c) => {
            const cellDiv = document.createElement("div");
            if (cell === null) {
                cellDiv.className = "hex hidden";
            } else {
                cellDiv.className = "hex";
                cellDiv.dataset.row = r;
                cellDiv.dataset.col = c;
                cellDiv.innerHTML = `<span class="weight">${cell.weight}</span><span class="letter">${cell.letter}</span><span class="clicks">${cell.clicks}</span>`;
                if (isGameStarted && currentPlayerId === myPlayerId) {
                    cellDiv.onclick = () => selectCell(r, c, cell.letter);
                    cellDiv.style.cursor = "pointer";
                } else {
                    cellDiv.style.cursor = "default";
                }
            }
            rowDiv.appendChild(cellDiv);
        });
        gridDiv.appendChild(rowDiv);
    });
    console.log("Grid rendered, clickable:", isGameStarted && currentPlayerId === myPlayerId);
}

function renderPlayers(players) {
    const playersDiv = document.getElementById("players-info");
    playersDiv.innerHTML = "";
    players.forEach(p => {
        const playerDiv = document.createElement("div");
        playerDiv.textContent = `${p.name}: ${p.score} очков, ${p.lives} жизней`;
        if (p.id === currentPlayerId) playerDiv.style.fontWeight = "bold";
        if (p.words && p.words.length > 0) {
            const wordsDiv = document.createElement("div");
            wordsDiv.textContent = `Слова: ${p.words.join(", ")}`;
            wordsDiv.style.fontSize = "14px";
            wordsDiv.style.color = "#B0BEC5";
            playerDiv.appendChild(wordsDiv);
        }
        playersDiv.appendChild(playerDiv);
    });
}

function selectCell(row, col, letter) {
    console.log(`Attempting to select cell: row=${row}, col=${col}, letter=${letter}, ws.readyState=${ws.readyState}, isGameStarted=${isGameStarted}, isMyTurn=${currentPlayerId === myPlayerId}`);
    if (!isGameStarted || currentPlayerId !== myPlayerId) {
        console.log("Cannot select cell: game not started or not my turn");
        document.getElementById("message").textContent = "Ошибка: игра не началась или не ваш ход";
        return;
    }
    if (selectedCells.length === 0 || isNeighbor(selectedCells[selectedCells.length - 1], [row, col])) {
        selectedCells.push([row, col]);
        const wordInput = document.getElementById("current-word");
        wordInput.value += letter;
        document.querySelector(`.hex[data-row="${row}"][data-col="${col}"]`).classList.add("selected");
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                action: "increment_click",
                row: row,
                col: col
            }));
            console.log(`Sent increment_click: row=${row}, col=${col}, word=${wordInput.value}`);
        } else {
            console.log("WebSocket not open, queuing click");
            document.getElementById("message").textContent = "Соединение с сервером потеряно, пытаемся переподключиться...";
            reconnectWebSocket();
        }
    } else {
        console.log("Cannot select cell: not a neighbor");
        document.getElementById("message").textContent = "Ошибка: выберите соседнюю ячейку";
    }
}

function isNeighbor(prev, curr) {
    const [pr, pc] = prev;
    const [cr, cc] = curr;
    let directions;
    if (pr % 2 === 0) {
        directions = [[-1, 0], [1, 0], [0, -1], [0, 1], [-1, -1], [1, -1]];
    } else {
        directions = [[-1, 0], [1, 0], [0, -1], [0, 1], [-1, 1], [1, 1]];
    }
    const isNeighbor = directions.some(([dr, dc]) => pr + dr === cr && pc + dc === cc);
    console.log(`Checking neighbor: prev=(${pr},${pc}), curr=(${cr},${cc}), isNeighbor=${isNeighbor}`);
    return isNeighbor;
}

function submitWord() {
    const word = document.getElementById("current-word").value;
    console.log(`Attempting to submit word: ${word}, ws.readyState=${ws.readyState}, isGameStarted=${isGameStarted}, isMyTurn=${currentPlayerId === myPlayerId}`);
    if (word && isGameStarted && currentPlayerId === myPlayerId) {
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                action: "submit_word",
                word: word,
                path: selectedCells
            }));
            clearInterval(timerInterval);
            document.getElementById("timer").style.display = "none";
            console.log("Word submitted:", word);
        } else {
            console.log("WebSocket not open, cannot submit word");
            document.getElementById("message").textContent = "Соединение с сервером потеряно, пытаемся переподключиться...";
            reconnectWebSocket();
        }
    } else {
        console.log("Cannot submit word: no word, game not started, or not my turn");
        document.getElementById("message").textContent = "Ошибка: нет слова, игра не началась или не ваш ход";
    }
}

function startTimer() {
    const timerDiv = document.getElementById("timer");
    timerDiv.style.display = currentPlayerId === myPlayerId && isGameStarted ? "block" : "none";
    clearInterval(timerInterval);
    if (currentPlayerId === myPlayerId && isGameStarted) {
        let time = 30;
        timerDiv.textContent = time;
        document.getElementById("message").textContent = "Ваш ход!";
        timerInterval = setInterval(() => {
            time--;
            timerDiv.textContent = time;
            if (time <= 0) {
                clearInterval(timerInterval);
                timerDiv.style.display = "none";
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ action: "timeout" }));
                }
            }
        }, 1000);
    }
}