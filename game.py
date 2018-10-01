import pygame
import json
import socket
import time

from pygame.locals import *
from threading import Thread


WIDTH, HEIGHT = 800, 600
RESOLUTION = (WIDTH, HEIGHT)
PADDING = 5
BALL_SPEED = 2
PADDLE_SPEED = 4

BLACK_COLOR = (0, 0, 0)
WHITE_COLOR = (255, 255, 255)
BALL_COLOR = (100, 100, 255)
DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 8888
MAX_PLAYERS = 4
BUFFER_SIZE = 1024
POSITIONS = {
    'TOP', 'BOTTOM',
    'LEFT', 'RIGHT'
}


# class Ball:
#     def render(self, screen, data):
#         pygame.draw.circle(screen, self.color, self.rect.center, self.radius, 0)
#         pygame.draw.circle(screen, BLACK_COLOR, self.rect.center, self.radius, 1)
#
#
# class TopPaddle:
#     def render(self, screen):
#         pygame.draw.rect(screen, self.color, self.rect, 0)
#         pygame.draw.rect(screen, BLACK_COLOR, self.rect, 1)
#
#
# class BottomPaddle:
#     def render(self, screen):
#         pygame.draw.rect(screen, self.color, self.rect, 0)
#         pygame.draw.rect(screen, BLACK_COLOR, self.rect, 1)


class GameClient:
    def __init__(self, screen, player_name):
        self.screen = screen
        self.name = player_name
        self.position = None
        self.client = None
        self.data = None
        self.listener_th = Thread(target=self._server_listener, args=())
        self.join_server()

    def join_server(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.client = socket.socket()
        try:
            self.client.connect((host, port))
        except OSError as why:
            print("Error joining server: {}:{}: {}".format(host, port, why))
            return
        else:
            self.client.send(self.name.encode())
            self.position = self.client.recv(BUFFER_SIZE).decode()
        self.listener_th.start()

    def move_paddle(self, direction):
        self.client.send(str(direction).encode())

    def _server_listener(self):
        while True:
            self.data = self.client.recv(BUFFER_SIZE).decode()
            if not self.data:
                break
            self.render()
        print("No connection to server!")
        self.client.close()

    def render(self):
        try:
            self.data = json.loads(self.data)
        except json.JSONDecodeError as why:
            print("Error parsing data: {}".format(why))
            return

        # rendering ball
        data = json.loads(self.data['ball'])
        pygame.draw.circle(self.screen, data['color'],
                           data['center'], data['radius'], 0)
        pygame.draw.circle(self.screen, BLACK_COLOR,
                           data['center'], data['radius'], 1)

        # rendering top

        # rendering bottom

        # rendering left

        # rendering right

        pygame.display.flip()


def main():
    pygame.init()
    screen = pygame.display.set_mode(RESOLUTION)
    clock = pygame.time.Clock()
    gc = GameClient(screen, 'player')
    running = True
    while running:
        # setting fps
        clock.tick(60)

        # event handling
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                pass
            elif event.type == KEYUP:
                pass


        # objects updates
        # ...

        screen.fill(BLACK_COLOR)
        # pygame.display.flip()
    pygame.quit()


if __name__ == '__main__':
    main()
