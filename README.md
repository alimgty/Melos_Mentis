📷 Emotion Detection using VGG16 and FER2013 Dataset  

This project implements Emotion Detection using a fine-tuned version of the VGG16 deep learning model. The model is trained and validated on the FER2013 dataset and is capable of recognizing facial emotions from images with high accuracy.  



🔍 Overview  

The project leverages Transfer Learning, utilizing the pretrained VGG16 model on ImageNet and fine-tuning it with the FER2013 dataset. The goal is to classify facial expressions into one of the seven emotion categories:  

Angry 😠

Disgust 🤢

Fear 😨

Happy 😄

Sad 😢

Surprise 😲

Neutral 😐



🧠 Model Architecture

Base Model: VGG16 (pretrained on ImageNet)



Modifications:

Removed top layers of original VGG16

Added custom fully connected layers for emotion classification

Fine-tuned the last few convolutional blocks for domain adaptation



📊 Dataset

FER2013 dataset:

Source: Kaggle

Contains grayscale 48x48 pixel images

Labeled into 7 emotion categories



🛠️ Installation

Clone the repository:

bash
Copy
Edit
git clone https://github.com/0Nikki0/EmotionDetection.git
cd EmotionDetection
Create and activate a virtual environment (optional but recommended):

bash
Copy
Edit
python -m venv venv
source venv/bin/activate  # for Unix
venv\Scripts\activate     # for Windows
Install dependencies:

bash
Copy
Edit
pip install -r requirements.txt
Run the application:

bash
Copy
Edit
python app.py



🌐 Web Application
The Flask web app allows users to use a webcam to detect facial emotions in real-time.



📓 Colab Notebook

You can find the full model training and experimentation in the Google Colab notebook:
🔗 Google Colab - [VGG16 Fine-tuning on FER2013](https://colab.research.google.com/drive/1kOieLMeOLPIep9DZaSlC90Zwq5Mng11p?usp=sharing)



🧪 Results

The fine-tuned model achieved high validation accuracy and showed good generalization on unseen samples. You can try it on your own images via the web interface.



✨ Features

Transfer learning using pretrained VGG16

Emotion classification into 7 categories

Real-time detection via webcam or static images

Lightweight Flask-based web interface



🛠️ Technologies Used

Python

TensorFlow / Keras

OpenCV

Flask

HTML/CSS (for frontend)

Google Colab