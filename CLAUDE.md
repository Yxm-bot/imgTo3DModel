# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Chinese-language 3D model generation system that converts single images into 3D models using the TripoSR open-source model. The repository contains two main components:

1. **imgTo3DModel**: A simplified wrapper application with a user-friendly Gradio interface
2. **TripoSR**: The core TripoSR implementation (from Stability AI and Tripo AI)

The system is designed primarily for Windows users with NVIDIA GPUs and provides both web interface and command-line tools.

## Repository Structure

```
imgTo3DModel1/
├── imgTo3DModel/           # Simplified wrapper application
│   ├── app/
│   │   ├── main.py         # Main Gradio web application
│   │   └── requirements.txt # Application dependencies
│   ├── src/
│   │   ├── __init__.py
│   │   └── tsr.py          # TripoSR module wrapper/loader
│   └── README.md           # Chinese user documentation
├── TripoSR/                # Core TripoSR implementation
│   ├── tsr/                # Core library modules
│   │   ├── system.py       # TSR model class and loading logic
│   │   ├── utils.py        # Utility functions
│   │   ├── models/         # Model components (isosurface, nerf, transformers, etc.)
│   │   └── bake_texture.py # Texture baking functionality
│   ├── run.py              # Command-line inference script
│   ├── gradio_app.py       # Original TripoSR Gradio demo
│   └── requirements.txt    # TripoSR dependencies
├── models/                 # Model weights (auto-downloaded)
├── output/                 # Generated 3D models
└── logs/                   # Application logs
```

## Key Architecture Details

### Model Loading

The system uses two approaches for loading TripoSR:

1. **Direct Import** (TripoSR/gradio_app.py, TripoSR/run.py): Imports from `tsr.system` directly
2. **Path Resolution** (imgTo3DModel/src/tsr.py): Dynamically locates and imports TripoSR from multiple possible paths

The `TSR.from_pretrained()` method handles both local and HuggingFace Hub model loading:
- Local: `models/TripoSR` directory with `config.yaml` and `model.ckpt`
- Remote: `stabilityai/TripoSR` from HuggingFace Hub

### Image Processing Pipeline

1. **Background Removal**: Uses `rembg` library to isolate foreground subjects
2. **Foreground Resizing**: Adjusts subject size using `resize_foreground()` with configurable ratio (0.5-1.0)
3. **Background Filling**: Fills transparent areas with 50% gray
4. **Model Inference**: Processes through TSR model to generate scene codes
5. **Mesh Extraction**: Uses Marching Cubes algorithm at configurable resolution (64-512)

### 3D Generation Process

The generation flow in imgTo3DModel/app/main.py:287:
1. `preprocess_image()` - Handles background removal and image preparation
2. `model([image], device=device)` - Generates scene codes (latent 3D representation)
3. `model.extract_mesh(scene_codes, resolution=mc_resolution)` - Extracts triangle mesh
4. `to_gradio_3d_orientation(mesh)` - Corrects orientation for display
5. `mesh.export()` - Saves to OBJ/GLB format

### Device Management

- Auto-detects CUDA availability and falls back to CPU
- Default device: `cuda:0` if available, else `cpu`
- Chunk size of 8192 is used to balance VRAM usage vs computation time

## Common Development Commands

### Running the Simplified Application

```bash
cd imgTo3DModel/app
python main.py --port 7860
```

Options:
- `--port <number>`: Specify server port (default: 7860)
- `--share`: Create public sharing link via Gradio

### Running Original TripoSR Gradio Demo

```bash
cd TripoSR
python gradio_app.py --port 7860
```

Options:
- `--username <user>` / `--password <pass>`: Add authentication
- `--listen`: Allow network requests (0.0.0.0)
- `--share`: Create public sharing link
- `--queuesize <number>`: Set queue max size (default: 1)

### Command-Line Inference

```bash
cd TripoSR
python run.py examples/chair.png --output-dir output/
```

Important options:
- `--device cuda:0`: Specify device (default: cuda:0, fallback to cpu)
- `--pretrained-model-name-or-path <path>`: Local path or HuggingFace model ID (default: stabilityai/TripoSR)
- `--chunk-size 8192`: Balance VRAM vs speed (0 for no chunking)
- `--mc-resolution 256`: Marching cubes resolution (higher = finer detail)
- `--no-remove-bg`: Skip automatic background removal
- `--foreground-ratio 0.85`: Adjust foreground size (0.5-1.0)
- `--model-save-format obj|glb`: Output format
- `--bake-texture`: Generate texture atlas instead of vertex colors
- `--texture-resolution 2048`: Texture size when using --bake-texture
- `--render`: Save NeRF-rendered video

### Installing Dependencies

For imgTo3DModel:
```bash
cd imgTo3DModel/app
pip install -r requirements.txt
```

For TripoSR:
```bash
cd TripoSR
pip install -r requirements.txt
```

Note: Ensure PyTorch CUDA version matches system CUDA version before installing.

## Important Technical Notes

### CUDA Compatibility

If you encounter `torchmcubes` CUDA errors:
1. Verify PyTorch CUDA major version matches system CUDA major version
2. Ensure `setuptools>=49.6.0`
3. Reinstall: `pip uninstall torchmcubes && pip install git+https://github.com/tatsy/torchmcubes.git`

### Model Path Resolution

The imgTo3DModel/src/tsr.py:14-26 wrapper searches for TripoSR in this order:
1. `../../TripoSR` (project root sibling)
2. `../TripoSR` (parent directory)
3. `models/TripoSR` (models subdirectory)

### Memory Requirements

- Minimum: 6GB VRAM for single image at default settings
- Recommended: 12GB+ VRAM for batch processing or high resolution
- CPU mode: 16GB+ system RAM recommended

### Output Formats

- **OBJ**: Vertex colors, widely compatible with 3D software (Blender, 3ds Max)
- **GLB**: Binary format, optimized for web and mobile (three.js, WebGL)
- **Texture-baked**: Use `--bake-texture` for UV-mapped texture atlas (requires xatlas)

### Logging

- imgTo3DModel logs: `logs/app_YYYYMMDD_HHMMSS.log`
- Format: timestamp, log level, message
- Both file and console output

## Testing Images

Example images are located in `TripoSR/examples/`:
- chair.png, hamburger.png, robot.png, teapot.png, etc.
- Pre-processed images work best with `--no-remove-bg` enabled

## Configuration Parameters

### Marching Cubes Resolution
- 128: Fast, lower quality
- 256: Recommended balance
- 512: High quality, slower processing

### Foreground Ratio
- 0.5: Subject takes 50% of image
- 0.85: Default, good for most cases
- 1.0: Maximum subject size

### Chunk Size
- 0: No chunking (highest VRAM usage)
- 8192: Default balanced setting
- Higher values: Faster but more VRAM

## License

MIT License - Free for commercial and personal use
