# 🎬 GUIDE DÉFINITIF — Modèles Open-Source pour Animation de Personnages
## Image de personne + Prompt → Vidéo animée fluide pour raconter des histoires

> **Date** : 7 juin 2026  
> **Objectif** : Identifier les modèles réellement disponibles, open-source, téléchargeables, pour générer des animations fluides à partir de photos de personnes et de prompts narratifs.

---

## TABLEAU DE SYNTHÈSE — DISPONIBILITÉ RÉELLE

| # | Modèle | Open-Source ? | Poids dispo ? | Code dispo ? | GPU min | Meilleur pour |
|---|--------|:---:|:---:|:---:|---|---|
| 1 | **Wan 2.1/2.2 VACE** | ✅ Oui | ✅ HuggingFace | ✅ GitHub | 12-24GB | 🥇 **CHOIX #1** — Animation complète |
| 2 | **LoomVideo** | ✅ Oui | ✅ HuggingFace | ✅ GitHub | 24-80GB | 🥈 Édition fashion / multi-image |
| 3 | **LTX-Video 13B** | ✅ Oui | ✅ HuggingFace | ✅ GitHub | 12GB | 🥉 Rapide, léger, storytelling |
| 4 | **Wan 2.2 Fun (VACE)** | ✅ Oui | ✅ HuggingFace | ✅ ComfyUI | 16-24GB | Animation stylisée |
| 5 | **LHM (Large Human Model)** | ✅ Oui | ✅ HuggingFace | ✅ GitHub | 24GB | Animation 3D de personnes |
| 6 | **SkyReels V1** | ✅ Oui | ✅ HuggingFace | ✅ GitHub | 80GB | Cinématique, haute qualité |
| 7 | **HunyuanVideo** | ✅ Oui | ✅ HuggingFace | ✅ GitHub | 48-80GB | Vidéo haute fidélité |
| 8 | **FashionChameleon** | ⚠️ Partiel | ❌ **Pas encore** | ✅ GitHub | ? | Temps réel fashion (à venir) |
| 9 | **OmniVTON** | ✅ Oui | ✅ (training-free) | ✅ GitHub | 12-24GB | Try-on sans entraînement |
| 10 | **AnimateDiff** | ✅ Oui | ✅ HuggingFace | ✅ Diffusers | 8-16GB | Animation SD1.5, léger |

---

## 1. 🥇 WAN 2.1/2.2 + VACE — LE CHOIX #1

### Pourquoi c'est le meilleur pour ton cas d'usage

C'est le framework le plus complet, le plus accessible et le plus polyvalent pour :
- Prendre une **image de personne** → Générer une **vidéo animée**
- Ajouter un **prompt textuel** pour guider l'histoire
- **Éditer** des vidéos existantes (changer vêtements, fond, actions)
- **Animer n'importe quoi** à partir d'images de référence

### Disponibilité

| Élément | URL | Statut |
|---------|-----|--------|
| Code VACE | https://github.com/ali-vilab/VACE | ✅ Disponible |
| Wan2.1 VACE 1.3B | https://huggingface.co/Wan-AI/Wan2.1-VACE-1.3B-Preview | ✅ Téléchargeable |
| Wan2.1 VACE 14B | https://huggingface.co/Wan-AI/Wan2.1-VACE-14B | ✅ Téléchargeable |
| Wan2.2 T2V A14B | https://huggingface.co/Wan-AI/Wan2.2-T2V-A14B | ✅ Téléchargeable |
| Wan2.2 I2V A14B | https://huggingface.co/Wan-AI/Wan2.2-I2V-A14B | ✅ Téléchargeable |
| ComfyUI workflows | Communauté r/StableDiffusion | ✅ Disponibles |
| Diffusers intégration | `diffusers` Python lib | ✅ Native |
| Licence | Apache-like (commercial OK) | ✅ |

### Ce que tu peux faire concrètement

