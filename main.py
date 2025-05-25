import traceback

import uvicorn
from loguru import logger

from app.config import CONFIG


def main():

    print()

    try:

        logger.info(f"Подключение и настройка базы данных")

        logger.info(f"Запуск APP: http://{CONFIG.api.full_path}")
        logger.info(f"Swagger: http://{CONFIG.api.docs}")
        uvicorn.run(
            app="app.app:APP",
            host=CONFIG.api.ip,
            port=CONFIG.api.port,
            log_level="debug",
            reload=True
        )

    except KeyboardInterrupt:
        logger.info(f"Сервер остановлен")
    except Exception as e:
        logger.exception(f"{e} {traceback.format_exc()}")
    finally:
        logger.info(f"Выключение APP")


if __name__ == "__main__":
    main()
