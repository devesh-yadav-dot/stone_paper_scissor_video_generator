import pygame
import random
import math
import os
from collections import deque

# Initialize Pygame
pygame.init()
pygame.mixer.init()  # Initialize the mixer for audio

# Windowed mode
WINDOW_WIDTH = 540
WINDOW_HEIGHT = 750

# Game area with 9:16 aspect ratio
GAME_WIDTH = 540
GAME_HEIGHT = 960
GAME_OFFSET_X = (WINDOW_WIDTH - GAME_WIDTH) // 2
GAME_OFFSET_Y = (WINDOW_HEIGHT - GAME_HEIGHT) // 2

FPS = 60

# Colors - Clean and modern
BLACK = (10, 10, 15)
DARK_GRAY = (20, 20, 30)
GRAY = (40, 40, 50)
LIGHT_GRAY = (150, 150, 160)
WHITE = (240, 240, 255)
GOLD = (255, 200, 50)
PURPLE = (180, 100, 255)  # For survival mode
ZOLDA_BLUE = (100, 180, 255)  # ZoldaAI signature color
ZOLDA_PURPLE = (140, 100, 255)  # Secondary Zolda color

# Team Colors - Soft and distinguishable
ROCK_COLOR = (255, 120, 120)      # Soft red
PAPER_COLOR = (100, 255, 140)     # Soft green
SCISSORS_COLOR = (100, 160, 255)  # Soft blue

TYPE_COLORS = [ROCK_COLOR, PAPER_COLOR, SCISSORS_COLOR]
TYPE_NAMES = ["ROCK", "PAPER", "SCISSORS"]
TYPE_ICONS = ["🪨", "📄", "✂️"]

# Prey relationships (what each type hunts)
PREY_TYPE = [2, 0, 1]  # Rock hunts Scissors(2), Paper hunts Rock(0), Scissors hunts Paper(1)
PREDATOR_TYPE = [1, 2, 0]  # Rock is hunted by Paper(1), Paper is hunted by Scissors(2), Scissors is hunted by Rock(0)

# Play area - more space
PLAY_AREA_TOP = 140
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

# ZoldaAI watermark position (center of play area)
ZOLDA_CENTER_X = (PLAY_AREA_LEFT + PLAY_AREA_RIGHT) // 2
ZOLDA_CENTER_Y = (PLAY_AREA_TOP + PLAY_AREA_BOTTOM) // 2

