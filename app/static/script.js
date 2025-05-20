console.log("script.js loaded");

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
        const gameIdInput = document.getElementById("game-id");
        if (gameIdInput) {
            gameIdInput.value = pathParts[2];
        } else {
            console.error("game-id input not found");
        }
        showJoinForm();
        const playerNameInput = document.getElementById("player-name-join");
        if (playerNameInput) {
            console.log("player-name-join found, focusing");
            playerNameInput.focus();
            playerNameInput.addEventListener("keypress", (e) => {
                if (e.key === "Enter" && playerNameInput.value.trim().length >= 2) {
                    console.log("Enter pressed, calling joinGame with name:", playerNameInput.value);
                    joinGame();
                }
            });
        } else {
            console.error("player-name-join input not found");
            document.getElementById("message").textContent = "Ошибка: поле имени не найдено";
        }
    }
};

function showNotification(message) {
    console.log("Showing notification:", message);
    const notification = document.getElementById("notification");
    notification.textContent = message;
    notification.classList.add("show");
    setTimeout(() => {
        notification.classList.remove("show");
        notification.textContent = "";
    }, 3000);
}

async function createGame() {
    console.log("Create Game button clicked");
    const playerNameElem = document.getElementById("player-name")
    const roomNameElem = document.getElementById("room-name");
    const timerCountElem = document.getElementById("timer-count");
    const livesCountElem = document.getElementById("lives-count");

    const playerName = playerNameElem.value;
    const roomName = roomNameElem.value;
    const timerCount = timerCountElem.value;
    const livesCount = livesCountElem.value;

    if (!playerName || playerName.length < 2) {
        showNotification("'Имя' должно быть более 2х символов", true);
        playerNameElem.classList.add("shake");
        playerNameElem.focus();
        document.getElementById("message").textContent = "'Имя' должно быть более 2х символов";
        setTimeout(() => playerNameElem.classList.remove("shake"), 300);
        return;
    }

    if (!roomName || roomName.length < 2) {
        showNotification("'Название комнаты' должно быть более 2х символов", true);
        roomNameElem.classList.add("shake");
        roomNameElem.focus();
        document.getElementById("message").textContent = "'Название комнаты' должно быть более 2х символов";
        setTimeout(() => roomNameElem.classList.remove("shake"), 300);
        return;
    }

    if (!timerCount || Number(timerCount) < 10 || Number(timerCount) > 300 ) {
        showNotification("Время на принятие решения должно быть от 10 до 300 секунд", true);
        timerCountElem.classList.add("shake");
        timerCountElem.focus();
        document.getElementById("message").textContent = "Время на принятие решения должно быть от 10 до 300 секунд";
        setTimeout(() => timerCountElem.classList.remove("shake"), 300);
        return;
    }


    console.log("Creating game for:", playerName);
    try {
        const response = await fetch(rootPath + "/create", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ player_name: playerName, room_name: roomName, timer: timerCount, lives: livesCount})
        });
        console.log("Fetch response status:", response.status);
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP error! Status: ${response.status}, Message: ${errorText}`);
        }
        const data = await response.json();

        if (data.error) {
            document.getElementById("message").textContent = "Такое название комнаты уже существует";
            return
        }
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

    const playerNameInput = document.getElementById("player-name-join");
    const gameIdInput = document.getElementById("game-id");

    if (!playerNameInput || !gameIdInput) {
        console.error("Input elements not found", { playerNameInput, gameIdInput });
        document.getElementById("message").textContent = "Ошибка: элементы формы не найдены";
        return;
    }

    const playerName = playerNameInput.value.trim();
    const inputGameId = gameIdInput.value.trim();
    console.log("joinGame inputs:", { playerName, inputGameId });

    if (!inputGameId) {
        console.error("No game ID provided");
        document.getElementById("message").textContent = "Ошибка: введите код игры";
        gameIdInput.focus();
        return;
    }

    if (!playerName || playerName.length < 2) {
        console.error("No valid player name provided", { playerName, length: playerName.length });
        document.getElementById("message").textContent = "Ошибка: введите имя (минимум 2 символа)";
        playerNameInput.focus();
        return;
    }

    console.log("Attempting to join game:", inputGameId, "as", playerName);
    document.getElementById("message").textContent = "Присоединение к игре...";

    try {
        const response = await fetch(rootPath + "/join", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ game_id: inputGameId, player_name: playerName })
        });
        console.log("Fetch response status:", response.status, "Response:", response);

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
        creatorId = data.creator_id;
        startWebSocket();

    } catch (error) {
        console.error("Error joining game:", error);
        document.getElementById("message").textContent = `Ошибка: ${error.message}`;
    }
}

function showJoinForm() {
    console.log("Show Join Form");
    const mainForm = document.getElementById("main-form");
    const createForm = document.getElementById("create-form");
    const joinForm = document.getElementById("join-form");
    const roomsForm = document.getElementById("rooms-form");
    const message = document.getElementById("message");
    if (!joinForm) {
        console.error("join-form not found");
        message.textContent = "Ошибка: форма присоединения не найдена";
        return;
    }

    mainForm.style.display = "none";
    createForm.style.display = "none";
    joinForm.style.display = "flex";
    roomsForm.style.display = "none";
    message.textContent = "";
}

function showCreateForm() {
    console.log("Show Join Form");
    const mainForm = document.getElementById("main-form");
    const createForm = document.getElementById("create-form");
    const joinForm = document.getElementById("join-form");
    const roomsForm = document.getElementById("rooms-form");
    const message = document.getElementById("message");

    if (!joinForm) {
        console.error("join-form not found");
        message.textContent = "Ошибка: форма присоединения не найдена";
        return;
    }
    mainForm.style.display = "none";
    createForm.style.display = "flex";
    joinForm.style.display = "none";
    roomsForm.style.display = "none";
    message.textContent = "";
}


function showMainMenu() {
    console.log("Show Main Menu button clicked");
    document.getElementById("main-form").style.display = "flex";
    document.getElementById("create-form").style.display = "none";
    document.getElementById("join-form").style.display = "none";
    document.getElementById("rooms-form").style.display = "none";
    document.getElementById("message").textContent = "";
}

async function showRoomsForm() {
    console.log("Show Rooms Form button clicked");
    document.getElementById("create-form").style.display = "none";
    document.getElementById("join-form").style.display = "none";
    document.getElementById("rooms-form").style.display = "flex";
    document.getElementById("message").textContent = "";

    try {
        const response = await fetch(rootPath + "/api/rooms");
        console.log("Fetch rooms response status:", response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        console.log("Rooms data:", data);
        const roomsList = document.getElementById("rooms-list");
        roomsList.innerHTML = "";
        if (data.rooms.length === 0) {
            roomsList.innerHTML = "<p>Нет доступных комнат</p>";
        } else {
            data.rooms.forEach(room => {
                const button = document.createElement("button");
//                const short_id = room.game_id.substr(room.game_id.length - 12);
                const room_name = room.room_name;
                const player_num = '👾'.repeat(room.players)

                button.textContent = `${room_name} [${player_num}]`; // Название комнаты и количество игроков
                button.onclick = () => joinRoom(room.game_id);
                roomsList.appendChild(button);
            });
        }
    } catch (error) {
        console.error("Error fetching rooms:", error);
        document.getElementById("message").textContent = `Ошибка при загрузке комнат: ${error.message}`;
    }
}

async function joinRoom(gameId) {
    console.log("Join Room button clicked, game_id:", gameId);
    document.getElementById("game-id").value = gameId;
    showJoinForm();
    const playerNameInput = document.getElementById("player-name-join");
    if (playerNameInput) {
        playerNameInput.focus();
    }
}

async function startGame() {
    console.log("Start Game button clicked, WebSocket state:", ws?.readyState, "myPlayerId:", myPlayerId, "creatorId:", creatorId);
    if (ws && ws.readyState === WebSocket.OPEN) {
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
//    const shareButtonDiv = document.getElementById("share-button");
//    shareButtonDiv.innerHTML = `
//        <button onclick="shareGame()">Поделиться</button>
//        <a href="${rootPath}/join/${gameId}" target="_blank">Присоединиться к игре</a>
//    `;
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
    console.log("Share Game button clicked");
    const shareUrl = `${window.location.origin}${rootPath}/join/${gameId}`;
    console.log("Share URL:", shareUrl);
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
            else if (playersCount < min_players) reason = "Ожидаем игроков";
            document.getElementById("message").textContent = reason ? `${reason}` : "";
        } else {
            document.getElementById("message").textContent = "Готово к началу игры";
        }
    } else {
        document.getElementById("message").textContent = isGameStarted ? "" : "Ожидание начала игры";
    }
    document.getElementById("start-game-button").style.display = showStartButton ? "block" : "none";
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
        renderStats(data.players);
