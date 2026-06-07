# 🇨🇳 RECHERCHE COMPLÉMENTAIRE — Universités & Labs Chinois
## Virtual Try-On, Fashion Video Generation & Technologies Connexes

> **Date** : 7 juin 2026  
> **Complément au document** : Fashion_Chameleon_Plan.md

---

## ⚠️ DÉCOUVERTE CRITIQUE : "FashionChameleon" EXISTE DÉJÀ !

### Le papier FashionChameleon d'Alibaba (arXiv:2605.15824, Mai 2026)

**"FashionChameleon: Towards Real-Time and Interactive Human-Garment Video Customization"**

Un papier portant **exactement le même nom** que ton projet a été publié par Alibaba le 15 mai 2026 !

| Détail | Valeur |
|--------|--------|
| **Auteurs** | Quanjian Song, Yefeng Shen, Mengting Chen, Hao Sun, Jinsong Lan, Xiaoyong Zhu, Bo Zheng, Liujuan Cao |
| **Affiliations** | Alibaba Group (Taobao & Tmall) |
| **Date** | 15 mai 2026 |
| **arXiv** | 2605.15824 |
| **HuggingFace** | https://huggingface.co/papers/2605.15824 |
| **Performance** | **23.8 FPS sur un seul GPU** — **30 à 180× plus rapide** que les baselines |

#### Architecture et Innovations Clés :

