import os
import json
import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np
from file_utils import read_animal_list
import config

# Load the saved model
model = tf.keras.models.load_model(f"./animal_classifier_models/{config.VERSION}.keras")
# model = tf.keras.models.load_model('animal_classifier_models/v0.3.h5')
# model = tf.keras.models.load_model('animal_classifier_models/v0.1.h5')

animals = read_animal_list()


def predict_image(img_path, model, classes, top_k=5):
    # Charger l'image
    img = image.load_img(img_path, target_size=(150, 150))
    img_tensor = image.img_to_array(img)
    img_tensor = np.expand_dims(img_tensor, axis=0)
    img_tensor /= 255.

    # Faire la prédiction
    ranked_predictions = model.predict(img_tensor)[0]  # Récupérer les prédictions
    top_indices = np.argsort(ranked_predictions)[::-1][:top_k]  # Indices des top_k prédictions

    # Créer le classement des animaux les plus probables
    ranked_classes = [(classes[i], ranked_predictions[i]) for i in top_indices]

    return ranked_classes


def get_animal_score_and_ranking(prediction, chosen_animal):
    for ranking, (animal, score) in enumerate(prediction, start=1):
        if animal == chosen_animal:
            return float(score), ranking
    return None, None


def predict_all_images():
    animals_predictions = {}
    root_path = config.PREDICTION_IMAGES_PATH

    for root_folder, subfolders, files in os.walk(root_path):
        animal_name = os.path.basename(root_folder)
        animal_predictions = {}
        scores_percentage = []
        rankings = []
        best_score_differences = []

        print(f"\n--- Start the prediction for : {animal_name} ---")

        for file in files:
            image_path = os.path.join(root_folder, file)
            prediction = predict_image(image_path, model, animals, top_k=config.NUM_ANIMALS)

            animal_score, animal_ranking = get_animal_score_and_ranking(prediction, animal_name)
            animal_prediction = {}

            if animal_score:
                score_percentage = round(animal_score * 100, 2)
                animal_prediction["score_percentage"] = f"{score_percentage}%"
                scores_percentage.append(score_percentage)
            else:
                animal_prediction["score_percentage"] = None
                scores_percentage.append(0)

            if animal_ranking:
                animal_prediction["ranking"] = f"{animal_ranking}/{config.NUM_ANIMALS}"
                rankings.append(animal_ranking)
            else:
                animal_prediction["ranking"] = None
                rankings.append(config.NUM_ANIMALS)

            if animal_ranking > 1:
                best_animal, best_score = prediction[0]
                difference_best_score_percentage = round((best_score - animal_score) * 100, 2)
                animal_prediction["best_animal"] = best_animal
                animal_prediction[
                    "best_score_percentage"] = f"{round(best_score * 100, 2)}% (+{difference_best_score_percentage}%)"
                best_score_differences.append(difference_best_score_percentage)
            else:
                animal_prediction["best_animal"] = None
                animal_prediction["best_score_percentage"] = None
                best_score_differences.append(0)

            animal_predictions[file] = animal_prediction

        if animal_name != root_path:
            # Calculate statistics for the current animal
            stats = calculate_statistics(scores_percentage, rankings, best_score_differences)

            # Combine statistics with individual predictions
            stats.update(animal_predictions)
            animals_predictions[animal_name] = stats

    return animals_predictions


def calculate_statistics(scores, ranks, differences):
    if scores:
        avg_score = f"{round(sum(scores) / len(scores), 2)}%"
        min_score = f"{min(scores)}%"
        max_score = f"{max(scores)}%"
    else:
        avg_score = min_score = max_score = None

    if ranks:
        avg_rank = f"{round(sum(ranks) / len(ranks), 2)}/{config.NUM_ANIMALS}"
        min_rank = f"{min(ranks)}/{config.NUM_ANIMALS}"
        max_rank = f"{max(ranks)}/{config.NUM_ANIMALS}"
    else:
        avg_rank = min_rank = max_rank = f"0/{config.NUM_ANIMALS}"

    if differences:
        avg_difference = f"+{round(sum(differences) / len(differences), 2)}%"
        min_difference = f"+{min(differences)}%"
        max_difference = f"+{max(differences)}%"
    else:
        avg_difference = min_difference = max_difference = "+0%"

    return {
        "average_scores_percentage": avg_score,
        "min_score_percentage": min_score,
        "max_score_percentage": max_score,

        "average_rankings": avg_rank,
        "min_ranking": min_rank,
        "max_ranking": max_rank,

        "average_difference_with_best_scores": avg_difference,
        "min_difference_with_best_scores": min_difference,
        "max_difference_with_best_scores": max_difference,
    }


predictions = predict_all_images()
print(json.dumps(predictions, indent=4))
