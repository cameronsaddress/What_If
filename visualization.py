"""
River of Destiny — SVG visualization generator for branching life-path timelines.
Creates interactive SVG with Bezier curves, hover effects, and mobile adaptation.
"""

import svgwrite
import random
from typing import List, Tuple, Dict
import base64


class RiverOfDestiny:
    def __init__(self, width: int = 800, height: int = 600):
        self.width = width
        self.height = height
        self.colors = {
            "main_river": "#7c3aed",
            "branches": ["#60a5fa", "#34d399", "#f59e0b", "#f87171"],
            "nodes": "#FFFFFF",
            "text": "#e0e0ff",
        }

    def generate_river_svg(self, branches: List[Dict], decision: str) -> str:
        dwg = svgwrite.Drawing(size=(self.width, self.height))

        dwg.defs.add(dwg.style("""
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
            .branch-path {
                stroke-width: 10;
                fill: none;
                opacity: 0.85;
                transition: all 0.3s ease;
                cursor: pointer;
                filter: drop-shadow(0 0 12px rgba(124, 58, 237, 0.3));
            }
            .branch-path:hover {
                stroke-width: 14;
                opacity: 1;
                filter: drop-shadow(0 0 24px rgba(124, 58, 237, 0.6));
            }
            .event-node {
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .event-node:hover {
                r: 14;
                filter: drop-shadow(0 0 16px rgba(255, 255, 255, 0.8));
            }
            .branch-title {
                font-family: 'Inter', sans-serif;
                font-size: 15px;
                font-weight: 600;
                fill: #e0e0ff;
            }
            .decision-text {
                font-family: 'Inter', sans-serif;
                font-size: 20px;
                font-weight: 700;
                fill: #a78bfa;
                text-anchor: middle;
            }
            .fate-score {
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                fill: #8888aa;
                font-weight: 500;
            }
        """))

        # Dark gradient background
        gradient = dwg.defs.add(
            dwg.radialGradient(id="bg-gradient", cx="50%", cy="50%", r="80%")
        )
        gradient.add_stop_color(offset="0%", color="#302b63", opacity="0.4")
        gradient.add_stop_color(offset="100%", color="#0f0c29", opacity="0.6")
        dwg.add(
            dwg.rect(
                insert=(0, 0),
                size=(self.width, self.height),
                fill="url(#bg-gradient)",
                rx=16,
                ry=16,
            )
        )

        # Subtle particle dots
        for _ in range(10):
            x = random.randint(40, self.width - 40)
            y = random.randint(40, self.height - 40)
            dwg.add(dwg.circle(center=(x, y), r=1.5, fill="#a78bfa", opacity="0.3"))

        # Title
        title_group = dwg.g()
        title_bg = dwg.rect(
            insert=(self.width / 2 - 180, 15),
            size=(360, 44),
            fill="rgba(255, 255, 255, 0.06)",
            rx=22,
            ry=22,
            stroke="#7c3aed",
            stroke_width=1,
            stroke_opacity=0.3,
        )
        title_group.add(title_bg)
        title_text = dwg.text(
            decision[:40] + ("..." if len(decision) > 40 else ""),
            insert=(self.width / 2, 42),
            class_="decision-text",
        )
        title_group.add(title_text)
        dwg.add(title_group)

        # Main river trunk
        start_x = self.width // 2
        start_y = 75
        fork_y = 190

        # Glow
        dwg.add(
            dwg.path(
                d=f"M {start_x},{start_y} C {start_x},{start_y+50} {start_x},{fork_y-50} {start_x},{fork_y}",
                stroke=self.colors["main_river"],
                stroke_width=20,
                fill="none",
                opacity=0.2,
            )
        )
        # Trunk
        dwg.add(
            dwg.path(
                d=f"M {start_x},{start_y} C {start_x},{start_y+50} {start_x},{fork_y-50} {start_x},{fork_y}",
                stroke=self.colors["main_river"],
                stroke_width=12,
                fill="none",
                opacity=0.85,
            )
        )

        # Branches
        spacing = self.width / (len(branches) + 1)

        for i, branch in enumerate(branches):
            branch_x = spacing * (i + 1)
            color = self.colors["branches"][i % len(self.colors["branches"])]

            path_data = self._create_branch_path(start_x, fork_y, branch_x, self.height - 90, i)
            dwg.add(
                dwg.path(
                    d=path_data,
                    stroke=color,
                    class_="branch-path",
                    id=f"branch-{branch['branch_id']}",
                )
            )

            # Title
            title_y = fork_y + 55
            dwg.add(
                dwg.text(
                    branch["title"],
                    insert=(branch_x, title_y),
                    class_="branch-title",
                    text_anchor="middle",
                )
            )

            # Fate score
            dwg.add(
                dwg.text(
                    f"Score: {branch['fate_score']}/100",
                    insert=(branch_x, title_y + 18),
                    class_="fate-score",
                    text_anchor="middle",
                )
            )

            # Event nodes
            events = branch.get("key_events", [])[:3]
            for j, event in enumerate(events):
                t = (j + 1) / (len(events) + 1)
                node_x, node_y = self._get_point_on_curve(
                    start_x, fork_y, branch_x, self.height - 90, t, i
                )

                g = dwg.g()

                # Glow ring
                g.add(
                    dwg.circle(
                        center=(node_x, node_y),
                        r=12,
                        fill=color,
                        opacity=0.2,
                    )
                )

                # Node
                g.add(
                    dwg.circle(
                        center=(node_x, node_y),
                        r=8,
                        fill="#1a1a2e",
                        stroke=color,
                        stroke_width=3,
                        class_="event-node",
                        id=f"event-{branch['branch_id']}-{j}",
                    )
                )

                # Inner dot
                g.add(dwg.circle(center=(node_x, node_y), r=3, fill=color, opacity=0.8))

                # Tooltip
                g.add(dwg.title(event))
                dwg.add(g)

        # Legend
        self._add_legend(dwg)

        return dwg.tostring()

    def _create_branch_path(
        self, start_x: int, start_y: int, end_x: int, end_y: int, index: int
    ) -> str:
        c1x = start_x + (end_x - start_x) * 0.3 + random.randint(-15, 15)
        c1y = start_y + (end_y - start_y) * 0.3
        c2x = start_x + (end_x - start_x) * 0.7 + random.randint(-15, 15)
        c2y = start_y + (end_y - start_y) * 0.7
        return f"M {start_x},{start_y} C {c1x},{c1y} {c2x},{c2y} {end_x},{end_y}"

    def _get_point_on_curve(
        self, sx: int, sy: int, ex: int, ey: int, t: float, idx: int
    ) -> Tuple[float, float]:
        c1x = sx + (ex - sx) * 0.3 + (idx - 1.5) * 10
        c1y = sy + (ey - sy) * 0.3
        c2x = sx + (ex - sx) * 0.7 + (idx - 1.5) * 10
        c2y = sy + (ey - sy) * 0.7

        x = (1-t)**3*sx + 3*(1-t)**2*t*c1x + 3*(1-t)*t**2*c2x + t**3*ex
        y = (1-t)**3*sy + 3*(1-t)**2*t*c1y + 3*(1-t)*t**2*c2y + t**3*ey
        return x, y

    def _add_legend(self, dwg):
        lx, ly = 16, self.height - 65

        g = dwg.g()
        g.add(
            dwg.rect(
                insert=(lx - 10, ly - 22),
                size=(185, 60),
                fill="rgba(255, 255, 255, 0.04)",
                stroke="rgba(255, 255, 255, 0.08)",
                stroke_width=1,
                rx=10,
                ry=10,
            )
        )

        items = [
            ("Branches = alternate timelines", "#a78bfa"),
            ("Hover to reveal events", "#60a5fa"),
            ("Dots = key milestones", "#34d399"),
        ]
        for i, (text, color) in enumerate(items):
            g.add(
                dwg.text(
                    text,
                    insert=(lx, ly + i * 16),
                    style=f"font-family: 'Inter', sans-serif; font-size: 11px; fill: {color}; font-weight: 400;",
                )
            )

        dwg.add(g)

    def create_shareable_image(self, svg_content: str) -> str:
        return base64.b64encode(svg_content.encode("utf-8")).decode("utf-8")


class MobileRiverAdapter:
    @staticmethod
    def adapt_for_mobile(svg_content: str, screen_width: int) -> str:
        if screen_width < 768:
            svg_content = svg_content.replace(
                "<svg ",
                '<svg viewBox="0 0 800 600" preserveAspectRatio="xMidYMid meet" ',
            )
        return svg_content