```python
# EXEMPLE 1 : Image de personne → Vidéo animée avec prompt narratif
import torch
from diffusers import DiffusionPipeline
from diffusers.utils import load_image, export_to_video

pipe = DiffusionPipeline.from_pretrained(
    "Wan-AI/Wan2.1-VACE-14B",
    dtype=torch.bfloat16
)
pipe.to("cuda")

# Charger ton image de personne
image = load_image("./ma_photo.png")

# Prompt narratif pour l'histoire
prompt = """A young woman walks through a sunlit Parisian street,
she pauses at a flower shop, picks up a bouquet of roses,
smiles warmly, and continues walking with a gentle breeze
flowing through her hair."""

output = pipe(image=image, prompt=prompt).frames
export_to_video(output, "histoire_paris.mp4", fps=16)
```

```bash
# EXEMPLE 2 : Via le script VACE natif (plus de contrôle)
git clone https://github.com/ali-vilab/VACE.git && cd VACE
pip install -r requirements.txt
pip install wan@git+https://github.com/Wan-Video/Wan2.1

# Animation d'une personne avec référence image
python vace/vace_wan_inference.py \
    --ckpt_dir models/VACE-Wan2.1-14B \
    --src_ref_images ./ma_photo.png \
    --prompt "The person walks confidently down a runway, \
              turns elegantly, poses, then walks back" \
    --size 720p
```

### Tâches VACE pour tes histoires

| Tâche VACE | Entrée | Sortie | Usage storytelling |
|------------|--------|--------|-------------------|
| **Reference-to-Video (R2V)** | Image(s) personne + prompt | Vidéo animée | Animer un personnage |
| **Video-to-Video (V2V)** | Vidéo + prompt éditorial | Vidéo modifiée | Changer le style/lieu |
| **Masked V2V (MV2V)** | Vidéo + masque + ref image | Vidéo éditée localement | Changer un vêtement |
| **Animate Anything** | Image quelconque + prompt | Vidéo animée | Donner vie à n'importe quoi |
| **Temporal Extension** | Vidéo courte | Vidéo plus longue | Étendre une scène |
| **Composition libre** | Combiner tout ci-dessus | Vidéo complexe | Scénario multi-scènes |

### Configurations matérielles

| GPU | Modèle VACE | Résolution | Notes |
|-----|------------|------------|-------|
| RTX 4090 (24GB) | 1.3B | 480p | Avec `--offload_model True --t5_cpu` |
| RTX 4090 (24GB) | 14B | 480p | Avec offloading agressif |
| 2× A100 (80GB) | 14B | 720p | Configuration recommandée |
| H100 (80GB) | 14B | 720p | Performance optimale |

---

## 2. 🥈 LOOMVIDEO — Spécialisé Fashion + Multi-Image

### Disponibilité

| Élément | URL | Statut |
|---------|-----|--------|
| Code | https://github.com/MSALab-PKU/LoomVideo | ✅ Disponible |
| Poids (Stage 3) | https://huggingface.co/MSALab/LoomVideo | ✅ Téléchargeable |
| Paper | https://arxiv.org/abs/2606.06042 | ✅ Publié |
| Licence | Open research | ✅ |

### Cas d'usage unique : Multi-Image Storytelling

LoomVideo excelle là où VACE ne peut pas : **combiner PLUSIEURS images de référence** dans une seule vidéo narrative.

```bash
# Exemple : Combiner personne + vêtement + décor
NUM_GPUS=1 accelerate launch --num_processes=1 \
    scripts/inference/generate.py \
    --config_path configs/inference/generation.yaml \
    --ckpt_path checkpoints/LoomVideo \
    --task mi2v \
    --prompt "The woman (@Image 1) walks through the garden (@Image 3), \
              wearing the elegant red dress (@Image 2). She stops to \
              admire the flowers, twirls gracefully, and continues \
              down the path with a serene smile." \
    --ref_image_paths photos/woman.jpg photos/red_dress.jpg photos/garden.jpg \
    --num_frames 97 \
    --num_inference_steps 50 \
    --output_path outputs/story_garden.mp4
```

