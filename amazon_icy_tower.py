"""
Amazon Icy Tower - An authentic recreation of the classic Icy Tower game
Built with Python and PyGame

Controls:
- WASD or Arrow Keys: Move left/right and jump  
- SPACE: Jump (alternative to up arrow/W)
- ESC: Quit game
- SPACE: Restart game (when game over)

Game Features:
- Momentum-based physics with wall bouncing
- Progressive difficulty with moving floors
- Combo system for multi-floor jumps
- Varying platform lengths based on floor levels
- Checkpoint platforms every 10 floors
- Authentic Harold character design
- Real-time statistics and scoring
"""

import pygame
import random
import math
import sys

# Initialize Pygame
pygame.init()

# Game constants - Based on original Icy Tower mechanics
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
GRAVITY = 0.3  # Reduced from 0.4 to make vertical movement even slower
JUMP_STRENGTH = -8  # Reduced from -9 to compensate for even lower gravity
MAX_SPEED = 10
ACCELERATION = 0.4
FRICTION = 0.85
WALL_BOUNCE_FACTOR = 0.9  # Maintain most speed when bouncing off walls
PLATFORM_HEIGHT = 30  # Match the height of side brick tiles
CAMERA_SMOOTH = 0.15

# Floor spacing - matches original game progression
FLOOR_SPACING = 100  # Distance between floors
COMBO_MIN_FLOORS = 2  # Minimum floors to jump for combo

# Colors - Based on original floor types with distinct visual sets
FLOOR_COLORS = {
    'stone': (100, 150, 100),    # Green (0-9)
    'ice': (100, 150, 255),      # Blue (10-19)
    'wood': (139, 69, 19),       # Brown (20-29)
    'metal': (169, 169, 169),    # Gray (30-39)
    'gum': (255, 105, 180),      # Pink (40-49)
    'bone': (245, 245, 220),     # Beige (50-59)
    'vines': (34, 139, 34),      # Dark Green (60-69)
    'pipe': (105, 105, 105),     # Dark Gray (70-79)
    'cloud': (240, 248, 255),    # Light Blue (80-89)
    'rainbow': (255, 0, 255),    # Magenta (90-99)
    'glass': (173, 216, 230)     # Light Blue (100+)
}

# Game colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (100, 150, 255)
GREEN = (100, 255, 100)
RED = (255, 100, 100)
YELLOW = (255, 255, 100)
PURPLE = (200, 100, 255)
ORANGE = (255, 165, 0)
PINK = (255, 192, 203)

# Harold's authentic colors
LIGHT_SKIN = (255, 220, 177)    # Light skin tone
DARK_BLUE_HAT = (25, 25, 112)   # Dark blue hat (changed from orange)
GREEN_SWEATER = (34, 139, 34)   # Green sweater
DARK_BROWN_PANTS = (101, 67, 33) # Dark brown pants (same as shoes before)
BROWN_SHOES = (70, 45, 20)      # Even darker brown sneakers

# Well/Tower background colors
DARK_GRAY_TILE = (60, 60, 60)      # Darker uniform gray tiles
MORTAR_GRAY = (40, 40, 40)          # Darker mortar between tiles

# Spark colors for combos
SPARK_COLORS = [YELLOW, ORANGE, RED, PINK, WHITE, GREEN, PURPLE]

class Spark:
    """Lightweight particle for combo effects"""
    def __init__(self, x, y, vel_x, vel_y, color, life):
        self.x = x
        self.y = y
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.color = color
        self.life = life
        self.max_life = life
        
    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.vel_y += 0.2  # Gravity on sparks
        self.life -= 1
        return self.life > 0
    
    def draw(self, screen, camera_y):
        if self.life > 0:
            # Fade alpha based on remaining life
            alpha = int(255 * (self.life / self.max_life))
            color_with_alpha = (*self.color, alpha)
            
            # Draw as a small rectangle (1-2 pixels)
            size = 2 if self.life > self.max_life // 2 else 1
            pygame.draw.rect(screen, self.color, 
                           (int(self.x), int(self.y - camera_y), size, size))

