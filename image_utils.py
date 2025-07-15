import tensorflow as tf
from tensorflow.keras.models import load_model
from PIL import Image, ImageOps
import numpy as np

# Load the model
model = load_model("AI.h5", compile=False)

# Load the labels
class_names = open("labels.txt", "r").readlines()

def preprocess_image(img_path,):
    # Replace this with the path to your image
    image = Image.open(img_path).convert("RGB")

    # resizing the image to be at least 224x224 and then cropping from the center
    size = (224, 224)
    image = ImageOps.fit(image, size, Image.LANCZOS)

    # turn the image into a numpy array
    image_array = np.asarray(image)

    # Normalize the image
    normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1

    # Load the image into the array
    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
    data[0] = normalized_image_array
    return data

def recognize_food(img_path,servings=1):
    processed_img = preprocess_image(img_path)

    # Predicts the model
    prediction = model.predict(processed_img)
    index = np.argmax(prediction)
    class_name = class_names[index]
    confidence_score = prediction[0][index]

    # Add nutrient and calorie information
    nutrients_list = [
    {"Protein": 3.4, "Carbs": 19.2, "Fat": 0.4, "Iron": 1.2, "Magnesium": 21.0, "Calcium": 120.0},  # Upma
    {"Protein": 10.8, "Carbs": 57.5, "Fat": 15.2, "Iron": 2.0, "Magnesium": 45.0, "Calcium": 30.0},  # Biriyani
    {"Protein": 8.0, "Carbs": 12.0, "Fat": 7.8, "Iron": 0.1, "Magnesium": 24.0, "Calcium": 276.0},  # Milk
    {"Protein": 5.0, "Carbs": 27.0, "Fat": 2.0, "Iron": 3.0, "Magnesium": 56.0, "Calcium": 32.0},  # Oat Meal
    {"Protein": 2.0, "Carbs": 22.0, "Fat": 2.0, "Iron": 1.5, "Magnesium": 26.0, "Calcium": 10.0},  # Dosa
    {"Protein": 3.0, "Carbs": 15.0, "Fat": 1.0, "Iron": 0.9, "Magnesium": 21.0, "Calcium": 8.0},  # Chapati
    {"Protein": 2.5, "Carbs": 30.0, "Fat": 15.0, "Iron": 1.8, "Magnesium": 30.0, "Calcium": 40.0},  # Sadhya
    {"Protein": 1.0, "Carbs": 70.0, "Fat": 10.0, "Iron": 0.5, "Magnesium": 12.0, "Calcium": 5.0},  # Jalebi
    {"Protein": 20.0, "Carbs": 15.0, "Fat": 5.0, "Iron": 2.2, "Magnesium": 40.0, "Calcium": 60.0},  # Fish Curry
    {"Protein": 6.5, "Carbs": 0.6, "Fat": 5.0, "Iron": 1.2, "Magnesium": 12.0, "Calcium": 28.0},  # Egg
    {"Protein": 0.5, "Carbs": 19.0, "Fat": 0.3, "Iron": 0.1, "Magnesium": 5.0, "Calcium": 6.0},  # Apple
    {"Protein": 0.8, "Carbs": 14.0, "Fat": 0.6, "Iron": 0.1, "Magnesium": 9.0, "Calcium": 11.0}  # Mango

]

    micronutrients = [
    {"Iron": 1.2, "Magnesium": 21.0, "Calcium": 120.0},  # Upma
    {"Iron": 2.0, "Magnesium": 45.0, "Calcium": 30.0},  # Biriyani
    {"Iron": 0.1, "Magnesium": 24.0, "Calcium": 276.0},  # Milk
    {"Iron": 3.0, "Magnesium": 56.0, "Calcium": 32.0},  # Oat Meal
    {"Iron": 1.5, "Magnesium": 26.0, "Calcium": 10.0},  # Dosa
    {"Iron": 0.9, "Magnesium": 21.0, "Calcium": 8.0},  # Chapati
    {"Iron": 1.8, "Magnesium": 30.0, "Calcium": 40.0},  # Sadhya
    {"Iron": 0.5, "Magnesium": 12.0, "Calcium": 5.0},  # Jalebi
    {"Iron": 2.2, "Magnesium": 40.0, "Calcium": 60.0},  # Fish Curry
    {"Iron": 1.2, "Magnesium": 12.0, "Calcium": 28.0},  # Egg
    {"Iron": 0.1, "Magnesium": 5.0, "Calcium": 6.0},  # Apple
    {"Iron": 0.1, "Magnesium": 9.0, "Calcium": 11.0}  # Mango
]

    
    calories_list = [250, 360, 150, 150, 130, 120, 2000, 80, 300, 80, 95, 65]
    recognized_nutrients = nutrients_list[index]
    recognized_micronutrients = micronutrients[index]  # Get the micronutrients for the recognized food
    calories = calories_list[index]  # Assign calories based on predicted index

    # Multiply nutrients and micronutrients by the number of servings
    nutrients = {k: v * servings for k, v in recognized_nutrients.items()}
    micronutrient_info = {k: v * servings for k, v in recognized_micronutrients.items()}

    return class_name[2:], nutrients, calories, confidence_score, micronutrient_info