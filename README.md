# Amazon Icy Tower

An authentic recreation of the classic Icy Tower game built with Python and PyGame. Climb as high as you can by jumping from platform to platform while building momentum and creating epic combo streaks!

## Setup

The project uses a Python virtual environment to manage dependencies. Everything is already set up for you!

## Game Overview

Amazon Icy Tower faithfully recreates the original Icy Tower experience with momentum-based physics, combo systems, and progressive difficulty. Build speed by moving left and right to make longer jumps, and chain together multi-floor jumps to create massive combos!

## Controls

- **WASD** or **Arrow Keys** - Move left/right and jump
- **SPACE** - Jump (alternative to up arrow/W)
- **ESC** - Quit game
- **SPACE** - Restart game (when game over)

## How to Play

### Basic Movement
- Move left and right across floors to build momentum
- The more momentum you have, the higher and farther you can jump
- Use the walls on the sides to bounce and change direction while maintaining speed

### Combo System
- Make multi-floor jumps to start a combo
- Chain together consecutive multi-floor jumps to extend your combo
- Combos end when you:
  - Make a single-floor jump
  - Fall to a lower floor
  - Take too long between jumps (about 3 seconds)

### Progressive Difficulty
- **Floors 0-4**: Stationary floors to get started
- **Floor 5+**: Floors begin moving downward slowly
- **Every 30 seconds**: Floor speed increases with "Hurry up!" warning
- **Game Over**: Fall off the bottom of the screen or get pushed down by a moving floor

### Floor Types
The appearance of floors changes every 100 floors:
- **Floors 0-9**: Stone
- **Floors 10-19**: Ice
- **Floors 20-29**: Wood
- **Floors 30-39**: Metal
- **Floors 40-49**: Chewing gum
- **Floors 50-59**: Bone
- **Floors 60-69**: Vines
- **Floors 70-79**: Pipe
- **Floors 80-89**: Cloud
- **Floors 90-99**: Rainbow
- **Floors 100+**: Glass

## Scoring

Points are awarded based on:
- **Highest floor reached** - Primary scoring metric
- **Combo performance** - Bonus points for multi-floor jump sequences
- **Overall performance** - Time spent and consistency

## How to Run

### Option 1: Quick start script
```bash
./run_game.sh
# Then run: python3 amazon_icy_tower.py
```

### Option 2: Manual setup
```bash
# Activate virtual environment
source pygame_game_env/bin/activate

# Run the game
python3 amazon_icy_tower.py
```

## Game Features

### Authentic Mechanics
- **Momentum-based physics** - Build speed for longer jumps just like the original
- **Wall bouncing** - Use side walls to change direction while maintaining momentum
- **Combo system** - Chain multi-floor jumps for high scores
- **Progressive floor movement** - Floors start moving down after floor 5
- **Increasing difficulty** - Floor speed increases every 30 seconds

### Visual Features
- **Authentic floor designs** - Different textures every 100 floors
- **Smooth camera following** - Camera tracks player movement
- **Real-time statistics** - Current floor, highest floor, and combo tracking
- **Game over screen** - Shows final statistics and restart option

### Technical Features
- **Smooth 60 FPS gameplay**
- **Responsive controls** with momentum physics
- **Dynamic platform generation**
- **Screen wrapping** like the original game
- **Collision detection** for platforms and walls

## Tips for High Scores

1. **Build momentum** - Move left and right to gain speed before jumping
2. **Use the walls** - Bounce off walls to change direction quickly
3. **Plan your route** - Look ahead to plan multi-floor jump sequences
4. **Master combos** - Chain together multi-floor jumps for bonus points
5. **Stay calm under pressure** - Don't panic when floors start moving faster

## Technical Details

- **Python Version:** 3.12+
- **PyGame Version:** 2.6.1
- **Virtual Environment:** `pygame_game_env/`
- **Resolution:** 800x600
- **Frame Rate:** 60 FPS

## Troubleshooting

If you encounter issues:

1. Make sure the virtual environment is activated:
   ```bash
   source pygame_game_env/bin/activate
   ```

2. Check if PyGame is installed:
   ```bash
   pip list | grep pygame
   ```

3. If PyGame is missing, reinstall:
   ```bash
   pip install pygame
   ```

## File Structure

```
/home/vixthewiz/
├── pygame_game_env/          # Virtual environment
├── amazon_icy_tower.py       # Main game file
├── icy_tower_scores.json     # High scores (auto-generated)
├── run_game.sh              # Quick start script
└── README.md                # This file
```

## About the Original

This game is inspired by the classic Icy Tower by Free Lunch Design, originally released in 2001. This recreation aims to capture the authentic feel and mechanics that made the original so addictive and fun to play.

Enjoy climbing to new heights! 🏗️
