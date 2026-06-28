import pygame
import random
import math
import os
from collections import deque

# Initialize Pygame and mixer
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# Windowed mode
WINDOW_WIDTH = 540
WINDOW_HEIGHT = 750

# Game area with 9:16 aspect ratio
GAME_WIDTH = 540
GAME_HEIGHT = 960
GAME_OFFSET_X = (WINDOW_WIDTH - GAME_WIDTH) // 2
GAME_OFFSET_Y = (WINDOW_HEIGHT - GAME_HEIGHT) // 2

FPS = 60

# Colors - Clean coding vibes
BLACK = (10, 10, 10)
DARK_GRAY = (30, 30, 30)
GRAY = (50, 50, 50)
LIGHT_GRAY = (100, 100, 100)
WHITE = (220, 220, 220)
GREEN = (0, 255, 0)  # Console green

# Team Colors
ROCK_COLOR = (255, 100, 100)      # Red
PAPER_COLOR = (100, 255, 100)     # Green
SCISSORS_COLOR = (100, 100, 255)  # Blue

TYPE_COLORS = [ROCK_COLOR, PAPER_COLOR, SCISSORS_COLOR]
TYPE_NAMES = ["ROCK", "PAPER", "SCISSORS"]

# Prey relationships
PREY_TYPE = [2, 0, 1]  # Rock hunts Scissors(2), Paper hunts Rock(0), Scissors hunts Paper(1)
PREDATOR_TYPE = [1, 2, 0]  # Rock is hunted by Paper(1), Paper is hunted by Scissors(2), Scissors is hunted by Rock(0)

# Play area
PLAY_AREA_TOP = 160  # Moved down to make room for caption
PLAY_AREA_BOTTOM = GAME_HEIGHT - 100
PLAY_AREA_LEFT = 80
PLAY_AREA_RIGHT = GAME_WIDTH - 80

# Grid system for fair distribution
GRID_COLS = 8
GRID_ROWS = 12
CELL_WIDTH = (PLAY_AREA_RIGHT - PLAY_AREA_LEFT) // GRID_COLS
CELL_HEIGHT = (PLAY_AREA_BOTTOM - PLAY_AREA_TOP) // GRID_ROWS

# Balance mechanic thresholds
LOW_COUNT_THRESHOLD = 5
CRITICAL_COUNT_THRESHOLD = 2
BALANCE_FACTOR = 0.3
SURVIVAL_FACTOR = 0.6

class SoundLoader:
    """Simple sound loader"""
    def __init__(self):
        self.sounds = {}
        self.load_sounds()
    
    def load_sounds(self):
        # Try to load conversion sound
        conversion_files = ['change.mp3', 'change.wav', 'conversion.mp3', 'conversion.wav']
        for filename in conversion_files:
            if os.path.exists(filename):
                try:
                    self.sounds['conversion'] = pygame.mixer.Sound(filename)
                    self.sounds['conversion'].set_volume(0.3)  # 30% volume
                    print(f"✅ Loaded conversion sound: {filename}")
                    break
                except:
                    pass
        
        # Try to load win sound
        win_files = ['win.mp3', 'win.wav', 'victory.mp3', 'victory.wav']
        for filename in win_files:
            if os.path.exists(filename):
                try:
                    self.sounds['win'] = pygame.mixer.Sound(filename)
                    self.sounds['win'].set_volume(0.5)  # 50% volume
                    print(f"✅ Loaded win sound: {filename}")
                    break
                except:
                    pass
        
        # Create beep sounds as fallback if files don't exist
        if 'conversion' not in self.sounds:
            print("⚠️ No conversion sound file found, using beep")
            self.create_beep_sound('conversion', frequency=440, duration=0.1)
        
        if 'win' not in self.sounds:
            print("⚠️ No win sound file found, using beep")
            self.create_beep_sound('win', frequency=880, duration=0.3)
    
    def create_beep_sound(self, name, frequency=440, duration=0.1):
        """Create a simple beep sound as fallback"""
        sample_rate = 22050
        n_samples = int(sample_rate * duration)
        
        # Create a sine wave
        buf = pygame.sndarray.make_sound(
            ([[int(32767.0 * math.sin(2.0 * math.pi * frequency * t / sample_rate))] 
              for t in range(n_samples)] * 2)
        )
        self.sounds[name] = buf
    
    def play_conversion(self):
        if 'conversion' in self.sounds:
            self.sounds['conversion'].play()
    
    def play_win(self):
        if 'win' in self.sounds:
            self.sounds['win'].play()

