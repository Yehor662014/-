import pygame
import random
import sys
import numpy as np
import sounddevice as sd
import time

pygame.init()

info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
WIN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Flappy Bird (Voice Control)")

WHITE = (255, 255, 255)
BLUE = (135, 206, 235)
GREEN = (0, 200, 0)
DARK_GREEN = (0, 150, 0)

font = pygame.font.SysFont("comicsans", 60)

BIRD_WIDTH, BIRD_HEIGHT = 50, 40
bird_x = WIDTH // 6
bird_y = HEIGHT // 2
bird_vel = 0
gravity = 0.6
jump = -10

pipe_width = 100
pipe_gap = 250
pipes = []
pipe_vel = -6
SPAWNPIPE = pygame.USEREVENT
pygame.time.set_timer(SPAWNPIPE, 1500)

score = 0

# ----------- Настройки звука ----------
SAMPLE_RATE = 16000
BLOCKSIZE = 1024
voice_level = 0.0
threshold = 0.05
last_flap = 0
flap_cooldown = 0.3


def audio_callback(indata, frames, time_info, status):
    global voice_level
    volume_norm = np.linalg.norm(indata) / frames
    voice_level = 0.7 * voice_level + 0.3 * volume_norm


stream = sd.InputStream(callback=audio_callback, channels=1,
                        samplerate=SAMPLE_RATE, blocksize=BLOCKSIZE)
stream.start()


def draw_pipe(pipe, is_top=False):
    rect = pipe["rect"]
    pygame.draw.rect(WIN, GREEN, rect)
    head_height = 30
    if is_top:
        head_rect = pygame.Rect(rect.x - 10, rect.bottom - head_height, pipe_width + 20, head_height)
    else:
        head_rect = pygame.Rect(rect.x - 10, rect.top, pipe_width + 20, head_height)
    pygame.draw.rect(WIN, DARK_GREEN, head_rect)


def draw_window(bird_x, bird_y, pipes, score):
    WIN.fill(BLUE)
    pygame.draw.ellipse(WIN, (255, 255, 0), (bird_x, bird_y, BIRD_WIDTH, BIRD_HEIGHT))
    for i, pipe in enumerate(pipes):
        draw_pipe(pipe, is_top=(i % 2 == 0))
    text = font.render(f"{score}", True, WHITE)
    WIN.blit(text, (WIDTH//2 - text.get_width()//2, 30))

    # Индикатор громкости
    bar_w = int(min(1.0, voice_level * 40) * (WIDTH - 60))
    pygame.draw.rect(WIN, (50, 180, 255), (30, 20, bar_w, 10))
    thr_x = 30 + int(min(1.0, threshold * 40) * (WIDTH - 60))
    pygame.draw.line(WIN, (200, 50, 50), (thr_x, 18), (thr_x, 32), 2)

    pygame.display.update()


def main():
    global bird_x, bird_y, bird_vel, pipes, score, last_flap
    clock = pygame.time.Clock()
    run = True
    score = 0
    bird_x = WIDTH // 6
    bird_y = HEIGHT // 2
    bird_vel = 0
    pipes = []
    last_flap = 0

    while run:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:  # пробел
                    bird_vel = jump
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            if event.type == SPAWNPIPE:
                height = random.randint(100, HEIGHT - pipe_gap - 100)
                pipes.append({"rect": pygame.Rect(WIDTH, 0, pipe_width, height), "passed": False})
                pipes.append({"rect": pygame.Rect(WIDTH, height + pipe_gap, pipe_width, HEIGHT - height - pipe_gap), "passed": False})

        # --- Голосовое управление ---
        now = time.time()
        if voice_level > threshold and (now - last_flap) > flap_cooldown:
            bird_vel = jump
            last_flap = now

        # Физика
        bird_vel += gravity
        bird_y += bird_vel

        for pipe in pipes:
            pipe["rect"].x += pipe_vel

        pipes = [pipe for pipe in pipes if pipe["rect"].x + pipe_width > 0]

        # Столкновения
        bird_rect = pygame.Rect(bird_x, bird_y, BIRD_WIDTH, BIRD_HEIGHT)
        for pipe in pipes:
            if bird_rect.colliderect(pipe["rect"]):
                bird_x -= 30  # откидываем птицу назад
                bird_vel = -5  # подбрасываем немного вверх

        # Проигрыш если вышел за экран
        if bird_y > HEIGHT or bird_y < 0:
            run = False

        # Подсчёт очков
        for i in range(0, len(pipes), 2):
            pipe = pipes[i+1]
            if pipe["rect"].x + pipe_width < bird_x and not pipe["passed"]:
                score += 1
                pipe["passed"] = True

        draw_window(bird_x, bird_y, pipes, score)


if __name__ == "__main__":
    main()
