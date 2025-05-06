from fastapi import APIRouter
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

from app.storage import GAMES

r_ws = APIRouter(tags=['WEB SOCKET'])


@r_ws.websocket("/ws/{game_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str, player_id: str):
    await websocket.accept()
    logger.info(f"WebSocket connected: game_id={game_id}, player_id={player_id}")
    game = GAMES.get(game_id)
    if not game:
        logger.error(f"WebSocket error: Game {game_id} not found")
        await websocket.send_json({"type": "error", "message": "Game not found"})
        await websocket.close()
        return

    player = next((p for p in game.players if p.id == player_id), None)
    if not player:
        logger.error(f"WebSocket error: Player {player_id} not found in game {game_id}")
        await websocket.send_json({"type": "error", "message": f"Player {player_id} not found"})
        await websocket.close()
        return

    player.websocket = websocket
    try:
        await game.broadcast({
            "type": "init",
            "grid": game.grid,
            "players": [{"id": p.id, "name": p.name, "score": p.score, "lives": p.lives, "words": p.words} for p in game.players],
            "current_player": game.players[game.current_player_index].id if game.is_started and game.players else None,
            "current_player_name": game.players[game.current_player_index].name if game.is_started and game.players else None,
            "is_started": game.is_started
        })
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            logger.info(f"Received WebSocket action: {action}, from player_id={player_id}, game_id={game_id}")
            if action == "start_game":
                received_player_id = data.get("player_id", player_id)
                logger.info(f"Processing start_game: received_player_id={received_player_id}, websocket_player_id={player_id}")
                result = game.start_game(received_player_id)
                if result.get("error"):
                    logger.warning(f"Start game failed: {result['error']}")
                    await websocket.send_json({"type": "error", "message": result["error"]})
                else:
                    game.is_started = True
                    logger.info(f"Game started successfully: game_id={game_id}")
                    await game.broadcast({
                        "type": "start",
                        "grid": game.grid,
                        "players": [{"id": p.id, "name": p.name, "score": p.score, "lives": p.lives, "words": p.words} for p in game.players],
                        "current_player": game.players[game.current_player_index].id if game.players else None,
                        "current_player_name": game.players[game.current_player_index].name if game.is_started and game.players else None,
                        "is_started": True,
                        "message": "Игра началась!"
                    })
            elif action == "submit_word":
                word = data.get("word")
                path = data.get("path")
                result = game.submit_word(player_id, word, path)
                game.next_turn()
                await game.broadcast({
                    "type": "update",
                    "result": result,
                    "grid": game.grid,
                    "players": [{"id": p.id, "name": p.name, "score": p.score, "lives": p.lives, "words": p.words} for p in game.players],
                    "current_player": game.players[game.current_player_index].id if game.players else None,
                    "current_player_name": game.players[game.current_player_index].name if game.is_started and game.players else None,
                    "is_started": True,
                    "message": f"Ход игрока {game.players[game.current_player_index].name}" if game.players else "Игра продолжается"
                })
            elif action == "increment_click":
                row = data.get("row")
                col = data.get("col")
                result = game.increment_click(player_id, row, col)
                if result["valid"]:
                    await game.broadcast({
                        "type": "click_update",
                        "grid": game.grid,
                        "row": row,
                        "col": col,
                        "clicks": game.grid[row][col]["clicks"]
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": result["reason"]
                    })
            elif action == "timeout":
                if game.players and game.players[game.current_player_index].id == player_id:
                    game.players[game.current_player_index].lives -= 1
                    game.next_turn()
                    await game.broadcast({
                        "type": "update",
                        "result": {"valid": False, "reason": "Time out"},
                        "grid": game.grid,
                        "players": [{"id": p.id, "name": p.name, "score": p.score, "lives": p.lives, "words": p.words} for p in game.players],
                        "current_player": game.players[game.current_player_index].id if game.players else None,
                        "current_player_name": game.players[game.current_player_index].name if game.is_started and game.players else None,
                        "is_started": True,
                        "message": f"Ход игрока {game.players[game.current_player_index].name}" if game.players else "Игра продолжается"
                    })
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: player_id={player_id}, game_id={game_id}")
        disconnected_player = game.remove_player(player_id)
        if disconnected_player:
            message = f"Игрок {disconnected_player.name} покинул игру"
            if not game.players:
                logger.info(f"No players left in game {game_id}, removing game")
                del GAMES[game_id]
                return
            if game.is_started and game.players and game.current_player_index < len(game.players) and game.players[game.current_player_index].id == player_id:
                game.next_turn()
                await game.broadcast({
                    "type": "update",
                    "grid": game.grid,
                    "players": [{"id": p.id, "name": p.name, "score": p.score, "lives": p.lives, "words": p.words} for p in game.players],
                    "current_player": game.players[game.current_player_index].id if game.players else None,
                    "current_player_name": game.players[game.current_player_index].name if game.is_started and game.players else None,
                    "is_started": True,
                    "message": f"{message}. Ход игрока {game.players[game.current_player_index].name}" if game.players else message
                })
            else:
                await game.broadcast({
                    "type": "info",
                    "message": message,
                    "players": [{"id": p.id, "name": p.name, "score": p.score, "lives": p.lives, "words": p.words} for p in game.players]
                })
            if len(game.players) == 1 and game.is_started:
                await game.broadcast({
                    "type": "info",
                    "message": "Вы остались один. Продолжить игру?",
                    "players": [{"id": p.id, "name": p.name, "score": p.score, "lives": p.lives, "words": p.words} for p in game.players]
                })
    except Exception as e:
        logger.error(f"WebSocket error: game_id={game_id}, player_id={player_id}, error={e}")
        await websocket.send_json({"type": "error", "message": f"Server error: {str(e)}"})
        await websocket.close()

if __name__ == "__main__":
    pass