class ImageLoader:
    """Simple image loader"""
    def __init__(self):
        self.images = {}
        self.load_images()
    
    def load_images(self):
        image_variations = [
            ['rock.png', 'Rock.png', 'ROCK.png'],
            ['paper.png', 'Paper.png', 'PAPER.png'],
            ['scissors.png', 'scissor.png', 'Scissors.png', 'SCISSORS.png']
        ]
        
        for i, variations in enumerate(image_variations):
            loaded = False
            for filename in variations:
                if os.path.exists(filename):
                    try:
                        img = pygame.image.load(filename).convert_alpha()
                        img = pygame.transform.smoothscale(img, (24, 24))
                        self.images[i] = img
                        print(f"✅ Loaded {TYPE_NAMES[i]}")
                        loaded = True
                        break
                    except:
                        pass
            
            if not loaded:
                # Simple circle fallback
                surf = pygame.Surface((24, 24), pygame.SRCALPHA)
                pygame.draw.circle(surf, TYPE_COLORS[i], (12, 12), 10)
                pygame.draw.circle(surf, WHITE, (12, 12), 10, 2)
                self.images[i] = surf
    
    def get_image(self, agent_type):
        return self.images.get(agent_type)

class Agent:
    def __init__(self, x, y, agent_type, image_loader):
        self.x = x
        self.y = y
        self.type = agent_type
        self.image_loader = image_loader

        # Random movement
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1.2, 2.0)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

        self.size = 12
        self.balance_boost = 1.0
        self.survival_mode = False
        
    def find_nearest(self, agents, target_type):
        """Find the nearest agent of a specific type"""
        nearest = None
        nearest_dist = float('inf')
        
        for agent in agents:
            if agent is not self and agent.type == target_type:
                dx = agent.x - self.x
                dy = agent.y - self.y
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest = agent
        
        return nearest, nearest_dist
    
    def move(self, agents, counts):
        # Check if this agent is in survival mode
        survival_mode = counts[self.type] <= CRITICAL_COUNT_THRESHOLD
        low_team_mode = counts[self.type] <= LOW_COUNT_THRESHOLD
        
        # Calculate boosts
        if survival_mode:
            target_boost = 1.0 + BALANCE_FACTOR + SURVIVAL_FACTOR
            self.survival_mode = True
        elif low_team_mode:
            target_boost = 1.0 + BALANCE_FACTOR
            self.survival_mode = False
        else:
            target_boost = 1.0
            self.survival_mode = False
        
        # Smoothly adjust boost
        self.balance_boost += (target_boost - self.balance_boost) * 0.05
        
        # Survival mode behavior
        if survival_mode and len(agents) > 1:
            predator_type = PREDATOR_TYPE[self.type]
            predator, predator_dist = self.find_nearest(agents, predator_type)
            
            prey_type = PREY_TYPE[self.type]
            prey, prey_dist = self.find_nearest(agents, prey_type)
            
            if predator and predator_dist < 150:
                # Run from predator
                dx = self.x - predator.x
                dy = self.y - predator.y
                dist = max(1, math.sqrt(dx*dx + dy*dy))
                flee_strength = 0.8 * (1 - predator_dist/300)
                self.vx += (dx / dist) * flee_strength
                self.vy += (dy / dist) * flee_strength
                
            elif prey and prey_dist < 200:
                # Chase prey
                dx = prey.x - self.x
                dy = prey.y - self.y
                dist = max(1, math.sqrt(dx*dx + dy*dy))
                chase_strength = 0.6 * (1 - prey_dist/400)
                self.vx += (dx / dist) * chase_strength
                self.vy += (dy / dist) * chase_strength
            
            if random.random() < 0.03:
                angle = random.uniform(0, 2 * math.pi)
                self.vx += math.cos(angle) * 0.3
                self.vy += math.sin(angle) * 0.3
        else:
            # Normal movement
            if random.random() < 0.01:
                angle = random.uniform(0, 2 * math.pi)
                self.vx += math.cos(angle) * 0.2
                self.vy += math.sin(angle) * 0.2

        # Apply movement
        self.x += self.vx * self.balance_boost
        self.y += self.vy * self.balance_boost

        # Bounce
        margin = self.size
        if self.x <= PLAY_AREA_LEFT + margin:
            self.vx = abs(self.vx)
            self.x = PLAY_AREA_LEFT + margin
        if self.x >= PLAY_AREA_RIGHT - margin:
            self.vx = -abs(self.vx)
            self.x = PLAY_AREA_RIGHT - margin
        if self.y <= PLAY_AREA_TOP + margin:
            self.vy = abs(self.vy)
            self.y = PLAY_AREA_TOP + margin
        if self.y >= PLAY_AREA_BOTTOM - margin:
            self.vy = -abs(self.vy)
            self.y = PLAY_AREA_BOTTOM - margin
    
    def draw(self, screen):
        img = self.image_loader.get_image(self.type)
        if img:
            # Add survival mode indicator
            if self.survival_mode:
                # Draw purple ring
                pygame.draw.circle(screen, (180, 100, 255), 
                                 (int(self.x), int(self.y)), 16, 2)
            img_rect = img.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(img, img_rect)
    
    def interact(self, other):
        # Rock-Paper-Scissors rules
        if self.type == 0 and other.type == 2:
            other.type = 0
            return True, 0
        elif self.type == 1 and other.type == 0:
            other.type = 1
            return True, 1
        elif self.type == 2 and other.type == 1:
            other.type = 2
            return True, 2
        elif other.type == 0 and self.type == 2:
            self.type = 0
            return True, 0
        elif other.type == 1 and self.type == 0:
            self.type = 1
            return True, 1
        elif other.type == 2 and self.type == 1:
            self.type = 2
            return True, 2
        
        return False, None