class MusicManager:
    """Manages background music"""
    def __init__(self):
        self.music_file = 'bg.mp3'
        self.volume = 0.5  # 50% volume
        self.is_playing = False
        self.load_music()
    
    def load_music(self):
        """Load and setup background music"""
        if os.path.exists(self.music_file):
            try:
                pygame.mixer.music.load(self.music_file)
                pygame.mixer.music.set_volume(self.volume)
                print(f"✅ Loaded background music: {self.music_file}")
                return True
            except Exception as e:
                print(f"⚠️ Error loading music: {e}")
                return False
        else:
            print(f"⚠️ Music file not found: {self.music_file}")
            return False
    
    def play(self, loops=-1):
        """Play background music (loops indefinitely by default)"""
        if not self.is_playing:
            try:
                pygame.mixer.music.play(loops)
                self.is_playing = True
                print("🎵 Background music started")
            except Exception as e:
                print(f"⚠️ Error playing music: {e}")
    
    def stop(self):
        """Stop background music"""
        if self.is_playing:
            pygame.mixer.music.stop()
            self.is_playing = False
            print("🎵 Background music stopped")
    
    def pause(self):
        """Pause background music"""
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
    
    def unpause(self):
        """Unpause background music"""
        if not self.is_playing:
            pygame.mixer.music.unpause()
            self.is_playing = True
    
    def set_volume(self, volume):
        """Set volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.volume)
    
    def toggle(self):
        """Toggle play/pause"""
        if self.is_playing:
            self.pause()
        else:
            self.unpause()

class ImageLoader:
    """Simple image loader with better filename handling"""
    def __init__(self):
        self.images = {}
        self.load_images()
    
    def load_images(self):
        # Try multiple possible filenames for each type
        image_variations = [
            ['rock.png', 'Rock.png', 'ROCK.png'],
            ['paper.png', 'Paper.png', 'PAPER.png'],
            ['scissors.png', 'scissor.png', 'Scissors.png', 'SCISSORS.png', 'sicssors.png']
        ]
        
        for i, variations in enumerate(image_variations):
            loaded = False
            for filename in variations:
                if os.path.exists(filename):
                    try:
                        img = pygame.image.load(filename).convert_alpha()
                        img = pygame.transform.smoothscale(img, (28, 28))
                        self.images[i] = img
                        print(f"✅ Loaded {TYPE_NAMES[i]}: {filename}")
                        loaded = True
                        break
                    except Exception as e:
                        print(f"⚠️ Error loading {filename}: {e}")
            
            if not loaded:
                print(f"⚠️ Using fallback for {TYPE_NAMES[i]}")
                self.images[i] = self.create_fallback(i)
    
    def create_fallback(self, agent_type):
        """Simple fallback circle with icon"""
        surf = pygame.Surface((28, 28), pygame.SRCALPHA)
        color = TYPE_COLORS[agent_type]
        
        # Background
        pygame.draw.circle(surf, color, (14, 14), 12)
        pygame.draw.circle(surf, WHITE, (14, 14), 12, 2)
        
        # Icon
        font = pygame.font.Font(None, 18)
        icon = font.render(TYPE_ICONS[agent_type], True, WHITE)
        icon_rect = icon.get_rect(center=(14, 14))
        surf.blit(icon, icon_rect)
        
        return surf
    
    def get_image(self, agent_type):
        return self.images.get(agent_type)

class Particle:
    """Simple particle effect"""
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.life = 1.0
        self.vx = random.uniform(-1, 1)
        self.vy = random.uniform(-1, 1)
        self.size = random.randint(2, 3)
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 0.02
        return self.life > 0
    
    def draw(self, screen):
        if self.life > 0:
            alpha = int(self.life * 200)
            size = int(self.size * self.life)
            if size > 0:
                pygame.draw.circle(screen, (*self.color, alpha), 
                                 (int(self.x), int(self.y)), size)

class Agent:
    def __init__(self, x, y, agent_type, image_loader):
        self.x = x
        self.y = y
        self.type = agent_type
        self.image_loader = image_loader
        self.original_type = agent_type

        # Random movement
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1.2, 2.0)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

        self.size = 15
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
        # Check if this agent is in survival mode (team critically low)
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
        
        # SURVIVAL MODE: Smart behavior - avoid predators, hunt prey
        if survival_mode and len(agents) > 1:
            # Find nearest predator (enemy that can kill this agent)
            predator_type = PREDATOR_TYPE[self.type]
            predator, predator_dist = self.find_nearest(agents, predator_type)
            
            # Find nearest prey (enemy this agent can kill)
            prey_type = PREY_TYPE[self.type]
            prey, prey_dist = self.find_nearest(agents, prey_type)
            
            # Decision making: Run from predators, chase prey
            if predator and predator_dist < 150:  # Predator is close
                # Run away from predator
                dx = self.x - predator.x
                dy = self.y - predator.y
                dist = max(1, math.sqrt(dx*dx + dy*dy))
                
                # Strong flee behavior
                flee_strength = 0.8 * (1 - predator_dist/300)
                self.vx += (dx / dist) * flee_strength
                self.vy += (dy / dist) * flee_strength
                
            elif prey and prey_dist < 200:  # Prey is in range
                # Chase prey
                dx = prey.x - self.x
                dy = prey.y - self.y
                dist = max(1, math.sqrt(dx*dx + dy*dy))
                
                # Calculated chase
                chase_strength = 0.6 * (1 - prey_dist/400)
                self.vx += (dx / dist) * chase_strength
                self.vy += (dy / dist) * chase_strength
            
            # More frequent direction changes in survival mode
            if random.random() < 0.03:
                angle = random.uniform(0, 2 * math.pi)
                self.vx += math.cos(angle) * 0.3
                self.vy += math.sin(angle) * 0.3
        
        else:
            # Normal or low team behavior (random movement with slight boost)
            direction_change_chance = 0.01
            if low_team_mode:
                direction_change_chance = 0.015
            
            if random.random() < direction_change_chance:
                angle = random.uniform(0, 2 * math.pi)
                self.vx += math.cos(angle) * 0.2
                self.vy += math.sin(angle) * 0.2

        # Apply balance boost to movement
        self.x += self.vx * self.balance_boost
        self.y += self.vy * self.balance_boost

        # Bounce within play area - NO ENERGY LOSS (perfect bounces)
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

        # NO SPEED LIMIT - agents can go as fast as they want
    
    def draw(self, screen):
        # Draw agent
        img = self.image_loader.get_image(self.type)
        if img:
            img_rect = img.get_rect(center=(int(self.x), int(self.y)))
            
            # Different glow effects based on situation
            if self.survival_mode:
                # Survival mode - purple glow (smart and dangerous)
                glow_size = 25
                glow_surf = pygame.Surface((glow_size*2, glow_size*2), pygame.SRCALPHA)
                
                # Pulsing effect for survival mode
                pulse = 0.7 + 0.3 * math.sin(pygame.time.get_ticks() * 0.005)
                
                # Inner glow
                pygame.draw.circle(glow_surf, (*PURPLE, int(60 * pulse)), 
                                 (glow_size, glow_size), glow_size)
                # Outer ring
                pygame.draw.circle(glow_surf, (*PURPLE, int(40 * pulse)), 
                                 (glow_size, glow_size), glow_size + 5, 2)
                
                screen.blit(glow_surf, (int(self.x - glow_size), int(self.y - glow_size)))
                
                # Draw a small "smart" indicator
                font = pygame.font.Font(None, 14)
                smart_text = font.render("⚡", True, PURPLE)
                screen.blit(smart_text, (int(self.x) + 10, int(self.y) - 20))
                
            elif self.balance_boost > 1.0:
                # Low team mode - subtle colored glow
                glow_size = 20
                glow_surf = pygame.Surface((glow_size*2, glow_size*2), pygame.SRCALPHA)
                glow_color = TYPE_COLORS[self.type]
                pygame.draw.circle(glow_surf, (*glow_color, 30), 
                                 (glow_size, glow_size), glow_size)
                screen.blit(glow_surf, (int(self.x - glow_size), int(self.y - glow_size)))
            
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
        # Create window
        self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Rock Paper Scissors • ZoldaAI Arena")
        
        # Game surface
        self.game_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        
        self.clock = pygame.time.Clock()
        self.image_loader = ImageLoader()
        self.music_manager = MusicManager()  # Initialize music manager
        
        # Game objects
        self.agents = []
        self.particles = []
        self.total_wins = [0, 0, 0]
        self.match_history = []
        self.match_winner = None
        self.match_end_time = 0
        self.match_restart_delay = 3000
        self.match_in_progress = True
        
        # Balance mechanic tracking
        self.balance_activated = False
        self.survival_activated = False
        self.last_low_team = None
        self.last_critical_team = None
        
        # Fonts - Clean and modern
        self.font_huge = pygame.font.Font(None, 72)
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 18)
        self.font_tiny = pygame.font.Font(None, 14)
        
        # Controls
        self.paused = False
        
        # ZoldaAI watermark animation
        self.zolda_pulse = 0
        self.zolda_angle = 0
        
        # Start background music
        self.music_manager.play()
        
        self.reset_match()
        self.running = True
    
    def get_grid_positions(self):
        """Generate evenly distributed positions across the grid"""
        positions = []
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                x = PLAY_AREA_LEFT + col * CELL_WIDTH + CELL_WIDTH // 2
                y = PLAY_AREA_TOP + row * CELL_HEIGHT + CELL_HEIGHT // 2
                # Add small random offset for natural look
                x += random.uniform(-5, 5)
                y += random.uniform(-5, 5)
                positions.append((x, y))
        return positions
    
    def reset_match(self):
        self.agents = []
        self.particles = []
        self.balance_activated = False
        self.survival_activated = False
        self.last_low_team = None
        self.last_critical_team = None
        
        # Get evenly distributed positions
        all_positions = self.get_grid_positions()
        random.shuffle(all_positions)
        
        # Distribute 10 of each type evenly
        positions_per_type = len(all_positions) // 3
        
        for agent_type in range(3):
            start_idx = agent_type * positions_per_type
            end_idx = start_idx + 10  # Take first 10 positions for this type
            
            for i in range(start_idx, end_idx):
                if i < len(all_positions):
                    x, y = all_positions[i]
                    self.agents.append(Agent(x, y, agent_type, self.image_loader))
        
        random.shuffle(self.agents)
        self.match_in_progress = True
        
        # Record starting distribution for fairness check
        print(f"Match started - Rock:10 Paper:10 Scissors:10")
    
    def create_explosion(self, x, y, color):
        for _ in range(5):
            self.particles.append(Particle(x, y, color))
    
    def handle_collisions(self):
        # Spatial partitioning for efficiency
        cell_size = 50
        grid = {}
        
        # Place agents in grid
        for i, agent in enumerate(self.agents):
            grid_x = int(agent.x / cell_size)
            grid_y = int(agent.y / cell_size)
            key = (grid_x, grid_y)
            if key not in grid:
                grid[key] = []
            grid[key].append((i, agent))
        
        # Check collisions in neighboring cells
        checked = set()
        for (grid_x, grid_y), cells in grid.items():
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    neighbor_key = (grid_x + dx, grid_y + dy)
                    if neighbor_key in grid and neighbor_key not in checked:
                        for i1, agent1 in grid[neighbor_key]:
                            for i2, agent2 in grid.get((grid_x, grid_y), []):
                                if i1 >= i2:
                                    continue
                                
                                dx = agent1.x - agent2.x
                                dy = agent1.y - agent2.y
                                distance = math.sqrt(dx**2 + dy**2)
                                
                                if distance < 25:
                                    transformed, winner_type = agent1.interact(agent2)
                                    if transformed:
                                        self.create_explosion(
                                            (agent1.x + agent2.x) / 2,
                                            (agent1.y + agent2.y) / 2,
                                            TYPE_COLORS[winner_type]
                                        )
                                        
                                        if distance > 0:
                                            overlap = 25 - distance
                                            angle = math.atan2(dy, dx)
                                            push_x = math.cos(angle) * overlap * 0.3
                                            push_y = math.sin(angle) * overlap * 0.3
                                            agent1.x += push_x
                                            agent1.y += push_y
                                            agent2.x -= push_x
                                            agent2.y -= push_y
            checked.add((grid_x, grid_y))
    
    def count_types(self):
        counts = [0, 0, 0]
        for agent in self.agents:
            counts[agent.type] += 1
        return counts
    
    def check_balance_status(self, counts):
        """Check if any team is low on members and show subtle indicator"""
        low_teams = []
        critical_teams = []
        
        for i, count in enumerate(counts):
            if count <= CRITICAL_COUNT_THRESHOLD and count > 0:
                critical_teams.append(i)
            elif count <= LOW_COUNT_THRESHOLD and count > 0:
                low_teams.append(i)
        
        # Update status
        if critical_teams:
            if not self.survival_activated:
                self.survival_activated = True
                self.last_critical_team = critical_teams[0]
                print(f"⚡ SURVIVAL MODE - {TYPE_NAMES[critical_teams[0]]} fights smart!")
        elif low_teams:
            if not self.balance_activated:
                self.balance_activated = True
                self.last_low_team = low_teams[0]
                print(f"⚖️ Balance activated - {TYPE_NAMES[low_teams[0]]} needs help!")
        else:
            self.balance_activated = False
            self.survival_activated = False
    
    def check_match_winner(self):
        counts = self.count_types()
        alive_types = [i for i, count in enumerate(counts) if count > 0]
        
        # Check balance status
        self.check_balance_status(counts)
        
        if len(alive_types) == 1 and self.match_in_progress:
            self.match_winner = alive_types[0]
            self.total_wins[self.match_winner] += 1
            self.match_end_time = pygame.time.get_ticks()
            self.match_in_progress = False
            
            # Record match result
            self.match_history.append(self.match_winner)
            if len(self.match_history) > 10:
                self.match_history.pop(0)
            
            # Show match duration info
            winner_name = TYPE_NAMES[self.match_winner]
            print(f"🏆 {winner_name} wins! Match ended")
            
            return True
        return False
    
    def draw_zolda_watermark(self):
        """Draw the ZoldaAI watermark in the center of the play area"""
        current_time = pygame.time.get_ticks()
        
        # Pulsing and rotating effect
        self.zolda_pulse = 0.7 + 0.3 * math.sin(current_time * 0.002)
        self.zolda_angle = (current_time * 0.01) % 360
        
        # Create a surface for the watermark
        watermark_size = 180
        watermark_surf = pygame.Surface((watermark_size, watermark_size), pygame.SRCALPHA)
        
        # Draw outer ring (rotating)
        ring_rect = pygame.Rect(0, 0, watermark_size, watermark_size)
        ring_center = (watermark_size // 2, watermark_size // 2)
        
        # Rotating gradient effect
        for i in range(3):
            angle_offset = self.zolda_angle + i * 120
            color = ZOLDA_BLUE if i % 2 == 0 else ZOLDA_PURPLE
            alpha = int(40 * self.zolda_pulse)
            
            # Draw arc segments
            points = []
            for j in range(0, 360, 30):
                rad = math.radians(angle_offset + j)
                x = ring_center[0] + 80 * math.cos(rad)
                y = ring_center[1] + 80 * math.sin(rad)
                points.append((x, y))
            
            if len(points) > 2:
                pygame.draw.polygon(watermark_surf, (*color, alpha), points, 2)
        
        # Main ZoldaAI text
        font_large = pygame.font.Font(None, int(42 * self.zolda_pulse))
        font_small = pygame.font.Font(None, int(18 * self.zolda_pulse))
        
        # "ZOLDA" with glow
        zolda_text = font_large.render("ZOLDA", True, ZOLDA_BLUE)
        zolda_rect = zolda_text.get_rect(center=(watermark_size // 2, watermark_size // 2 - 15))
        
        # Glow effect
        for offset in [(0, 0)]:  # Simplified glow
            glow_text = font_large.render("ZOLDA", True, (*ZOLDA_BLUE, 30))
            glow_rect = glow_text.get_rect(center=(watermark_size // 2 + offset[0], 
                                                   watermark_size // 2 - 15 + offset[1]))
            watermark_surf.blit(glow_text, glow_rect)
        
        watermark_surf.blit(zolda_text, zolda_rect)
        
        # "AI" with purple
        ai_text = font_large.render("AI", True, ZOLDA_PURPLE)
        ai_rect = ai_text.get_rect(center=(watermark_size // 2, watermark_size // 2 + 15))
        watermark_surf.blit(ai_text, ai_rect)
        
        # Small tech dots
        dot_positions = [(watermark_size // 2 - 60, watermark_size // 2),
                         (watermark_size // 2 + 60, watermark_size // 2),
                         (watermark_size // 2, watermark_size // 2 - 60),
                         (watermark_size // 2, watermark_size // 2 + 60)]
        
        for i, (dx, dy) in enumerate(dot_positions):
            pulse_offset = math.sin(current_time * 0.003 + i) * 0.5 + 0.5
            dot_size = int(3 * pulse_offset) + 1
            pygame.draw.circle(watermark_surf, (*ZOLDA_BLUE, int(100 * pulse_offset)), 
                             (dx, dy), dot_size)
        
        # Blit the watermark centered in play area
        watermark_x = ZOLDA_CENTER_X - watermark_size // 2
        watermark_y = ZOLDA_CENTER_Y - watermark_size // 2
        self.game_surface.blit(watermark_surf, (watermark_x, watermark_y))
        
        # Draw "AI ARENA" subtitle with pulse
        if self.zolda_pulse > 0.9:
            subtitle = self.font_tiny.render("AI ARENA", True, (ZOLDA_BLUE[0], ZOLDA_BLUE[1], ZOLDA_BLUE[2], 100))
            subtitle_rect = subtitle.get_rect(center=(ZOLDA_CENTER_X, ZOLDA_CENTER_Y + 60))
            self.game_surface.blit(subtitle, subtitle_rect)
    
    def draw_ui(self):
        # Top bar - Clean and minimal
        bar_y = 20
        bar_height = 100
        
        # Semi-transparent background
        bar_surf = pygame.Surface((GAME_WIDTH - 40, bar_height), pygame.SRCALPHA)
        bar_surf.fill((20, 20, 30, 200))
        self.game_surface.blit(bar_surf, (20, bar_y))
        
        # Title with ZoldaAI reference
        title = self.font_medium.render("ZOLDA AI ARENA • ROCK PAPER SCISSORS", True, GOLD)
        title_rect = title.get_rect(center=(GAME_WIDTH//2, bar_y + 25))
        self.game_surface.blit(title, title_rect)
        
        # Team stats
        counts = self.count_types()
        stats_y = bar_y + 50
        
        for i in range(3):
            x = 70 + i * 150
            
            # Icon
            icon = self.image_loader.get_image(i)
            if icon:
                small_icon = pygame.transform.smoothscale(icon, (20, 20))
                self.game_surface.blit(small_icon, (x - 30, stats_y))
            
            # Count with threshold indicator
            count_text = self.font_large.render(str(counts[i]), True, TYPE_COLORS[i])
            
            # Highlight based on situation
            if counts[i] <= CRITICAL_COUNT_THRESHOLD and counts[i] > 0:
                # Critical - purple glow
                glow_rect = pygame.Rect(x - 20, stats_y - 15, 50, 50)
                pygame.draw.rect(self.game_surface, (*PURPLE, 80), glow_rect, 3)
                # Add "SMART" indicator
                smart_text = self.font_small.render("SMART", True, PURPLE)
                self.game_surface.blit(smart_text, (x - 15, stats_y - 30))
            elif counts[i] <= LOW_COUNT_THRESHOLD and counts[i] > 0:
                # Low - team color glow
                glow_rect = pygame.Rect(x - 15, stats_y - 10, 40, 40)
                pygame.draw.rect(self.game_surface, (*TYPE_COLORS[i], 50), glow_rect, 2)
            
            self.game_surface.blit(count_text, (x, stats_y - 5))
            
            # Name
            name_text = self.font_small.render(TYPE_NAMES[i], True, LIGHT_GRAY)
            self.game_surface.blit(name_text, (x - 10, stats_y + 30))
        
        # Wins
        wins_y = bar_y + 85
        wins_text = f"🏆 {self.total_wins[0]}  |  {self.total_wins[1]}  |  {self.total_wins[2]}"
        wins_surf = self.font_small.render(wins_text, True, GOLD)
        wins_rect = wins_surf.get_rect(center=(GAME_WIDTH//2, wins_y))
        self.game_surface.blit(wins_surf, wins_rect)
        
        # Bottom bar
        bottom_y = GAME_HEIGHT - 70
        
        bar_surf = pygame.Surface((GAME_WIDTH - 40, 50), pygame.SRCALPHA)
        bar_surf.fill((20, 20, 30, 200))
        self.game_surface.blit(bar_surf, (20, bottom_y))
        
        # Controls and status indicators
        controls = "⏯️ SPACE  |  🔄 R  |  ❌ Q  |  🎵 M"
        if self.paused:
            controls = "⏸️ PAUSED  |  🔄 R  |  ❌ Q  |  🎵 M"
        
        control_text = self.font_small.render(controls, True, WHITE)
        control_rect = control_text.get_rect(center=(GAME_WIDTH//2, bottom_y + 20))
        self.game_surface.blit(control_text, control_rect)
        
        # Music indicator
        music_indicator = "🎵 ON" if self.music_manager.is_playing else "🎵 OFF"
        music_color = GOLD if self.music_manager.is_playing else LIGHT_GRAY
        music_text = self.font_small.render(music_indicator, True, music_color)
        self.game_surface.blit(music_text, (GAME_WIDTH - 100, bottom_y + 35))
        
        # Status indicators
        if self.survival_activated and self.last_critical_team is not None:
            status_text = self.font_small.render(f"⚡ SURVIVAL: {TYPE_NAMES[self.last_critical_team]}", True, PURPLE)
            self.game_surface.blit(status_text, (50, bottom_y + 35))
        elif self.balance_activated and self.last_low_team is not None:
            status_text = self.font_small.render(f"⚖️ BOOST: {TYPE_NAMES[self.last_low_team]}", True, GOLD)
            self.game_surface.blit(status_text, (50, bottom_y + 35))
    
    def draw_winner(self, current_time):
        if not self.match_in_progress and self.match_winner is not None:
            # Semi-transparent overlay
            overlay = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill(BLACK)
            self.game_surface.blit(overlay, (0, 0))
            
            # Pulsing effect
            pulse = 1 + math.sin(current_time * 0.003) * 0.1
            
            # Winner text
            winner_text = self.font_huge.render(
                f"{TYPE_NAMES[self.match_winner]} WINS!",
                True, TYPE_COLORS[self.match_winner]
            )
            
            # Scale with pulse
            winner_text = pygame.transform.scale(winner_text, 
                (int(winner_text.get_width() * pulse), 
                 int(winner_text.get_height() * pulse)))
            
            text_rect = winner_text.get_rect(center=(GAME_WIDTH//2, GAME_HEIGHT//2 - 50))
            self.game_surface.blit(winner_text, text_rect)
            
            # Countdown
            remaining = max(0, (self.match_restart_delay - 
                              (current_time - self.match_end_time)) // 1000 + 1)
            countdown = self.font_large.render(f"Next in {remaining}s", True, WHITE)
            countdown_rect = countdown.get_rect(center=(GAME_WIDTH//2, GAME_HEIGHT//2 + 50))
            self.game_surface.blit(countdown, countdown_rect)
            
            # Match history
            history_y = GAME_HEIGHT//2 + 120
            history_text = self.font_small.render("Recent winners:", True, LIGHT_GRAY)
            self.game_surface.blit(history_text, (GAME_WIDTH//2 - 60, history_y))
            
            for i, winner in enumerate(reversed(self.match_history[-5:])):
                winner_name = TYPE_NAMES[winner][0]
                color = TYPE_COLORS[winner]
                hist = self.font_medium.render(winner_name, True, color)
                self.game_surface.blit(hist, (GAME_WIDTH//2 - 30 + i * 30, history_y + 25))
    
    def draw_grid_lines(self):
        """Draw subtle grid lines to show fair distribution"""
        grid_color = (30, 30, 40)
        
        # Vertical lines
        for i in range(GRID_COLS + 1):
            x = PLAY_AREA_LEFT + i * CELL_WIDTH
            pygame.draw.line(self.game_surface, grid_color, 
                           (x, PLAY_AREA_TOP), (x, PLAY_AREA_BOTTOM), 1)
        
        # Horizontal lines
        for i in range(GRID_ROWS + 1):
            y = PLAY_AREA_TOP + i * CELL_HEIGHT
            pygame.draw.line(self.game_surface, grid_color,
                           (PLAY_AREA_LEFT, y), (PLAY_AREA_RIGHT, y), 1)
    
    def draw(self, current_time):
        # Clear game surface
        self.game_surface.fill((12, 12, 18))
        
        # Draw subtle grid
        self.draw_grid_lines()
        
        # Draw play area border
        pygame.draw.rect(self.game_surface, (40, 40, 50), 
                        (PLAY_AREA_LEFT, PLAY_AREA_TOP, 
                         PLAY_AREA_RIGHT - PLAY_AREA_LEFT, 
                         PLAY_AREA_BOTTOM - PLAY_AREA_TOP), 1)
        
        # Draw ZoldaAI watermark in the center
        self.draw_zolda_watermark()
        
        # Get current counts for balance mechanic
        counts = self.count_types()
        
        # Draw agents (pass counts and full agent list for smart behavior)
        for agent in self.agents:
            agent.move(self.agents, counts)  # Pass agents list and counts
            agent.draw(self.game_surface)
        
        # Draw particles
        for particle in self.particles:
            particle.draw(self.game_surface)
        
        # Draw UI
        self.draw_ui()
        self.draw_winner(current_time)
    
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
                    elif event.key == pygame.K_m:
                        self.music_manager.toggle()  # Toggle music on/off
                    elif event.key == pygame.K_q:
                        self.running = False
            
            if not self.paused:
                if not self.match_in_progress:
                    if current_time - self.match_end_time > self.match_restart_delay:
                        self.reset_match()
                
                if self.match_in_progress:
                    # Handle collisions and check winner
                    self.handle_collisions()
                    self.check_match_winner()
                
                # Update particles
                self.particles = [p for p in self.particles if p.update()]
            
            # Draw (includes movement with counts and agent list)
            self.draw(current_time)
            
            # Clear window
            self.window.fill((5, 5, 10))
            
            # Blit game surface centered
            self.window.blit(self.game_surface, (GAME_OFFSET_X, GAME_OFFSET_Y))
            
            # Draw side panels info
            if GAME_OFFSET_X > 0:
                info_text = self.font_small.render("ZoldaAI Arena", True, (60, 60, 70))
                self.window.blit(info_text, (10, 10))
                
                # Mechanic indicators
                mech_text = self.font_small.render("⚖️ Boost | ⚡ Survival | 🎵 M", True, GOLD)
                self.window.blit(mech_text, (WINDOW_WIDTH - 280, 10))
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        # Stop music when game closes
        self.music_manager.stop()
        pygame.quit()

if __name__ == "__main__":
    sim = Simulation()
    sim.run()