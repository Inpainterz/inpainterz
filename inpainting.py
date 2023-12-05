# -*- coding: utf-8 -*-
import cv2
from PIL import Image
import numpy as np
import importlib
import os
from tqdm import tqdm
import torch
import torchvision

from E2FGVI.core.utils import to_tensors
from E2FGVI.model.e2fgvi import InpaintGenerator

# sample reference frames from the whole video
def get_ref_index(f, neighbor_ids, length):
    ref_length = 10
    num_ref = -1
    ref_index = []
    if num_ref == -1:
        for i in range(0, length, ref_length):
            if i not in neighbor_ids:
                ref_index.append(i)
    else:
        start_idx = max(0, f - ref_length * (num_ref // 2))
        end_idx = min(length, f + ref_length * (num_ref // 2))
        for i in range(start_idx, end_idx + 1, ref_length):
            if i not in neighbor_ids:
                if len(ref_index) > num_ref:
                    break
                ref_index.append(i)
    return ref_index


# read frame-wise masks
def read_mask(mpath, size):
    masks = []
    mnames = os.listdir(mpath)
    mnames.sort()
    for mp in mnames:
        m = Image.open(os.path.join(mpath, mp))
        m = m.resize(size, Image.NEAREST)
        m = np.array(m.convert('L'))
        m = np.array(m > 0).astype(np.uint8)
        m = cv2.dilate(m,
                       cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3)),
                       iterations=4)
        masks.append(Image.fromarray(m * 255))
    return masks


#  read frames from video
def read_frame_from_videos(npath):
    frames = []
    lst = os.listdir(npath)
    lst.sort()
    fr_lst = [npath + '/' + name for name in lst]
    for fr in fr_lst:
        image = cv2.imread(fr)
        image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        frames.append(image)
    return frames


# resize frames
def resize_frames(frames, size=None):
    frames = [f.resize(size) for f in frames]
    
    return frames, size

# create directory
def create_dir(dir_path):
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
    
    else:
        os.system(f"rm -r {dir_path}")
        os.makedirs(dir_path)
        
def inpainting_result_output(input_video):
    if input_video is not None:
        video_name = os.path.basename(input_video).split('.')[0]
    else:
        return None, None
    
    tracking_result_dir = f'{os.path.join(os.path.dirname(__file__), "tracking_results", f"{video_name}")}'
    inpainting_result_dir = f'{os.path.join(os.path.dirname(__file__), "inpainting_results", f"{video_name}")}'
    create_dir(inpainting_result_dir)
    
    aot_model2ckpt = {
        "e2fgvi": "./E2FGVI/release_model/E2FGVI-CVPR22.pth",
    }
    io_args = {
        'nomal_frame_dir': f'{tracking_result_dir}/{video_name}_nomal_frames',
        'mask_frame_dir': f'{tracking_result_dir}/{video_name}_masks',
        'seg_video': f'{tracking_result_dir}/{video_name}_seg1.mp4',
        'output_video': f'{inpainting_result_dir}/{video_name}_inpainting.mp4',
        'output_video_h264': f'{inpainting_result_dir}/{video_name}_inpainting_h264.mp4',
    }
    
    cap = cv2.VideoCapture(input_video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    
    return main_worker(aot_model2ckpt, io_args, fps)

def main_worker(aot_model2ckpt, io_args, fps=24, neighbor_stride=5):
    size = (432, 240)
    
    # set up models
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    model = InpaintGenerator().to(device)
    data = torch.load(aot_model2ckpt["e2fgvi"], map_location=device)
    model.load_state_dict(data)
    print(f'Loading model from: {aot_model2ckpt["e2fgvi"]}')
    model.eval()
    
    print(f'Loading masked frame and nomal frame from {io_args["mask_frame_dir"]} | {io_args["nomal_frame_dir"]}')
    
    frames = read_frame_from_videos(io_args['nomal_frame_dir'])
    frames, size = resize_frames(frames, size)
    h, w = size[1], size[0]
    video_length = len(frames)
    imgs = to_tensors()(frames).unsqueeze(0) * 2 - 1
    frames = [np.array(f).astype(np.uint8) for f in frames]

    masks = read_mask(io_args['mask_frame_dir'], size)
    binary_masks = [
        np.expand_dims((np.array(m) != 0).astype(np.uint8), 2) for m in masks
    ]
    masks = to_tensors()(masks).unsqueeze(0)
    imgs, masks = imgs.to(device), masks.to(device)
    comp_frames = [None] * video_length

    # completing holes by e2fgvi
    print(f'Start test...')
    for f in tqdm(range(0, video_length, neighbor_stride)):
        neighbor_ids = [
            i for i in range(max(0, f - neighbor_stride),
                             min(video_length, f + neighbor_stride + 1))
        ]
        ref_ids = get_ref_index(f, neighbor_ids, video_length)
        selected_imgs = imgs[:1, neighbor_ids + ref_ids, :, :, :]
        selected_masks = masks[:1, neighbor_ids + ref_ids, :, :, :]
        with torch.no_grad():
            masked_imgs = selected_imgs * (1 - selected_masks)
            mod_size_h = 60
            mod_size_w = 108
            h_pad = (mod_size_h - h % mod_size_h) % mod_size_h
            w_pad = (mod_size_w - w % mod_size_w) % mod_size_w
            masked_imgs = torch.cat(
                [masked_imgs, torch.flip(masked_imgs, [3])],
                3)[:, :, :, :h + h_pad, :]
            masked_imgs = torch.cat(
                [masked_imgs, torch.flip(masked_imgs, [4])],
                4)[:, :, :, :, :w + w_pad]
            pred_imgs, _ = model(masked_imgs, len(neighbor_ids))
            pred_imgs = pred_imgs[:, :, :h, :w]
            pred_imgs = (pred_imgs + 1) / 2
            pred_imgs = pred_imgs.cpu().permute(0, 2, 3, 1).numpy() * 255
            for i in range(len(neighbor_ids)):
                idx = neighbor_ids[i]
                img = np.array(pred_imgs[i]).astype(
                    np.uint8) * binary_masks[idx] + frames[idx] * (
                        1 - binary_masks[idx])
                if comp_frames[idx] is None:
                    comp_frames[idx] = img
                else:
                    comp_frames[idx] = comp_frames[idx].astype(
                        np.float32) * 0.5 + img.astype(np.float32) * 0.5

    # saving videos
    print('Saving videos...')
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(io_args['output_video'], fourcc, fps, size)
    inpainting_frames = []
    for f in range(video_length):
        comp = comp_frames[f].astype(np.uint8)
        inpainting_frames.append(comp)
        writer.write(comp)
    writer.release()
    print(f'Finish test! The result video is saved in: {io_args["output_video"]}.')

    # convert codec
    inpainting_frames = torch.from_numpy(np.asarray(inpainting_frames))
    torchvision.io.write_video(io_args['output_video_h264'], inpainting_frames, fps=fps, video_codec="h264")

    return io_args['output_video_h264']

if __name__ == '__main__':
    pass
