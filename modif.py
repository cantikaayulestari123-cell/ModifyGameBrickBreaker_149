import pygame
import random
import math
import array
import os

pygame.init()

# Setup Audio Synthesizer Safe Mode (Cegah crash jika tidak ada speaker)
HAS_AUDIO = True
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
except Exception:
    HAS_AUDIO = False

def generate_tone(frequency, duration, volume=0.2):
    if not HAS_AUDIO:
        return None
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    buf = array.array('h', [0] * n_samples)
    for i in range(n_samples):
        t = float(i) / sample_rate
        envelope = (1.0 - (i / n_samples))
        val = int(32767.0 * volume * envelope * math.sin(2.0 * math.pi * frequency * t))
        buf[i] = val
    return pygame.mixer.Sound(buf)

def play_sound(sound):
    if HAS_AUDIO and sound:
        sound.play()

# Efek Suara (SFX)
sound_bounce = generate_tone(523.25, 0.08, 0.2)
sound_block = generate_tone(783.99, 0.1, 0.25)
sound_lose = generate_tone(261.63, 0.3, 0.3)

# Melodi Musik Latar (BGM)
bgm_notes = [392.00, 440.00, 493.88, 523.25, 587.33, 523.25, 493.88, 440.00]
bgm_sounds = [generate_tone(f, 0.18, 0.08) for f in bgm_notes]

# Dimensions
WIDTH, HEIGHT = 600, 500

# Palette Warna Pastel & Dark Fallback
BG_COLOR_FALLBACK = (25, 28, 36) # Charcoal Gelap jika gambar tidak ada
STRIKER_COLOR = (147, 112, 219)   # Medium Purple
BALL_COLOR = (255, 182, 193)      # Pink Pastel
TEXT_COLOR = (255, 255, 255)      # Putih Terang

# Warna Balok Pastel
PASTEL_PINK = (255, 179, 186)
PASTEL_GREEN = (186, 255, 201)
PASTEL_BLUE = (186, 225, 255)
PASTEL_PURPLE = (225, 190, 231)
PASTEL_YELLOW = (255, 255, 186)

# Fonts
font = pygame.font.Font('freesansbold.ttf', 16)
font_large = pygame.font.Font('freesansbold.ttf', 36)
font_sub = pygame.font.Font('freesansbold.ttf', 18)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Block Breaker - Cute Particle Edition")

clock = pygame.time.Clock()
FPS = 30


