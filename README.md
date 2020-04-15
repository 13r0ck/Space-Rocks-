# 3d Space Rocks Simulator 2020
This is currently a project to create a video game written in Python and powered by the Panda3d game engine.

**This project is currently under development**

### Current Features
* Infinie space flight
* Missles
* 3d percedural generation of asteroids via simplex noise

### Planned Features
* Generate the missle geometry in code to keep the application to one file
* More realistic Space flight
* Menu
* Colisons w/ Splitting asteroids
* Point system
* Muli-sized asteroids
* A fail state

### Broken things
* Missle light could be improved
* There is now a memory leak :)

### Things Fixed this Commit
* Cleaned code more
* Added fullscreen toggle (f11)
* Added fps toggle (f12)
* Fps now stays in corner when toggling full screen
* Fixed fog, and incresed fog distance
* Fixed astoeroid animations, they now actually work
* Fixed Inifnite space flight with the procedutally generated asteroids
* Fixed precedurally generated asteroid seed, so that all asteroids will be unique
* Combined the 3d space rocks and "generate asteroid..." files
* Asteroids now spawn in 3 different sizes, with varying speed

### Requirements
#### A compiled version is not yet available, running the .py is required
* pip install opensimplex
* pip install panda3d
