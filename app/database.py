
import mysql.connector
from app.config import Config


def obtener_conexion():
    """
    Abre una conexión con la base de datos MySQL.
    Si falla, muestra el error real en la terminal de Flask.
    """

    if not Config.DB_HOST:
        raise RuntimeError("Falta DB_HOST en el archivo .env")

    if not Config.DB_USER:
        raise RuntimeError("Falta DB_USER en el archivo .env")

    if not Config.DB_NAME:
        raise RuntimeError("Falta DB_NAME en el archivo .env")

    return mysql.connector.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        connection_timeout=10,
        autocommit=False
    )
