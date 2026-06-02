# CODE Portal 3 UML klašu diagramma

Projekta vispārīgs apraksts un spēles mehānikas ir [README.md](README.md).

Viss, kas šeit redzams, nāk no paša koda. Neko klāt neizdomāju. Lai diagrammu būtu vieglāk lasīt un bultas mazāk krustotos, sadalīju to četrās daļās pa moduļiem.

Par apzīmējumiem: `+` ir public, `-` ir private (Python kodā tas ir `_` prefikss priekšā), un `$` apzīmē statisku jeb klases atribūtu. Python redzamību piespiedu kārtā neuztur, tāpēc `protected` (`#`) diagrammā nav. Kodā nav arī īstu interfeisu vai abstraktu klašu, un `enum` tipus neatradu nevienu.

---

## 1. Flīžu (tile) sistēma un pasaule (`tile.py`, `tile_registry.py`, `world.py`)

```mermaid
classDiagram
    direction LR

    class TileDefinition {
        -_id: str
        -_name: str
        -_image_filename: str
        -_image: pygame.Surface
        -_solid: bool
        -_kills: bool
        -_is_portal: bool
        -_level_id: int
        -_climbable: bool
        -_decoration: bool
        -_special: str
        -_door_exit: bool
        -_background: bool
        -_frames: list
        -_frame_speed: int
        -_fallback_color: tuple
        +get_id() str
        +get_name() str
        +get_image() pygame.Surface
        +has_image() bool
        +get_fallback_color() tuple
        +set_frames(frames)
        +get_frames() list
        +get_frame_speed() int
        +is_animated() bool
        +is_solid() bool
        +kills_player() bool
        +is_portal() bool
        +get_level_id() int
        +is_climbable() bool
        +is_decoration() bool
        +get_special() str
        +is_spawn() bool
        +is_door_exit() bool
        +is_background() bool
    }

    class TileRegistry {
        -_registry_file: str
        -_categories: list
        -_tiles_by_id: dict
        -_tiles_by_category: dict
        -_loaded_images_count: int
        -_missing_images_count: int
        +load() bool
        +get_tile(tile_id) TileDefinition
        +has_tile(tile_id) bool
        +get_all_tile_ids() list
        +get_categories() list
        +get_tiles_in_category(name) list
        +get_tile_count() int
        +draw_tile(screen, tile_id, x, y, frame)
        -_try_load_image(filename) pygame.Surface
        -_try_load_sprite_sheet(sheet, count) list
    }

    class Tile {
        -_grid_x: int
        -_grid_y: int
        -_tile_id: str
        -_registry: TileRegistry
        -_definition: TileDefinition
        -_animation_frame: int
        -_rect: pygame.Rect
        +get_pixel_x() int
        +get_pixel_y() int
        +get_rect() pygame.Rect
        +get_grid_x() int
        +get_grid_y() int
        +is_solid() bool
        +kills_player() bool
        +is_portal() bool
        +get_level_id() int
        +is_decoration() bool
        +is_background() bool
        +is_climbable() bool
        +get_type() str
        +get_name() str
        +draw(screen, cam_x, cam_y)
        +to_dict() dict
    }

    class SolidTile {
        +is_solid() bool
    }

    class PortalTile {
        -_is_active: bool
        -_is_completed: bool
        +deactivate()
        +activate()
        +is_active() bool
        +is_completed() bool
        +draw(screen, cam_x, cam_y)
    }

    class HazardTile {
        +kills_player() bool
    }

    class DoorExitTile {
        -_rect: pygame.Rect
        -_locked: bool
        -_font_label
        -_font_exit
        +unlock()
        +lock()
        +is_locked() bool
        +draw(screen, cam_x, cam_y)
    }

    class BackgroundTile {
        -_pattern_cache: dict$
        -_tint_surf$
        -_draw_surf: pygame.Surface
        -_get_pattern_surf() pygame.Surface
        +draw(screen, cam_x, cam_y)
    }

    class World {
        -_tiles: list
        -_tile_at: dict
        -_platforms: list
        -_portals: list
        -_hazards: list
        -_climbables: list
        -_doors: list
        -_bg_tiles: list
        -_bg_tile_at: dict
        -_solid_rects_cache
        -_climbable_rects_cache
        -_spawn_x: int
        -_spawn_y: int
        -_world_width: int
        -_world_height: int
        -_registry: TileRegistry
        +add_tile(type, gx, gy)
        +remove_tile(gx, gy)
        +remove_bg_tile(gx, gy)
        +get_tile_at(gx, gy) Tile
        +get_bg_tile_at(gx, gy) Tile
        +clear()
        +draw(screen, cam_x, cam_y)
        +get_solid_rects() list
        +get_climbable_rects() list
        +check_portal_collision(rect) PortalTile
        +check_hazard_collision(rect) HazardTile
        +check_door_collision(rect) bool
        +unlock_door()
        +lock_doors()
        +get_portal_count() int
        +get_doors() list
        +save_to_file(filename)
        +load_from_file(filename) bool
        +create_demo_world()
        +get_tiles() list
        +get_platforms() list
        +get_portals() list
        +get_hazards() list
        +get_spawn_position() tuple
        +get_world_size() tuple
        +get_tile_count() int
    }

    Tile <|-- SolidTile
    Tile <|-- PortalTile
    Tile <|-- HazardTile
    Tile <|-- DoorExitTile
    Tile <|-- BackgroundTile

    TileRegistry "1" *-- "0..*" TileDefinition : satur
    Tile "0..*" --> "1" TileDefinition : _definition
    Tile "0..*" o-- "1" TileRegistry : _registry
    World "1" *-- "0..*" Tile : owns
    World "1" o-- "1" TileRegistry : _registry
```

