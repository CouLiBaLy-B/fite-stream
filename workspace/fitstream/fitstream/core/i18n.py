"""
FitStream Internationalization (i18n)
Multi-language prompt translation and enhancement.

Supports: English, French, Chinese, Japanese, Spanish, Arabic, Korean, Portuguese.

The video models (Wan, LoomVideo) understand English and Chinese natively.
For other languages, prompts are translated to English before generation,
and UI messages are served in the user's language.

Usage:
    from fitstream.core.i18n import I18n, translate_prompt
    
    # Translate a French prompt for the AI model
    en_prompt = translate_prompt("Une femme marche dans Paris au coucher du soleil", "fr")
    # → "A woman walks in Paris at sunset"
    
    # Get UI messages in French
    i18n = I18n("fr")
    print(i18n.t("status.processing"))  # → "En cours de génération..."
"""

from typing import Optional, Dict
from loguru import logger


# ============================================================
# UI Translations
# ============================================================

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        "app.title": "FitStream — AI Animation",
        "app.tagline": "Transform photos into animated stories",
        "status.queued": "Queued",
        "status.processing": "Generating...",
        "status.completed": "Done!",
        "status.failed": "Generation failed",
        "tab.animate": "Animate",
        "tab.story": "Story",
        "tab.tryon": "Try-On",
        "tab.compose": "Compose",
        "tab.gallery": "Gallery",
        "tab.style": "Style",
        "upload.person": "Upload person photo",
        "upload.garment": "Upload garment photo",
        "upload.images": "Upload reference images",
        "prompt.placeholder": "Describe the animation you want...",
        "story.placeholder": "Write your story here...",
        "btn.generate": "Generate",
        "btn.tryon": "Try It On",
        "btn.compose": "Create Composition",
        "quality.draft": "Draft (~15s)",
        "quality.standard": "Standard (~45s)",
        "quality.high": "High Quality (~2min)",
        "error.no_image": "Please upload an image",
        "error.no_prompt": "Please enter a prompt",
        "error.gpu_unavailable": "No GPU available",
    },
    "fr": {
        "app.title": "FitStream — Animation IA",
        "app.tagline": "Transformez vos photos en histoires animées",
        "status.queued": "En file d'attente",
        "status.processing": "En cours de génération...",
        "status.completed": "Terminé !",
        "status.failed": "Échec de la génération",
        "tab.animate": "Animer",
        "tab.story": "Histoire",
        "tab.tryon": "Essayage",
        "tab.compose": "Composer",
        "tab.gallery": "Galerie",
        "tab.style": "Style",
        "upload.person": "Télécharger une photo de personne",
        "upload.garment": "Télécharger une photo de vêtement",
        "upload.images": "Télécharger les images de référence",
        "prompt.placeholder": "Décrivez l'animation souhaitée...",
        "story.placeholder": "Écrivez votre histoire ici...",
        "btn.generate": "Générer",
        "btn.tryon": "Essayer",
        "btn.compose": "Créer la composition",
        "quality.draft": "Brouillon (~15s)",
        "quality.standard": "Standard (~45s)",
        "quality.high": "Haute qualité (~2min)",
        "error.no_image": "Veuillez télécharger une image",
        "error.no_prompt": "Veuillez saisir un prompt",
        "error.gpu_unavailable": "Aucun GPU disponible",
    },
    "zh": {
        "app.title": "FitStream — AI动画",
        "app.tagline": "将照片变成动画故事",
        "status.queued": "排队中",
        "status.processing": "生成中...",
        "status.completed": "完成！",
        "status.failed": "生成失败",
        "tab.animate": "动画",
        "tab.story": "故事",
        "tab.tryon": "试穿",
        "tab.compose": "合成",
        "tab.gallery": "画廊",
        "tab.style": "风格",
        "upload.person": "上传人物照片",
        "upload.garment": "上传服装照片",
        "prompt.placeholder": "描述您想要的动画...",
        "btn.generate": "生成",
        "btn.tryon": "试穿",
        "quality.draft": "草稿 (~15秒)",
        "quality.standard": "标准 (~45秒)",
        "quality.high": "高质量 (~2分钟)",
    },
    "ja": {
        "app.title": "FitStream — AIアニメーション",
        "app.tagline": "写真をアニメーションストーリーに変換",
        "status.processing": "生成中...",
        "status.completed": "完了！",
        "tab.animate": "アニメ化",
        "tab.story": "ストーリー",
        "tab.tryon": "試着",
        "tab.gallery": "ギャラリー",
        "btn.generate": "生成する",
    },
    "es": {
        "app.title": "FitStream — Animación IA",
        "app.tagline": "Transforma fotos en historias animadas",
        "status.processing": "Generando...",
        "status.completed": "¡Completado!",
        "tab.animate": "Animar",
        "tab.story": "Historia",
        "tab.tryon": "Probador",
        "tab.gallery": "Galería",
        "btn.generate": "Generar",
    },
    "ar": {
        "app.title": "FitStream — رسوم متحركة بالذكاء الاصطناعي",
        "status.processing": "...جاري التوليد",
        "status.completed": "!تم",
        "btn.generate": "توليد",
    },
    "ko": {
        "app.title": "FitStream — AI 애니메이션",
        "status.processing": "생성 중...",
        "status.completed": "완료!",
        "btn.generate": "생성",
    },
    "pt": {
        "app.title": "FitStream — Animação IA",
        "status.processing": "Gerando...",
        "status.completed": "Concluído!",
        "btn.generate": "Gerar",
    },
}