# Particle Class untuk Efek Kena Bola (Sparkle)
class Particle:
    def __init__(self, posx, posy, color):
        self.posx = posx
        self.posy = posy
        self.color = color
        # Memberikan arah gerak acak (ledakan kecil)
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(-4, 4)
        self.radius = random.randint(2, 5)
        self.lifetime = 255  # Berdasarkan opacity / keawetan partikel
        self.fade_speed = random.randint(8, 15)

    def update(self):
        self.posx += self.vx
        self.posy += self.vy
        self.lifetime -= self.fade_speed
        if self.radius > 0.5:
            self.radius -= 0.1

    def display(self, surface):
        if self.lifetime > 0 and self.radius > 0:
            # Membuat efek pudar menggunakan Surface dengan alpha channel
            p_surf = pygame.Surface((int(self.radius * 2), int(self.radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(p_surf, (self.color[0], self.color[1], self.color[2], self.lifetime), 
                               (int(self.radius), int(self.radius)), int(self.radius))
            surface.blit(p_surf, (int(self.posx - self.radius), int(self.posy - self.radius)))


# Striker class
class Striker:
    def __init__(self, posx, posy, width, height, speed, color):
        self.posx, self.posy = posx, posy
        self.width, self.height = width, height
        self.speed = speed
        self.color = color

        self.strikerRect = pygame.Rect(
            self.posx, self.posy, self.width, self.height)

    def display(self):
        pygame.draw.rect(screen, self.color, self.strikerRect, border_radius=12)

    def update(self, xFac):
        self.posx += self.speed * xFac

        if self.posx <= 0:
            self.posx = 0
        elif self.posx + self.width >= WIDTH:
            self.posx = WIDTH - self.width

        self.strikerRect = pygame.Rect(
            self.posx, self.posy, self.width, self.height)

    def getRect(self):
        return self.strikerRect


# Block Class (Bentuk Kucing Imut)
class Block:
    def __init__(self, posx, posy, width, height, color):
        self.posx, self.posy = posx, posy
        self.width, self.height = width, height
        self.color = color
        self.damage = 100

        if color in [PASTEL_PURPLE, PASTEL_PINK]:
            self.health = 200
        else:
            self.health = 100

        self.blockRect = pygame.Rect(
            self.posx, self.posy, self.width, self.height)

    def display(self):
        if self.health > 0:
            x, y, w, h = self.posx, self.posy, self.width, self.height
            
            # Telinga Kucing (Kiri & Kanan)
            ear_w, ear_h = w // 4, h // 2
            pygame.draw.polygon(screen, self.color, [(x + 2, y), (x + ear_w, y - ear_h), (x + ear_w * 2, y)])
            pygame.draw.polygon(screen, self.color, [(x + w - ear_w * 2, y), (x + w - ear_w, y - ear_h), (x + w - 2, y)])
            
            # Badan Balok Kucing
            pygame.draw.rect(screen, self.color, self.blockRect, border_radius=6)

            # Mata & Hidung Kucing
            eye_color = (40, 40, 50)
            pygame.draw.circle(screen, eye_color, (int(x + w * 0.3), int(y + h * 0.45)), 2)
            pygame.draw.circle(screen, eye_color, (int(x + w * 0.7), int(y + h * 0.45)), 2)
            pygame.draw.circle(screen, (255, 105, 180), (int(x + w * 0.5), int(y + h * 0.65)), 1)

    def hit(self):
        self.health -= self.damage

    def getRect(self):
        return self.blockRect

    def getHealth(self):
        return self.health


# Ball Class
class Ball:
    def __init__(self, posx, posy, radius, speed, color):
        self.posx, self.posy = posx, posy
        self.radius = radius
        self.speed = speed
        self.color = color
        self.xFac, self.yFac = 1, -1

        self.ball = pygame.Rect(self.posx - radius, self.posy - radius, radius * 2, radius * 2)

    def display(self):
        pygame.draw.circle(
            screen, self.color, (int(self.posx), int(self.posy)), self.radius)

    def update(self):
        self.posx += self.xFac * self.speed
        self.posy += self.yFac * self.speed

        if self.posx - self.radius <= 0 or self.posx + self.radius >= WIDTH:
            self.xFac *= -1
            play_sound(sound_bounce)

        if self.posy - self.radius <= 0:
            self.yFac *= -1
            play_sound(sound_bounce)

        self.ball = pygame.Rect(self.posx - self.radius, self.posy - self.radius, self.radius * 2, self.radius * 2)

        if self.posy >= HEIGHT:
            play_sound(sound_lose)
            return True

        return False

    def reset(self):
        self.posx = WIDTH // 2
        self.posy = HEIGHT - 150
        self.xFac, self.yFac = 1, -1

    def hit(self):
        self.yFac *= -1

    def getRect(self):
        return self.ball


def collisionChecker(rect, ball):
    return pygame.Rect.colliderect(rect, ball)


def populateBlocks(blockWidth, blockHeight, horizontalGap, verticalGap):
    listOfBlocks = []
    pastel_colors = [PASTEL_PINK, PASTEL_GREEN, PASTEL_BLUE, PASTEL_PURPLE, PASTEL_YELLOW]

    for i in range(25, WIDTH - blockWidth, blockWidth + horizontalGap):
        for j in range(50, HEIGHT // 2, blockHeight + verticalGap):
            color = random.choice(pastel_colors)
            listOfBlocks.append(
                Block(i, j, blockWidth, blockHeight, color))

    return listOfBlocks


# GUI Tampilan Game Over
def showGameOverGUI(final_score):
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(200)
    overlay.fill((15, 15, 20))
    screen.blit(overlay, (0, 0))

    card_rect = pygame.Rect(WIDTH // 2 - 170, HEIGHT // 2 - 120, 340, 240)
    pygame.draw.rect(screen, (35, 38, 50), card_rect, border_radius=16)
    pygame.draw.rect(screen, PASTEL_PINK, card_rect, width=2, border_radius=16)

    title_text = font_large.render("GAME OVER", True, PASTEL_PINK)
    title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 70))
    screen.blit(title_text, title_rect)

    score_text = font_sub.render(f"Final Score : {final_score}", True, TEXT_COLOR)
    score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 15))
    screen.blit(score_text, score_rect)

    restart_text = font.render("Press [ SPACE ] to Restart", True, PASTEL_GREEN)
    restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40))
    screen.blit(restart_text, restart_rect)

    quit_text = font.render("Press [ ESC ] to Quit", True, PASTEL_BLUE)
    quit_rect = quit_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70))
    screen.blit(quit_text, quit_rect)

    pygame.display.update()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return True
                if event.key == pygame.K_ESCAPE:
                    return False
        clock.tick(FPS)