//        document.getElementById("timer-word").style.display = currentPlayerId === myPlayerId && isGameStarted ? "flex" : "none";
        document.getElementById("timer-word").style.display = isGameStarted ? "flex" : "none";

        document.getElementById("word-buttons").style.display = currentPlayerId === myPlayerId && isGameStarted ? "flex" : "none";
        document.getElementById("toggle-buttons").style.display = isGameStarted ? "flex" : "none";
        updateStartButton(data.players.length);

        if (data.type === "start") {
            document.getElementById("message").textContent = data.message || "Игра началась!";

        } else if (data.type === "update") {
            selectedCells = [];
            document.getElementById("current-word").value = "";
            document.getElementById("message").textContent = data.message || data.result?.reason || "";
            if (data.result && data.result.word) {
                console.log("Backend response:", JSON.stringify(data.result));
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
            startTimer(data.timer);
        }

    } else if (data.type === "click_update") {
        const cell = document.querySelector(`.hex[data-row="${data.row}"][data-col="${data.col}"]`);
        if (cell) {
            cell.querySelector(".clicks").textContent = data.clicks;
        }

    } else if (data.type === "info") {
        document.getElementById("message").textContent = data.message;
        renderPlayers(data.players || []);
        renderStats(data.players || []);
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
    console.log("Rendering grid", grid);
    const gridDiv = document.getElementById("grid");
    gridDiv.innerHTML = "";
    grid.forEach((row, r) => {
        const rowDiv = document.createElement("div");
        rowDiv.className = `row ${r % 2 === 0 ? "even" : "odd"}`;
        row.forEach((cell, c) => {
            const cellDiv = document.createElement("div");
            if (cell != null) {
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
    console.log("Rendering players:", players);
    const playersDiv = document.getElementById("players-info");
    playersDiv.innerHTML = "";
    players.forEach(p => {
        const playerDiv = document.createElement("div");
        const nameHeader = document.createElement("h2");

             nameHeader.innerHTML = `
            <span>${p.name}</span>
            <span>✨ ${p.score}</span><br>
            <span>${'❤️'.repeat(p.lives)}</span>
        `;

//        nameHeader.textContent = `${p.name} (${p.score} очков, ${p.lives} жизней)`;
        playerDiv.appendChild(nameHeader);

        if (p.words && p.words.length > 0) {
            const wordsDiv = document.createElement("div");
            wordsDiv.textContent = `Слова: ${p.words.join(", ")}`;
            playerDiv.appendChild(wordsDiv);
        }
        if (p.user_id === currentPlayerId) {
            playerDiv.style.border = "2px solid #2196F3";
        }
        playersDiv.appendChild(playerDiv);
    });
}

function renderStats(players) {
    console.log("Rendering stats:", players);
    const statsLeft = document.getElementById("stats-left");
    const statsRight = document.getElementById("stats-right");
    statsLeft.innerHTML = "";
    statsRight.innerHTML = "";

    if (!players || players.length === 0) return;

    const leftCount = Math.ceil(players.length / 2);
    const leftPlayers = players.slice(0, leftCount);
    const rightPlayers = players.slice(leftCount);

    leftPlayers.forEach(p => {
        const statDiv = document.createElement("div");
        statDiv.className = `stat ${p.user_id === currentPlayerId ? "current" : ""}`;
        statDiv.innerHTML = `
            <span><b>${p.name}</b></span>
            <span>✨ ${p.score}</span>
            <span>${'❤️'.repeat(p.lives)}</span>
        `;
        statsLeft.appendChild(statDiv);

        if (p.user_id === currentPlayerId) {
            statDiv.classList.add("shake");
            statDiv.focus();
            setTimeout(() => statDiv.classList.remove("shake"), 300);
        }

    });

    rightPlayers.forEach(p => {
        const statDiv = document.createElement("div");
        statDiv.className = `stat ${p.user_id === currentPlayerId ? "current" : ""}`;
        statDiv.innerHTML = `
            <span><b>${p.name}</b></span>
            <span>✨ ${p.score}</span>
            <span>${'❤️'.repeat(p.lives)}</span>
        `;
        statsRight.appendChild(statDiv);

        if (p.user_id === currentPlayerId) {
            statDiv.classList.add("shake");
            statDiv.focus();
            setTimeout(() => statDiv.classList.remove("shake"), 300);
        }
    });
}

function selectCell(row, col, letter) {
    console.log(`Attempting to select cell: row=${row}, col=${col}, letter=${letter}, ws.readyState=${ws?.readyState}, isGameStarted=${isGameStarted}, isMyTurn=${currentPlayerId === myPlayerId}`);
    if (!isGameStarted || currentPlayerId !== myPlayerId) {
        console.log("Cannot select cell: game not started or not my turn");
        document.getElementById("message").textContent = "Ошибка: игра не началась или не ваш ход";
        return;
    }

    const wordInput = document.getElementById("current-word");
    const currentCell = [row, col];
    const isAlreadySelected = selectedCells.some(([r, c]) => r === row && c === col);

    if (isAlreadySelected || selectedCells.length === 0 || isNeighbor(selectedCells[selectedCells.length - 1], currentCell)) {
        selectedCells.push([row, col]);
        wordInput.value += letter;

//        document.querySelector(`.hex[data-row="${row}"][data-col="${col}"]`)

        const hex = document.querySelector(`.hex[data-row="${row}"][data-col="${col}"]`);
        hex.classList.add("selected");
        const clicksSpan = hex.querySelector('.clicks');
        clicksSpan.textContent = parseInt(clicksSpan.textContent) + 1;


        if (ws && ws.readyState === WebSocket.OPEN) {
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
        directions = [[0, -1], [1, 0], [0, 1], [1, -1], [-1, -1], [-1, 0]];
    } else {
        directions = [[-1, 1], [1, 0], [1, 1], [0, 1], [-1, 0], [0, -1]];
    }
    const isNeighbor = directions.some(([dr, dc]) => pr + dr === cr && pc + dc === cc);
    console.log(`Checking neighbor: prev=(${pr},${pc}), curr=(${cr},${cc}), isNeighbor=${isNeighbor}`);
    return isNeighbor;
}

function submitWord() {
    console.log("Submit Word button clicked");
    const word = document.getElementById("current-word").value.toLowerCase();
    console.log(`Submitting word: ${word}, Path: ${JSON.stringify(selectedCells)}, ws.readyState=${ws?.readyState}, isGameStarted=${isGameStarted}, isMyTurn=${currentPlayerId === myPlayerId}`);
    if (word && isGameStarted && currentPlayerId === myPlayerId) {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                action: "submit_word",
                word: word,
                path: selectedCells
            }));
            clearInterval(timerInterval);
            document.getElementById("timer").style.display = "none";
            console.log("Word submitted:", word, "Path:", selectedCells);
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

function clearWord() {
    console.log("Clear Word button clicked");
    const wordInput = document.getElementById("current-word");
    wordInput.value = "";
    selectedCells.forEach(([row, col]) => {
        const cell = document.querySelector(`.hex[data-row="${row}"][data-col="${col}"]`);
        if (cell) {
            cell.classList.remove("selected");


//            cell.querySelectorAll('.clicks').forEach(element => {
//              // Преобразуем textContent в число и вычитаем 1
//              let currentValue = parseInt(element.textContent);
//              if (!isNaN(currentValue)) { // Проверяем, является ли содержимое числом
//                element.textContent = currentValue - 1;
//              }
//            });
        }
    });
    selectedCells = [];
    console.log("Word and selection cleared");
}

function startTimer(_time) {
    console.log("Starting timer");
    const timerDiv = document.getElementById("timer");
    timerDiv.style.display = currentPlayerId === myPlayerId && isGameStarted ? "block" : "none";
    clearInterval(timerInterval);
    if (currentPlayerId === myPlayerId && isGameStarted) {
        timerDiv.textContent = _time;
        document.getElementById("message").textContent = "Ваш ход!";
        timerInterval = setInterval(() => {
            _time--;
            timerDiv.textContent = _time;
            if (_time <= 0) {
                clearInterval(timerInterval);
                timerDiv.style.display = "none";
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ action: "timeout" }));
                }
            }
        }, 1000);
    }
}

function togglePlayersInfo() {
    console.log("Toggle Players button clicked");
    const playersPanel = document.getElementById("players-panel");
    const toggleButton = document.getElementById("toggle-players");
    if (playersPanel.classList.contains("show")) {
        playersPanel.classList.remove("show");
        toggleButton.textContent = "Показать статистику";
    } else {
        playersPanel.classList.add("show");
        toggleButton.textContent = "Скрыть статистику";
    }
}