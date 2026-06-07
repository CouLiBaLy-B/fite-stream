"""
FitStream Prompt Templates Library
Pre-built prompt templates for common scenarios.

Categories:
  - Actions (walking, dancing, sitting, etc.)
  - Locations (Paris, beach, forest, studio, etc.)
  - Emotions (happy, contemplative, dramatic, etc.)
  - Camera work (dolly, pan, close-up, tracking, etc.)
  - Story arcs (introduction, conflict, resolution, etc.)
  - Fashion (runway, editorial, street style, etc.)

Usage:
    from fitstream.core.prompt_templates import PromptTemplateLibrary

    lib = PromptTemplateLibrary()

    # Get a template and fill it
    prompt = lib.get("fashion.runway", person="a woman", garment="red dress")
    # → "A woman walks confidently down a high-fashion runway wearing a red dress..."

    # Browse categories
    categories = lib.list_categories()
    templates = lib.list_templates("actions")
"""

from dataclasses import dataclass


@dataclass
class PromptTemplate:
    """A reusable prompt template with fill-in variables."""

    id: str
    category: str
    name: str
    template: str  # Use {variable} for placeholders
    description: str = ""
    variables: list[str] | None = None  # Expected variables
    tags: list[str] | None = None
    example: str = ""

    def __post_init__(self) -> None:
        if self.variables is None:
            # Auto-detect variables from template
            import re

            self.variables = re.findall(r"\{(\w+)\}", self.template)
        if self.tags is None:
            self.tags = [self.category]

    def fill(self, **kwargs) -> str:
        """Fill in the template with provided values."""
        result = self.template
        for key, value in kwargs.items():
            result = result.replace(f"{{{key}}}", str(value))
        # Remove unfilled placeholders with sensible defaults
        import re

        result = re.sub(r"\{person\}", "the person", result)
        result = re.sub(r"\{garment\}", "a stylish outfit", result)
        result = re.sub(r"\{location\}", "a beautiful setting", result)
        result = re.sub(r"\{\w+\}", "", result)
        return result.strip()


# ============================================================
# Template Library
# ============================================================

