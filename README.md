# inpainterz

# Getting Started

🎮Conda Default Environment
```shell
pip install torch==1.11.0+cu113 torchvision==0.12.0+cu113 torchaudio==0.11.0 --extra-index-url https://download.pytorch.org/whl/cu113
pip install mmcv-full==1.4.8 -f https://download.openmmlab.com/mmcv/dist/cu113/torch1.11/index.html
# script > delete opencv-python
# cd /DATA/inpainterz/Inpainterz_Video_Inpainting
bash script/install.sh
pip install gradio==3.39
pip install av
```

📑Requirements
The Segment-Anything repository has been cloned and renamed as sam, and the aot-benchmark repository has been cloned and renamed as aot.

Please check the dependency requirements in SAM and DeAOT.

The implementation is tested under python 3.9, as well as pytorch 1.11.0+cu113 and torchvision 0.12.0+cu113 We recommend equivalent or higher pytorch version.

Use the install.sh to install the necessary libs for SAM-Track-Inpainting

```
bash script/install.sh
```

⭐Model Preparation
Download SAM model to ckpt, the default model is SAM-VIT-B (sam_vit_b_01ec64.pth).

Download DeAOT/AOT model to ckpt, the default model is R50-DeAOT-L (R50_DeAOTL_PRE_YTB_DAV.pth).

Download Grounding-Dino model to ckpt, the default model is GroundingDINO-T (groundingdino_swint_ogc).

Download E2fgvi model to ckpt, the default model is E2FGVI-CVPR22 (E2FGVI-CVPR22.pth)

You can download the default weights using the command line as shown below.

```
bash script/download_ckpt.sh
```
