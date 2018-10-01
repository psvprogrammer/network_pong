import socket
import pygame
import json
import time

from threading import Thread


WIDTH, HEIGHT = 800, 600
RESOLUTION = (WIDTH, HEIGHT)

PADDING = 5
BALL_SPEED = 2
PADDLE_SPEED = 4

BLACK_COLOR = (0, 0, 0)
WHITE_COLOR = (255, 255, 255)
BALL_COLOR = (100, 100, 255)

BUFFER_SIZE = 1024
DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 8888
MAX_PLAYERS = 4
POSITIONS = (
    'top', 'bottom',
    'left', 'right'
)


class CircleRenderObject:
    def __str__(self):
        return json.dumps({
            'color': self.color,
            'center': self.rect.center,
            'radius': self.radius
        })


class RectRenderObject:
    def __str__(self):
        return json.dumps({
            'color': self.color,
            'rect': {
                'left': self.left,
                'top': self.top,
                'width': self.width,
                'height': self.height
            },
        })


# game object classes
class Ball(CircleRenderObject):
    def __init__(self, screensize=RESOLUTION):
        self.screensize = screensize
        self.x = int(screensize[0] * 0.5)
        self.y = int(screensize[1] * 0.5)
        self.radius = 10

        self.left = self.x-self.radius
        self.top = self.y-self.radius
        self.width = self.radius*2
        self.height = self.radius*2
        self.rect = pygame.Rect(self.left, self.top, self.width, self.height)
        self.color = WHITE_COLOR
        self.direction = [1, 1]

        # ball speed
        self.xspeed = BALL_SPEED
        self.yspeed = BALL_SPEED

        # what side edge hit
        self.hit_edge_left = False
        self.hit_edge_right = False
        self.hit_edge_top = False
        self.hit_edge_bottom = False

    def update(self, paddles=None):
        self.x += self.direction[0] * self.xspeed
        self.y += self.direction[1] * self.yspeed

        self.rect.center = (self.x, self.y)

        # add check paddles on each side
        # ...

        if self.rect.top <= 0:
            self.direction[1] = 1
        elif self.rect.bottom >= self.screensize[1]-1:
            self.direction[1] = -1

        if self.rect.left <= 0:
            self.direction[0] = 1
        elif self.rect.right >= self.screensize[0]-1:
            self.direction[0] = -1


class TopPaddle(RectRenderObject):
    def __init__(self, screensize=RESOLUTION):
        self.screen_size = screensize

        self.width = 100
        self.height = 10

        self.x = int(self.screen_size[0] * 0.5)
        self.y = int(self.height * 0.5) + PADDING

        self.left = self.x-int(self.width * 0.5)
        self.top = self.y-int(self.height * 0.5)
        self.rect = pygame.Rect(self.left, self.top, self.width, self.height)
        self.color = WHITE_COLOR
        self.speed = PADDLE_SPEED

    def move(self, direction):
        self.x += direction * self.speed
        self.rect.center = (self.x, self.y)


class BottomPaddle(RectRenderObject):
    def __init__(self, screensize=RESOLUTION):
        self.screen_size = screensize

        self.width = 100
        self.height = 10

        self.x = int(self.screen_size[0] * 0.5)
        self.y = self.screen_size[1] - int(self.height * 0.5) - PADDING

        self.left = self.x-int(self.width * 0.5)
        self.top = self.y-int(self.height * 0.5)
        self.rect = pygame.Rect(self.left, self.top, self.width, self.height)

        self.color = WHITE_COLOR
        self.speed = PADDLE_SPEED

    def move(self, direction):
        self.x += direction * self.speed
        self.rect.center = (self.x, self.y)


class Server:
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.socket = socket.socket()
        self.ip, self.port = host, port
        try:
            self.socket.bind((host, port))
            self.socket.listen(MAX_PLAYERS)
        except OSError as why:
            print("Error starting server: {}".format(why))
            raise
        else:
            print("Server started")

        # game objects
        self.ball = Ball()
        self.top = TopPaddle()
        self.bottom = BottomPaddle()
        # self.left = LeftPaddle()
        # self.right = RightPaddle()

        # init positions
        self.objects = {
            'ball': self.ball,
            'top': self.top,
            'bottom': self.bottom,
            # 'left': self.left,
            # 'right': self.right
        }

        # players
        self.players = {
            'top': None,
            'bottom': None,
            'left': None,
            'right': None
        }

        self.positions = list(POSITIONS)
        self.accept_player_th = Thread(target=self._accept_new_player, args=())
        self.accept_player_th.start()

        # running the game?
        self.is_running = False
        self.game_th = Thread(target=self._send_updates, args=())

    @property
    def has_free_slot(self):
        for position in self.positions:
            if self.players.get(position) is None:
                return True
        return False

    def add_player(self, conn, ip, port):
        player_name = conn.recv(BUFFER_SIZE).decode()
        position = self.positions.pop()
        conn.send(position.encode())
        player_listener_th = Thread(target=self._listener, args=(position,))
        self.players[position] = {
            'name': player_name,
            'conn': conn,
            'address': (ip, port),
            'listener': player_listener_th
        }
        player_listener_th.start()

        if not self.is_running:
            self.start_game()

    def start_game(self):
        self.is_running = True
        self.game_th.start()

    def _accept_new_player(self):
        while self.has_free_slot:
            (conn, (ip, port)) = self.socket.accept()
            print('Greeting new player! {}:{}'.format(ip, port))
            self.add_player(conn, ip, port)
        print('We got max players!')

    def _listener(self, position):
        while self.is_running:
            conn = self.players[position]['conn']
            data = conn.recv(BUFFER_SIZE).decode()
            if not data:
                print("Player '{}' disconnected"
                      "".format(self.players[position]['name']))
                self.players[position] = None
                break
            try:
                direction = int(data)
            except ValueError as why:
                print("Error converting received data "
                      "from player: {}".format(why))
                break
            else:
                # updating player paddle position
                paddle = getattr(self, position)
                paddle.move(direction)

    def update(self):
        self.ball.update()
        return {key: str(value) for key, value in self.objects.items()}

    def _send_updates(self):
        self.clock = pygame.time.Clock()
        while self.is_running:
            self.clock.tick(60)
            data = self.update()
            for player in self.players.values():
                if player and player.get('conn'):
                    try:
                        player['conn'].send(json.dumps(data).encode())
                    except OSError as why:
                        print("Player disconnected!")
                        player['conn'] = None
                        continue
            # time.sleep(0.0001)


if __name__ == '__main__':
    server = Server()