TEMPLATES: list[PromptTemplate] = [
    # ---------- ACTIONS ----------
    PromptTemplate(
        id="actions.walk",
        category="actions",
        name="Walking",
        template="{person} walks naturally with confident strides, arms swaying gently, looking ahead with a calm expression",
        description="Natural walking motion",
    ),
    PromptTemplate(
        id="actions.walk_toward_camera",
        category="actions",
        name="Walk Toward Camera",
        template="{person} walks directly toward the camera with a confident stride, making eye contact, slight smile",
        description="Approaching the viewer",
    ),
    PromptTemplate(
        id="actions.turn_360",
        category="actions",
        name="360° Turn",
        template="{person} slowly turns in a full 360 degrees, showing all angles, pausing briefly at each quarter turn",
        description="Full rotation to show all sides",
    ),
    PromptTemplate(
        id="actions.sit_and_read",
        category="actions",
        name="Sitting and Reading",
        template="{person} sits comfortably in a chair, picks up a book, opens it, and begins reading with a thoughtful expression",
    ),
    PromptTemplate(
        id="actions.dance",
        category="actions",
        name="Dancing",
        template="{person} dances joyfully to music, fluid movements, spinning gracefully, arms outstretched with a beaming smile",
    ),
    PromptTemplate(
        id="actions.wave",
        category="actions",
        name="Waving Hello",
        template="{person} looks at the camera, smiles warmly, and waves hello with a friendly, natural gesture",
    ),
    # ---------- LOCATIONS ----------
    PromptTemplate(
        id="locations.paris_street",
        category="locations",
        name="Parisian Street",
        template="{person} in a charming Parisian street with Haussmann buildings, cobblestone sidewalks, and a distant view of the Eiffel Tower, warm afternoon light",
    ),
    PromptTemplate(
        id="locations.beach_sunset",
        category="locations",
        name="Beach at Sunset",
        template="{person} on a pristine sandy beach at golden hour, gentle waves lapping at the shore, warm orange and pink sunset sky reflecting on the water",
    ),
    PromptTemplate(
        id="locations.forest",
        category="locations",
        name="Enchanted Forest",
        template="{person} in a lush green forest with dappled sunlight filtering through tall trees, moss-covered rocks, and a gentle mist",
    ),
    PromptTemplate(
        id="locations.studio",
        category="locations",
        name="Professional Studio",
        template="{person} in a clean professional photography studio with soft white backdrop, studio lighting creating gentle shadows, minimalist setup",
    ),
    PromptTemplate(
        id="locations.cafe",
        category="locations",
        name="Cozy Café",
        template="{person} in a cozy European café with warm wooden interior, soft ambient lighting, coffee cups on marble tables, vintage decor",
    ),
    PromptTemplate(
        id="locations.rooftop_city",
        category="locations",
        name="City Rooftop",
        template="{person} on a modern rooftop terrace overlooking a city skyline at twilight, city lights beginning to glow, dramatic sky",
    ),
    # ---------- EMOTIONS ----------
    PromptTemplate(
        id="emotions.joyful",
        category="emotions",
        name="Joyful",
        template="{person} radiates genuine joy, bright smile, eyes sparkling with happiness, natural laughter, warm and inviting energy",
    ),
    PromptTemplate(
        id="emotions.contemplative",
        category="emotions",
        name="Contemplative",
        template="{person} gazes thoughtfully into the distance, serene expression, gentle breeze, quiet moment of reflection",
    ),
    PromptTemplate(
        id="emotions.confident",
        category="emotions",
        name="Confident",
        template="{person} stands with powerful confident posture, shoulders back, chin slightly raised, commanding presence, determined gaze",
    ),
    PromptTemplate(
        id="emotions.mysterious",
        category="emotions",
        name="Mysterious",
        template="{person} partially in shadow, enigmatic half-smile, dramatic side lighting, an air of mystery and intrigue",
    ),
    # ---------- CAMERA ----------
    PromptTemplate(
        id="camera.dolly_in",
        category="camera",
        name="Dolly In",
        template="Camera slowly dollies in toward {person}, starting from a medium-wide shot and ending in a close-up, smooth continuous motion",
    ),
    PromptTemplate(
        id="camera.orbit",
        category="camera",
        name="Orbit Around",
        template="Camera orbits smoothly around {person}, circling 180 degrees while maintaining focus, revealing the scene from multiple angles",
    ),
    PromptTemplate(
        id="camera.low_angle",
        category="camera",
        name="Low Angle Hero Shot",
        template="Low angle camera looking up at {person}, dramatic perspective making them appear powerful, sky visible in background, heroic framing",
    ),
    PromptTemplate(
        id="camera.tracking_walk",
        category="camera",
        name="Tracking Walk",
        template="Camera tracks alongside {person} as they walk, smooth lateral movement, keeping them centered in frame, background gently blurring",
    ),
    # ---------- FASHION ----------
    PromptTemplate(
        id="fashion.runway",
        category="fashion",
        name="Runway Walk",
        template="{person} walks confidently down a high-fashion runway wearing {garment}, dramatic catwalk lighting, audience in background, fierce expression, editorial pose at the end",
        description="Fashion show runway scene",
    ),
    PromptTemplate(
        id="fashion.editorial",
        category="fashion",
        name="Editorial Photoshoot",
        template="{person} poses in {garment} for a high-end fashion editorial, dramatic lighting, striking poses, magazine-quality composition, artistic angles",
    ),
    PromptTemplate(
        id="fashion.street_style",
        category="fashion",
        name="Street Style",
        template="{person} walks casually in {garment} through an urban setting, street photography style, natural daylight, candid vibe, city backdrop",
    ),
    PromptTemplate(
        id="fashion.fitting_room",
        category="fashion",
        name="Fitting Room Mirror",
        template="{person} tries on {garment} in a bright fitting room, checking the fit in a full-length mirror, turning to see different angles, satisfied expression",
    ),
    # ---------- STORY ARCS ----------
    PromptTemplate(
        id="story.introduction",
        category="story",
        name="Story Opening",
        template="{person} appears in {location}, the camera slowly reveals the scene, establishing the setting and character with a sense of beginning",
    ),
    PromptTemplate(
        id="story.discovery",
        category="story",
        name="Discovery Moment",
        template="{person} notices something surprising, eyes widen with curiosity, walks closer to investigate, the camera follows their gaze",
    ),
    PromptTemplate(
        id="story.climax",
        category="story",
        name="Emotional Climax",
        template="{person} experiences a powerful emotional moment, dramatic lighting shifts, time seems to slow, deep expression on their face, cinematic music feel",
    ),
    PromptTemplate(
        id="story.resolution",
        category="story",
        name="Peaceful Resolution",
        template="{person} relaxes into a peaceful moment, tension releases, gentle smile, golden hour lighting wraps around them, a sense of completion",
    ),
]


class PromptTemplateLibrary:
    """
    Browsable library of prompt templates.

    Usage:
        lib = PromptTemplateLibrary()

        # Get and fill a template
        prompt = lib.get("fashion.runway", person="a model", garment="red gown")

        # List categories
        categories = lib.list_categories()  # ["actions", "locations", ...]

        # Browse templates in a category
        templates = lib.list_templates("camera")
    """

    def __init__(self) -> None:
        self._templates: dict[str, PromptTemplate] = {t.id: t for t in TEMPLATES}

    def get(self, template_id: str, **kwargs) -> str | None:
        template = self._templates.get(template_id)
        if template:
            return template.fill(**kwargs)
        return None

    def get_template(self, template_id: str) -> PromptTemplate | None:
        """Get a template by ID and fill in variables."""
        return self._templates.get(template_id)

    def list_categories(self) -> list[str]:
        """Get a template object by ID."""
        """List all template categories."""
        return sorted(set(t.category for t in self._templates.values()))

    def list_templates(self, category: str | None = None) -> list[dict]:
        templates = list(self._templates.values())
        if category:
            templates = [t for t in templates if t.category == category]

        return [
            {
                "id": t.id,
                "category": t.category,
                "name": t.name,
                "description": t.description or t.template[:80] + "...",
                "variables": t.variables,
                "example": t.fill(
                    person="a young woman", garment="an elegant dress", location="a sunlit garden"
                )[:100]
                + "...",
            }
            for t in sorted(templates, key=lambda x: (x.category, x.name))
        ]

    def search(self, query: str) -> list[dict]:
        """List templates, optionally filtered by category."""
        q = query.lower()
        results = [
            t
            for t in self._templates.values()
            if q in t.name.lower()
            or q in t.template.lower()
            or q in t.description.lower()
            or any(q in tag for tag in t.tags)
        ]
        return [{"id": t.id, "name": t.name, "category": t.category} for t in results]

    def count(self) -> int:
        """Search templates by name, description, or template text."""
        """Count."""
        return len(self._templates)