Te der piebilst: `create_tile(tile_id, gx, gy, registry)` nav klase, bet gan moduļa funkcija. Tā paskatās uz `TileDefinition` karodziņiem un atgriež vajadzīgo `Tile` apakšklasi.

---

## 2. Līmeņi un uzdevumi (`level.py`, `task.py`)

```mermaid
classDiagram
    direction LR

    class Level {
        -_code_label: str$
        -_level_id: int
        -_title: str
        -_tasks: list
        -_time_limit: int
        -_overclock_duration_ms: int
        -_current_task_index: int
        -_theme_color: tuple
        -_rng: random.Random
        -_sound: SoundManager
        -_overlay_surf: pygame.Surface
        +load_tasks(tasks_file) bool
        +set_task_limit(n)
        +get_overclock_duration_ms() int
        +get_current_task() Task
        +next_task() Task
        +reset_typewriter()
        +skip_typewriter()
        +is_typewriter_complete() bool
        +is_complete() bool
        +check_answer(ans) bool
        +display_task(screen, font, attempts)
        +get_panel_layout() dict
        +get_current_task_index() int
        +get_time_limit() int
        +get_theme_color() tuple
    }

    class ConditionLevel {
        -_code_label: str$
        -_branch_type: str
    }
    class LoopLevel {
        -_code_label: str$
        -_loop_type: str
    }
    class FunctionLevel {
        -_code_label: str$
    }
    class AdvancedLevel {
        -_code_label: str$
    }
    class ExpertLevel {
        -_code_label: str$
    }

    class Task {
        -_question: str
        -_correct_answer: str
        -_hint: str
        -_points: int
        +verify(ans) bool
        +calculate_points(attempt) int
        +get_question() str
        +get_hint() str
    }

    class SoundManager {
        ... (skat. 4. diagrammu)
    }

    Level <|-- ConditionLevel
    Level <|-- LoopLevel
    Level <|-- FunctionLevel
    Level <|-- AdvancedLevel
    Level <|-- ExpertLevel

    Level "1" *-- "0..*" Task : _tasks
    Level "1" --> "1" SoundManager : _sound
```

Tāpat arī `create_level(level_id, overclock_ms)` ir tikai funkcija. Tā pēc `_LEVEL_CATALOGUE` tabulas izlemj, kuru līmeņa apakšklasi izveidot.

---

## 3. Spēles kodols un orķestrēšana (`game.py`, `player.py`, `player_sprite.py`, `camera.py`, `score_log.py`)

