#!/bin/bash
release_model="./E2FGVI/release_model"

if [ ! -d "$release_model" ]; then
    echo "Directory doesn't exist. Creating now."
    mkdir -p "$release_model"
    echo "Directory created."
else
    echo "Directory exists."
fi

# download E2FGVI-ckpt
gdown https://drive.google.com/uc?id=10wGdKSUOie0XmCr8SQ2A2FeDe-mfn5w3 -O ./E2FGVI/release_model/

gdown https://drive.google.com/uc?id=1tNJMTJ2gmWdIXJoHVi5-H504uImUiJW9 -O ./E2FGVI/release_model/ && \
unzip ./E2FGVI/release_model/E2FGVI_CVPR22_models.zip -d ./E2FGVI/release_model

# download aot-ckpt 
gdown https://drive.google.com/uc?id=1QoChMkTVxdYZ_eBlZhK2acq9KMQZccPJ -O ./ckpt/R50_DeAOTL_PRE_YTB_DAV.pth

# download sam-ckpt
wget -P ./ckpt https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth

# download grounding-dino ckpt
wget -P ./ckpt https://huggingface.co/ShilongLiu/GroundingDINO/resolve/main/groundingdino_swint_ogc.pth