### Tâches LoomVideo pour storytelling

| Tâche | Commande `--task` | Usage |
|-------|------------------|-------|
| Text-to-Video | `t2v` | Générer une scène from scratch |
| Multi-Image-to-Video | `mi2v` | **Combiner personnage + lieu + objets** |
| Instruction Editing | `edit` | Modifier un élément d'une vidéo existante |
| Reference Editing | `ref_edit` | Remplacer un objet par une image de référence |

### Exigences matérielles

- **Minimum** : 1× GPU 24GB (avec offloading)
- **Recommandé** : 1× GPU 80GB (A100/H100) pour 50 steps
- **Optimal** : 2-4× GPU pour vidéos longues

---

## 3. 🥉 LTX-VIDEO 13B — Rapide et Léger

### Pourquoi c'est intéressant

- **Très rapide** : génération en quelques secondes
- **Léger** : tourne sur GPU 12GB
- **Keyframe conditioning** : spécifie des images à des moments précis de la vidéo
- **Distilled version** : encore plus rapide

### Disponibilité

| Élément | URL | Statut |
|---------|-----|--------|
| Code | https://github.com/Lightricks/LTX-Video | ✅ |
| Poids 13B | https://huggingface.co/Lightricks/LTX-Video | ✅ |
| Distilled | Configs fournis | ✅ |
| Diffusers | Support natif | ✅ |

```python
# LTX-Video : Image personne → Vidéo avec keyframes
python inference.py \
    --prompt "A person telling a story, gesturing expressively, \
              warm lighting, cinematic feel" \
    --conditioning_media_paths person.jpg scene_end.jpg \
    --conditioning_start_frames 0 80 \
    --height 480 --width 832 \
    --num_frames 97 \
    --pipeline_config configs/ltxv-13b-0.9.8-distilled.yaml
```

---

## 4. LHM — Animation 3D de Personnage depuis UNE Photo

### C'est quoi ?

LHM (Large Animatable Human Model) prend **une seule photo** d'une personne et génère un **personnage 3D animable** que tu peux faire bouger avec n'importe quelle séquence de mouvement.

### Disponibilité

| Élément | URL | Statut |
|---------|-----|--------|
| Code | https://github.com/aigc3d/LHM | ✅ ICCV 2025 |
| Poids 500M/1B | HuggingFace | ✅ |
| Modèles HF-optimized | LHM-500M-HF, LHM-1B-HF | ✅ |

```bash
# Prendre une photo → Animer avec une séquence de mouvement
bash inference.sh LHM-1B-HF ./photos/personne.jpg ./motions/walk_and_turn/smplx_params
```

**Idéal pour** : Créer un avatar 3D de ta personne, puis le faire danser, marcher, gesticuler.

---

## 5. FASHIONCHAMELEON (Alibaba) — ⚠️ PAS ENCORE DISPONIBLE

### Statut actuel (7 juin 2026)

| Élément | Statut |
|---------|--------|
| Code GitHub | ✅ https://github.com/QuanjianSong/FashionChameleon |
| Poids du modèle | ❌ **Non publié** — marqué "Todo" dans le README |
| Dataset HGC-Bench | ❌ **Non publié** — issue #1 ouverte sur GitHub |
| Paper | ✅ arXiv:2605.15824 |

**Conclusion** : Le code est là mais **les poids ne sont pas encore publiés**. On ne peut pas l'utiliser pour l'instant. À surveiller.

---

## 6. OMNIVTON — Try-On Training-Free

### Pourquoi c'est magique

- **Aucun entraînement nécessaire** : fonctionne directement avec Stable Diffusion / FLUX
- Utilise DDIM inversion + garment morphing
- **Multi-personne** supporté
- Idéal pour du try-on rapide sans infrastructure d'entraînement

### Disponibilité

