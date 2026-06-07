# 🦎 FASHION CHAMELEON — Plan de Construction Complet
## Application d'Essayage Virtuel en Live par IA/AR

> **Date** : 7 juin 2026  
> **Recherche basée sur** : LoomVideo (PKU/Alibaba), Eevee (CVPR 2026), iTryOn (ICML 2026), VACE/Wan2.1, Zero10, et l'écosystème complet Virtual Try-On 2025-2026

---

## TABLE DES MATIÈRES

1. [Synthèse de la Recherche](#1-synthèse-de-la-recherche)
2. [Papiers Clés de l'Université de Pékin](#2-papiers-clés-de-luniversité-de-pékin)
3. [État de l'Art — Technologies VTON 2025-2026](#3-état-de-lart--technologies-vton-2025-2026)
4. [Solutions Commerciales Existantes](#4-solutions-commerciales-existantes)
5. [Architecture Technique de Fashion Chameleon](#5-architecture-technique-de-fashion-chameleon)
6. [Plan de Construction en 6 Phases](#6-plan-de-construction-en-6-phases)
7. [Stack Technique Recommandé](#7-stack-technique-recommandé)
8. [Datasets et Entraînement](#8-datasets-et-entraînement)
9. [Défis et Solutions](#9-défis-et-solutions)
10. [Budget et Timeline](#10-budget-et-timeline)
11. [Roadmap Produit](#11-roadmap-produit)

---

## 1. SYNTHÈSE DE LA RECHERCHE

### 1.1 Panorama du Domaine

Le Virtual Try-On (VTON) a connu une révolution en 2025-2026 avec la convergence de trois avancées majeures :

| Avancée | Impact | Papiers Clés |
|---------|--------|-------------|
| **Diffusion Transformers (DiT)** | Remplacement des GANs/UNets par des architectures plus performantes | LoomVideo, ITVTON, Voost |
| **Video Virtual Try-On (VVT)** | Passage de l'image statique à la vidéo avec cohérence temporelle | Eevee, iTryOn, KeyTailor, CatV2TON |
| **Interactive VVT** | Interactions réalistes humain-vêtement (zip, boutons, étirement) | iTryOn (ICML 2026) |

### 1.2 Découverte Critique : Le "Live" n'est pas encore du temps réel

**Constat important** : Aucune solution actuelle ne fait du try-on véritablement en temps réel sur la caméra (< 50ms/frame) avec la qualité des modèles de diffusion. Le paysage se divise en :

| Approche | Latence | Qualité | Exemples |
|----------|---------|---------|----------|
| **AR temps réel (3D mesh)** | ~15ms | Moyenne (3D overlay) | Zero10, Camweara |
| **AI Image (Diffusion)** | 1-22s / image | Excellente (photoréaliste) | IDM-VTON, CatVTON, FASHN.ai |
| **AI Vidéo (Diffusion)** | 30s-5min / clip | Excellente | Eevee, LoomVideo, iTryOn |
| **Hybride (notre cible)** | ~2-5s → live stream | Très bonne | **Fashion Chameleon** |

---

## 2. PAPIERS CLÉS DE L'UNIVERSITÉ DE PÉKIN

### 2.1 🌟 LoomVideo — Le Paper Principal (arXiv:2606.06042, Juin 2026)
**"Unifying Multimodal Inputs into Video Generation and Editing"**

**Auteurs** : Jianzong Wu, Hao Lian et al. (Peking University + Alibaba Group)

**Architecture révolutionnaire** :
- **Base** : Wan 2.2 TI2V 5B + Qwen3-VL-8B comme encodeur multimodal
- **Seulement 5B paramètres** (vs 13B+ pour les concurrents)
- **5.41× plus rapide** que les modèles comparables

**3 Innovations clés** :

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARCHITECTURE LOOMVIDEO                       │
│                                                                 │
│  ┌──────────────┐    Deepstack     ┌──────────────────┐        │
│  │  Qwen3-VL-8B │───Injection───▶│  Diffusion         │        │
│  │   (MLLM)     │   (layer-to-    │  Transformer (DiT) │        │
│  │              │    layer)       │  5B params          │        │
│  └──────────────┘                └──────────────────┘        │
│         │                               │                     │
│  ┌──────┴──────┐              ┌────────┴──────────┐          │
│  │ Text+Images │              │ Scale-and-Add      │          │
│  │ interleaved │              │ Conditioning       │          │
│  │ multimodal  │              │ (ZÉRO overhead)    │          │
│  └─────────────┘              └───────────────────┘          │
│                                                                 │
│  ┌──────────────────────────────────────────────────┐          │
│  │ Negative Temporal RoPE : indices temporels       │          │
│  │ négatifs pour les images de référence            │          │
│  │ (-τ, -2τ, ...) vs positifs pour le target        │          │
│  └──────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

**Pourquoi c'est crucial pour Fashion Chameleon** :
1. **FashionVideoBench** : benchmark dédié mode/e-commerce avec des tâches exactement alignées :
   - `text_video_to_video / product_edit` : Changer un vêtement dans une vidéo
   - `text_video_product_image_to_video` : Remplacer un article par un produit réel
   - `video_model_image_to_video` : Transférer des mouvements
   - `text_multi_image_to_video` : Combiner plusieurs références
2. **Code open-source** : https://github.com/MSALab-PKU/LoomVideo
3. **Poids disponibles** : https://huggingface.co/MSALab/LoomVideo

### 2.2 OSP-Next (arXiv:2605.28691, Mai 2026)
**"Efficient High-Quality Video Generation with Sparse Sequence Parallelism"**

**Auteurs** : Yunyang Ge et al. (PKU-YuanGroup)

**Pertinence** : Optimisation de l'inférence vidéo
- Attention sparse hybride (Skiparse-2D)
- Sparse Sequence Parallelism (SSP) : -75% communication
- Quantification HiF8 : entraînement 8-bit stable
- **1.64× speedup single-GPU**, **2.27× speedup multi-GPU**
- VBench score : 83.73% (surpasse Wan2.1 baseline)

**Application** : Accélérer l'inférence de Fashion Chameleon pour approcher le temps réel.

### 2.3 Autres papiers PKU pertinents

| Papier | arXiv | Pertinence |
|--------|-------|------------|
| AffordanceVLA | 2606.06155 | Vision-Language-Action pour interactions vêtement |
| Helios | 2025.03 | Génération vidéo longue en temps réel |
| OpenS2V-Nexus | 2025.05 | Subject-to-Video generation (person → video) |
| VideoTetris | 2025 | Composition text-to-video |
| ChronoMagic-Bench | 2024.04 | Benchmark évaluation vidéo |

---

## 3. ÉTAT DE L'ART — TECHNOLOGIES VTON 2025-2026

### 3.1 Image Virtual Try-On (le socle)

| Modèle | Architecture | Params | Latence | Forces |
|--------|-------------|--------|---------|--------|
| **IDM-VTON** | Dual UNet (SDXL) | 7B+ | 6.6s | Meilleure fidélité texture |
| **CatVTON** | Single UNet | 860M | 1.3s | Léger, bonne structure |
| **OOTDiffusion** | Dual UNet | ~2B | 1.5s | Outfitting Fusion efficace |
| **Re-CatVTON** | Single UNet amélioré | 860M | 1.3s | Qualité dual-UNet, coût single |
| **Leffa** | Dual UNet + Flow | ~2B | 2.7s | Flow fields attention loss |
| **SPM-Diff** | Dual UNet + Points sémantiques | ~2B | ~2s | Préservation détails (ICLR 2025) |
| **LPH-VTON** | Hybride CatVTON+IDM-VTON | ~2B | ~3s | Résout dilemme structure/texture |
| **ITVTON** | Single DiT | 1.07B | ~1.5s | DiT léger, state-of-the-art |
| **Voost** | DiT unifié (VTON+VTOFF) | ~2B | ~2s | Bidirectionnel, meilleure attention |

### 3.2 Video Virtual Try-On (la frontière)

| Modèle | Conférence | Base | Résolution | Innovation |
|--------|-----------|------|------------|------------|
| **Eevee** | CVPR 2026 | VACE + LoRA | 1088×816 | Close-up HD, dataset 9364 paires |
| **iTryOn** | ICML 2026 | Video DiT | Variable | Interactions main-vêtement |
| **LoomVideo** | arXiv 2026 | Wan 2.2 + Qwen3 | 480-720p | Editing e-commerce, 5.41× vitesse |
| **KeyTailor** | arXiv 2025 | DiT | 810×1080 | Keyframe injection, dataset ViT-HD |
| **CatV2TON** | CVPR 2025 WS | DiT | Variable | Temporal concatenation |
| **3DV-TON** | arXiv 2025 | Diffusion + 3D mesh | Variable | Guidage 3D explicite |
| **DreamVVT** | arXiv 2025 | Stage-wise DiT | Variable | Stage-wise framework |

### 3.3 Frameworks Unifiés (génération + édition vidéo)

| Framework | Éditeur | Tâches | Usage pour Fashion Chameleon |
|-----------|---------|--------|------------------------------|
| **VACE** (Wan2.1) | Alibaba | R2V, V2V, MV2V, composition libre | Backbone principal |
| **LoomVideo** | PKU + Alibaba | Génération + Édition unifiée | Spécialisation mode |
| **Wan 2.2** | Wan-AI | Génération vidéo de base | Modèle fondation |

---

## 4. SOLUTIONS COMMERCIALES EXISTANTES

### 4.1 AR Temps Réel (Approche 3D)

| Produit | Type | Tech | Limites |
|---------|------|------|---------|
| **Zero10** | AR Mirror + App iOS | 3D body tracking + cloth simulation + segmentation | Nécessite modèles 3D par vêtement |
| **Camweara** | App/SDK | 2D/3D overlay en live | Rendu moins réaliste |
| **Fibbl** | SaaS | Modèles 3D GLB | Pas de live camera |

**Zero10 en détail** (le leader AR) :
- SDK iOS natif (Swift Package Manager)
- Pipeline : `TryOnSession → prepare() → garment download → TryOnSheet`
- Technologies : 3D body tracking, segmentation multi-classe temps réel, cloth simulation
- Partenariats : Nike/JD Sports, Coach, Maisie Wilen
- AR Mirror : supercomputer + rendu 4K
- **Limitation** : chaque vêtement nécessite un modèle 3D créé manuellement (coûteux)

### 4.2 AI Image/Video (Approche Diffusion)

| Produit | Type | Fonctionnalité |
|---------|------|---------------|
| **FASHN.ai** | API | VTON image + video API, Consistent Models |
| **Camclo** | SaaS | Image VTON + vidéo via Kling/Veo3 |
| **SellerPic AI** | SaaS | Vêtements + accessoires + vidéo |
| **WearView** | SaaS | AI Virtual Models, pas de photoshoot |
| **Kling AI** | Plateforme | Plateforme créative générale + VTON |
| **Pic Copilot** | Alibaba | VTON rapide pour marketplaces |
| **Google Vertex AI** | API Enterprise | VTON image, pas vidéo |

### 4.3 Positionnement de Fashion Chameleon

```
                    Qualité Visuelle
                         ▲
                         │
           Diffusion     │    ★ Fashion Chameleon
           Video VTON ●──┼────●──────────────────
                         │         Near Real-Time
                         │         + Haute Qualité
           Diffusion     │
           Image VTON ●──┤
                         │
                         │
           AR 3D ●───────┤
           (Zero10)      │
                         └──────────────────────▶
                              Vitesse / Interactivité
```

---

## 5. ARCHITECTURE TECHNIQUE DE FASHION CHAMELEON

### 5.1 Vision Produit

**Fashion Chameleon** = Essayage virtuel "near-live" qui combine :
1. **AR instantanée** (première impression en <100ms via 3D overlay léger)
2. **Raffinement IA** (résultat photoréaliste en 2-5s via diffusion)
3. **Vidéo interactive** (clips de défilé avec interaction vêtement)

### 5.2 Architecture en 3 Couches

```
┌──────────────────────────────────────────────────────────────────────┐
│                    FASHION CHAMELEON ARCHITECTURE                     │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                    COUCHE 1 : CAPTURE                          │  │
│  │                                                                │  │
│  │  📱 Camera Feed ──▶ Body Pose Estimation (MediaPipe/HBPE)     │  │
│  │                  ──▶ Body Segmentation (SAM-2 / DensePose)     │  │
│  │                  ──▶ Garment Region Detection                  │  │
│  │                  ──▶ 3D Body Mesh Reconstruction               │  │
│  │                                                                │  │
│  │  ⏱️ Latence cible : < 30ms par frame                          │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│                              ▼                                       │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                    COUCHE 2 : PREVIEW INSTANTANÉE              │  │
│  │                                                                │  │
│  │  Mode AR Rapide :                                              │  │
│  │  ┌──────────────┐     ┌──────────────┐    ┌───────────────┐   │  │
│  │  │ Garment Image│──▶ │ Warping      │──▶│ Blend + Render │   │  │
│  │  │ (flat-lay)   │     │ (Thin-plate  │    │ (GPU overlay)  │   │  │
│  │  └──────────────┘     │  spline +    │    └───────────────┘   │  │
│  │                        │  UV mapping) │                        │  │
│  │                        └──────────────┘                        │  │
│  │  ⏱️ Latence : < 50ms (aperçu approximatif)                   │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│                              ▼                                       │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                    COUCHE 3 : RAFFINEMENT IA                   │  │
│  │                                                                │  │
│  │  Pipeline Diffusion (Server-side) :                            │  │
│  │                                                                │  │
│  │  ┌─────────────────────────────────────────────────────────┐   │  │
│  │  │  Option A : Image VTON (2-5s)                           │   │  │
│  │  │  Re-CatVTON / ITVTON → Image photoréaliste             │   │  │
│  │  ├─────────────────────────────────────────────────────────┤   │  │
│  │  │  Option B : Video VTON (10-30s)                         │   │  │
│  │  │  Eevee/LoomVideo → Clip vidéo HD                        │   │  │
│  │  ├─────────────────────────────────────────────────────────┤   │  │
│  │  │  Option C : Interactive VTON (20-60s)                   │   │  │
│  │  │  iTryOn → Vidéo avec interactions main-vêtement         │   │  │
│  │  └─────────────────────────────────────────────────────────┘   │  │
│  │                                                                │  │
│  │  Optimisations :                                               │  │
│  │  • OSP-Next Sparse Attention (1.64-2.27× speedup)            │  │
│  │  • LCM-LoRA (30 steps → 5 steps, 22s → 5s)                   │  │
│  │  • TensorRT / ONNX quantization                               │  │
│  │  • Streaming chunked generation (VACE autoregressive)         │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                    INFRASTRUCTURE                              │  │
│  │                                                                │  │
│  │  📦 Catalogue Vêtements :                                     │  │
│  │  • Images produit (flat-lay, mannequin, portées)              │  │
│  │  • Descriptions textuelles (auto-générées par Qwen-VL)        │  │
│  │  • Close-up images (détails texture)                           │  │
│  │  • Masques & annotations automatiques                         │  │
│  │                                                                │  │
│  │  🖥️ Compute Backend :                                         │  │
│  │  • GPU Cloud (NVIDIA H100/H200, ou Ascend 950PR)             │  │
│  │  • Queue de jobs par utilisateur                               │  │
│  │  • Cache de résultats pré-calculés                            │  │
│  │  • CDN pour livraison vidéo                                   │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

### 5.3 Flux Utilisateur

```
Utilisateur ouvre l'app
       │
       ▼
[1] Sélectionne un vêtement dans le catalogue
       │
       ▼
[2] Active la caméra → Body detection instantanée
       │
       ▼
[3] Aperçu AR immédiat (~50ms) ← Overlay 2D/3D basique
       │
       ├─── L'utilisateur est satisfait → [4a] "Affiner"
       │                                        │
       │                                        ▼
       │                              Envoi au serveur GPU
       │                              ITVTON/Re-CatVTON (2-5s)
       │                                        │
       │                                        ▼
       │                              Image photoréaliste retournée
       │
       ├─── L'utilisateur veut une vidéo → [4b] "Voir en mouvement"
       │                                        │
       │                                        ▼
       │                              Capture frame + sélection pose
       │                              LoomVideo/Eevee (15-30s)
       │                                        │
       │                                        ▼
       │                              Clip vidéo HD retourné
       │
       └─── L'utilisateur veut interagir → [4c] "Essayer vraiment"
                                                 │
                                                 ▼
                                       iTryOn (30-60s)
                                       Vidéo avec zip/boutons/étirement
                                                 │
                                                 ▼
                                       Vidéo interactive retournée
```

---

## 6. PLAN DE CONSTRUCTION EN 6 PHASES

### Phase 1 : Fondations & Recherche (Semaines 1-4)
**Objectif** : Valider les modèles, installer l'environnement

| Tâche | Détail | Livrable |
|-------|--------|----------|
| Setup GPU cloud | Provisionner 2-4× H100 80GB | Infra ready |
| Cloner & tester LoomVideo | `git clone MSALab-PKU/LoomVideo`, download checkpoints | Inférence fonctionnelle |
| Cloner & tester VACE | `git clone ali-vilab/VACE`, installer Wan2.1 | Pipeline V2V opérationnel |
| Tester Eevee baseline | Download dataset Eevee (JianhaoZeng/Eevee sur HF) | Benchmark baseline |
| Tester modèles image VTON | IDM-VTON, CatVTON, Re-CatVTON, ITVTON | Comparatif qualité/vitesse |
| Évaluer OSP-Next | Tester speedup sparse attention | Mesures de latence |
| Prototype body detection | MediaPipe + DensePose sur webcam | Demo temps réel |

**Code de démarrage LoomVideo** :
```bash
# Installation
git clone https://github.com/MSALab-PKU/LoomVideo.git
cd LoomVideo

# Download model
huggingface-cli download MSALab/LoomVideo --local-dir checkpoints/LoomVideo

# Test Fashion Try-On : remplacement de vêtement
NUM_GPUS=1 accelerate launch --num_processes=${NUM_GPUS} \
    scripts/inference/generate.py \
    --config_path configs/inference/generation.yaml \
    --ckpt_path checkpoints/LoomVideo \
    --task mi2v \
    --prompt "The woman wearing a red dress (@Image 2), walking forward on the runway (@Image 1)" \
    --ref_image_paths assets/demo/person.jpg assets/demo/dress.jpg \
    --num_frames 97 \
    --num_inference_steps 50 \
    --seed 0 \
    --output_path outputs/fashion_tryon_demo.mp4
```

**Code de démarrage VACE** :
```bash
# Installation
git clone https://github.com/ali-vilab/VACE.git && cd VACE
pip install -r requirements.txt
pip install wan@git+https://github.com/Wan-Video/Wan2.1

# Inférence Try-On via masking + reference
python vace/vace_wan_inference.py \
    --ckpt_dir models/VACE-Wan2.1-1.3B-Preview \
    --src_video examples/person_walking.mp4 \
    --src_mask examples/garment_region_mask.mp4 \
    --src_ref_images examples/target_garment.png \
    --prompt "The person is now wearing the red floral dress from the reference image"
```

### Phase 2 : Pipeline Image VTON (Semaines 5-8)
**Objectif** : API fonctionnelle image → try-on photoréaliste

| Tâche | Détail | Livrable |
|-------|--------|----------|
| Fine-tune ITVTON / Re-CatVTON | Sur dataset mode personnalisé | Modèle spécialisé |
| Pipeline de preprocessing | SAM-2 segmentation + DensePose + masking auto | Module automatique |
| API REST backend | FastAPI + GPU worker (Celery/Redis) | Endpoint `/api/tryon/image` |
| Optimisation inférence | LCM-LoRA (5 steps), TensorRT | Latence < 3s |
| Catalogue vêtements | Ingestion, caption auto (Qwen-VL), masking | Base de données vêtements |

**Architecture API** :
```python
# POST /api/tryon/image
{
    "person_image": "base64...",      # Photo utilisateur
    "garment_id": "SKU-12345",        # ID du vêtement catalogue
    "category": "upper_body",          # upper_body / lower_body / dress
    "options": {
        "quality": "high",             # draft (2s) / high (5s)
        "preserve_background": true
    }
}

# Response
{
    "result_image": "url...",
    "processing_time_ms": 2800,
    "confidence_score": 0.94
}
```

### Phase 3 : Module AR Preview (Semaines 9-12)
**Objectif** : Aperçu instantané sur caméra live

| Tâche | Détail | Livrable |
|-------|--------|----------|
| Body pose estimation | MediaPipe Holistic ou custom HBPE | Tracking 30fps |
| Body segmentation temps réel | Lightweight SAM ou custom model | Masque vêtement live |
| Garment warping engine | Thin-plate spline + UV mapping | Overlay réaliste |
| Rendering pipeline | WebGL/Metal/Vulkan blending | Rendu < 16ms |
| App mobile prototype | React Native + native modules | App iOS/Android |

**Stack AR** :
```
┌─────────────────────────────────────────┐
│           Mobile App (Client)            │
│                                          │
│  Camera → MediaPipe → Body Landmarks    │
│                    → Segmentation Mask   │
│                    → Depth Estimation    │
│                                          │
│  Garment Image → TPS Warping            │
│               → UV Mapping               │
│               → Lighting Adaptation      │
│               → Alpha Blending           │
│                    → Display on screen   │
│                                          │
│  [Bouton "Affiner"] → API Cloud VTON    │
└─────────────────────────────────────────┘
```

### Phase 4 : Pipeline Video VTON (Semaines 13-18)
**Objectif** : Génération de clips vidéo try-on

| Tâche | Détail | Livrable |
|-------|--------|----------|
| Intégrer LoomVideo | Pipeline fashion-specific avec FashionVideoBench | Endpoint `/api/tryon/video` |
| Fine-tune sur Eevee dataset | 9364 paires, full-shot + close-up | Modèle vidéo HD |
| VACE streaming adaptation | Chunked autoregressive pour streaming | Génération progressive |
| OSP-Next optimisation | Sparse attention + SSP pour speedup | 1.6-2.3× accélération |
| Métriques qualité | VGID (garment consistency), VBench, FID | Dashboard qualité |

**Tâches LoomVideo pour Fashion** :
```yaml
fashion_tasks:
  - product_edit:        "Remove/change/add garment elements"
  - model_replacement:   "Replace person keeping clothes or vice-versa"
  - garment_swap:        "Replace garment from product image reference"
  - style_transfer:      "Change style while keeping silhouette"
  - multi_reference:     "Combine outfit from multiple product images"
```

### Phase 5 : Interactive Try-On & Polish (Semaines 19-24)
**Objectif** : Interactions réalistes + finitions produit

| Tâche | Détail | Livrable |
|-------|--------|----------|
| Intégrer iTryOn concepts | 3D hand prior + A-RoPE | Interactions zip/boutons |
| Fine-tune sur VVT-Interact | Dataset interactions humain-vêtement | Modèle interactif |
| UX/UI app complète | Design system, animations, transitions | App production-ready |
| Social features | Partage vidéo, comparaison looks | Module social |
| Analytics | Tracking conversion, temps d'engagement | Dashboard analytics |
| E-commerce integration | Shopify/WooCommerce plugins + API | Intégration marchands |

### Phase 6 : Scaling & Launch (Semaines 25-30)
**Objectif** : Mise en production, scaling

| Tâche | Détail | Livrable |
|-------|--------|----------|
| Infrastructure auto-scaling | Kubernetes + GPU orchestration | Scaling automatique |
| CDN & caching | Pré-calcul résultats populaires | Latence réduite |
| Modèle de pricing | Freemium + API B2B | Business model |
| Beta test | 500-1000 utilisateurs pilote | Feedback & itération |
| Launch marketing | Contenu social, démos, partenariats | Lancement public |
| Monitoring | Alerting, performance, qualité | Ops dashboard |

---

## 7. STACK TECHNIQUE RECOMMANDÉ

### 7.1 Backend AI / ML

| Composant | Technologie | Justification |
|-----------|-------------|---------------|
| **Modèle fondation vidéo** | Wan 2.2 / VACE | Open-source, meilleur rapport qualité/taille |
| **Spécialisation mode** | LoomVideo (5B) | State-of-the-art fashion, open-source |
| **Image VTON** | ITVTON (1B DiT) ou Re-CatVTON | Léger, rapide, excellente qualité |
| **Video VTON** | Eevee (VACE + LoRA) | CVPR 2026, dataset HD inclus |
| **Interactive VTON** | Concepts iTryOn | ICML 2026, interactions réalistes |
| **Accélération** | OSP-Next + LCM-LoRA | Réduction 50-80% du temps d'inférence |
| **Encodeur multimodal** | Qwen3-VL-8B | Compréhension texte+image unifiée |
| **Segmentation** | SAM-2 / Grounded SAM-2 | Masques précis, state-of-the-art |
| **Pose estimation** | DensePose (Detectron2) | UV mapping corps complet |
| **Caption auto** | Qwen-VL-Max | Description détaillée des vêtements |

### 7.2 Backend Infrastructure

| Composant | Technologie |
|-----------|-------------|
| **API** | FastAPI (Python) |
| **Queue de tâches** | Celery + Redis |
| **GPU Inference** | NVIDIA Triton Inference Server |
| **Conteneurisation** | Docker + Kubernetes |
| **GPU Cloud** | RunPod / Lambda Labs / AWS (H100) |
| **Stockage** | S3 + CloudFront CDN |
| **Base de données** | PostgreSQL + Redis cache |
| **Auth** | Clerk / Auth0 |

### 7.3 Frontend / Mobile

| Composant | Technologie |
|-----------|-------------|
| **App mobile** | React Native + native modules (Swift/Kotlin) |
| **AR Engine** | ARKit (iOS) / ARCore (Android) |
| **Body tracking** | MediaPipe Holistic / Vision framework |
| **Rendering** | Metal (iOS) / Vulkan (Android) |
| **Web app** | Next.js + WebGL |
| **Garment preview** | Three.js / Babylon.js |

### 7.4 Data Pipeline

| Composant | Technologie |
|-----------|-------------|
| **Preprocessing** | VACE annotators (DensePose, OpenPose, SAM-2) |
| **Caption génération** | Qwen-VL-Max batch API |
| **Masking pipeline** | Grounded SAM-2 + AniLines (lineart) |
| **Dataset format** | Structure Eevee (voir ci-dessous) |

**Structure dataset recommandée (format Eevee)** :
```
catalog/
├── upper_body/
│   ├── SKU-001/
│   │   ├── garment.png              # Image vêtement in-shop
│   │   ├── garment_detail.png       # Close-up détails
│   │   ├── garment_caption.txt      # Description auto (Qwen-VL)
│   │   ├── garment_line.png         # Lineart (AniLines)
│   │   ├── garment_mask.png         # Masque binaire (SAM-2)
│   │   ├── person.png               # Personne portant le vêtement
│   │   ├── person_mask.png          # Masque zone vêtement
│   │   ├── person_agnostic.png      # Personne sans vêtement visible
│   │   ├── video_0.mp4              # Vidéo full-shot
│   │   ├── video_0_densepose.mp4    # DensePose UV
│   │   ├── video_0_mask.mp4         # Masque vidéo
│   │   ├── video_1.mp4              # Vidéo close-up
│   │   └── video_1_densepose.mp4    # DensePose close-up
│   ├── SKU-002/
│   └── ...
├── lower_body/
└── dresses/
```

---

## 8. DATASETS ET ENTRAÎNEMENT

### 8.1 Datasets Publics Disponibles

| Dataset | Taille | Résolution | Type | Source |
|---------|--------|------------|------|--------|
| **Eevee** | 9,364 paires | 2400×1800 (img), 1088×816 (vid) | Video VTON | CVPR 2026, HuggingFace |
| **VITON-HD** | 13,679 paires | 1024×768 | Image VTON | Standard benchmark |
| **DressCode** | 53,792 paires | 1024×768 | Image VTON (3 catégories) | Multi-catégorie |
| **ViT-HD** | 15,070 vidéos | 810×1080 | Video VTON | KeyTailor |
| **VVT-Interact** | ~5,000+ | Variable | Interactive VVT | iTryOn / ICML 2026 |
| **FashionVideoBench** | 2,536+ | Variable | Benchmark fashion | LoomVideo |

### 8.2 Stratégie d'Entraînement

```
Phase 1 : Pré-entraînement
├── Base : Wan 2.2 TI2V 5B (déjà entraîné)
└── ITVTON DiT 1B (déjà entraîné sur VITON-HD)

Phase 2 : Fine-tuning Image VTON
├── Dataset : VITON-HD + DressCode + données propres
├── Méthode : LoRA fine-tuning sur Re-CatVTON/ITVTON
├── GPU : 4× H100 80GB
├── Durée : 2-3 jours
└── Objectif : SSIM > 0.90, LPIPS < 0.05

Phase 3 : Fine-tuning Video VTON
├── Dataset : Eevee (9,364 paires) + ViT-HD (15,070 vidéos)
├── Méthode : LoRA sur VACE backbone
├── GPU : 8× H100 80GB
├── Durée : 5-7 jours
└── Objectif : VGID compétitif, cohérence temporelle

Phase 4 : Spécialisation Fashion
├── Dataset : Données propres + FashionVideoBench
├── Méthode : RL post-training (Mix-GRPO, comme OSP-Next)
├── GPU : 8× H100 80GB
├── Durée : 3-5 jours
└── Objectif : Qualité e-commerce production
```

---

## 9. DÉFIS ET SOLUTIONS

### 9.1 Défi Critique : Latence

| Problème | Solution | Impact |
|----------|----------|--------|
| Diffusion = lent (22s+) | LCM-LoRA : 30→5 steps | 22s → 5s |
| Attention quadratique | OSP-Next sparse attention | 1.6-2.3× speedup |
| Sequence length | LoomVideo Scale-and-Add (pas de concat) | 5.41× speedup |
| Modèle trop gros | ITVTON (1B) vs IDM-VTON (7B) | 5× plus petit |
| Quantization | HiF8 (OSP-Next) + TensorRT | 1.7-2.3× speedup |
| Multi-GPU | SSP (Sparse Sequence Parallelism) | Scaling linéaire |

**Latence combinée estimée** :
```
Image VTON :  22s (baseline IDM-VTON)
            → 5s  (LCM-LoRA, 5 steps)
            → 3s  (+ ITVTON léger)
            → 1.5s (+ TensorRT FP16)
            → ~1s  (+ batch optimization)

Video VTON :  5min (baseline LoomVideo 50 steps)
            → 1min (+ Scale-and-Add = 5.41× speedup)
            → 30s  (+ OSP-Next sparse = 1.6×)
            → 15s  (+ quantization + fewer steps)
```

### 9.2 Défi : Qualité des Détails

| Problème | Solution |
|----------|----------|
| Perte texture haute fréquence | Close-up images (dataset Eevee) |
| Logo/texte flous | SPM-Diff semantic point matching |
| Dilemme structure vs texture | LPH-VTON (handover latent process) |
| Fidélité couleur | Descriptions textuelles détaillées (Qwen-VL) |

### 9.3 Défi : Cohérence Temporelle (Vidéo)

| Problème | Solution |
|----------|----------|
| Flickering inter-frames | Temporal attention layers + VACE |
| Dérive couleur | KeyTailor keyframe injection |
| Mains/visage déformés | iTryOn 3D hand prior |
| Fond instable | Collaborative background optimization (KeyTailor) |

### 9.4 Défi : Variété de Vêtements

| Problème | Solution |
|----------|----------|
| Une seule photo produit | Zero10's single-image pipeline |
| Accessoires (sacs, chapeaux) | LoomVideo multi-reference (@Image N) |
| Multi-couche (veste + t-shirt) | VACE masked composition |
| Tailles / morphologies | DensePose UV mapping adaptatif |

---

## 10. BUDGET ET TIMELINE

### 10.1 Timeline

```
Mois 1-2   ████████ Phase 1 : Fondations & Recherche
Mois 2-3   ████████ Phase 2 : Pipeline Image VTON
Mois 3-4   ████████ Phase 3 : Module AR Preview
Mois 4-6   ████████████ Phase 4 : Pipeline Video VTON
Mois 6-7   ████████ Phase 5 : Interactive & Polish
Mois 7-8   ████████ Phase 6 : Scaling & Launch
```

**Total : ~8 mois** pour un MVP complet

### 10.2 Équipe Minimale

| Rôle | Nombre | Compétences |
|------|--------|-------------|
| ML Engineer (Video Gen) | 2 | PyTorch, DiT, diffusion models |
| ML Engineer (VTON) | 1 | VTON literature, training |
| AR/3D Engineer | 1 | ARKit/ARCore, computer vision |
| Backend Engineer | 1 | FastAPI, GPU infra, K8s |
| Mobile Developer | 1 | React Native + native |
| UI/UX Designer | 1 | Fashion-oriented design |
| **Total** | **7 personnes** | |

### 10.3 Budget Infrastructure (mensuel)

| Poste | Coût Estimé |
|-------|-------------|
| GPU Training (8× H100, 3 mois) | $15,000-25,000/mois |
| GPU Inference (2-4× H100 on-demand) | $5,000-15,000/mois |
| Cloud (API, storage, CDN) | $500-2,000/mois |
| Outils (HuggingFace Pro, monitoring) | $200-500/mois |
| **Total mensuel (production)** | **$6,000-18,000/mois** |

---

## 11. ROADMAP PRODUIT

### MVP (Mois 1-4) — "Fashion Chameleon Lite"
- ✅ Image VTON via API (< 3s, photoréaliste)
- ✅ AR Preview basique (overlay temps réel)
- ✅ Catalogue 100-500 vêtements
- ✅ App mobile iOS

### V1.0 (Mois 5-6) — "Fashion Chameleon"
- ✅ Video VTON (clips 5-10s, HD)
- ✅ AR Preview amélioré (meilleur warping)
- ✅ App Android
- ✅ API B2B pour marchands
- ✅ Intégration Shopify

### V1.5 (Mois 7-8) — "Fashion Chameleon Pro"
- ✅ Interactive VTON (interactions main-vêtement)
- ✅ Multi-garment composition
- ✅ Close-up generation automatique
- ✅ Social sharing features
- ✅ Analytics dashboard marchands

### V2.0 (Mois 9+) — "Fashion Chameleon Live"
- 🔮 Near-real-time diffusion refinement (StreamDiffusion V2)
- 🔮 Full outfit composition temps réel
- 🔮 AR Mirror pour retail (borne physique)
- 🔮 Integration metaverse / avatar
- 🔮 Haptic feedback (2027+)

---

## ANNEXES

### A. Liens Essentiels

| Ressource | URL |
|-----------|-----|
| LoomVideo Code | https://github.com/MSALab-PKU/LoomVideo |
| LoomVideo Weights | https://huggingface.co/MSALab/LoomVideo |
| LoomVideo Paper | https://arxiv.org/abs/2606.06042 |
| Eevee Code | https://github.com/AMAP-ML/Eevee |
| Eevee Dataset | https://huggingface.co/JianhaoZeng/Eevee |
| Eevee Paper | https://arxiv.org/abs/2511.18957 |
| iTryOn Page | https://zhengjun-ai.github.io/itryon-page/ |
| VACE Code | https://github.com/ali-vilab/VACE |
| OSP-Next Code | https://github.com/PKU-YuanGroup/OSP-Next |
| Zero10 SDK | https://github.com/zero10-app/zero10-sdk |
| Awesome VTON | https://github.com/minar09/awesome-virtual-try-on |
| Awesome Try-On Models | https://github.com/Zheng-Chong/Awesome-Try-On-Models |

### B. Citations Clés

```bibtex
@article{wu2026loomvideo,
  title={LoomVideo: Unifying Multimodal Inputs into Video Generation and Editing},
  author={Wu, Jianzong and Lian, Hao and Yang, Jiongfan and others},
  journal={arXiv preprint arXiv:2606.06042},
  year={2026}
}

@article{zeng2025eevee,
  title={Eevee: Towards Close-up High-resolution Video-based Virtual Try-on},
  author={Zeng, Jianhao and others},
  journal={arXiv preprint arXiv:2511.18957},
  year={2025}
}

@inproceedings{zheng2026itryon,
  title={iTryOn: Mastering Interactive Video Virtual Try-On with Spatial-Semantic Guidance},
  author={Zheng, Jun and others},
  booktitle={ICML},
  year={2026}
}

@misc{ge2026ospnext,
  title={OSP-Next: Efficient High-Quality Video Generation},
  author={Ge, Yunyang and others},
  journal={arXiv preprint arXiv:2605.28691},
  year={2026}
}
```

### C. Métriques d'Évaluation

| Métrique | Usage | Cible |
|----------|-------|-------|
| **SSIM** | Similarité structurelle | > 0.90 |
| **LPIPS** | Similarité perceptuelle | < 0.05 |
| **FID** | Qualité distribution images | < 10 |
| **CLIP-I** | Cohérence sémantique | > 0.85 |
| **VGID** | Consistance vêtement vidéo (Eevee) | State-of-the-art |
| **VBench** | Qualité vidéo globale | > 83% |

---

*Document généré le 7 juin 2026 — Fashion Chameleon Research & Build Plan*
*Basé sur une analyse approfondie de 30+ papiers de recherche et 15+ solutions commerciales*
