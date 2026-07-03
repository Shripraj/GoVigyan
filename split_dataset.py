import os
import shutil
import random

DATASET_DIR = "dataset"
TRAIN_DIR = os.path.join(DATASET_DIR, "train")
VAL_DIR = os.path.join(DATASET_DIR, "val")

VAL_SPLIT = 0.20  # 20%

os.makedirs(VAL_DIR, exist_ok=True)

for breed in os.listdir(TRAIN_DIR):
    breed_train_path = os.path.join(TRAIN_DIR, breed)
    if not os.path.isdir(breed_train_path):
        continue

    breed_val_path = os.path.join(VAL_DIR, breed)
    os.makedirs(breed_val_path, exist_ok=True)

    images = os.listdir(breed_train_path)
    random.shuffle(images)

    val_count = int(len(images) * VAL_SPLIT)

    val_images = images[:val_count]

    for img in val_images:
        src = os.path.join(breed_train_path, img)
        dst = os.path.join(breed_val_path, img)
        try:
            shutil.move(src, dst)
        except:
            pass

print("DONE! Validation dataset created at dataset/val")
