from transformers import SegformerImageProcessor, AutoModelForSemanticSegmentation
from PIL import Image
import requests
import matplotlib.pyplot as plt
import torch.nn as nn
import numpy as np
from collections import Counter
import colorsys

image = Image.open("images/chel.png")
tatarin = Image.open("images/tatarin_png3.png")

def img_resize(image, fixed_width):
    width_percent = (fixed_width / float(tatarin.size[0]))
    height_size = int((float(image.size[1]) * float(width_percent)))
    new_image = image.resize((fixed_width, height_size))
    return new_image

def find_common_color(array):
    sublist, count = max(Counter(tuple(sorted(x)) for x in array).items(), key=lambda x: x[1])
    return list(sublist)


def segmentation(image):
    image_matrix = np.array(image)
    inputs = processor(images=image, return_tensors="pt")

    outputs = model(**inputs)
    logits = outputs.logits.cpu()

    upsampled_logits = nn.functional.interpolate(
        logits,
        size=image.size[::-1],
        mode="bilinear",
        align_corners=False,
    )

    pred_seg = upsampled_logits.argmax(dim=1)[0]
    colors = [[] for _ in range(17)]
    for i in range(len(pred_seg)):
        for j in range(len(pred_seg[0])):
            colors[int(pred_seg[i][j])].append(image_matrix[i][j])
    plt.imshow(pred_seg)
    return colors


processor = SegformerImageProcessor.from_pretrained("mattmdjaga/segformer_b2_clothes")
model = AutoModelForSemanticSegmentation.from_pretrained("mattmdjaga/segformer_b2_clothes")

colors = segmentation(image)

hair_pixels = colors[2]
upper_clothes_pixels = colors[4]
pants_pixels = colors[6]
shoes_pixels = colors[9] + colors[10]

red, green, blue = find_common_color(hair_pixels)
hair_metric = 1 - (0.299 * red + 0.587 * green + 0.114 * blue) / 255
if hair_metric <= 0.5:
    hair_color_to_change = [210, 168, 124, 255]
    hair_glare_color_to_change = [223, 184, 144, 255]
elif 0.5 < hair_metric <= 0.79:
    hair_color_to_change = [161, 131, 100, 255]
    hair_glare_color_to_change = [210, 168, 124, 255]
else:
    hair_color_to_change = [0, 0, 0, 255]
    hair_glare_color_to_change = [23, 23, 23, 255]

upper_clothes_color_to_change = find_common_color(upper_clothes_pixels) + [255]
pants_color_to_change = find_common_color(pants_pixels) + [255]
shoes_color_to_change = find_common_color(shoes_pixels) + [255]

def change_colors(image_tatarin: Image) -> Image:
    hair_color = np.array([0, 0, 0, 255])
    hair_glare_color = np.array([23, 23, 23, 255])
    upper_clothes_color = np.array([253, 166, 7, 255])
    upper_clothes_shadow1_color = np.array([218, 134, 12, 255])
    upper_clothes_shadow2_color = np.array([205, 100, 9, 255])
    pants_color = np.array([30, 14, 1, 255])
    shoes_color = np.array([1, 1, 3, 255])

    matrix = np.array(image_tatarin)
    height, width, pixels = matrix.shape

    for i in range(height):
        for j in range(width):
            if (matrix[i][j] == upper_clothes_color).all():
                matrix[i][j] = upper_clothes_color_to_change
            elif (matrix[i][j] == upper_clothes_shadow1_color).all():
                matrix[i][j] = upper_clothes_color_to_change
                r, g, b, a = upper_clothes_color_to_change
                h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
                new_color = np.array([h * 179, s * 100, v * 100 - 15, a])
                h, s, v, a = new_color
                r, g, b = colorsys.hsv_to_rgb(h / 179, s / 100, v / 100)
                matrix[i][j] = np.array([r * 255, g * 255, b * 255, a])
            elif (matrix[i][j] == upper_clothes_shadow2_color).all():
                matrix[i][j] = upper_clothes_color_to_change
                r, g, b, a = upper_clothes_color_to_change
                h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
                new_color = np.array([h * 179, s * 100, v * 100 - 25, a])
                h, s, v, a = new_color
                r, g, b = colorsys.hsv_to_rgb(h / 179, s / 100, v / 100)
                matrix[i][j] = np.array([r * 255, g * 255, b * 255, a])
            elif (matrix[i][j] == pants_color).all():
                matrix[i][j] = pants_color_to_change
            elif (matrix[i][j] == shoes_color).all():
                matrix[i][j] = shoes_color_to_change
            elif (matrix[i][j] == hair_color).all():
                matrix[i][j] = hair_color_to_change
            elif (matrix[i][j] == hair_glare_color).all():
                matrix[i][j] = hair_glare_color_to_change

    result = Image.fromarray(matrix).convert('RGBA')
    return result


new_tatarin = change_colors(tatarin)
new_tatarin_to_demo = img_resize(new_tatarin, 250)
new_tatarin.save("images/result.png")