class ParticleSystem:
    """Manages all particles/sparks"""
    def __init__(self):
        self.sparks = []
    
    def add_combo_sparks(self, x, y, combo_level):
        """Add sparks for combo effects"""
        num_sparks = min(combo_level * 3, 20)  # More sparks for higher combos
        
        for _ in range(num_sparks):
            # Random velocity in all directions
            vel_x = random.uniform(-4, 4)
            vel_y = random.uniform(-6, -2)
            
            # Color based on combo level
            if combo_level >= 10:
                color = random.choice([PINK, PURPLE, WHITE])
            elif combo_level >= 5:
                color = random.choice([YELLOW, ORANGE, RED])
            else:
                color = random.choice([GREEN, YELLOW])
            
            life = random.randint(20, 40)
            spark = Spark(x + random.randint(-10, 10), y + random.randint(-5, 5), 
                         vel_x, vel_y, color, life)
            self.sparks.append(spark)
    
    def update(self):
        """Update all sparks and remove dead ones"""
        self.sparks = [spark for spark in self.sparks if spark.update()]
    
    def draw(self, screen, camera_y):
        """Draw all sparks"""
        for spark in self.sparks:
            spark.draw(screen, camera_y)

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 30  # Match the actual visual character width
        self.height = 45  # Match Harold's actual visual height
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = True
        self.color = BLUE
        
        # Rotation for combo jumps
        self.rotation = 0
        self.rotation_speed = 0
        
        # Combo system
        self.combo_active = False
        self.combo_floors = 0
        self.combo_timer = 0
        self.combo_max_time = 180  # 3 seconds at 60 FPS (increased from 60 for longer display)
        self.total_combo_floors = 0
        self.last_floor = 0
        
        # Statistics
        self.highest_floor = 0
        self.score = 0
        
    def update(self, platforms, current_floor, particle_system=None):
        # Handle input
        keys = pygame.key.get_pressed()
        
        # Horizontal movement with acceleration - key to original mechanics
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x -= ACCELERATION
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x += ACCELERATION
            
        # Apply friction when not pressing keys
        if not (keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_RIGHT] or keys[pygame.K_d]):
            self.vel_x *= FRICTION
            
        # Limit horizontal speed
        self.vel_x = max(-MAX_SPEED, min(MAX_SPEED, self.vel_x))
        
        # Jumping - only from ground/platforms
        if keys[pygame.K_SPACE] and self.on_ground:
            # Jump strength based on horizontal speed (original mechanic)
            speed_factor = abs(self.vel_x) / MAX_SPEED
            jump_boost = speed_factor * 1.0  # Reduced from 1.5 to 1.0 for even slower combo movement
            self.vel_y = JUMP_STRENGTH - jump_boost
            self.on_ground = False
            
            # Set rotation speed for combo jumps (faster spinning for more dynamic effect)
            if self.combo_active or speed_factor > 0.5:  # High speed or combo jump
                self.rotation_speed = abs(self.vel_x) * 1.5  # Increased from 0.8 to 1.5 for faster spinning
        
        # Apply gravity
        self.vel_y += GRAVITY
        
        # Update rotation when in air during combos
        if not self.on_ground and (self.combo_active or abs(self.vel_x) > 6):
            self.rotation += self.rotation_speed
            if self.rotation >= 360:
                self.rotation -= 360
        else:
            # Reset rotation when on ground
            self.rotation = 0
            self.rotation_speed = 0
        
        # Update position
        self.x += self.vel_x
        self.y += self.vel_y
        
        # Wall bouncing - CRITICAL original mechanic
        # Harold should not be able to reach the actual walls - they are boundaries
        wall_boundary_left = 100  # Left wall boundary (matches wall width)
        wall_boundary_right = WINDOW_WIDTH - 100  # Right wall boundary
        
        if self.x < wall_boundary_left:
            self.x = wall_boundary_left
            if self.vel_x < 0:
                self.vel_x = -self.vel_x * WALL_BOUNCE_FACTOR  # Bounce with most speed maintained
        elif self.x + self.width > wall_boundary_right:
            self.x = wall_boundary_right - self.width
            if self.vel_x > 0:
                self.vel_x = -self.vel_x * WALL_BOUNCE_FACTOR  # Bounce with most speed maintained
        
        # Platform collision detection - prioritize platforms directly above
        self.on_ground = False
        player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        # First, check if character has ground support (prevent levitation when moving off edges)
        if self.vel_y >= 0:  # Only check when falling or stationary
            has_ground_support = False
            ground_check_rect = pygame.Rect(self.x, self.y + self.height, self.width, 5)  # Small rect below character
            
            for platform in platforms:
                platform_rect = pygame.Rect(platform['x'], platform['y'], platform['width'], platform['height'])
                
                # Check if there's a platform directly below the character
                if (platform['y'] >= self.y + self.height and  # Platform is below character
                    platform['y'] <= self.y + self.height + 10):  # Within small distance
                    
                    # Check horizontal overlap for support
                    player_left = self.x
                    player_right = self.x + self.width
                    platform_left = platform['x']
                    platform_right = platform['x'] + platform['width']
                    
                    support_left = max(player_left, platform_left)
                    support_right = min(player_right, platform_right)
                    support_width = max(0, support_right - support_left)
                    
                    # Require at least 50% support for narrower character
                    min_support_needed = self.width * 0.5
                    
                    if support_width >= min_support_needed:
                        has_ground_support = True
                        # Snap to platform if very close
                        if abs(platform['y'] - (self.y + self.height)) <= 5:
                            self.y = platform['y'] - self.height
                            self.vel_y = 0
                            self.on_ground = True
                            
                            # Floor tracking for ground support landing
                            landed_floor = platform['floor']
                            if landed_floor > self.highest_floor:
                                self.highest_floor = landed_floor
                                if landed_floor > 0:
                                    self.score += 10
                            
                            floors_jumped = landed_floor - self.last_floor
                            if floors_jumped >= COMBO_MIN_FLOORS:
                                if not self.combo_active:
                                    self.combo_active = True
                                    self.total_combo_floors = floors_jumped
                                else:
                                    self.total_combo_floors += floors_jumped
                                
                                self.combo_timer = self.combo_max_time
                                self.combo_floors = floors_jumped
                                
                                if floors_jumped == 2:
                                    self.score += 20
                                elif floors_jumped == 3:
                                    self.score += 50
                                elif floors_jumped >= 4:
                                    self.score += floors_jumped * 25
                                
                                if particle_system:
                                    spark_x = self.x + self.width // 2
                                    spark_y = self.y + self.height // 2
                                    particle_system.add_combo_sparks(spark_x, spark_y, floors_jumped)
                            else:
                                if self.combo_active:
                                    self.end_combo()
                            
                            self.last_floor = landed_floor
                            return  # Found ground support, no need to check collisions
                        break
            
            # If no ground support and character is falling, they should continue falling
            if not has_ground_support and self.vel_y >= 0:
                self.on_ground = False
        
        # Enhanced platform grabbing for stunt jumps - check for nearby platforms during upward movement
        if self.vel_y < 0 and abs(self.vel_x) > 4:  # Moving up with good horizontal speed (stunt jump)
            grab_distance = 35  # Distance Harold can reach to grab a platform during stunt jumps
            speed_factor = abs(self.vel_x) / MAX_SPEED
            enhanced_grab_distance = grab_distance + (speed_factor * 15)  # Up to 50 pixels for max speed
            
            # Create a grab zone above Harold
            grab_rect = pygame.Rect(self.x - 10, self.y - enhanced_grab_distance, self.width + 20, enhanced_grab_distance)
            
            for platform in platforms:
                platform_rect = pygame.Rect(platform['x'], platform['y'], platform['width'], platform['height'])
                
                # Check if platform is within grab range
                if (grab_rect.colliderect(platform_rect) and 
                    platform['y'] < self.y and  # Platform is above Harold
                    platform['y'] > self.y - enhanced_grab_distance):  # Within enhanced grab distance
                    
                    # Check horizontal alignment - Harold needs reasonable overlap
                    player_center_x = self.x + self.width // 2
                    platform_left = platform['x']
                    platform_right = platform['x'] + platform['width']
                    
                    # More generous horizontal alignment for stunt jumps
                    horizontal_tolerance = 15 + (speed_factor * 10)  # Up to 25 pixels tolerance
                    horizontal_overlap = (player_center_x >= platform_left - horizontal_tolerance and 
                                        player_center_x <= platform_right + horizontal_tolerance)
                    
                    if horizontal_overlap:
                        # Harold grabs the platform and lands on top
                        self.y = platform['y'] - self.height
                        self.vel_y = 0
                        self.on_ground = True
                        
                        # Adjust horizontal position slightly toward platform center if needed
                        platform_center = platform['x'] + platform['width'] // 2
                        if abs(player_center_x - platform_center) > platform['width'] // 2:
                            if player_center_x < platform_center:
                                self.x = max(platform['x'] - 5, self.x)
                            else:
                                self.x = min(platform['x'] + platform['width'] - self.width + 5, self.x)
                        
                        # Floor tracking and combo system for grabbed platforms
                        landed_floor = platform['floor']
                        if landed_floor > self.highest_floor:
                            self.highest_floor = landed_floor
                            if landed_floor > 0:
                                self.score += 10
                        
                        floors_jumped = landed_floor - self.last_floor
                        if floors_jumped >= COMBO_MIN_FLOORS:
                            if not self.combo_active:
                                self.combo_active = True
                                self.total_combo_floors = floors_jumped
                            else:
                                self.total_combo_floors += floors_jumped
                            
                            self.combo_timer = self.combo_max_time
                            self.combo_floors = floors_jumped
                            
                            # Bonus points for multi-floor jumps
                            if floors_jumped == 2:
                                self.score += 20
                            elif floors_jumped == 3:
                                self.score += 50
                            elif floors_jumped >= 4:
                                self.score += floors_jumped * 25
                        else:
                            if self.combo_active:
                                self.end_combo()
                        
                        self.last_floor = landed_floor
                        return  # Successfully grabbed platform, skip regular collision detection
        
        # Find platforms that the player is colliding with
        colliding_platforms = []
        for platform in platforms:
            platform_rect = pygame.Rect(platform['x'], platform['y'], platform['width'], platform['height'])
            if player_rect.colliderect(platform_rect):
                colliding_platforms.append((platform, platform_rect))
        
        # Sort platforms by Y position (highest first for upward jumps, lowest first for falling)
        if self.vel_y < 0:  # Jumping up
            colliding_platforms.sort(key=lambda x: x[0]['y'], reverse=True)  # Highest platforms first
        else:  # Falling down
            colliding_platforms.sort(key=lambda x: x[0]['y'])  # Lowest platforms first
        
        for platform, platform_rect in colliding_platforms:
            # Calculate overlaps more precisely
            overlap_top = (self.y + self.height) - platform['y']
            overlap_bottom = (platform['y'] + platform['height']) - self.y
            overlap_left = (self.x + self.width) - platform['x']
            overlap_right = (platform['x'] + platform['width']) - self.x
            
            # Determine collision type based on player movement and overlap
            # More generous collision detection for bigger Harold
            if self.vel_y >= 0 and overlap_top > 0 and overlap_top < self.height * 0.8:
                # Check if player has enough support on the platform (prevent levitation)
                player_left = self.x
                player_right = self.x + self.width
                platform_left = platform['x']
                platform_right = platform['x'] + platform['width']
                
                # Calculate how much of the player is supported by the platform
                support_left = max(player_left, platform_left)
                support_right = min(player_right, platform_right)
                support_width = max(0, support_right - support_left)
                
                # Require at least 50% of the player's width to be supported
                min_support_needed = self.width * 0.5
                
                if support_width >= min_support_needed:
                    # Landing on top of platform (falling down or just touching)
                    self.y = platform['y'] - self.height
                    self.vel_y = 0
                    self.on_ground = True
                else:
                    # Not enough support - player should fall
                    continue
                
                # Floor tracking and combo system
                landed_floor = platform['floor']
                if landed_floor > self.highest_floor:
                    self.highest_floor = landed_floor
                    # 10 points per floor starting from floor 1
                    if landed_floor > 0:
                        self.score += 10
                
                # Combo system - original mechanics with enhanced scoring
                floors_jumped = landed_floor - self.last_floor
                if floors_jumped >= COMBO_MIN_FLOORS:
                    if not self.combo_active:
                        # Start new combo
                        self.combo_active = True
                        self.total_combo_floors = floors_jumped
                    else:
                        # Continue combo
                        self.total_combo_floors += floors_jumped
                    
                    self.combo_timer = self.combo_max_time
                    self.combo_floors = floors_jumped
                    
                    # Bonus points for multi-floor jumps
                    if floors_jumped == 2:
                        self.score += 20  # Double jump bonus
                    elif floors_jumped == 3:
                        self.score += 50  # Triple jump bonus
                    elif floors_jumped >= 4:
                        self.score += floors_jumped * 25  # Big jump bonus
                    
                    # Generate combo sparks
                    if particle_system:
                        spark_x = self.x + self.width // 2
                        spark_y = self.y + self.height // 2
                        particle_system.add_combo_sparks(spark_x, spark_y, floors_jumped)
                else:
                    # End combo if jump was too small
                    if self.combo_active:
                        self.end_combo()
                
                self.last_floor = landed_floor
                break  # Stop checking other platforms once we land
                
            elif self.vel_y <= 0 and overlap_bottom > 0 and overlap_bottom < self.height * 0.8:
                # Hit platform from below (jumping up) or just touching
                # First check if there's meaningful horizontal overlap to avoid invisible collisions
                player_left = self.x
                player_right = self.x + self.width
                platform_left = platform['x']
                platform_right = platform['x'] + platform['width']
                
                # Check horizontal overlap - must have reasonable overlap to interact
                horizontal_overlap_left = max(player_left, platform_left)
                horizontal_overlap_right = min(player_right, platform_right)
                horizontal_overlap_width = max(0, horizontal_overlap_right - horizontal_overlap_left)
                
                # Only process collision if there's meaningful horizontal overlap (at least 30%)
                if horizontal_overlap_width >= self.width * 0.3:
                    # Check if we can land on top instead of bouncing off bottom
                    player_top = self.y
                    platform_top = platform['y']
                    
                    # Enhanced threshold for landing - MORE generous for stunt jumps
                    base_threshold = 35  # Increased for bigger Harold
                    speed_factor = abs(self.vel_x) / MAX_SPEED
                    
                    # Increase threshold for high-speed stunt jumps (spacebar + arrow)
                    if speed_factor > 0.6:  # High horizontal speed (stunt jump)
                        landing_threshold = base_threshold + (speed_factor * 25)  # Up to 60 pixels
                    elif abs(self.vel_x) < 2:  # Vertical jumps
                        landing_threshold = base_threshold + 15  # 50 pixels for straight up
                    else:
                        landing_threshold = base_threshold
                    
                    # If player's top is close to platform's top, land on it
                    if abs(player_top - platform_top) < landing_threshold:
                        # Calculate how much of the player is supported by the platform
                        support_left = max(player_left, platform_left)
                        support_right = min(player_right, platform_right)
                        support_width = max(0, support_right - support_left)
                        
                        # Require at least 50% of the player's width to be supported
                        min_support_needed = self.width * 0.5
                        
                        if support_width >= min_support_needed:
                            self.y = platform['y'] - self.height
                            self.vel_y = 0
                            self.on_ground = True
                        else:
                            # Not enough support - continue with normal bottom collision
                            self.y = platform['y'] + platform['height']
                            self.vel_y = 0
                            break
                        
                        # Floor tracking and combo system (same as above)
                        landed_floor = platform['floor']
                        if landed_floor > self.highest_floor:
                            self.highest_floor = landed_floor
                            # 10 points per floor starting from floor 1
                            if landed_floor > 0:
                                self.score += 10
                        
                        floors_jumped = landed_floor - self.last_floor
                        if floors_jumped >= COMBO_MIN_FLOORS:
                            if not self.combo_active:
                                self.combo_active = True
                                self.total_combo_floors = floors_jumped
                            else:
                                self.total_combo_floors += floors_jumped
                            
                            self.combo_timer = self.combo_max_time
                            self.combo_floors = floors_jumped
                            
                            # Bonus points for multi-floor jumps
                            if floors_jumped == 2:
                                self.score += 20  # Double jump bonus
                            elif floors_jumped == 3:
                                self.score += 50  # Triple jump bonus
                            elif floors_jumped >= 4:
                                self.score += floors_jumped * 25  # Big jump bonus
                        else:
                            if self.combo_active:
                                self.end_combo()
                        
                        self.last_floor = landed_floor
                        break  # Land on first reachable platform, don't check others
                    else:
                        # Normal bottom collision - bounce off
                        self.y = platform['y'] + platform['height']
                        self.vel_y = 0
                        break
                # If no meaningful horizontal overlap, skip this collision entirely
                    
            elif abs(self.vel_x) > 0.1:  # Side collision
                # Only trigger side collision if we're actually hitting the side, not just grazing
                # Check if this is a genuine side collision vs. a landing attempt
                
                # Calculate vertical overlap to determine if this is more of a side hit or landing attempt
                vertical_overlap = min(overlap_top, overlap_bottom)
                horizontal_overlap = min(overlap_left, overlap_right)
                
                # Only treat as side collision if:
                # 1. Horizontal overlap is small (actually hitting the side)
                # 2. Vertical overlap is significant (not just grazing the top/bottom)
                # 3. Character is moving horizontally with reasonable speed
                
                if (horizontal_overlap < 8 and vertical_overlap > 10 and 
                    abs(self.vel_x) > 2):  # More restrictive conditions
                    
                    if overlap_left < overlap_right:  # Hit from left side
                        self.x = platform['x'] - self.width
                        self.vel_x = -abs(self.vel_x) * 0.7  # Bounce away
                        break
                    else:  # Hit from right side
                        self.x = platform['x'] + platform['width']
                        self.vel_x = abs(self.vel_x) * 0.7  # Bounce away
                        break
        
        # Update combo timer
        if self.combo_active:
            self.combo_timer -= 1
            if self.combo_timer <= 0:
                self.end_combo()
    
    def end_combo(self):
        if self.combo_active and self.total_combo_floors > 0:
            # Award combo points based on total floors climbed
            combo_score = self.total_combo_floors * self.total_combo_floors * 10
            self.score += combo_score
            
        self.combo_active = False
        self.combo_floors = 0
        self.total_combo_floors = 0
        self.combo_timer = 0
    
    def get_combo_text(self):
        if not self.combo_active:
            return ""
        
        if self.total_combo_floors >= 50:
            return "EXTREME!"
        elif self.total_combo_floors >= 30:
            return "AMAZING!"
        elif self.total_combo_floors >= 20:
            return "WOW!"
        elif self.total_combo_floors >= 15:
            return "GREAT!"
        elif self.total_combo_floors >= 10:
            return "SWEET!"
        elif self.total_combo_floors >= 5:
            return "GOOD!"
        else:
            return "COMBO"
    
    def draw_pixelated_harold(self, screen, x, y, combo_glow_color=None):
        """Draw a pixelated Harold character with authentic colors - bigger with baggy clothes"""
        # Harold is now 30x45 pixels, bigger and baggier
        
        # Dark Blue Beanie (12x8 pixels at top, covers eyes completely)
        beanie_color = DARK_BLUE_HAT
        if combo_glow_color and self.combo_active:
            # Add glow effect during combos
            r, g, b = beanie_color
            glow_r, glow_g, glow_b = combo_glow_color
            beanie_color = (min(255, r + glow_r//3), min(255, g + glow_g//3), min(255, b + glow_b//3))
        
        # Beanie covers the entire head area and eyes
        pygame.draw.rect(screen, beanie_color, (x + 9, y, 12, 8))
        pygame.draw.rect(screen, BLACK, (x + 9, y, 12, 8), 1)
        
        # Beanie rim/edge (slightly wider)
        pygame.draw.rect(screen, beanie_color, (x + 8, y + 6, 14, 2))
        pygame.draw.rect(screen, BLACK, (x + 8, y + 6, 14, 2), 1)
        
        # Light skin face (visible below beanie, 8x4 pixels)
        pygame.draw.rect(screen, LIGHT_SKIN, (x + 11, y + 8, 8, 4))
        pygame.draw.rect(screen, BLACK, (x + 11, y + 8, 8, 4), 1)
        
        # Mouth (based on combo state) - no eyes visible due to beanie
        if self.combo_active and self.total_combo_floors >= 5:
            # Happy mouth (smile) - 3 pixels
            pygame.draw.rect(screen, BLACK, (x + 13, y + 10, 3, 1))
        else:
            # Normal mouth - 2 pixels
            pygame.draw.rect(screen, BLACK, (x + 14, y + 10, 2, 1))
        
        # Green Baggy Sweater body (14x12 pixels - much baggier)
        sweater_color = GREEN_SWEATER
        if combo_glow_color and self.combo_active:
            # Add glow effect during combos
            r, g, b = sweater_color
            glow_r, glow_g, glow_b = combo_glow_color
            sweater_color = (min(255, r + glow_r//4), min(255, g + glow_g//4), min(255, b + glow_b//4))
        
        pygame.draw.rect(screen, sweater_color, (x + 8, y + 12, 14, 12))
        pygame.draw.rect(screen, BLACK, (x + 8, y + 12, 14, 12), 1)
        
        # Light skin arms (4x3 pixels each, animated based on movement)
        arm_offset = 0
        if not self.on_ground and abs(self.vel_x) > 2:
            arm_offset = 2 if int(self.x / 10) % 2 else -2
        
        # Left arm (coming out of baggy sweater)
        pygame.draw.rect(screen, LIGHT_SKIN, (x + 4, y + 15 + arm_offset, 4, 3))
        pygame.draw.rect(screen, BLACK, (x + 4, y + 15 + arm_offset, 4, 3), 1)
        # Right arm  
        pygame.draw.rect(screen, LIGHT_SKIN, (x + 22, y + 15 - arm_offset, 4, 3))
        pygame.draw.rect(screen, BLACK, (x + 22, y + 15 - arm_offset, 4, 3), 1)
        
        # Baggy Khaki pants (12x10 pixels - wider and baggier)
        pygame.draw.rect(screen, DARK_BROWN_PANTS, (x + 9, y + 24, 12, 10))
        pygame.draw.rect(screen, BLACK, (x + 9, y + 24, 12, 10), 1)
        
        # Baggy legs with khaki pants (5x8 pixels each, animated when moving)
        leg_offset = 0
        if self.on_ground and abs(self.vel_x) > 1:
            leg_offset = 2 if int(self.x / 8) % 2 else -2
        
        # Left leg (baggy khaki pants)
        pygame.draw.rect(screen, DARK_BROWN_PANTS, (x + 7, y + 34, 5, 8))
        pygame.draw.rect(screen, BLACK, (x + 7, y + 34, 5, 8), 1)
        if leg_offset != 0:
            pygame.draw.rect(screen, DARK_BROWN_PANTS, (x + 7 + leg_offset, y + 36, 5, 6))
            pygame.draw.rect(screen, BLACK, (x + 7 + leg_offset, y + 36, 5, 6), 1)
        
        # Right leg (baggy khaki pants)
        pygame.draw.rect(screen, DARK_BROWN_PANTS, (x + 18, y + 34, 5, 8))
        pygame.draw.rect(screen, BLACK, (x + 18, y + 34, 5, 8), 1)
        if leg_offset != 0:
            pygame.draw.rect(screen, DARK_BROWN_PANTS, (x + 18 - leg_offset, y + 36, 5, 6))
            pygame.draw.rect(screen, BLACK, (x + 18 - leg_offset, y + 36, 5, 6), 1)
        
        # Brown sneakers (6x3 pixels each - bigger shoes)
        # Left shoe
        pygame.draw.rect(screen, BROWN_SHOES, (x + 6, y + 42, 6, 3))
        pygame.draw.rect(screen, BLACK, (x + 6, y + 42, 6, 3), 1)
        # Right shoe
        pygame.draw.rect(screen, BROWN_SHOES, (x + 18, y + 42, 6, 3))
        pygame.draw.rect(screen, BLACK, (x + 18, y + 42, 6, 3), 1)

    def draw(self, screen, camera_y):
        # Combo glow color based on combo level
        combo_glow_color = None
        if self.combo_active:
            if self.total_combo_floors >= 20:
                combo_glow_color = PURPLE
            elif self.total_combo_floors >= 10:
                combo_glow_color = YELLOW
            elif self.total_combo_floors >= 5:
                combo_glow_color = GREEN
            else:
                combo_glow_color = RED
        
        # Draw character with rotation during combos
        char_x = self.x + self.width // 2
        char_y = self.y - camera_y + self.height // 2
        
        if self.rotation > 0 and not self.on_ground:
            # Create a surface for the rotating pixelated character
            char_surface = pygame.Surface((self.width * 3, self.height * 3), pygame.SRCALPHA)
            # Center the character in the surface
            self.draw_pixelated_harold(char_surface, self.width, self.height, combo_glow_color)
            
            # Rotate the surface
            rotated_surface = pygame.transform.rotate(char_surface, self.rotation)
            rotated_rect = rotated_surface.get_rect(center=(char_x, char_y))
            screen.blit(rotated_surface, rotated_rect)
        else:
            # Normal pixelated character drawing - character is already 30 pixels wide, matches collision box
            self.draw_pixelated_harold(screen, self.x, self.y - camera_y, combo_glow_color)

class AmazonIcyTower:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Amazon Icy Tower")
        self.clock = pygame.time.Clock()
        
        # Player starts on ground floor - adjusted for Harold's correct height
        ground_y = WINDOW_HEIGHT - 100  # Platform top is at y=500
        # Harold's bottom should be at ground_y, so his top should be at ground_y - height
        self.player = Player(WINDOW_WIDTH // 2, ground_y - 45)  # Harold's height is 45
        self.player.on_ground = True  # Ensure Harold starts on ground
        
        # Camera system
        self.camera_y = 0
        self.target_camera_y = 0
        
        # Screen shake system
        self.shake_intensity = 0
        self.shake_duration = 0
        self.shake_x = 0
        self.shake_y = 0
        
        # Particle system for combo effects
        self.particle_system = ParticleSystem()
        
        # Tower system
        self.platforms = []
        self.generate_tower()
        
        # Game state
        self.game_over = False
        self.scroll_speed = 0.1  # Tower scrolling speed
        self.scroll_timer = 0
        self.speedup_timer = 1800  # 30 seconds at 60 FPS
        
        # UI
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
    def generate_tower(self):
        # Generate ground floor (floor 0)
        ground_y = WINDOW_HEIGHT - 100
        ground_platform = {
            'x': 0,
            'y': ground_y,
            'width': WINDOW_WIDTH,
            'height': PLATFORM_HEIGHT,
            'floor': 0,
            'type': 'stone',
            'checkpoint': True
        }
        self.platforms.append(ground_platform)
        
        # Define wall boundaries - platforms should not overlap with these areas
        left_wall_width = 100  # Reduced width, closer to Harold
        right_wall_width = 100  # Same width as left wall for consistency
        playable_area_start = left_wall_width + 20  # Smaller buffer from wall
        playable_area_end = WINDOW_WIDTH - right_wall_width - 20  # Smaller buffer from wall
        playable_width = playable_area_end - playable_area_start
        
        # Generate tower floors
        for floor in range(1, 200):
            y = ground_y - (floor * FLOOR_SPACING)
            
            # Checkpoint platforms every 10 floors (10, 20, 30, etc.)
            is_checkpoint = (floor % 10 == 0)
            
            if is_checkpoint:
                # Checkpoint platforms span from wall boundary to wall boundary (where Harold bounces)
                wall_boundary_left = 100   # Left wall boundary (matches Harold's bounce point)
                wall_boundary_right = WINDOW_WIDTH - 100  # Right wall boundary
                platform_width = wall_boundary_right - wall_boundary_left  # Full width between boundaries
                x = wall_boundary_left  # Start at the left wall boundary
            else:
                # Varying platform lengths based on floor level
                base_width = 200  # Increased base width for longer platforms
                
                # Determine platform length variation based on floor ranges
                if floor <= 99:
                    # Floors 1-99: Much longer platforms for easier gameplay
                    length_choices = ['extra_long', 'extra_long', 'long', 'long']  # 50% extra long, 50% long
                elif floor <= 199:
                    # Floors 100-199: 50:50 mix
                    length_choices = ['long', 'medium', 'short', 'short']  # 25% long, 25% medium, 50% short
                elif floor <= 399:
                    # Floors 200-399: Mostly smaller platforms
                    length_choices = ['short', 'short', 'short', 'medium']  # 75% short, 25% medium
                else:
                    # Floors 400+: Mix of all sizes
                    length_choices = ['long', 'medium', 'short', 'short']  # 25% long, 25% medium, 50% short
                
                # Select platform length
                length_type = random.choice(length_choices)
                
                if length_type == 'extra_long':
                    # Extra long platforms for early floors (minimal reduction) - much longer for momentum
                    width_reduction = min(floor * 0.3, 20)  # Even gentler reduction
                    platform_width = int(max(base_width * 1.2 - width_reduction, 220))  # Much longer: 220-240px
                elif length_type == 'long':
                    # Standard long platforms - made much longer for momentum building
                    width_reduction = min(floor * 0.8, 40)  # Less aggressive reduction
                    platform_width = int(max(base_width - width_reduction, 180))  # Much longer: 180-200px
                elif length_type == 'medium':
                    # Medium length platforms
                    width_reduction = min(floor * 1.2, 60)
                    platform_width = int(max(base_width * 0.6 - width_reduction, 80))  # Minimum 80 for medium
                else:  # short
                    # Short platforms (50% of current length)
                    width_reduction = min(floor * 1.5, 80)
                    current_length = max(base_width * 0.5 - width_reduction, 60)
                    platform_width = int(max(current_length * 0.5, 30))  # 50% of current, minimum 30
                
                # Ensure platform fits within playable area
                if platform_width > playable_width:
                    platform_width = int(playable_width - 20)
                
                # Position platforms with better reachability
                available_space = int(playable_width - platform_width)
                if available_space > 0:
                    # For early floors, make platforms more reachable
                    if floor <= 50:
                        # Early floors: More centered positioning for easier gameplay
                        position_choice = random.choice(['center', 'center', 'far_left', 'far_right'])
                    else:
                        # Higher floors: More challenging positioning
                        position_choice = random.choice(['far_left', 'far_right', 'center_gap'])
                    
                    if position_choice == 'center':
                        # Center the platform for easier access
                        x = int(playable_area_start + available_space // 2)
                    elif position_choice == 'far_left':
                        # Position near left side of playable area
                        max_offset = min(30, available_space // 3)
                        x = int(playable_area_start + random.randint(0, max_offset))
                    elif position_choice == 'far_right':
                        # Position near right side of playable area  
                        max_offset = min(30, available_space // 3)
                        x = int(playable_area_end - platform_width - random.randint(0, max_offset))
                    else:  # center_gap
                        # Position with significant gaps on both sides
                        gap_size = min(60, available_space // 3)
                        remaining_space = available_space - 2 * gap_size
                        if remaining_space > 0:
                            x = int(playable_area_start + gap_size + random.randint(0, remaining_space))
                        else:
                            x = int(playable_area_start + gap_size)
                else:
                    # Fallback if platform is too wide
                    x = int(playable_area_start)
            
            # Determine floor type based on original game
            floor_type = self.get_floor_type(floor)
            
            platform = {
                'x': x,
                'y': y,
                'width': platform_width,
                'height': PLATFORM_HEIGHT,
                'floor': floor,
                'type': floor_type,
                'checkpoint': is_checkpoint
            }
            self.platforms.append(platform)
    
    def get_floor_type(self, floor):
        # Original Icy Tower floor progression
        floor_group = (floor // 10) % 10
        types = ['stone', 'ice', 'wood', 'metal', 'gum', 'bone', 'vines', 'pipe', 'cloud', 'rainbow']
        if floor >= 100:
            return 'glass'
        return types[floor_group]
    
    def update_camera(self):
        # Camera follows player smoothly but ONLY MOVES UP
        player_screen_y = self.player.y - self.camera_y
        
        # Keep player in view, focusing on upper portion when climbing
        if player_screen_y < WINDOW_HEIGHT * 0.4:
            new_target = self.player.y - WINDOW_HEIGHT * 0.4
            # Only move camera up, never down
            if new_target < self.target_camera_y:
                self.target_camera_y = new_target
        
        # Smooth camera movement (upward only)
        if self.target_camera_y < self.camera_y:
            self.camera_y += (self.target_camera_y - self.camera_y) * CAMERA_SMOOTH
        
        # Tower scrolling (original mechanic) - always upward
        self.camera_y += self.scroll_speed
        
        # Speed up every 30 seconds
        self.speedup_timer -= 1
        if self.speedup_timer <= 0:
            self.scroll_speed += 0.05
            self.speedup_timer = 1800  # Reset timer
    
    def check_game_over(self):
        # Game over if player falls off bottom of visible screen
        player_screen_y = self.player.y - self.camera_y
        
        # If Harold is below the bottom of the screen, game over
        if player_screen_y > WINDOW_HEIGHT:
            self.game_over = True
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_p:
                    # Pause functionality could be added here
                    pass
                elif self.game_over and event.key == pygame.K_SPACE:
                    self.restart_game()
        return True
    
    def restart_game(self):
        ground_y = WINDOW_HEIGHT - 100
        self.player = Player(WINDOW_WIDTH // 2, ground_y - 45)  # Adjusted for Harold's correct height
        self.camera_y = 0
        self.target_camera_y = 0
        self.platforms = []
        self.generate_tower()
        self.game_over = False
        self.scroll_speed = 0.1
        self.speedup_timer = 1800
    
    def update(self):
        if not self.game_over:
            current_floor = max(0, int((WINDOW_HEIGHT - 100 - self.player.y) / FLOOR_SPACING))
            self.player.update(self.platforms, current_floor)
            self.update_camera()
            self.check_game_over()
    
    def draw_background(self):
        # Fill with dark background first
        self.screen.fill((40, 40, 40))
        
        # Draw well/tower walls with rectangular brick tiles
        brick_width = 60   # Wider rectangular bricks
        brick_height = 30  # Shorter height for brick proportions
        
        # Calculate camera offset for brick scrolling
        camera_brick_offset_y = int(self.camera_y) % brick_height
        
        # Draw left wall (consistent with platform generation)
        left_wall_width = 100  # Must match platform generation - reduced and consistent
        for row, y in enumerate(range(-camera_brick_offset_y, WINDOW_HEIGHT + brick_height, brick_height)):
            # Brick pattern: alternate rows are offset by half brick width
            x_offset = (brick_width // 2) if row % 2 == 1 else 0
            
            for x in range(-x_offset, left_wall_width + brick_width, brick_width):
                # Only draw if brick is within wall bounds
                if x + brick_width > 0 and x < left_wall_width:
                    # Clip brick to wall boundaries
                    brick_x = max(0, x)
                    brick_w = min(brick_width, left_wall_width - brick_x)
                    
                    if brick_w > 0:
                        # Use consistent dark tile color
                        tile_color = DARK_GRAY_TILE
                        
                        # Draw brick
                        pygame.draw.rect(self.screen, tile_color, (brick_x, y, brick_w, brick_height))
                        # Draw mortar lines
                        pygame.draw.rect(self.screen, MORTAR_GRAY, (brick_x, y, brick_w, brick_height), 2)
        
        # Draw right wall (consistent with platform generation)  
        right_wall_width = 100  # Same width as left wall
        right_wall_start = WINDOW_WIDTH - right_wall_width  # Must match platform generation
        for row, y in enumerate(range(-camera_brick_offset_y, WINDOW_HEIGHT + brick_height, brick_height)):
            # Brick pattern: alternate rows are offset by half brick width
            x_offset = (brick_width // 2) if row % 2 == 1 else 0
            
            for x in range(right_wall_start - x_offset, WINDOW_WIDTH + brick_width, brick_width):
                # Only draw if brick is within wall bounds
                if x + brick_width > right_wall_start and x < WINDOW_WIDTH:
                    # Clip brick to wall boundaries
                    brick_x = max(right_wall_start, x)
                    brick_w = min(brick_width, WINDOW_WIDTH - brick_x)
                    
                    if brick_w > 0:
                        # Use consistent dark tile color
                        tile_color = DARK_GRAY_TILE
                        
                        # Draw brick
                        pygame.draw.rect(self.screen, tile_color, (brick_x, y, brick_w, brick_height))
                        # Draw mortar lines
                        pygame.draw.rect(self.screen, MORTAR_GRAY, (brick_x, y, brick_w, brick_height), 2)
        
        # Draw back wall with uniform light gray rectangular bricks
        center_start = left_wall_width
        center_width = WINDOW_WIDTH - left_wall_width - right_wall_width
        
        # Back wall bricks (larger rectangular bricks for depth)
        back_brick_width = 80   # Larger rectangular bricks for background
        back_brick_height = 40
        back_camera_offset = int(self.camera_y * 0.3) % back_brick_height  # Slower parallax
        
        for row, y in enumerate(range(-back_camera_offset, WINDOW_HEIGHT + back_brick_height, back_brick_height)):
            # Brick pattern: alternate rows are offset by half brick width
            x_offset = (back_brick_width // 2) if row % 2 == 1 else 0
            
            for x in range(center_start - x_offset, center_start + center_width + back_brick_width, back_brick_width):
                # Only draw if brick is within background bounds
                if x + back_brick_width > center_start and x < center_start + center_width:
                    # Clip brick to background boundaries
                    brick_x = max(center_start, x)
                    brick_w = min(back_brick_width, center_start + center_width - brick_x)
                    
                    if brick_w > 0:
                        # Uniform light gray tiles (no checkerboard pattern)
                        tile_color = (140, 140, 140)  # Single light gray color
                        
                        # Draw back wall brick
                        pygame.draw.rect(self.screen, tile_color, (brick_x, y, brick_w, back_brick_height))
                        # Subtle mortar lines for brick definition
                        pygame.draw.rect(self.screen, (120, 120, 120), (brick_x, y, brick_w, back_brick_height), 1)
    
    def draw_platforms(self):
        for platform in self.platforms:
            platform_y = platform['y'] - self.camera_y
            if -50 < platform_y < WINDOW_HEIGHT + 50:  # Only draw visible platforms
                # Get floor color
                floor_color = FLOOR_COLORS.get(platform['type'], FLOOR_COLORS['stone'])
                
                # Checkpoint platforms have special appearance (brighter color only)
                if platform.get('checkpoint', False):
                    # Brighter color for checkpoints
                    r, g, b = floor_color
                    floor_color = (min(255, r + 30), min(255, g + 30), min(255, b + 30))
                
                pygame.draw.rect(self.screen, floor_color, 
                               (platform['x'], platform_y, platform['width'], platform['height']))
                
                # Normal black border for all platforms
                pygame.draw.rect(self.screen, BLACK, 
                               (platform['x'], platform_y, platform['width'], platform['height']), 2)
                
                # Draw floor number on platform
                if platform['floor'] > 0:
                    floor_text = self.small_font.render(str(platform['floor']), True, BLACK)
                    text_x = platform['x'] + platform['width'] // 2 - floor_text.get_width() // 2
                    self.screen.blit(floor_text, (text_x, platform_y + 2))
    
    def draw_ui(self):
        # Left side UI - Game stats
        ui_x = 10
        ui_y = 10
        line_height = 25
        
        # Score
        score_text = self.font.render(f"Score: {self.player.score:,}", True, WHITE)
        self.screen.blit(score_text, (ui_x, ui_y))
        ui_y += line_height
        
        # Floor
        floor_text = self.font.render(f"Floor: {self.player.highest_floor}", True, WHITE)
        self.screen.blit(floor_text, (ui_x, ui_y))
        ui_y += line_height
        
        # Floor set indicator
        floor_set = self.player.highest_floor // 10
        floor_type = self.get_floor_type(self.player.highest_floor)
        
        # Floor set range and type
        set_start = floor_set * 10
        set_end = set_start + 9
        if self.player.highest_floor >= 100:
            set_text = f"Floors {set_start}+: Glass"
        else:
            set_text = f"Floors {set_start}-{set_end}: {floor_type.title()}"
        
        set_surface = self.small_font.render(set_text, True, WHITE)
        self.screen.blit(set_surface, (ui_x, ui_y))
        ui_y += 30
        
        # Combo meter and text
        if self.player.combo_active:
            # Combo meter (left side)
            meter_height = 150
            meter_width = 15
            meter_x = 60
            meter_y = WINDOW_HEIGHT // 2 - meter_height // 2
            
            # Background
            pygame.draw.rect(self.screen, BLACK, (meter_x, meter_y, meter_width, meter_height), 2)
            
            # Fill based on timer
            fill_height = int((self.player.combo_timer / self.player.combo_max_time) * meter_height)
            if fill_height > 0:
                pygame.draw.rect(self.screen, RED, 
                               (meter_x + 2, meter_y + meter_height - fill_height, meter_width - 4, fill_height))
            
            # Combo text
            combo_text = self.player.get_combo_text()
            if combo_text:
                combo_surface = self.font.render(combo_text, True, YELLOW)
                combo_rect = combo_surface.get_rect(center=(WINDOW_WIDTH // 2, 80))
                self.screen.blit(combo_surface, combo_rect)
                
                # Combo floors
                floors_text = self.small_font.render(f"{self.player.total_combo_floors} floors", True, WHITE)
                floors_rect = floors_text.get_rect(center=(WINDOW_WIDTH // 2, 105))
                self.screen.blit(floors_text, floors_rect)
        
        # Right side UI - Game info
        right_x = WINDOW_WIDTH - 200
        right_y = 10
        
        # Speed indicator
        speed_text = self.small_font.render(f"Tower Speed: {self.scroll_speed:.2f}", True, WHITE)
        self.screen.blit(speed_text, (right_x, right_y))
        right_y += 20
        
        # Time to next speedup
        time_left = self.speedup_timer // 60
        time_text = self.small_font.render(f"Next speedup: {time_left}s", True, WHITE)
        self.screen.blit(time_text, (right_x, right_y))
        right_y += 40
        
        # Controls - Bottom right, well aligned
        controls_x = WINDOW_WIDTH - 280
        controls_y = WINDOW_HEIGHT - 160
        control_line_height = 18
        
        controls = [
            "CONTROLS:",
            "Arrow Keys/WASD: Move",
            "SPACE: Jump",
            "ESC: Quit Game",
            "",
            "TIPS:",
            "Build speed for higher jumps!",
            "Use walls to change direction!",
            "",
            "GAME OVER: Fall off screen bottom"
        ]
        
        for i, control in enumerate(controls):
            if control:  # Skip empty lines
                if control == "CONTROLS:" or control == "TIPS:":
                    color = YELLOW
                    font = self.small_font
                elif control.startswith("GAME OVER:"):
                    color = RED
                    font = self.small_font
                else:
                    color = WHITE
                    font = self.small_font
                    
                text = font.render(control, True, color)
                self.screen.blit(text, (controls_x, controls_y + i * control_line_height))
    
    def draw_game_over(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        game_over_text = self.font.render("GAME OVER!", True, WHITE)
        game_over_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 80))
        self.screen.blit(game_over_text, game_over_rect)
        
        final_score_text = self.font.render(f"Final Score: {self.player.score}", True, WHITE)
        final_score_rect = final_score_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 40))
        self.screen.blit(final_score_text, final_score_rect)
        
        final_floor_text = self.font.render(f"Highest Floor: {self.player.highest_floor}", True, WHITE)
        final_floor_rect = final_floor_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.screen.blit(final_floor_text, final_floor_rect)
        
        restart_text = self.font.render("Press SPACE to restart or ESC to quit", True, WHITE)
        restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 60))
        self.screen.blit(restart_text, restart_rect)
    
    def draw(self):
        self.draw_background()
        self.draw_platforms()
        self.player.draw(self.screen, self.camera_y)
        self.draw_ui()
        
        if self.game_over:
            self.draw_game_over()
        
        pygame.display.flip()
    
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = AmazonIcyTower()
    game.run()