```
┌─────────────────────────────────────────────────────────────────────┐
│              FASHIONCHAMELEON (Alibaba) — Architecture               │
│                                                                     │
│  1️⃣ Teacher Model with In-Context Learning                         │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ • Entraîné avec "mismatch learning" :                         │ │
│  │   Référence vidéo (pose) ≠ Vêtement cible                    │ │
│  │ • Force le découplage pose dynamique / apparence vêtement     │ │
│  │ • Utilise SEULEMENT des données single-garment video          │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│                              ▼                                      │
│  2️⃣ Streaming Distillation with In-Context Learning                │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ • Architecture Teacher-Student pour temps réel                │ │
│  │ • In-context teacher forcing + gradient-reweighted DMD        │ │
│  │ • Le Student Model atteint 23.8 FPS                           │ │
│  │ • Extrapolation cohérente pour vidéos longues                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│                              ▼                                      │
│  3️⃣ Training-Free KV Cache Rescheduling                            │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ • Garment KV Refresh : injecte les features du nouveau        │ │
│  │   vêtement dans le cache                                      │ │
│  │ • Historical KV Withdraw : retire l'info de l'ancien          │ │
│  │   vêtement du cache                                           │ │
│  │ • Reference KV Disentangle : sépare pose / apparence          │ │
│  │ • Résultat : changement de vêtement INSTANTANÉ en streaming   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  🎯 Résultat : Switch interactif de vêtements pendant la           │
│     génération vidéo, en temps réel (23.8 FPS)                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### ⚡ Implications pour ton projet :
1. **Le nom "Fashion Chameleon" est déjà pris** → Il faudra renommer ton app
2. **C'est exactement la technologie que tu veux** → Tu peux utiliser/adapter ce papier
3. **Alibaba l'a open-sourcé** (GitHub disponible, 234 likes sur HF en quelques jours)
4. **23.8 FPS = quasi temps réel** → C'est la breakthrough que tu cherchais

---

## 1. UNIVERSITÉS CHINOISES — CONTRIBUTIONS MAJEURES PAR INSTITUTION

### 1.1 🏛️ Université de Tianjin (天津大学) — Prof. Dan Song

**Spécialisation** : Virtual try-on in-the-wild, mask-free methods

| Papier | Conférence | Innovation |
|--------|-----------|------------|
| **BooW-VTON** | **CVPR 2025** | Premier paradigme mask-free pour VTON in-the-wild, pseudo-data augmentation |
| **Better Fit** | IEEE TCSVT 2024 | Adaptation aux variations de types de vêtements |
| **Landmark-Guided Shape Matching** | AAAI 2021 | Correspondance forme par landmarks pour VTON réaliste |

**BooW-VTON** (Boosting In-the-Wild Virtual Try-On) — Détails :
- Entraîné **sans masque** : plus besoin de parser/segmenter les vêtements
- Utilise des pseudo-données et augmentation in-the-wild
- Try-on localization loss pour focaliser l'attention sur la zone d'essayage
- **State-of-the-art** sur scénarios complexes (occlusions, poses variées)
- Auteurs : Xuanpu Zhang, Dan Song, Pengxin Zhan et al.

### 1.2 🌊 Ocean University of China (中国海洋大学) — Prof. Yong Du

**Spécialisation** : Training-free universal VTON, multi-person try-on

| Papier | Conférence | Innovation |
|--------|-----------|------------|
| **OmniVTON** | **ICCV 2025** | Premier framework training-free universal (in-shop + in-the-wild) |
| **OmniVTON++** | arXiv 2026 | Extension avec Principal Pose Guidance + support FLUX backbone |

**OmniVTON** — Détails révolutionnaires :
- **Training-free** : fonctionne sans aucun entraînement spécifique !
- Unifie les scénarios in-shop et in-the-wild
- 3 modules clés :
  - **Structured Garment Morphing (SGM)** : alignement vêtement-corps par squelette
  - **Continuous Boundary Stitching (CBS)** : transitions seamless aux frontières
  - **Spectral Pose Injection (SPI)** : alignement pose sans contamination texture
- **Premier framework multi-person VTON** : essayage sur plusieurs personnes simultanément
- Collaborateurs : Singapore Management University, Harbin Institute of Technology (Shenzhen)
- Code : https://github.com/Jerome-Young/OmniVTON

### 1.3 🎓 Hong Kong Polytechnic University (香港理工大学)

**Spécialisation** : Datasets multi-vêtements, outfit-level VTON

| Papier | Conférence | Innovation |
|--------|-----------|------------|
| **Garments2Look** | **CVPR 2026** | Premier dataset outfit-level (80K paires, 40 catégories, 300+ sous-catégories) |

**Garments2Look** — Dataset révolutionnaire :
- **80,000 paires** many-garments-to-one-look
- 3-12 vêtements de référence par outfit (moyenne 4.48)
- **40 catégories principales**, **300+ sous-catégories**
- Inclut vêtements, chaussures, sacs, bijoux, accessoires
- Annotations textuelles : descriptions items, layering order, styling techniques
- Résolution ~1024×1024
- Auteurs : Junyao Hu, Zhongwei Cheng, Waikeung Wong, Xingxing Zou

### 1.4 🏫 Tsinghua University (清华大学) + ShengShu Technology

**Spécialisation** : Accélération inférence vidéo, génération temps réel

| Papier | Conférence | Innovation |
|--------|-----------|------------|
| **TurboDiffusion** | Open-source, 2025 | **100-200× speedup** génération vidéo ! |
| **SageAttention** | Intégré dans TensorRT | Attention efficace adoptée par Tencent, ByteDance, Google, etc. |

**TurboDiffusion** — Breakthrough vitesse :
- Vidéo 5s SD : de 3 min → **1.9 secondes** (100× speedup)
- Vidéo 5s HD : de 80 min → **24 secondes** (200× speedup)
- Sur un seul GPU RTX 5090
- Utilise sparse linear attention + distillation de modèle
- **Open-source** sur GitHub
- Adopté par : Tencent Hunyuan, ByteDance Doubao, Alibaba, Google Veo3, SenseTime, vLLM
- Surnommé "le DeepSeek Moment de la génération vidéo"

### 1.5 🏭 Alibaba Group (阿里巴巴) — DAMO Academy / Taobao & Tmall

**Spécialisation** : Infrastructure mode/e-commerce, frameworks unifiés

| Projet | Type | Innovation |
|--------|------|-----------|
| **FashionChameleon** | arXiv 2026 | Try-on vidéo temps réel 23.8 FPS, KV Cache Rescheduling |
| **VACE** (Wan2.1) | ICCV 2025 | Framework unifié R2V + V2V + MV2V |
| **LoomVideo** (avec PKU) | arXiv 2026 | Génération/édition vidéo unifiée 5B, spécialisé fashion |
| **Eevee** (AMAP-ML) | CVPR 2026 | Dataset HD video try-on, close-up |
| **Lumos** | ICLR 2026 | Modèle vidéo unifié autorégressif |
| **Lumos-Custom** | NeurIPS 2025 | Personnalisation vidéo |
| **Pic Copilot** | Produit | VTON pour marketplaces Alibaba |
| **Aliwood** | Produit | Génération vidéo e-commerce automatique |

### 1.6 🔬 Harbin Institute of Technology — Shenzhen (哈尔滨工业大学深圳)

| Papier | Conférence | Innovation |
|--------|-----------|------------|
| Collaborateur OmniVTON/++ | ICCV 2025 | Universal training-free VTON |
| Nanjing University of S&T collaboration | - | Pose guidance |

### 1.7 🧪 Westlake University (西湖大学) — Endless AI Lab / Prof. Yuliang Xiu

**Spécialisation** : Reconstruction 3D d'humains habillés, avatars

| Papier | Conférence | Innovation |
|--------|-----------|------------|
| **ICON** | CVPR 2022 | Humains habillés 3D depuis images normales |
| **ECON** | CVPR 2023 (Highlight) | Optimisation clothed humans via normals |
| **ChatGarment** | CVPR 2025 | Estimation/génération/édition vêtements via LLM |
| **ETCH** | ICCV 2025 (Highlight) | Body fitting to clothed humans via equivariant tightness |
| **Human3R** | ICLR 2026 | Reconstruction 3D multi-personnes |

**ChatGarment** — Pertinent pour Fashion Chameleon :
- Utilise un LLM pour estimer, générer et éditer des vêtements 3D
- Interface conversationnelle : "change la longueur des manches", "ajoute un col"
- Collaborateurs : Shanghai Jiao Tong University, Max Planck Institute

### 1.8 🏢 Shanghai Jiao Tong University (上海交通大学)

| Labo | Spécialisation | Papiers pertinents |
|------|---------------|-------------------|
| Computer Vision Lab | Reconstruction 3D humains, body estimation | AlphaPose (TPAMI), reconstruction vêtements 3D |
| DART Lab | Modèles de mains articulées | Hand-garment interaction |

### 1.9 🏢 Tencent (腾讯)

| Projet | Innovation |
|--------|-----------|
| **Hunyuan Video** | Génération vidéo avec support pose guidance, templates culturels |
| Intégration TurboDiffusion | Adoption de SageAttention pour accélération |

### 1.10 🏢 ByteDance (字节跳动)

| Projet | Innovation |
|--------|-----------|
| **Doubao** (Génération vidéo) | Génération texte/vidéo, scripts publicitaires |
| **Helios** (avec PKU) | Génération vidéo longue temps réel |
| Intégration TurboDiffusion | Adoption pour accélération |

### 1.11 📊 Autres contributions chinoises notables

| Université/Lab | Papier | Conférence | Innovation |
|----------------|--------|-----------|-----------|
| **Sun Yat-sen University** (中山大学) + Alibaba | iTryOn | **ICML 2026** | Try-on vidéo interactif avec 3D hand prior |
| **Nanjing University of S&T** (南京理工大学) | Collaborateur OmniVTON++ | - | Pose guidance |
| **University of Melbourne** + Sydney | CatV2TON | CVPR 2025 WS | DiT pour Video VTON avec temporal concatenation |
| **Zhejiang University** (浙江大学) + Alibaba | Aliwood | Produit | Génération vidéo e-commerce automatique |
| **USTC** (中国科学技术大学) + PKU + CUHK | ShareGPT4Video | 2024 | Video understanding et génération améliorées |
| **ShanghaiTech University** | MV-Fashion | arXiv 2026 | Dataset multi-vue vidéo mode avec sizing estimation |
| Shanghai AI Laboratory | InternLM, OpenGVLab | - | Modèles vision ouverts, infrastructure AI |
| **SenseTime** (商汤科技) | SenseNova 5.0 | 2024 | Multimodal, synthesis GAN/diffusion |
| **ShengShu Technology** (生数科技) | Vidu | 2024 | Text-to-video, équivalent chinois de Sora |

---

## 2. SOLUTIONS & FRAMEWORKS CHINOIS — CLASSEMENT PAR PERTINENCE

### 2.1 🥇 Tier 1 — Directement applicables à ton projet

| Solution | Auteur | Pourquoi l'utiliser |
|----------|--------|-------------------|
| **FashionChameleon** | Alibaba | **EXACTEMENT ton cas d'usage** : temps réel (23.8 FPS), switch interactif |
| **LoomVideo** | PKU + Alibaba | Édition vidéo fashion, 5.41× speedup, FashionVideoBench |
| **VACE** (Wan2.1) | Alibaba | Framework unifié vidéo, backbone idéal |
| **Eevee** | Alibaba (AMAP-ML) | Dataset HD le plus complet, baseline CVPR 2026 |
| **TurboDiffusion** | Tsinghua + ShengShu | 100-200× speedup, approche temps réel |

### 2.2 🥈 Tier 2 — Technologies complémentaires

| Solution | Auteur | Pourquoi c'est utile |
|----------|--------|---------------------|
| **OmniVTON/++** | Ocean Univ. China | Training-free, multi-person, universel |
| **BooW-VTON** | Tianjin Univ. | Mask-free in-the-wild, CVPR 2025 |
| **iTryOn** | Sun Yat-sen + Alibaba | Interactions main-vêtement, ICML 2026 |
| **Garments2Look** | HK Polytechnic | Dataset outfit complet (80K), accessoires |
| **ChatGarment** | Westlake + SJTU | Édition vêtements par conversation LLM |
| **OSP-Next** | PKU | Accélération sparse attention |

### 2.3 🥉 Tier 3 — Recherche avancée / long-terme

| Solution | Auteur | Innovation |
|----------|--------|-----------|
| **LUIVITON** | - | Try-on 3D universel via SMPL proxy |
| **MV-Fashion** | ShanghaiTech | Multi-vue vidéo + size estimation |
| **UniFit** | - | VTON universel guidé par MLLM |
| **Human3R** | Westlake | Reconstruction 3D multi-personnes |

---

## 3. IMPACT SUR LE PLAN DE CONSTRUCTION

### 3.1 Révisions majeures suite aux découvertes

#### A. Renommer le projet
Le nom "Fashion Chameleon" est pris par Alibaba. Suggestions :
- **StyleShift** — Changement de style instantané
- **TryLive** — Essayage en live
- **MirrorAI** — Miroir intelligent
- **FitStream** — Essayage en streaming
- **DressMeUp** — Habille-moi
- **CatwalkAI** — Défilé IA

#### B. Nouvelle architecture recommandée

Grâce à la découverte de FashionChameleon d'Alibaba, l'architecture évolue :

```
AVANT (notre plan original) :
  AR Preview (50ms) → Image VTON (2-5s) → Video VTON (15-30s)

