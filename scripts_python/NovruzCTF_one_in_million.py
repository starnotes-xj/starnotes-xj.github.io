from PIL import Image
import random
import numpy as np
import time

img = Image.open('/CTF_Writeups/files/a87ad61f-e3a0-4547-a92c-e7957eaade3c.png')
pixels = np.array(img, dtype=np.uint8)
h, w, c = pixels.shape
flat = pixels.reshape(-1, 3)  # (22500, 3) - treat each pixel as RGB tuple
total_pixels = h * w

print(f"Image: {w}x{h}, {total_pixels} pixels")

def compute_gradient(img_2d):
    """Compute average gradient magnitude (low = structured image)"""
    f = img_2d.astype(np.float32)
    # Horizontal and vertical differences
    dx = np.abs(np.diff(f, axis=1)).mean()
    dy = np.abs(np.diff(f, axis=0)).mean()
    return dx + dy

# Baseline: current (shuffled) image gradient
baseline = compute_gradient(pixels)
print(f"Baseline gradient (shuffled): {baseline:.2f}")

# Test a known structured image for comparison
test_img = np.zeros_like(pixels)
test_img[50:100, 50:100] = 50  # White square
test_grad = compute_gradient(test_img)
print(f"Test structured image gradient: {test_grad:.2f}")

# Time one unshuffle operation
start = time.time()
random.seed(12345)
indices = list(range(total_pixels))
random.shuffle(indices)
elapsed_one = time.time() - start
print(f"One shuffle takes: {elapsed_one*1000:.1f}ms")
print(f"Estimated total time for 1M seeds: {elapsed_one * 999001 / 60:.0f} minutes")

# For pixel shuffle: shuffled[i] = original[perm[i]]
# To unshuffle: original[perm[i]] = shuffled[i]
# So: original = empty; for i, p in enumerate(perm): original[p] = shuffled[i]
start = time.time()
result = np.empty_like(flat)
for i, p in enumerate(indices):
    result[p] = flat[i]
result_img = result.reshape(h, w, c)
grad = compute_gradient(result_img)
print(f"Seed 12345 unshuffled gradient: {grad:.2f}")
print(f"One unshuffle+check takes: {(time.time()-start)*1000:.1f}ms")

# Now brute force - but only if fast enough
print("\nStarting brute force...")
start = time.time()
best_seed = -1
best_grad = baseline
threshold = baseline * 0.5  # Looking for significantly lower gradient

for seed in range(1000, 1000001):
    random.seed(seed)
    indices = list(range(total_pixels))
    random.shuffle(indices)

    result = np.empty_like(flat)
    for i, p in enumerate(indices):
        result[p] = flat[i]

    result_img = result.reshape(h, w, c)
    grad = compute_gradient(result_img)

    if grad < threshold:
        print(f"Seed {seed}: gradient={grad:.2f} - BELOW THRESHOLD!")
        Image.fromarray(result_img).save(f'D:/GolandProjects/LearnGO/needle_unshuffle_{seed}.png')
        if grad < best_grad:
            best_grad = grad
            best_seed = seed

    if seed % 1000 == 0:
        elapsed = time.time() - start
        rate = (seed - 999) / max(elapsed, 0.001)
        eta = (1000000 - seed) / max(rate, 1)
        print(f"Progress: {seed}/1000000 ({elapsed:.0f}s, {rate:.0f}/s, ETA: {eta:.0f}s)", end='\r')

print(f"\nDone in {time.time()-start:.0f}s")
print(f"Best seed: {best_seed}, best gradient: {best_grad:.2f}")
