import logging

from discord.ext import commands


class QueueEmitHandler(logging.Handler):
    def __init__(self, bot: commands.Bot, /):
        self.bot = bot
        super().__init__(logging.INFO)

    def emit(self, record: logging.LogRecord):
        self.bot.logging_queue.put_nowait(record)


class LogHandler:
    def __init__(self, *, bot: commands.Bot):
        self.log: logging.Logger = logging.getLogger()
        self.bot: commands.Bot = bot
        self.debug = self.log.debug
        self.info = self.log.info
        self.warning = self.log.warning
        self.error = self.log.error
        self.critical = self.log.critical

    async def __aenter__(self):
        return self.__enter__()

    def __enter__(self):
        logging.getLogger("discord").setLevel(logging.INFO)
        logging.getLogger("discord.http").setLevel(logging.INFO)
        logging.getLogger("discord.state").setLevel(logging.WARNING)
        logging.getLogger("discord.gateway").setLevel(logging.WARNING)

        self.log.setLevel(logging.INFO)

        self.log.addHandler(QueueEmitHandler(self.bot))

    async def __aexit__(self, *args) -> None:
        return self.__exit__(*args)

    def __exit__(self, *args) -> None:
        handlers = self.log.handlers[:]
        for hdlr in handlers:
            hdlr.close()
            self.log.removeHandler(hdlr)