```mermaid
classDiagram
    direction TB

    class Game {
        -_pipeline: ShaderPipeline
        -_screen: pygame.Surface
        -_clock
        -_player: Player
        -_player_sprite: PlayerSprite
        -_world: World
        -_camera: Camera
        -_registry: TileRegistry
        -_current_level: Level
        -_score_log: ScoreLog
        -_sound: SoundManager
        -_world_index: int
        -_current_world_config: dict
        -_door_unlocked: bool
        -_endless_mode: bool
        -_state: str
        +__init__(player_name)
        -_load_world(index)
        -_update()
        -_update_playing()
        -_update_transition()
        -_open_task(portal)
        -_close_task_success()
    }

    class Player {
        -_name: str
        -_score: int
        -_attempts: int
        -_max_attempts: int
        -_level_reached: int
        -_tasks_completed: int
        +add_score(points)
        +deduct_score(points)
        +reset_attempts()
        +set_max_attempts(n)
        +increment_attempts()
        +has_attempts_left() bool
        +advance_level()
        +set_level_reached(level)
        +get_name() str
        +get_score() int
        +get_attempts() int
        +get_level_reached() int
        +get_tasks_completed() int
        +__str__() str
    }

    class PlayerSprite {
        -_x: float
        -_y: float
        -_spawn_x: float
        -_spawn_y: float
        -_width: int
        -_height: int
        -_vel_x: float
        -_vel_y: float
        -_on_ground: bool
        -_facing_right: bool
        -_is_moving: bool
        -_is_jumping: bool
        -_is_sprinting: bool
        -_is_dead: bool
        -_coyote_timer: int
        -_jump_buffer: int
        -_on_ladder: bool
        -_climb_dir: int
        -_sprites_r: dict
        -_sprites_l: dict
        -_anim_state: str
        +update(platforms, climbables)
        +move_left(sprint)
        +move_right(sprint)
        +stop()
        +climb_up()
        +climb_down()
        +stop_climbing()
        +is_on_ladder() bool
        +jump()
        +start_death_anim()
        +clear_death_anim()
        +respawn(x, y)
        +nudge(dx, dy)
        +draw(screen, cam_x, cam_y)
        -_apply_gravity()
        -_move_horizontal(platforms)
        -_move_vertical(platforms)
        -_check_world_bounds()
    }

    class Camera {
        -_x: float
        -_y: float
        -_target
        -_smoothness_x: float
        -_smoothness_y: float
        -_is_following: bool
        -_lookahead_x: float
        -_vel_x: float
        -_vel_y: float
        -_min_y: float
        -_motion_blur_enabled: bool
        +set_target(target)
        +remove_target()
        +follow(enabled)
        +update()
        +set_min_y(value)
        +move(dx, dy)
        +screen_to_world(sx, sy) tuple
    }

    class ScoreLog {
        -_filename: str
        -_log_filename: str
        -_entries: list
        -_session_id: str
        -_timestamp: str
        +save_score(player) bool
        +load_scores() list
        +get_top_scores(limit) list
        +get_total_games() int
        +get_average_score() int
        +write_log(msg)
        -_generate_session_id() str
        -_ensure_csv_exists()
    }

    class World
    class Camera
    class TileRegistry
    class ParallaxBackground
    class ShaderPipeline
    class Level
    class SoundManager
    class PortalTile

    Game "1" *-- "1" Player : _player
    Game "1" *-- "1" PlayerSprite : _player_sprite
    Game "1" *-- "1" World : _world
    Game "1" *-- "1" Camera : _camera
    Game "1" *-- "1" TileRegistry : _registry
    Game "1" *-- "1" ParallaxBackground
    Game "1" *-- "1" ScoreLog : _score_log
    Game "1" *-- "1" ShaderPipeline : _pipeline
    Game "1" *-- "0..1" Level : _current_level
    Game --> SoundManager : _sound
    Game ..> PortalTile : _open_task

    Camera "1" --> "0..1" PlayerSprite : target
    ScoreLog ..> Player : save_score
```

---

## 4. Renderēšana, audio un ieejas punkti (`shader_pipeline.py`, `parallax_background.py`, `sound_manager.py`, `main.py`, `level_editor.py`)

