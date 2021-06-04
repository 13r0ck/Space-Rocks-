![](https://github.com/13r0ck/Space-Rocks-/blob/readme_update/Images/gif/main_menu.GIF?raw=true)

Space Rocks was a personal project to become more proficient with Python.
The goal of the project was to create a 3d clone of the classic game Asteroids.

### Personal Lessons from the Project
While by no means a fun game, Space Rocks! did accomplish its goal of teaching me parts of progamming that cannot be learned from a textbook. The main lesson was developing without the help of Stack Overflow. While I was able to learn many parts of Python through Stack Overflow, the game engine, Panda3d, have few and limited questions answered there. Most of the developemnt of the game involved reading the questionably written documentation and having to brute force my way to working code.

### Features of the Game
#### GUI
This project was my first foray into programing a GUI. The GUI uses the Panda3d API.
![](https://github.com/13r0ck/Space-Rocks-/blob/readme_update/Images/gif/ui_demo.GIF?raw=true)
#### Procedural Asteroid Generation
All asteroids are uniquely generated in 3d space via opensimplex noise with epoch time of each asteroid generation as the seed. Panda3d does not make 3d model creation/manipulation as simple as most modern game engines. Each vertex must have a unique coordinate in 3d space, and then the list of all verteces must be parsed manually and told (in the correct order) what other related verteces make each individual polygon of the asteroid. The texture of all asteroids is also procedurally generated, with deeper pits in the model being a darker gray.
![](https://github.com/13r0ck/Space-Rocks-/blob/readme_update/Images/gif/procedural-generation.GIF?raw=true)
#### Infinite Space Flight
The player can fly in any direction forever, and asteroids will populate the space around them. The same asteroids used at game launch are moved around the player as the player moves. Generation new asteroids would be possible but not computationaly fast enough for smooth gameplay.
![](https://github.com/13r0ck/Space-Rocks-/blob/readme_update/Images/gif/infinite-spaceflight.GIF?raw=true)
#### Space-Like Player Controls
The player can move freely with six degrees of freedom. All movement is relative to the players view. Similar to actual space, and the game Asteroids, the lack of friction will keep the player floating in any direction that force was given in. To maintain some arcade like gameplay there is a maximum velocity. Side note: The infinite spaceflight mechanic continues to work correctly when speed is unlocked even up to millions of m/s (Largest asteroid is ~10,000m in diameter.)
![](https://github.com/13r0ck/Space-Rocks-/blob/readme_update/Images/gif/space-lime-motion.GIF?raw=true)
#### Missles
It wouldn't bw an Asteroids clone if you couldn't shoot asteroids! Asteroids can be shot and will break from 1 Large -> 2 Medium -> 4 Small asteroids, exacxtly like the game Asteroids. Breaking a small asteroid create a "pointball" that is atracted to the player once the player gets close enough. The value of each pointball is realtive to the amount of time since the last small asteroid was shot. With a max value of 100 and a min of 20.
![](https://github.com/13r0ck/Space-Rocks-/blob/readme_update/Images/gif/missles.GIF?raw=true)
#### Space Death
It is possible to die is Space Rocks! Just like real space, you will die alone. Unlike real space the universe turns red when you die.

![](https://github.com/13r0ck/Space-Rocks-/blob/readme_update/Images/gif/death_state.GIF?raw=true)

# How To Play
Download the repository and then run `python3 "/path/to/repository/space-rocks!.py"`
The game is tested to run in both Windows and Linux (Fedora + Pop!_OS)

## Dependencies
`pip install opensimplex`

`pip install panda3d`

Future updates should not break the game, but if so, tested versions are:
opensimplex version 0.3
Panda3d 1.10.6.post2

### Controls
#### Camera Relative Controls
w - forward

a - left

s - right

d - left

q - rotate left

e - rotate right

ctrl/shift - down

space - up
#### Gameplay Controls
move mouse - move the mouse to point the camera
mouse1 - fire missle
#### Dev Controls
0 - Stop all spaceship movement
