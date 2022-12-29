# -*- coding: utf-8 -*-
"""Image Comparison.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1CbjBnuf3rXb2pSVND3zM2QQrOctlT3wN
"""

import os
from PIL import Image
import numpy as np
import pandas as pd
import cv2
import skimage.metrics
import matplotlib.pyplot as plt
import queue
from sentence_transformers import SentenceTransformer, util
!pip install ftfy

# Lazy load images using PIL
# Specify image_dir when mass-loading images from a directory
def load_images(image_paths, image_dir=''):
  return [Image.open(image_dir + path) for path in image_paths]

# Determine pairwise structural similarity index measure (SSIM)
def structural_similarity(image1, image2, visualize=False):
  # Ensure both images are grayscale
  if image1.mode != 'L' or image2.mode != 'L':
    image1 = image1.convert('L')
    image2 = image2.convert('L')
  # Resize to match dimensions
  if image1.size != image2.size:
    if image1.size > image2.size:
      image1 = image1.resize(image2.size)
    else:
      image2 = image2.resize(image1.size)
  # Calculate SSIM
  score, diff = skimage.metrics.structural_similarity(np.array(image1), np.array(image2), full=True)
  # Visualize differences if flag is true
  if visualize:
    diff = (diff * 255).astype(np.uint8)
    _, threshold = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    contours, _  = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filled = np.array(image2.convert('RGB')).copy()
    for c in contours:
      cv2.drawContours(filled, [c], 0, (0, 255, 0), -1)
    plt.figure()
    plt.imshow(filled, cmap='gray')
    plt.axis('off')
    plt.show()
  return score

# Calculate pairwise SSIM and return top K matches
def structural_comparison(image, dataset, top_k=50):
  matches = []
  for i in dataset:
    score = structural_similarity(image, i)
    matches += [[i.filename.split('/')[-1], score]]
  return np.sort(np.array(matches, dtype=object), axis=0)[::-1][:top_k]

# Helper function to convert dense vector comparison scores to matches format
def idx_to_file(dataset, scores):
  matches = []
  for score, idx in scores:
    matches += [[dataset[int(idx)-1].filename.split('/')[-1], score]]
  return np.array(matches, dtype=object)

# Use dense vector representations (ViT) to determine cosine similarity scores and return top K matches
def dense_vector_comparison(image, dataset, top_k=50, multiprocessing=True):
  model = SentenceTransformer('clip-ViT-B-32')
  if multiprocessing:
    # Use the power of multiprocessing!
    pool = model.start_multi_process_pool()
    encoded = model.encode_multi_process([image] + dataset, pool)
  else:
    encoded = model.encode([image] + dataset)
  scores = np.array(util.paraphrase_mining_embeddings(encoded, top_k=top_k), dtype=object)
  scores = (scores[np.where(scores[:,1] == 0)[0]])[:,[0,2]]
  return idx_to_file(dataset, scores)

# Combined score metric (TESTING ONLY)
def combined_score(ssim, dvrs):
  return (ssim**0.5) * (dvrs**2)

X = load_images(os.listdir('/content/CheXViz/Chexpert/0/'), '/content/CheXViz/Chexpert/0/')

t = structural_comparison(X[0], X)
t

t = dense_vector_comparison(X[0], X)
t