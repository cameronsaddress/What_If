"""
River of Destiny Visualization Generator
Creates interactive SVG visualizations for life path branches
"""

import svgwrite
import random
import math
from typing import List, Tuple, Dict
import base64
from io import BytesIO

class RiverOfDestiny:
    def __init__(self, width: int = 800, height: int = 600):
        self.width = width
        self.height = height
        self.colors = {
            'main_river': '#667eea',
            'branches': ['#FF6B6B', '#FFD700', '#4ECDC4', '#F093FB'],
            'nodes': '#FFFFFF',
            'text': '#333333',
            'background': 'transparent'
        }
    
    def generate_river_svg(self, branches: List[Dict], decision: str) -> str:
        """Generate the main River of Destiny SVG"""
        dwg = svgwrite.Drawing(size=(self.width, self.height))
        
        # Add CSS styles for interactivity
        dwg.defs.add(dwg.style("""
            @import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600;700&display=swap');
            .branch-path { 
                stroke-width: 12; 
                fill: none; 
                opacity: 0.9;
                transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
                cursor: pointer;
                filter: drop-shadow(0 0 20px rgba(102, 126, 234, 0.5));
            }
            .branch-path:hover { 
                stroke-width: 16; 
                opacity: 1;
                filter: drop-shadow(0 0 30px rgba(255, 107, 107, 0.8));
                transform: scale(1.02);
            }
            .event-node { 
                cursor: pointer;
                transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
                filter: drop-shadow(0 0 10px rgba(255, 215, 0, 0.6));
            }
            .event-node:hover { 
                r: 15;
                filter: drop-shadow(0 0 20px rgba(255, 215, 0, 1));
            }
            .branch-title {
                font-family: 'Fredoka', cursive;
                font-size: 18px;
                font-weight: 700;
                fill: #333;
                text-shadow: 2px 2px 4px rgba(255, 255, 255, 0.8);
            }
            .decision-text {
                font-family: 'Fredoka', cursive;
                font-size: 24px;
                font-weight: 700;
                fill: #667eea;
                text-anchor: middle;
                text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.2);
            }
            .fate-score {
                font-family: 'Fredoka', cursive;
                font-size: 14px;
                fill: #764ba2;
                font-weight: 600;
            }
            .event-node-group {
                animation: pulse 2s ease-in-out infinite;
            }
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.1); }
            }
        """))
        
        # Game-style gradient background
        gradient = dwg.defs.add(dwg.radialGradient(id="bg-gradient", cx="50%", cy="50%", r="80%"))
        gradient.add_stop_color(offset="0%", color="#FFE5B4", opacity="0.3")
        gradient.add_stop_color(offset="50%", color="#FFD700", opacity="0.1")
        gradient.add_stop_color(offset="100%", color="#FF6B6B", opacity="0.05")
        dwg.add(dwg.rect(insert=(0, 0), size=(self.width, self.height), fill="url(#bg-gradient)", rx=20, ry=20))
        
        # Add sparkle effects
        for _ in range(15):
            x = random.randint(50, self.width - 50)
            y = random.randint(50, self.height - 50)
            sparkle = dwg.circle(center=(x, y), r=2, fill="#FFD700", opacity="0.6")
            sparkle.add(dwg.animateTransform("rotate", "0 {} {}".format(x, y), "360 {} {}".format(x, y), 
                                            dur="10s", repeatCount="indefinite"))
            dwg.add(sparkle)
        
        # Add stylized title
        title_group = dwg.g()
        # Title background
        title_bg = dwg.rect(insert=(self.width/2 - 200, 15), size=(400, 50), 
                          fill="rgba(255, 255, 255, 0.8)", rx=25, ry=25,
                          stroke="#667eea", stroke_width=3)
        title_group.add(title_bg)
        # Title text
        title_text = dwg.text(f'🎆 {decision} 🎆', insert=(self.width/2, 45), 
                            class_="decision-text")
        title_group.add(title_text)
        dwg.add(title_group)
        
        # Main river source
        start_x = self.width // 2
        start_y = 80
        fork_y = 200
        
        # Draw main river with glow effect
        # Glow layer
        glow_path = dwg.path(d=f"M {start_x},{start_y} C {start_x},{start_y + 50} {start_x},{fork_y - 50} {start_x},{fork_y}",
                           stroke=self.colors['main_river'], stroke_width=25, fill="none", opacity=0.3,
                           filter="blur(10px)")
        dwg.add(glow_path)
        
        # Main river
        main_path = dwg.path(d=f"M {start_x},{start_y} C {start_x},{start_y + 50} {start_x},{fork_y - 50} {start_x},{fork_y}",
                           stroke=self.colors['main_river'], stroke_width=15, fill="none", opacity=0.9)
        dwg.add(main_path)
        
        # Calculate branch positions
        branch_spacing = self.width / (len(branches) + 1)
        
        for i, branch in enumerate(branches):
            branch_x = branch_spacing * (i + 1)
            color = self.colors['branches'][i % len(self.colors['branches'])]
            
            # Create curved branch path
            path_data = self._create_branch_path(start_x, fork_y, branch_x, self.height - 100, i)
            branch_path = dwg.path(d=path_data, stroke=color, class_="branch-path",
                                 id=f"branch-{branch['branch_id']}")
            dwg.add(branch_path)
            
            # Add branch title
            title_y = fork_y + 60
            dwg.add(dwg.text(branch['title'], insert=(branch_x, title_y), 
                           class_="branch-title", text_anchor="middle"))
            
            # Add fate score
            dwg.add(dwg.text(f"Fate Score: {branch['fate_score']}/100", 
                           insert=(branch_x, title_y + 20), 
                           class_="fate-score", text_anchor="middle"))
            
            # Add event nodes along the branch
            events = branch.get('key_events', [])[:3]  # Limit to 3 events
            for j, event in enumerate(events):
                event_y = fork_y + 120 + (j * 100)
                # Calculate position along the curve
                t = (j + 1) / (len(events) + 1)
                node_x, node_y = self._get_point_on_curve(start_x, fork_y, branch_x, 
                                                         self.height - 100, t, i)
                
                # Event node with game-style design
                g = dwg.g(class_="event-node-group")
                
                # Outer glow
                glow = dwg.circle(center=(node_x, node_y), r=15, 
                                fill=color, opacity=0.3, filter="blur(5px)")
                g.add(glow)
                
                # Main node
                circle = dwg.circle(center=(node_x, node_y), r=10, 
                                  fill="#FFFFFF", stroke=color, 
                                  stroke_width=4, class_="event-node",
                                  id=f"event-{branch['branch_id']}-{j}")
                
                # Inner star
                star = dwg.polygon(points=self._create_star_points(node_x, node_y, 5, 3),
                                 fill=color, opacity=0.8)
                
                # Add title element for tooltip
                title = dwg.title(event)
                g.add(circle)
                g.add(star)
                g.add(title)
                dwg.add(g)
        
        # Add legend
        self._add_legend(dwg)
        
        return dwg.tostring()
    
    def _create_branch_path(self, start_x: int, start_y: int, end_x: int, 
                           end_y: int, branch_index: int) -> str:
        """Create a curved path for a branch"""
        # Add some randomness to make branches look natural
        control1_x = start_x + (end_x - start_x) * 0.3 + random.randint(-20, 20)
        control1_y = start_y + (end_y - start_y) * 0.3
        
        control2_x = start_x + (end_x - start_x) * 0.7 + random.randint(-20, 20)
        control2_y = start_y + (end_y - start_y) * 0.7
        
        # Create smooth bezier curve
        path = f"M {start_x},{start_y} C {control1_x},{control1_y} {control2_x},{control2_y} {end_x},{end_y}"
        return path
    
    def _get_point_on_curve(self, start_x: int, start_y: int, end_x: int, 
                           end_y: int, t: float, branch_index: int) -> Tuple[float, float]:
        """Get a point along the bezier curve at parameter t (0-1)"""
        # Simplified bezier calculation
        control1_x = start_x + (end_x - start_x) * 0.3 + (branch_index - 1.5) * 10
        control1_y = start_y + (end_y - start_y) * 0.3
        
        control2_x = start_x + (end_x - start_x) * 0.7 + (branch_index - 1.5) * 10
        control2_y = start_y + (end_y - start_y) * 0.7
        
        # Cubic bezier formula
        x = ((1-t)**3 * start_x + 
             3*(1-t)**2*t * control1_x + 
             3*(1-t)*t**2 * control2_x + 
             t**3 * end_x)
        
        y = ((1-t)**3 * start_y + 
             3*(1-t)**2*t * control1_y + 
             3*(1-t)*t**2 * control2_y + 
             t**3 * end_y)
        
        return x, y
    
    def _create_star_points(self, cx: float, cy: float, outer_r: float, inner_r: float) -> str:
        """Create points for a 5-pointed star"""
        points = []
        for i in range(10):
            angle = (i * math.pi / 5) - (math.pi / 2)
            r = outer_r if i % 2 == 0 else inner_r
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append(f"{x},{y}")
        return " ".join(points)
    
    def _add_legend(self, dwg):
        """Add a legend to the visualization"""
        legend_x = 20
        legend_y = self.height - 80
        
        # Game-style legend box
        legend_group = dwg.g()
        
        # Legend background with gradient
        legend_grad = dwg.defs.add(dwg.linearGradient(id="legend-grad", x1="0%", y1="0%", x2="100%", y2="100%"))
        legend_grad.add_stop_color(offset="0%", color="#FFE5B4")
        legend_grad.add_stop_color(offset="100%", color="#FFDAB9")
        
        legend_bg = dwg.rect(insert=(legend_x - 15, legend_y - 30), 
                           size=(220, 85), 
                           fill="url(#legend-grad)", 
                           stroke="#FFD700", 
                           stroke_width=3,
                           rx=15, ry=15, 
                           opacity=0.95)
        legend_group.add(legend_bg)
        
        # Legend title with game font
        legend_title = dwg.text("🗺️ Quest Guide:", 
                              insert=(legend_x, legend_y), 
                              style="font-family: 'Fredoka', cursive; font-size: 16px; font-weight: 700; fill: #667eea;")
        legend_group.add(legend_title)
        
        # Legend items with icons
        items = [
            "🎈 Branches = Timeline Adventures",
            "✨ Hover = Reveal Magic",
            "💎 Events = Power-Up Points"
        ]
        
        for i, item in enumerate(items):
            legend_text = dwg.text(item, 
                                 insert=(legend_x, legend_y + 20 + i*18), 
                                 style="font-family: 'Fredoka', cursive; font-size: 13px; fill: #333; font-weight: 500;")
            legend_group.add(legend_text)
        
        dwg.add(legend_group)
    
    def create_shareable_image(self, svg_content: str) -> str:
        """Convert SVG to base64 for sharing"""
        return base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')

class MobileRiverAdapter:
    """Adapter for mobile-responsive visualizations"""
    
    @staticmethod
    def adapt_for_mobile(svg_content: str, screen_width: int) -> str:
        """Adapt SVG for mobile screens"""
        if screen_width < 768:
            # Add viewBox for responsive scaling
            svg_content = svg_content.replace(
                '<svg ', 
                '<svg viewBox="0 0 800 600" preserveAspectRatio="xMidYMid meet" '
            )
            # Make text slightly larger for mobile
            svg_content = svg_content.replace('font-size: 12px', 'font-size: 14px')
            svg_content = svg_content.replace('font-size: 14px', 'font-size: 16px')
        
        return svg_content