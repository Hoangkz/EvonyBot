"""Report template matches from screenshots explicitly captured with --shots.

Screenshots are diagnostic evidence for tuning image recognition, not normal test
output. ``real_run --shots`` prints the temporary directory to pass here.
"""
import argparse
from pathlib import Path

import cv2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path,
                        help="temporary directory printed by real_run --shots")
    args = parser.parse_args()

    images = [(path, cv2.imread(str(path))) for path in sorted(args.run.glob("*.png"))]
    templates = Path("Images/GiftClaims")
    for path in sorted(templates.rglob("*.png")):
        template = cv2.imread(str(path))
        matches = []
        for screenshot_path, screen in images:
            if screen is None or template is None:
                continue
            if screen.shape[0] < template.shape[0] or screen.shape[1] < template.shape[1]:
                continue
            score = float(cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED).max())
            matches.append((score, screenshot_path.name))
        score, screenshot = max(matches, default=(0.0, "-"))
        name = path.relative_to(templates).as_posix()
        print(f"{name:55} {score:.3f}  {screenshot}")


if __name__ == "__main__":
    main()