APRÈS (plan optimisé avec FashionChameleon + TurboDiffusion) :
  AR Preview (50ms) → Streaming VTON (23.8 FPS / ~42ms) → HD Refinement (1-5s)
                       ↑                                     ↑
                       FashionChameleon                       LoomVideo/Eevee
                       KV Cache Rescheduling                  + TurboDiffusion
```

Le gap entre "preview AR" et "diffusion photoréaliste" est **quasi comblé** par FashionChameleon (23.8 FPS) + TurboDiffusion (100-200× speedup).

#### C. Stack technique mis à jour

| Composant | Avant | Après |
|-----------|-------|-------|
| **Modèle principal** | LoomVideo seul | **FashionChameleon** (temps réel) + LoomVideo (HD) |
| **Accélération** | OSP-Next + LCM-LoRA | **TurboDiffusion** (100×) + OSP-Next + LCM-LoRA |
| **Image VTON** | ITVTON / Re-CatVTON | **OmniVTON++** (training-free) + ITVTON |
| **Mask-free** | Non prévu | **BooW-VTON** paradigme (plus besoin de masques !) |
| **Dataset outfit** | Eevee seul | Eevee + **Garments2Look** (80K outfits complets) |
| **Multi-person** | Non prévu | **OmniVTON** (premier multi-person VTON) |

#### D. Timeline révisée

```
Mois 1     ████ Phase 0 : Intégrer FashionChameleon d'Alibaba
                          + TurboDiffusion
