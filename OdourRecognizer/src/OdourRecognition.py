from OdourRecognizer.src.recognizers.RecognizerManager import RecognizerManager

if __name__ == "__main__":
    recognizer = RecognizerManager(models_folder_path="models")

    # Assume `data` is your input feature vector, e.g., from sensors
    data = [0.12, 0.34, 0.56, 0.78]

    best_result = recognizer.recognize_best(data)

    print(f"Best Model: {best_result['model_name']}")
    print(f"Prediction: {best_result['prediction']}")
    print(f"Confidence: {best_result['confidence']:.2f}")