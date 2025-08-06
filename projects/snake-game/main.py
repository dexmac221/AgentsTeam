import argparse
import sys
import pygame

try:
    from snake_game import SnakeGame
except ImportError as exc:
    raise ImportError("Failed to import snake_game module. Ensure it is in the PYTHONPATH.") from exc


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments for the Snake game.
    """
    parser = argparse.ArgumentParser(description="Play Snake")
    parser.add_argument(
        "--width",
        type=int,
        default=640,
    )
    parser.add_argument(
        "--height",
        type=int,
        default=480,
    )
    parser.add_argument(
        "--speed",
        type=int,
        default=10,
        help="Game speed (frames per second)",
    )
    return parser.parse_args()


def main() -> None:
    """
    Main entry point for the Snake game.
    """
    args = parse_arguments()

    pygame.init()
    pygame.display.set_caption("Snake")

    try:
        game = SnakeGame(
            width=args.width,
            height=args.height,
            speed=args.speed,
        )
    except Exception as exc:
        pygame.quit()
        sys.exit(1)

    try:
        game.run()
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f"An unexpected error occurred: {exc}", file=sys.stderr)
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()