| Élément | URL | Statut |
|---------|-----|--------|
| OmniVTON Code | https://github.com/Jerome-Young/OmniVTON | ✅ |
| OmniVTON++ Code | https://github.com/Jerome-Young/OmniVTON-PlusPlus | ✅ |
| Poids | Utilise SD 2.0 ou FLUX (pré-entraîné) | ✅ Rien à télécharger de spécial |

---

## 7. AUTRES MODÈLES NOTABLES

### AnimateDiff (léger, SD1.5-based)
- **GPU** : 8-16GB — tourne sur des machines modestes
- **ComfyUI** : intégration native
- **FreeNoise** : génère des vidéos longues avec des prompts évoluant dans le temps
- Parfait pour du prototypage rapide

### HunyuanVideo (Tencent)
- Très haute qualité, guidage par pose
- Open-source, poids disponibles
- Nécessite 48-80GB GPU

### SkyReels V1
- Qualité cinématique, entraîné sur films/séries
- Expressions faciales très réalistes
- Nécessite 80GB GPU

---

## 🏗️ PIPELINE RECOMMANDÉ POUR TON PROJET

### Architecture en 3 niveaux de qualité

```
┌──────────────────────────────────────────────────────────────────┐
│                 PIPELINE "PETITES HISTOIRES"                     │
│                                                                  │
│  ENTRÉE : Photo(s) personne + Script/prompt de l'histoire       │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  NIVEAU 1 — Brouillon rapide (10-30s)                     │  │
│  │                                                            │  │
│  │  Modèle : LTX-Video 13B (distilled)                       │  │
│  │  GPU : 12GB suffit                                         │  │
│  │  Usage : Voir si l'histoire "marche" visuellement          │  │
│  │  Résolution : 480p, 5-8 secondes                          │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  NIVEAU 2 — Production (1-5 min)                          │  │
│  │                                                            │  │
│  │  Modèle : Wan 2.1/2.2 VACE 14B                           │  │
│  │  GPU : 24-80GB                                             │  │
│  │  Usage : Scènes fluides, expressions, mouvements          │  │
│  │  Résolution : 720p, 10-20 secondes par clip               │  │
│  │  Features : R2V, temporal extension, composition           │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  NIVEAU 3 — Post-production (5-15 min)                    │  │
│  │                                                            │  │
│  │  Modèle : LoomVideo 5B                                    │  │
│  │  GPU : 80GB                                                │  │
│  │  Usage : Multi-image composition, changements de tenue    │  │
│  │  Features : Combiner personne + lieu + objets + texte     │  │
│  │  Résolution : 720p, 97 frames                             │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  SORTIE : Clips vidéo assemblés en mini-histoire                │
│           (concaténation via ffmpeg ou éditeur vidéo)            │
└──────────────────────────────────────────────────────────────────┘
```

### Workflow concret pour une "petite histoire"

```
ÉTAPE 1 : Écrire le script
─────────────────────────
"Marie marche dans Paris. Elle entre dans une boulangerie.
 Elle achète un croissant. Elle s'assoit à une terrasse de café.
 Elle regarde le coucher de soleil sur la Seine."

ÉTAPE 2 : Découper en scènes
─────────────────────────────
Scène 1 : Marie marche dans une rue parisienne
Scène 2 : Marie entre dans une boulangerie
Scène 3 : Marie avec un croissant, sort de la boulangerie
Scène 4 : Marie assise à une terrasse de café
Scène 5 : Coucher de soleil sur la Seine, Marie de dos

ÉTAPE 3 : Préparer les assets
──────────────────────────────
- photo_marie.jpg (photo de la personne)
- (optionnel) images de référence pour les lieux

ÉTAPE 4 : Générer chaque scène
───────────────────────────────
# Scène 1
python vace_inference.py --src_ref_images photo_marie.jpg \
    --prompt "A young woman walks confidently down a charming Parisian \
    street with Haussmann buildings, morning light, gentle smile" \
    --size 720p --num_frames 49

# Scène 2
python vace_inference.py --src_ref_images photo_marie.jpg \
    --prompt "The same woman pushes open the door of a cozy French \
    bakery, warm golden light from inside, she looks at the pastries" \
    --size 720p --num_frames 49

# ... etc pour chaque scène

ÉTAPE 5 : Assembler
────────────────────
ffmpeg -f concat -i scenes.txt -c copy histoire_marie.mp4
```

