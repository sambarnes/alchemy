import plyvel
import os


class AlchemyDB:
    def __init__(self, path: str = None, **kwargs):
        """
        An alchemy specific wrapper around level-db

        :param path: file-path to the leveldb database, defaults to: /$HOME/.pegnet/alchemy/data/
        """
        if path is None:
            home = os.getenv("HOME")
            path = f"{home}/.pegnet/alchemy/data/"
        self._db = plyvel.DB(path, **kwargs)

    def close(self):
        self._db.close()
