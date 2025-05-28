import pprint
import traceback

from fastapi import APIRouter
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger
from app.models.models import WsBroadcast, WsClickBroadcast, SubmitWordResult, WsInfoBroadcast
from app.storage import GM

from fastapi.responses import HTMLResponse
import os


r_ws = APIRouter(tags=['WEB SOCKET'])
index_path = os.path.join("app", "static", "index.html")


@r_ws.get("/test")
async def test():
    return {"message": "ok"}


@r_ws.websocket("/ws/{game_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str, player_id: str):

    await websocket.accept()

    logger.info(f"Подключаем WebSocket:\n{game_id=}\n{player_id=}")
    game = GM.games.get(game_id)
    if not game:
        # TODO если игра не найдена - перекинуть игроков в меню
        logger.error(f"WebSocket error. Игра не найдена:\n{game_id=}")
        await websocket.send_json({"type": "error", "message": "Игра не найдена."})
        await websocket.close()
        return

    player = next((p for p in game.players if p.player_id == player_id), None)
    if not player:
        logger.error(f"WebSocket error. Игрок {player_id} отсутствует в игре {game_id}")
        await websocket.send_json({"type": "error", "message": f"Игрок {player_id} не найден"})
        await websocket.close()
        return

    player.websocket = websocket

    try:
        wa_broadcast = WsBroadcast(
            type="init",
            grid=game.grid,
            timer=game.timer,
            min_players=game.min_players,
            max_players=game.max_players,
            players=[player.get_data() for player in game.players],
            current_player=game.players[game.current_player_index].player_id if game.is_started and game.players else "",
            current_player_name=game.players[game.current_player_index].name if game.is_started and game.players else "",
            is_started=game.is_started,
            message=f"Игрок {game.players[game.current_player_index].name} присоединился."
        )
        logger.debug(f"{wa_broadcast=}")
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

                    wa_broadcast = WsBroadcast(
                        type="start",
                        grid=game.grid,
                        timer=game.timer,
                        min_players=game.min_players,
                        max_players=game.max_players,
                        players=[player.get_data() for player in game.players],
                        current_player=game.players[game.current_player_index].player_id if game.players else "",
                        current_player_name=game.players[game.current_player_index].name if game.is_started and game.players else "",
                        is_started=True,
                        message=f"Ход игрока {game.players[game.current_player_index].name}"
                    )

                    await game.broadcast(wa_broadcast.model_dump())

            elif action == "submit_word":

                word = data.get("word")
                path = data.get("path")
                result = game.submit_word(player_id, word, path)    # Проверка слова

                if game.players[game.current_player_index].lives:

                    game.next_turn()

                    wa_broadcast = WsBroadcast(
                        type="update",
                        result=result,
                        grid=game.grid,
                        timer=game.timer,
                        min_players=game.min_players,
                        max_players=game.max_players,
                        players=[player.get_data() for player in game.players],
                        current_player=game.players[game.current_player_index].player_id if game.players else "",
                        current_player_name=game.players[game.current_player_index].name if game.is_started and game.players else "",
                        is_started=True,
                        message=f"Ход игрока {game.players[game.current_player_index].name}" if game.players else "Игра продолжается"
                    )

                    await game.broadcast(wa_broadcast.model_dump())

                else:

                    wa_broadcast = WsBroadcast(
                        type="update",
                        game_over=True,
                        result=result,
                        grid=game.grid,
                        timer=game.timer,
                        min_players=game.min_players,
                        max_players=game.max_players,
                        players=[player.get_data() for player in game.players],
                        current_player=game.players[game.current_player_index].player_id if game.players else "",
                        current_player_name=game.players[game.current_player_index].name if game.is_started and game.players else "",
                        is_started=True,
                        message=f"Конец игры"
                    )

                    await game.broadcast(wa_broadcast.model_dump())

            elif action == "increment_click":
                row = data.get("row")
                col = data.get("col")
                result = game.increment_click(player_id, row, col)

                if not result.success:
                    wa_broadcast = WsClickBroadcast(
                        type="click_update",
                        grid=game.grid,
                        result=result,
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

                    wa_broadcast = WsBroadcast(
                        type="update",
                        result=SubmitWordResult(valid=False, reason="Время вышло"),
                        grid=game.grid,
                        timer=game.timer,
                        min_players=game.min_players,
                        max_players=game.max_players,
                        players=[player.get_data() for player in game.players],
                        current_player=game.players[game.current_player_index].player_id if game.players else "",
                        current_player_name=game.players[game.current_player_index].name if game.is_started and game.players else "",
                        is_started=True,
                        message=f"Ход игрока {game.players[game.current_player_index].name}" if game.players else "Игра продолжается"
                    )

                    await game.broadcast(wa_broadcast.model_dump())

    except WebSocketDisconnect:

        try:
            logger.info(f"WebSocket disconnected: player_id={player_id}, game_id={game_id}")

            creator_out = True if game.creator_id == game.players[game.current_player_index].player_id else False  # Если вышел создатель игры
            # find_player = game.find_player(player_id)

            disconnected_player = game.remove_player(player_id)

            if disconnected_player:

                message = f"Игрок {disconnected_player.name} покинул игру"
                if not game.players:
                    message = f"В игре не осталось игроков. Удаляем комнату.\nID игры: {game_id}"
                    logger.info(message)
                    del GM.games[game_id]
                    return

                if (
                        (game.is_started and game.players) and
                        (
                                (game.current_player_index < len(game.players) and game.players[game.current_player_index].player_id == player_id) or
                                creator_out
                        )
                ):

                    game.next_turn()

                    wa_broadcast = WsBroadcast(
                        type="update",
                        grid=game.grid,
                        timer=game.timer,
                        min_players=game.min_players,
                        max_players=game.max_players,
                        players=[player.get_data() for player in game.players],
                        current_player=game.players[game.current_player_index].player_id if game.players else "",
                        current_player_name=game.players[game.current_player_index].name if game.is_started and game.players else "",
                        is_started=True,
                        message=f"{message}. Ход игрока {game.players[game.current_player_index].name}" if game.players else message
                    )

                    await game.broadcast(wa_broadcast.model_dump())

                else:
                    wa_broadcast = WsInfoBroadcast(
                        type="info",
                        message=message,
                        players=[player.get_data() for player in game.players],
                    )
                    await game.broadcast(wa_broadcast.model_dump())

                if len(game.players) == 1 and game.is_started:
                    wa_broadcast = WsInfoBroadcast(
                        type="info",
                        message=f"Вы остались один. Продолжить игру?",
                        players=[player.get_data() for player in game.players],
                    )
                    await game.broadcast(wa_broadcast.model_dump())

        except Exception as e:
            logger.error(f"Ошибка! Конец игры! {e} {traceback.format_exc()}")

    except Exception as e:
        logger.error(f"!! WebSocket error: game_id={game_id}, player_id={player_id}, error={e} {traceback.format_exc()}")
        await websocket.send_json({"type": "error", "message": f"Ошибка сервера: {str(e)}"})
        await websocket.close()


if __name__ == "__main__":
    pass