Mois 1-2   ████████ Phase 1 : Fondations avec pipeline accéléré
Mois 2-3   ████████ Phase 2 : Near-realtime VTON (cible 15-24 FPS)
Mois 3-4   ████████ Phase 3 : HD refinement + multi-garment
Mois 4-5   ████████ Phase 4 : Multi-person + outfit complet
Mois 5-6   ████████ Phase 5 : App mobile + intégration e-commerce
Mois 6-7   ████████ Phase 6 : Launch

Total réduit : ~7 mois (vs 8 mois initialement)
```

---

## 4. LIENS ET RESSOURCES COMPLÉMENTAIRES

### Papiers & Code

| Ressource | URL |
|-----------|-----|
| FashionChameleon Paper | https://arxiv.org/abs/2605.15824 |
| FashionChameleon HuggingFace | https://huggingface.co/papers/2605.15824 |
| OmniVTON Code | https://github.com/Jerome-Young/OmniVTON |
| OmniVTON++ Code | https://github.com/Jerome-Young/OmniVTON-PlusPlus |
| BooW-VTON (CVPR 2025) | https://arxiv.org/abs/2408.06047 |
| Garments2Look (CVPR 2026) | https://arxiv.org/abs/2603.14153 |
| ChatGarment (CVPR 2025) | Westlake / SJTU |
| LUIVITON | https://arxiv.org/abs/2509.05030 |
| TurboDiffusion | GitHub (open-source) |
| UniFit | https://github.com/zwplus/UniFit |
| MV-Fashion | https://arxiv.org/abs/2603.08147 |
| iTryOn | https://zhengjun-ai.github.io/itryon-page/ |
| Lumos (DAMO) | https://github.com/alibaba-damo-academy/Lumos |

### Awesome Lists (à suivre)

| Liste | URL |
|-------|-----|
| Awesome Virtual Try-On | https://github.com/minar09/awesome-virtual-try-on |
| Awesome Try-On Models | https://github.com/Zheng-Chong/Awesome-Try-On-Models |
| Cool GenAI Fashion Papers | https://github.com/wendashi/Cool-GenAI-Fashion-Papers |
| Awesome Video Diffusion | https://github.com/ChenHsing/Awesome-Video-Diffusion-Models |
| Training-Free Methods | https://github.com/littlewhitesea/training-free-methods |

### Organisations HuggingFace

| Org | URL |
|-----|-----|
| Peking University | https://huggingface.co/PekingUniversity |
| Alibaba DAMO | https://huggingface.co/Alibaba-DAMO-Academy |
| Wan-AI | https://huggingface.co/Wan-AI |
| MSALab (LoomVideo) | https://huggingface.co/MSALab |

---

## 5. CARTOGRAPHIE DE L'ÉCOSYSTÈME CHINOIS

```
                        ÉCOSYSTÈME VIRTUAL TRY-ON CHINOIS
                        ================================

    ACADÉMIQUE                          INDUSTRIEL
    ─────────                          ──────────

    Peking University (PKU)            Alibaba Group
    ├── LoomVideo (avec Alibaba)       ├── FashionChameleon ★★★
    ├── OSP-Next                       ├── VACE / Wan2.1
    ├── Helios (avec ByteDance)        ├── Eevee (AMAP-ML)
    └── OpenS2V-Nexus                  ├── Lumos (DAMO)
                                       ├── Pic Copilot
    Tsinghua University                └── Aliwood
    ├── TurboDiffusion ★★★
    └── SageAttention                  Tencent
                                       └── Hunyuan Video
    Tianjin University
    └── BooW-VTON (CVPR 2025) ★★       ByteDance
                                       ├── Doubao
    Ocean Univ. of China               └── Helios (avec PKU)
    └── OmniVTON/++ (ICCV 2025) ★★
                                       SenseTime
    HK Polytechnic University          └── SenseNova (multimodal)
    └── Garments2Look (CVPR 2026) ★★
                                       ShengShu (Shengshu)
    Westlake University                └── Vidu (text-to-video)
    ├── ChatGarment (CVPR 2025)
    ├── ECON, ICON                     MiniMax
    └── Human3R (ICLR 2026)            └── Hailuo (video gen)

    Sun Yat-sen University             Shanghai AI Lab
    └── iTryOn (ICML 2026) ★★          └── InternLM, OpenGVLab

    Shanghai Jiao Tong (SJTU)
    └── AlphaPose, 3D reconstruction

    ★ = Directement pertinent pour ton projet