# Game Manager
def main():
    running = True
    lives = 3
    score = 0

    # Load Gambar Latar Belakang yang Cantik (background.jpg)
    bg_filename = "background.jpg"
    bg_image = None

    if os.path.exists(bg_filename):
        try:
            loaded_img = pygame.image.load(bg_filename)
            bg_image = pygame.transform.scale(loaded_img, (WIDTH, HEIGHT))
        except Exception:
            bg_image = None

    striker = Striker(WIDTH // 2 - 50, HEIGHT - 40, 100, 14, 10, STRIKER_COLOR)
    strikerXFac = 0

    ball = Ball(WIDTH // 2, HEIGHT - 150, 8, 6, BALL_COLOR)

    blockWidth, blockHeight = 44, 18
    horizontalGap, verticalGap = 14, 16

    listOfBlocks = populateBlocks(
        blockWidth, blockHeight, horizontalGap, verticalGap)

    # Menampung seluruh partikel efek
    particles_list = []

    bgm_index = 0
    bgm_timer = 0

    while running:
        # Render Background (Gambar jika ada, atau Warna Gelap jika tidak ada)
        if bg_image:
            screen.blit(bg_image, (0, 0))
        else:
            screen.fill(BG_COLOR_FALLBACK)

        # Pemutar Musik BGM
        bgm_timer += 1
        if bgm_timer % 6 == 0:
            play_sound(bgm_sounds[bgm_index])
            bgm_index = (bgm_index + 1) % len(bgm_sounds)

        # Render HUD (Score & Lives)
        scoreText = font.render(f"Score : {score}", True, TEXT_COLOR)
        livesText = font.render(f"Lives : {lives}", True, TEXT_COLOR)

        screen.blit(scoreText, (30, HEIGHT - 30))
        screen.blit(livesText, (WIDTH - 110, HEIGHT - 30))

        if not listOfBlocks:
            listOfBlocks = populateBlocks(
                blockWidth, blockHeight, horizontalGap, verticalGap)

        # Cek Game Over
        if lives <= 0:
            restart = showGameOverGUI(score)
            if restart:
                listOfBlocks.clear()
                lives = 3
                score = 0
                listOfBlocks = populateBlocks(
                    blockWidth, blockHeight, horizontalGap, verticalGap)
                ball.reset()
                particles_list.clear()
            else:
                running = False
                break

        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    strikerXFac = -1
                if event.key == pygame.K_RIGHT:
                    strikerXFac = 1

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    strikerXFac = 0

        # Collisions
        if collisionChecker(striker.getRect(), ball.getRect()):
            ball.hit()
            play_sound(sound_bounce)
            
            # Efek letupan kecil saat bola memantul dari striker
            for _ in range(5):
                particles_list.append(Particle(ball.posx, ball.posy, BALL_COLOR))

        for block in listOfBlocks[:]:
            if collisionChecker(block.getRect(), ball.getRect()):
                ball.hit()
                block.hit()
                play_sound(sound_block)

                # TRIGGER EFEK PARTIKEL: Menelurkan serpihan (sparks) warna sesuai balok yang kena
                for _ in range(15):
                    particles_list.append(Particle(ball.posx, ball.posy, block.color))

                if block.getHealth() <= 0:
                    # Letupan ekstra besar saat balok hancur total
                    for _ in range(25):
                        particles_list.append(Particle(block.posx + block.width//2, 
                                                       block.posy + block.height//2, 
                                                       block.color))
                    listOfBlocks.remove(block)
                    score += 5

        # Update Position & Particles
        striker.update(strikerXFac)
        lifeLost = ball.update()

        if lifeLost:
            lives -= 1
            ball.reset()
            particles_list.clear() # bersihkan layar saat kalah nyawa

        # Update and Display Particles
        for particle in particles_list[:]:
            particle.update()
            particle.display(screen)
            if particle.lifetime <= 0 or particle.radius <= 0:
                particles_list.remove(particle)

        # Display Entities
        striker.display()
        ball.display()

        for block in listOfBlocks:
            block.display()

        pygame.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
    pygame.quit()