class Simulation:
    def __init__(self):
        self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("RPS Simulation • Grid Counters")
        
        self.game_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        
        self.clock = pygame.time.Clock()
        self.image_loader = ImageLoader()
        self.sound_loader = SoundLoader()  # Initialize sound loader
        
        # Game objects
        self.agents = []
        self.total_wins = [0, 0, 0]
        self.match_history = []
        self.match_winner = None
        self.match_end_time = 0
        self.match_restart_delay = 2000
        self.match_in_progress = True
        
        # Balance tracking
        self.survival_activated = False
        self.last_critical_team = None
        
        # Fonts - Monospace for console feel
        self.font_large = pygame.font.Font(None, 36)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)
        self.font_tiny = pygame.font.Font(None, 14)
        
        # Create watermark font
        self.watermark_font = pygame.font.Font(None, 48)
        self.caption_font = pygame.font.Font(None, 28)
        
        # Controls
        self.paused = False
        
        self.reset_match()
        self.running = True
    
    def get_grid_positions(self):
        """Generate evenly distributed positions"""
        positions = []
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                x = PLAY_AREA_LEFT + col * CELL_WIDTH + CELL_WIDTH // 2
                y = PLAY_AREA_TOP + row * CELL_HEIGHT + CELL_HEIGHT // 2
                x += random.uniform(-5, 5)
                y += random.uniform(-5, 5)
                positions.append((x, y))
        return positions
    
    def get_cluster_positions(self, center_x, center_y, count, radius=80):
        """Generate positions clustered around a center point"""
        positions = []
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, radius)
            x = center_x + math.cos(angle) * distance
            y = center_y + math.sin(angle) * distance
            
            # Clamp to play area
            x = max(PLAY_AREA_LEFT + 20, min(PLAY_AREA_RIGHT - 20, x))
            y = max(PLAY_AREA_TOP + 20, min(PLAY_AREA_BOTTOM - 20, y))
            
            positions.append((x, y))
        return positions
    
    def reset_match(self):
        self.agents = []
        self.survival_activated = False
        self.last_critical_team = None
        
        # Create three cluster centers
        cluster_centers = [
            (PLAY_AREA_LEFT + (PLAY_AREA_RIGHT - PLAY_AREA_LEFT) * 0.25, PLAY_AREA_TOP + (PLAY_AREA_BOTTOM - PLAY_AREA_TOP) * 0.5),  # Left center
            (PLAY_AREA_LEFT + (PLAY_AREA_RIGHT - PLAY_AREA_LEFT) * 0.5, PLAY_AREA_TOP + (PLAY_AREA_BOTTOM - PLAY_AREA_TOP) * 0.5),   # Center
            (PLAY_AREA_LEFT + (PLAY_AREA_RIGHT - PLAY_AREA_LEFT) * 0.75, PLAY_AREA_TOP + (PLAY_AREA_BOTTOM - PLAY_AREA_TOP) * 0.5)    # Right center
        ]
        
        # Shuffle which team gets which cluster
        team_order = [0, 1, 2]
        random.shuffle(team_order)
        
        # Spawn 8 agents in clusters
        for i, team in enumerate(team_order):
            cluster_positions = self.get_cluster_positions(cluster_centers[i][0], cluster_centers[i][1], 8)
            for x, y in cluster_positions:
                self.agents.append(Agent(x, y, team, self.image_loader))
        
        # Spawn remaining 2 agents randomly for each team
        all_positions = self.get_grid_positions()
        random.shuffle(all_positions)
        
        # Track how many we've spawned per team
        spawned_counts = [8, 8, 8]
        
        for team in range(3):
            while spawned_counts[team] < 10:
                # Take random positions from the grid
                if all_positions:
                    x, y = all_positions.pop()
                else:
                    # Fallback if we run out of positions
                    x = random.uniform(PLAY_AREA_LEFT + 20, PLAY_AREA_RIGHT - 20)
                    y = random.uniform(PLAY_AREA_TOP + 20, PLAY_AREA_BOTTOM - 20)
                
                self.agents.append(Agent(x, y, team, self.image_loader))
                spawned_counts[team] += 1
        
        random.shuffle(self.agents)
        self.match_in_progress = True
        print(f"Match started - Rock:10 Paper:10 Scissors:10 (8 clustered, 2 random each)")
    
    def handle_collisions(self):
        # Simple collision detection
        for i in range(len(self.agents)):
            for j in range(i + 1, len(self.agents)):
                agent1 = self.agents[i]
                agent2 = self.agents[j]
                
                dx = agent1.x - agent2.x
                dy = agent1.y - agent2.y
                distance = math.sqrt(dx**2 + dy**2)
                
                if distance < 24:
                    transformed, winner_type = agent1.interact(agent2)
                    if transformed:
                        # Play conversion sound
                        self.sound_loader.play_conversion()
                        
                        if distance > 0:
                            overlap = 24 - distance
                            angle = math.atan2(dy, dx)
                            push_x = math.cos(angle) * overlap * 0.3
                            push_y = math.sin(angle) * overlap * 0.3
                            agent1.x += push_x
                            agent1.y += push_y
                            agent2.x -= push_x
                            agent2.y -= push_y
    
    def count_types(self):
        counts = [0, 0, 0]
        for agent in self.agents:
            counts[agent.type] += 1
        return counts
    
    def check_balance_status(self, counts):
        """Check if any team is in survival mode"""
        critical_teams = []
        
        for i, count in enumerate(counts):
            if count <= CRITICAL_COUNT_THRESHOLD and count > 0:
                critical_teams.append(i)
        
        if critical_teams:
            if not self.survival_activated:
                self.survival_activated = True
                self.last_critical_team = critical_teams[0]
                print(f"⚡ {TYPE_NAMES[critical_teams[0]]} SURVIVAL MODE")
        else:
            self.survival_activated = False
    
    def check_match_winner(self):
        counts = self.count_types()
        alive_types = [i for i, count in enumerate(counts) if count > 0]
        
        self.check_balance_status(counts)
        
        if len(alive_types) == 1 and self.match_in_progress:
            self.match_winner = alive_types[0]
            self.total_wins[self.match_winner] += 1
            self.match_end_time = pygame.time.get_ticks()
            self.match_in_progress = False
            self.match_history.append(self.match_winner)
            if len(self.match_history) > 5:
                self.match_history.pop(0)
            
            # Play win sound
            self.sound_loader.play_win()
            
            print(f"🏆 {TYPE_NAMES[self.match_winner]} wins!")
            return True
        return False
    
    def draw_grid_counters(self):
        """Draw counters inside the grid cells"""
        counts = self.count_types()
        
        # Position counters in specific grid cells (top row, first few columns)
        # Using grid cells: (col 0, row 0), (col 1, row 0), (col 2, row 0)
        
        # Rock counter - first grid cell
        rock_x = PLAY_AREA_LEFT + CELL_WIDTH // 2
        rock_y = PLAY_AREA_TOP + CELL_HEIGHT // 2
        rock_text = self.font_medium.render(f"R:{counts[0]}", True, ROCK_COLOR)
        rock_rect = rock_text.get_rect(center=(rock_x, rock_y))
        # Draw background
        pygame.draw.rect(self.game_surface, DARK_GRAY, 
                        (rock_x - 30, rock_y - 15, 60, 30))
        pygame.draw.rect(self.game_surface, GRAY, 
                        (rock_x - 30, rock_y - 15, 60, 30), 1)
        self.game_surface.blit(rock_text, rock_rect)
        
        # Paper counter - second grid cell
        paper_x = PLAY_AREA_LEFT + CELL_WIDTH * 1 + CELL_WIDTH // 2
        paper_y = PLAY_AREA_TOP + CELL_HEIGHT // 2
        paper_text = self.font_medium.render(f"P:{counts[1]}", True, PAPER_COLOR)
        paper_rect = paper_text.get_rect(center=(paper_x, paper_y))
        pygame.draw.rect(self.game_surface, DARK_GRAY, 
                        (paper_x - 30, paper_y - 15, 60, 30))
        pygame.draw.rect(self.game_surface, GRAY, 
                        (paper_x - 30, paper_y - 15, 60, 30), 1)
        self.game_surface.blit(paper_text, paper_rect)
        
        # Scissors counter - third grid cell
        scissor_x = PLAY_AREA_LEFT + CELL_WIDTH * 2 + CELL_WIDTH // 2
        scissor_y = PLAY_AREA_TOP + CELL_HEIGHT // 2
        scissor_text = self.font_medium.render(f"S:{counts[2]}", True, SCISSORS_COLOR)
        scissor_rect = scissor_text.get_rect(center=(scissor_x, scissor_y))
        pygame.draw.rect(self.game_surface, DARK_GRAY, 
                        (scissor_x - 30, scissor_y - 15, 60, 30))
        pygame.draw.rect(self.game_surface, GRAY, 
                        (scissor_x - 30, scissor_y - 15, 60, 30), 1)
        self.game_surface.blit(scissor_text, scissor_rect)
        
        # Survival mode indicator in fourth grid cell if active
        if self.survival_activated and self.last_critical_team is not None:
            survival_x = PLAY_AREA_LEFT + CELL_WIDTH * 3 + CELL_WIDTH // 2
            survival_y = PLAY_AREA_TOP + CELL_HEIGHT // 2
            survival_text = self.font_small.render("⚡", True, (180, 100, 255))
            survival_rect = survival_text.get_rect(center=(survival_x, survival_y))
            pygame.draw.rect(self.game_surface, DARK_GRAY, 
                            (survival_x - 15, survival_y - 15, 30, 30))
            pygame.draw.rect(self.game_surface, (180, 100, 255), 
                            (survival_x - 15, survival_y - 15, 30, 30), 1)
            self.game_surface.blit(survival_text, survival_rect)
    
    def draw_controls(self):
        """Draw minimal controls at bottom"""
        controls_y = GAME_HEIGHT - 40
        controls_text = "SPACE:pause  R:reset  Q:quit"
        text = self.font_tiny.render(controls_text, True, LIGHT_GRAY)
        self.game_surface.blit(text, (20, controls_y))
        
        if self.paused:
            pause_text = self.font_medium.render("PAUSED", True, GREEN)
            pause_rect = pause_text.get_rect(center=(GAME_WIDTH // 2, GAME_HEIGHT // 2))
            self.game_surface.blit(pause_text, pause_rect)
    
    def draw_grid(self):
        """Draw subtle grid lines"""
        grid_color = (40, 40, 40)
        
        for i in range(GRID_COLS + 1):
            x = PLAY_AREA_LEFT + i * CELL_WIDTH
            pygame.draw.line(self.game_surface, grid_color, 
                           (x, PLAY_AREA_TOP), (x, PLAY_AREA_BOTTOM), 1)
        
        for i in range(GRID_ROWS + 1):
            y = PLAY_AREA_TOP + i * CELL_HEIGHT
            pygame.draw.line(self.game_surface, grid_color,
                           (PLAY_AREA_LEFT, y), (PLAY_AREA_RIGHT, y), 1)
    
    def draw_watermark(self):
        """Draw a single subtle ZOLDA AI watermark in the background"""
        watermark_text = "@zolda Ai"
        
        # Create a surface for the watermark with alpha
        watermark_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
        
        # Render with very low opacity (30 out of 255)
        text_surface = self.watermark_font.render(watermark_text, True, (80, 80, 80, 30))
        
        # Rotate slightly for a more subtle effect
        rotated_text = pygame.transform.rotate(text_surface, -15)
        rotated_rect = rotated_text.get_rect(center=(GAME_WIDTH // 2, GAME_HEIGHT // 2))
        
        # Blit onto watermark surface
        watermark_surface.blit(rotated_text, rotated_rect)
        
        # Blit onto game surface
        self.game_surface.blit(watermark_surface, (0, 0))
    
    def draw_caption(self):
        """Draw the video caption above the arena"""
        caption_text = "why did i watch the whole war till the end? 🤔⚔️🍿"
        
        # Create a gradient background for the caption
        caption_bg = pygame.Surface((GAME_WIDTH - 40, 40))
        caption_bg.set_alpha(180)
        caption_bg.fill(DARK_GRAY)
        self.game_surface.blit(caption_bg, (20, 110))
        
        # Draw border
        pygame.draw.rect(self.game_surface, GREEN, (20, 110, GAME_WIDTH - 40, 40), 1)
        
        # Render caption text
        caption_surface = self.caption_font.render(caption_text, True, GREEN)
        caption_rect = caption_surface.get_rect(center=(GAME_WIDTH // 2, 130))
        self.game_surface.blit(caption_surface, caption_rect)
        
        # Draw a subtle line under the caption
        pygame.draw.line(self.game_surface, GREEN, (30, 155), (GAME_WIDTH - 30, 155), 1)
    
    def draw(self, current_time):
        # Clear
        self.game_surface.fill(BLACK)
        
        # Draw single watermark
        self.draw_watermark()
        
        # Draw caption
        self.draw_caption()
        
        # Draw play area border
        pygame.draw.rect(self.game_surface, GRAY, 
                        (PLAY_AREA_LEFT, PLAY_AREA_TOP, 
                         PLAY_AREA_RIGHT - PLAY_AREA_LEFT, 
                         PLAY_AREA_BOTTOM - PLAY_AREA_TOP), 1)
        
        # Draw grid
        self.draw_grid()
        
        # Draw grid counters (inside the grid cells)
        self.draw_grid_counters()
        
        # Draw agents
        counts = self.count_types()
        for agent in self.agents:
            agent.move(self.agents, counts)
            agent.draw(self.game_surface)
        
        # Draw controls
        self.draw_controls()
        
        # Draw winner message if needed
        if not self.match_in_progress and self.match_winner is not None:
            if current_time - self.match_end_time < self.match_restart_delay:
                winner_text = self.font_large.render(
                    f"{TYPE_NAMES[self.match_winner]} WINS", 
                    True, TYPE_COLORS[self.match_winner]
                )
                text_rect = winner_text.get_rect(center=(GAME_WIDTH//2, GAME_HEIGHT//2))
                self.game_surface.blit(winner_text, text_rect)
    
    def run(self):
        while self.running:
            current_time = pygame.time.get_ticks()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset_match()
                    elif event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif event.key == pygame.K_q:
                        self.running = False
            
            if not self.paused:
                if not self.match_in_progress:
                    if current_time - self.match_end_time > self.match_restart_delay:
                        self.reset_match()
                
                if self.match_in_progress:
                    self.handle_collisions()
                    self.check_match_winner()
            
            # Draw
            self.draw(current_time)
            
            # Blit to window
            self.window.fill(BLACK)
            self.window.blit(self.game_surface, (GAME_OFFSET_X, GAME_OFFSET_Y))
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()

if __name__ == "__main__":
    sim = Simulation()
    sim.run()