```

---

## 6. CITATIONS COMPLÉMENTAIRES

```bibtex
@article{song2026fashionchameleon,
  title={FashionChameleon: Towards Real-Time and Interactive Human-Garment Video Customization},
  author={Song, Quanjian and Shen, Yefeng and Chen, Mengting and Sun, Hao and Lan, Jinsong and Zhu, Xiaoyong and Zheng, Bo and Cao, Liujuan},
  journal={arXiv preprint arXiv:2605.15824},
  year={2026}
}

@inproceedings{yang2025omnivton,
  title={OmniVTON: Training-Free Universal Virtual Try-On},
  author={Yang, Zhaotong and Li, Yuhui and He, Shengfeng and Li, Xinzhe and Xu, Yangyang and Dong, Junyu and Du, Yong},
  booktitle={ICCV},
  year={2025}
}

@inproceedings{zhang2025boow,
  title={BooW-VTON: Boosting In-the-Wild Virtual Try-On via Mask-Free Pseudo Data Training},
  author={Zhang, Xuanpu and Song, Dan and Zhan, Pengxin and others},
  booktitle={CVPR},
  year={2025}
}

@inproceedings{hu2026garments2look,
  title={Garments2Look: A Multi-Reference Dataset for High-Fidelity Outfit-Level Virtual Try-On with Clothing and Accessories},
  author={Hu, Junyao and Cheng, Zhongwei and Wong, Waikeung and Zou, Xingxing},
  booktitle={CVPR},
  year={2026}
}

@misc{turbodiffusion2025,
  title={TurboDiffusion: Real-Time AI Video Generation},
  author={ShengShu Technology and Tsinghua University TSAIL Lab},
  year={2025},
  note={Open-source, 100-200x speedup}
}
```

---

*Document généré le 7 juin 2026 — Recherche complémentaire universités chinoises*
*Analyse de 25+ papiers, 10+ universités, 8+ entreprises tech chinoises*
