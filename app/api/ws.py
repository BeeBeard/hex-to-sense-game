import pprint
import traceback

from fastapi import APIRouter
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger
from app.models.models import WsBroadcast, WsClickBroadcast, SubmitWordResult, WsInfoBroadcast
from app.storage import GM

r_ws = APIRouter(tags=['WEB SOCKET'])

@r_ws.get("/test")
async def test():
    return {"message": "ok"}

@r_ws.websocket("/ws/{game_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str, player_id: str):
    await websocket.accept()
    logger.info(f"WebSocket connected: game_id={game_id}, player_id={player_id}")
    game = GM.games.get(game_id)
    if not game:
        logger.error(f"WebSocket error: Game {game_id} not found")
        await websocket.send_json({"type": "error", "message": "Game not found"})
        await websocket.close()
        return

    player = next((p for p in game.players if p.player_id == player_id), None)
    if not player:
        logger.error(f"WebSocket error: Player {player_id} not found in game {game_id}")
        await websocket.send_json({"type": "error", "message": f"Player {player_id} not found"})
        await websocket.close()
        return

    player.websocket = websocket
    try:
        # await game.broadcast({
        #     "type": "init",
        #     "grid": game.grid,
        #     "players": [{"id": p.player_id, "name": p.name, "score": p.score, "lives": p.lives, "words": p.words} for p in game.players],
        #     "current_player": game.players[game.current_player_index].player_id if game.is_started and game.players else None,
        #     "current_player_name": game.players[game.current_player_index].name if game.is_started and game.players else None,
        #     "is_started": game.is_started
        # })

        wa_broadcast = WsBroadcast(
            type="init",
            grid=game.grid,
            players=[player.get_data() for player in game.players],
            current_player=game.players[game.current_player_index].player_id if game.is_started and game.players else "",
            current_player_name=game.players[game.current_player_index].name if game.is_started and game.players else "",
            is_started=game.is_started
        )

        pprint.pprint(wa_broadcast)
        await game.broadcast(wa_broadcast.model_dump())

        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            logger.info(f"Received WebSocket action: {action}, from player_id={player_id}, game_id={game_id}")

            if action == "start_game":
                received_player_id = data.get("player_id", player_id)
                logger.info(f"Processing start_game: received_player_id={received_player_id}, websocket_player_id={player_id}")
                result = game.start_game(received_player_id)

                if not result.success:
                    logger.warning(result.error)
                    await websocket.send_json({"type": "error", "message": result.message})

                else:
                    game.is_started = True
                    # logger.info(f"Game started successfully: game_id={game_id}")
                    # await game.broadcast({
                    #     "type": "start",
                    #     "grid": game.grid,
                    #     "players": [{"id": p.player_id, "name": p.name, "score": p.score, "lives": p.lives, "words": p.words} for p in game.players],
                    #     "current_player": game.players[game.current_player_index].player_id if game.players else None,
                    #     "current_player_name": game.players[game.current_player_index].name if game.is_started and game.players else None,
                    #     "is_started": True,
                    #     "message": "Игра началась!"
                    # })

                    wa_broadcast = WsBroadcast(
                        type="start",
                        grid=game.grid,
                        players=[player.get_data() for player in game.players],
                        current_player=game.players[game.current_player_index].player_id if game.players else "",
                        current_player_name=game.players[game.current_player_index].name if game.is_started and game.players else "",
                        is_started=True,
                        message=f"Игра началась!"
                    )

                    await game.broadcast(wa_broadcast.model_dump())



            elif action == "submit_word":
                word = data.get("word")
                path = data.get("path")
                result = game.submit_word(player_id, word, path)
                game.next_turn()
                # await game.broadcast({
                #     "type": "update",
                #     "result": result,
                #     "grid": game.grid,
                #     "players": [{"id": p.player_id, "name": p.name, "score": p.score, "lives": p.lives, "words": p.words} for p in game.players],
                #     "current_player": game.players[game.current_player_index].player_id if game.players else None,
                #     "current_player_name": game.players[game.current_player_index].name if game.is_started and game.players else None,
                #     "is_started": True,
                #     "message": f"Ход игрока {game.players[game.current_player_index].name}" if game.players else "Игра продолжается"
                # })

                wa_broadcast = WsBroadcast(
                    type="update",
                    result=result,
                    grid=game.grid,
                    players=[player.get_data() for player in game.players],
                    current_player=game.players[game.current_player_index].player_id if game.players else "",
                    current_player_name=game.players[game.current_player_index].name if game.is_started and game.players else "",
                    is_started=True,
                    message=f"Ход игрока {game.players[game.current_player_index].name}" if game.players else "Игра продолжается"
                )

                await game.broadcast(wa_broadcast.model_dump())


            elif action == "increment_click":
                row = data.get("row")
                col = data.get("col")
                result = game.increment_click(player_id, row, col)
                if not result.success:
                    # await game.broadcast({
                    #     "type": "click_update",
                    #     "grid": game.grid,
                    #     "row": row,
                    #     "col": col,
                    #     "clicks": game.grid[row][col].clicks
                    # })

                    wa_broadcast = WsClickBroadcast(
                        type="click_update",
                        grid=game.grid,
                        row=row,
                        col=col,
                        clicks=game.grid[row][col].clicks,
                        message=f"Игрок нажал на ячейку"
                    )

                    await game.broadcast(wa_broadcast.model_dump())


                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": result.message
                    })

            elif action == "timeout":
                if game.players and game.players[game.current_player_index].player_id == player_id:
                    game.players[game.current_player_index].lives -= 1
                    game.next_turn()
                    # await game.broadcast({
                    #     "type": "update",
                    #     "result": {"valid": False, "reason": "Time out"},
                    #     "grid": game.grid,
                    #     "players": [{"id": p.player_id, "name": p.name, "score": p.score, "lives": p.lives, "words": p.words} for p in game.players],
                    #     "current_player": game.players[game.current_player_index].player_id if game.players else None,
                    #     "current_player_name": game.players[game.current_player_index].name if game.is_started and game.players else None,
                    #     "is_started": True,
                    #     "message": f"Ход игрока {game.players[game.current_player_index].name}" if game.players else "Игра продолжается"
                    # })

                    wa_broadcast = WsBroadcast(
                        type="update",
                        result=SubmitWordResult(valid=False, reason="Время вышло"),
                        grid=game.grid,
                        players=[player.get_data() for player in game.players],
                        current_player=game.players[game.current_player_index].player_id if game.players else "",
                        current_player_name=game.players[game.current_player_index].name if game.is_started and game.players else "",
                        is_started=True,
                        message=f"Ход игрока {game.players[game.current_player_index].name}" if game.players else "Игра продолжается"
                    )

                    await game.broadcast(wa_broadcast.model_dump())



    except WebSocketDisconnect:

        logger.info(f"WebSocket disconnected: player_id={player_id}, game_id={game_id}")
        disconnected_player = game.remove_player(player_id)

        if disconnected_player:

            message = f"Игрок {disconnected_player.name} покинул игру"

            if not game.players:

                message = f"В игре не осталось игроков. Удаляем комнату.\nID игры: {game_id}"
                logger.info(message)
                del GM.games[game_id]
                return

            if game.is_started and game.players and game.current_player_index < len(game.players) and game.players[game.current_player_index].player_id == player_id:
                game.next_turn()
                # await game.broadcast({
                #     "type": "update",
                #     "grid": game.grid,
                #     "players": [{"id": p.player_id, "name": p.name, "score": p.score, "lives": p.lives, "words": p.words} for p in game.players],
                #     "current_player": game.players[game.current_player_index].player_id if game.players else None,
                #     "current_player_name": game.players[game.current_player_index].name if game.is_started and game.players else None,
                #     "is_started": True,
                #     "message": f"{message}. Ход игрока {game.players[game.current_player_index].name}" if game.players else message
                # })

                wa_broadcast = WsBroadcast(
                    type="update",
                    grid=game.grid,
                    players=[player.get_data() for player in game.players],
                    current_player=game.players[game.current_player_index].player_id if game.players else "",
                    current_player_name=game.players[game.current_player_index].name if game.is_started and game.players else "",
                    is_started=True,
                    message=f"{message}. Ход игрока {game.players[game.current_player_index].name}" if game.players else message
                )

                await game.broadcast(wa_broadcast.model_dump())

            else:
                # await game.broadcast({
                #     "type": "info",
                #     "message": message,
                #     "players": [{"id": p.player_id, "name": p.name, "score": p.score, "lives": p.lives, "words": p.words} for p in game.players]
                # })

                wa_broadcast = WsInfoBroadcast(
                    type="info",
                    message=message,
                    players=[player.get_data() for player in game.players],
                )
                await game.broadcast(wa_broadcast.model_dump())

            if len(game.players) == 1 and game.is_started:
                # await game.broadcast({
                #     "type": "info",
                #     "message": "Вы остались один. Продолжить игру?",
                #     "players": [{"id": p.player_id, "name": p.name, "score": p.score, "lives": p.lives, "words": p.words} for p in game.players]
                # })
                wa_broadcast = WsInfoBroadcast(
                    type="info",
                    message=f"Вы остались один. Продолжить игру?",
                    players=[player.get_data() for player in game.players],
                )
                await game.broadcast(wa_broadcast.model_dump())

    except Exception as e:
        logger.error(f"WebSocket error: game_id={game_id}, player_id={player_id}, error={e} {traceback.format_exc()}")
        await websocket.send_json({"type": "error", "message": f"Server error: {str(e)}"})
        await websocket.close()

if __name__ == "__main__":
    pass