---

## 📥 GUIDE D'INSTALLATION RAPIDE

### Option A : VACE + Wan2.1 (recommandé pour commencer)

```bash
# 1. Cloner
git clone https://github.com/ali-vilab/VACE.git && cd VACE

# 2. Installer
pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
pip install wan@git+https://github.com/Wan-Video/Wan2.1

# 3. Télécharger les poids (choisir selon ton GPU)
# Pour GPU 24GB :
huggingface-cli download Wan-AI/Wan2.1-VACE-1.3B-Preview --local-dir models/VACE-Wan2.1-1.3B-Preview

# Pour GPU 80GB :
huggingface-cli download Wan-AI/Wan2.1-VACE-14B --local-dir models/VACE-Wan2.1-14B

# 4. Tester !
python vace/vace_wan_inference.py \
    --ckpt_dir models/VACE-Wan2.1-1.3B-Preview \
    --src_ref_images ta_photo.png \
    --prompt "The person dances joyfully in a sunny meadow" \
    --size 480p
```

### Option B : LoomVideo (pour multi-image)

```bash
# 1. Cloner
git clone https://github.com/MSALab-PKU/LoomVideo.git && cd LoomVideo

# 2. Installer
pip install -r requirements.txt

# 3. Télécharger
huggingface-cli download MSALab/LoomVideo --local-dir checkpoints/LoomVideo

# 4. Tester
NUM_GPUS=1 accelerate launch --num_processes=1 \
    scripts/inference/generate.py \
    --config_path configs/inference/generation.yaml \
    --ckpt_path checkpoints/LoomVideo \
    --task mi2v \
    --prompt "The person (@Image 1) walks through the city" \
    --ref_image_paths ta_photo.png \
    --num_frames 49 --output_path output.mp4
```

### Option C : ComfyUI (interface visuelle, plus accessible)

ComfyUI supporte nativement Wan2.1/2.2 VACE avec des workflows prêts à l'emploi :
1. Installer ComfyUI
2. Télécharger les modèles Wan VACE dans `models/`
3. Charger les workflows de la communauté r/StableDiffusion
4. Glisser-déposer ton image → écrire le prompt → générer

---

## ⚡ COMPARATIF FINAL — QUEL MODÈLE POUR QUOI ?

| Besoin | Meilleur modèle | Pourquoi |
|--------|----------------|----------|
| **Animation rapide d'une personne** | Wan VACE 1.3B | Léger, rapide, bon résultat |
| **Qualité maximale** | Wan VACE 14B | Meilleur rapport qualité/contrôle |
| **Combiner plusieurs images** | LoomVideo | Seul à supporter `@Image N` dans les prompts |
| **Storytelling multi-scènes** | Wan VACE + temporal extension | Étendre et enchaîner les clips |
| **Changement de vêtement** | Wan VACE (MV2V) ou OmniVTON | Masking + inpainting guidé |
| **Avatar 3D animable** | LHM | Photo → personnage 3D → animation |
| **Prototypage ultra-rapide** | LTX-Video distilled | ~10 secondes de génération |
| **GPU limité (12GB)** | LTX-Video ou AnimateDiff | Optimisés pour consumer hardware |
| **Temps réel (quand dispo)** | FashionChameleon | 23.8 FPS — surveiller la release |

---

*Guide compilé le 7 juin 2026*
*Tous les modèles listés comme ✅ ont été vérifiés comme réellement téléchargeables et utilisables à cette date.*