SUPPORTED_LANGUAGES = list(TRANSLATIONS.keys())


# ============================================================
# Prompt Translation Maps (for non-English → English)
# ============================================================

# Common phrase translations for prompt construction
# (lightweight, no external API needed)
PROMPT_PHRASES: Dict[str, Dict[str, str]] = {
    "fr": {
        "une femme": "a woman",
        "un homme": "a man",
        "une personne": "a person",
        "marche": "walks",
        "danse": "dances",
        "sourit": "smiles",
        "court": "runs",
        "s'assoit": "sits down",
        "regarde": "looks at",
        "dans": "in",
        "sur": "on",
        "au coucher du soleil": "at sunset",
        "au lever du soleil": "at sunrise",
        "sous la pluie": "in the rain",
        "sous la neige": "in the snow",
        "une rue": "a street",
        "un jardin": "a garden",
        "une plage": "a beach",
        "un café": "a café",
        "une forêt": "a forest",
        "une robe": "a dress",
        "une veste": "a jacket",
        "un chapeau": "a hat",
        "des chaussures": "shoes",
        "rouge": "red",
        "bleu": "blue",
        "noir": "black",
        "blanc": "white",
        "élégant": "elegant",
        "joyeux": "joyful",
        "triste": "sad",
        "mystérieux": "mysterious",
        "Paris": "Paris",
    },
    "zh": {
        "一个女人": "a woman",
        "一个男人": "a man",
        "走路": "walks",
        "跳舞": "dances",
        "微笑": "smiles",
        "日落": "sunset",
        "花园": "garden",
        "海滩": "beach",
        "森林": "forest",
        "红色": "red",
        "蓝色": "blue",
        "黑色": "black",
        "白色": "white",
        "裙子": "dress",
        "优雅": "elegant",
        "快乐": "happy",
    },
    "es": {
        "una mujer": "a woman",
        "un hombre": "a man",
        "camina": "walks",
        "baila": "dances",
        "sonríe": "smiles",
        "en la playa": "on the beach",
        "vestido": "dress",
        "elegante": "elegant",
    },
}


def translate_prompt(prompt: str, source_lang: str) -> str:
    """
    Translate a prompt from source language to English.
    
    Uses a lightweight phrase-replacement approach. For production,
    integrate with a proper translation API (DeepL, Google Translate, etc.)
    
    Args:
        prompt: Original prompt in source language
        source_lang: ISO 639-1 code ("fr", "zh", "es", etc.)
    
    Returns:
        English translation (best-effort)
    """
    if source_lang == "en":
        return prompt
    
    phrases = PROMPT_PHRASES.get(source_lang, {})
    if not phrases:
        logger.warning(f"No translation phrases for language '{source_lang}', using original")
        return prompt
    
    result = prompt.lower()
    
    # Sort by length (longest first) to avoid partial replacements
    sorted_phrases = sorted(phrases.items(), key=lambda x: len(x[0]), reverse=True)
    for src, dst in sorted_phrases:
        result = result.replace(src.lower(), dst)
    
    # Capitalize first letter
    result = result.strip()
    if result:
        result = result[0].upper() + result[1:]
    
    logger.debug(f"Translated [{source_lang}→en]: '{prompt[:50]}...' → '{result[:50]}...'")
    return result


class I18n:
    """
    Internationalization helper for UI messages.
    
    Usage:
        i18n = I18n("fr")
        print(i18n.t("status.processing"))  # "En cours de génération..."
        print(i18n.t("nonexistent.key"))    # "nonexistent.key" (fallback)
    """
    
    def __init__(self, lang: str = "en") -> None:
        self.lang = lang if lang in SUPPORTED_LANGUAGES else "en"
        self._messages = TRANSLATIONS.get(self.lang, {})
        self._fallback = TRANSLATIONS.get("en", {})
    
    def t(self, key: str) -> str:
        return self._messages.get(key, self._fallback.get(key, key))
    
    def get_all(self) -> Dict[str, str]:
        """Translate a UI message key."""
        """Get all messages for the current language (with English fallback)."""
        merged = dict(self._fallback)
        merged.update(self._messages)
        return merged
    
    @staticmethod
    def supported_languages() -> list:
        """List all supported language codes."""
        return SUPPORTED_LANGUAGES