```mermaid
classDiagram
    direction TB

    class ShaderPipeline {
        -_render_size: tuple
        -_screen_size: tuple
        -_shader_name: str
        -_ctx
        -_glitch: float
        +create(size, fullscreen, shader, ...)$ ShaderPipeline
        +create_passthrough(size, fullscreen, ...)$ _PassthroughPipeline
        +present()
        +shutdown()
        +scale_mouse_pos(pos) tuple
        -_set_uniform(program, name, value)
        -_compile_program(name)
    }

    class _PassthroughPipeline {
        -_render_size: tuple
        -_display_size: tuple
        -_display: pygame.Surface
        -_surface: pygame.Surface
        -_needs_scale: bool
        +surface() pygame.Surface
        +set_shader(name)
        +set_enabled(e)
        +toggle() bool
        +pulse_glitch(a)
        +scale_mouse_pos(pos) tuple
        +present()
        +shutdown()
    }

    class ParallaxLayer {
        -_image: pygame.Surface
        -_scroll_speed: float
        -_y_offset: int
        -_width: int
        -_height: int
        +draw(screen, cam_x, cam_y)
    }

    class ParallaxBackground {
        -_layers: list
        -_sky_color: tuple
        +add_layer(image, speed, y_offset) ParallaxLayer
        +add_layer_from_file(filename, speed, ...) ParallaxLayer
    }

    class SoundManager {
        -_instance$
        -_sounds: dict
        -_sound_volume: float
        -_music_volume: float
        -_music_path: str
        -_ambience_sounds: list
        -_ambience_channel
        -_ambience_enabled: bool
        +__new__(cls)$
        +start_ambience()
        +stop_ambience()
        +update_ambience()
        +set_ambience_volume(volume)
        +play_sound(name)
        +play_music()
        +stop_music()
        +set_volume(volume)
        +set_music_volume(volume)
        -_load_sounds()
        -_prepare_music()
        -_load_ambience()
    }

    class MainMenu {
        -_pipeline: ShaderPipeline
        -_screen: pygame.Surface
        -_items: list
        -_selected: int
        -_logo: pygame.Surface
        +__init__()
        -_draw_brackets(rect, ...)
        -_draw_items()
        -_load_logo(target_h) pygame.Surface
    }

    class LevelEditor {
        -_pipeline: _PassthroughPipeline
        -_screen: pygame.Surface
        -_registry: TileRegistry
        -_world: World
        -_camera: Camera
        -_current_tile_id: str
        -_current_filename: str
        -_unsaved_changes: bool
        +__init__()
        -_select_first_tile()
        -_discover_levels() list
        -_next_level_filename() str
        -_create_new_level(force)
        -_switch_level(filename, force)
        -_paint_at_mouse(add)
    }

    class Game
    class ScoreLog
    class World
    class Camera
    class TileRegistry

    ShaderPipeline ..> _PassthroughPipeline : create() fallback
    ParallaxBackground "1" *-- "0..*" ParallaxLayer : _layers

    MainMenu "1" *-- "1" ShaderPipeline : _pipeline
    MainMenu ..> Game : palaiž
    MainMenu ..> LevelEditor : palaiž
    MainMenu ..> ScoreLog
    MainMenu --> SoundManager

    LevelEditor "1" *-- "1" World : _world
    LevelEditor "1" *-- "1" Camera : _camera
    LevelEditor "1" *-- "1" TileRegistry : _registry
    LevelEditor "1" *-- "1" _PassthroughPipeline : _pipeline
```

---

## Galvenās saistības, ko diagramma parāda

1. Kodā ir divas mantošanas hierarhijas. No `Tile` izaug pieci flīžu veidi (`SolidTile`, `PortalTile`, `HazardTile`, `DoorExitTile`, `BackgroundTile`), un no `Level` izaug pieci līmeņu veidi (`ConditionLevel`, `LoopLevel`, `FunctionLevel`, `AdvancedLevel`, `ExpertLevel`). Apakšklases pārraksta `draw()` un citas metodes katra pa savam.
2. Viss turas uz `Game`. Tā izveido un patur gandrīz visus pārējos gabalus (`World`, `PlayerSprite`, `Camera`, `Player`, `TileRegistry`, `ParallaxBackground`, `ScoreLog`, `ShaderPipeline`), un spēles laikā ar `create_level()` ģenerē līmeņus.
3. `World` un `TileRegistry` strādā kopā, tikai dažādi. Pašas flīzes `World` tur kā savu daļu (kompozīcija), bet uz `TileRegistry` tikai norāda (agregācija). Arī katra atsevišķā `Tile` norāda uz to pašu kopīgo `TileRegistry` un uz savu `TileDefinition`.
4. `SoundManager` ir vieninieks (singleton). To panāk ar `__new__` un `_instance`, tāpēc `Level`, `Game` un `MainMenu` visi runā ar vienu un to pašu skaņas objektu.
5. `ShaderPipeline` ir sagatavojusi sev rezervi. Ja `moderngl` nav uzinstalēts, `ShaderPipeline.create()` tā vietā atdod `_PassthroughPipeline`. Tā ir atkarība, nevis mantošana. No malas abas klases izskatās līdzīgi, taču kodā tām nav kopīgas bāzes klases.