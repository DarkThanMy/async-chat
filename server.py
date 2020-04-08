# Серверное приложение для соединений
import asyncio
from asyncio import transports


# Описывает протокол передачи данных между клиентами
class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    # Получение данных от клиента
    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        # Проверяем свойство login на наличе записанного в него значения
        if self.login is not None:
            self.send_message(decoded)
        else:
            # Проверка начала сообщения на наличие "login:"
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "").replace("\r\n", "")
                # Проверка на уникальность логина
                for user in self.server.clients:
                    if login == user.login:
                        self.transport.write(f"Логин {login} занят, попробуйте другой\n".encode())
                        self.transport.close()
                self.login = login
                self.send_history()
                self.transport.write(f"Привет, {self.login}!\n".encode())
            else:
                self.transport.write("Неправильный логин\n".encode())

    # Успешное подключение клиента к серверу
    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришёл новый клиент")

    # Отключение клиента от сервера
    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    # Отправка сообщения клиентам
    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"
        self.server.messages.append(message)

        for user in self.server.clients:
            user.transport.write(message.encode())

    # Вывод последних 10 сообщений
    def send_history(self):
        for message in self.server.messages[-10:]:
            print(f"{message}\n\n")
            self.transport.write(f"{message}\n".encode())


# Сервер приложения
class Server:
    clients: list
    messages: list

    def __init__(self):
        self.clients = []
        self.messages = []

    # Построение нового протокола
    def build_protocol(self):
        return ServerProtocol(self)

    # Запуск сервера
    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8000
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")