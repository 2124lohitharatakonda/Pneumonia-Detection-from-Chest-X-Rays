"""
MobileNetV2 Transfer Learning Training Script
=============================================
Trains a binary pneumonia classifier using MobileNetV2 pretrained on ImageNet.

Usage:
    python ml/train_mobilenet.py

Outputs:
    saved_models/mobilenetv2.h5
"""
import os
import sys
import logging

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

TRAIN_DIR  = os.path.join('DATASET', 'train')
TEST_DIR   = os.path.join('DATASET', 'test')
MODEL_DIR  = 'saved_models'
MODEL_PATH = os.path.join(MODEL_DIR, 'mobilenetv2.h5')
PLOTS_DIR  = os.path.join(MODEL_DIR, 'plots')

IMG_HEIGHT    = 224
IMG_WIDTH     = 224
BATCH_SIZE    = 32
EPOCHS        = 15
FINE_TUNE_EPOCHS = 5
LEARNING_RATE = 1e-4
FINE_TUNE_LR  = 1e-5
CLASSES       = ['NORMAL', 'PNEUMONIA']


def check_dataset():
    for split in (TRAIN_DIR, TEST_DIR):
        if not os.path.isdir(split):
            logger.error('Dataset directory not found: %s', split)
            sys.exit(1)


def build_generators():
    from tensorflow.keras.preprocessing.image import ImageDataGenerator

    train_datagen = ImageDataGenerator(
        rescale=1.0 / 255,
        rotation_range=10,
        width_shift_range=0.1,
        height_shift_range=0.1,
        horizontal_flip=True,
        zoom_range=0.1,
        fill_mode='nearest',
    )
    test_datagen = ImageDataGenerator(rescale=1.0 / 255)

    train_gen = train_datagen.flow_from_directory(
        TRAIN_DIR,
        target_size=(IMG_HEIGHT, IMG_WIDTH),
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        classes=CLASSES,
        shuffle=True,
        seed=42,
    )
    test_gen = test_datagen.flow_from_directory(
        TEST_DIR,
        target_size=(IMG_HEIGHT, IMG_WIDTH),
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        classes=CLASSES,
        shuffle=False,
    )
    return train_gen, test_gen


def build_model():
    import tensorflow as tf

    base = tf.keras.applications.MobileNetV2(
        input_shape=(IMG_HEIGHT, IMG_WIDTH, 3),
        include_top=False,
        weights='imagenet',
    )
    base.trainable = False

    inputs = tf.keras.Input(shape=(IMG_HEIGHT, IMG_WIDTH, 3))
    x = base(inputs, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dense(128, activation='relu')(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    outputs = tf.keras.layers.Dense(2, activation='softmax')(x)

    model = tf.keras.Model(inputs, outputs)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss='categorical_crossentropy',
        metrics=['accuracy'],
    )
    logger.info('MobileNetV2 model built. Total params: %s', model.count_params())
    return model, base


def plot_history(history, tag, save_dir):
    os.makedirs(save_dir, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].plot(history.history['accuracy'],     label='Train Accuracy', color='royalblue')
    axes[0].plot(history.history['val_accuracy'], label='Val Accuracy',   color='tomato')
    axes[0].set_title(f'{tag} — Accuracy')
    axes[0].set_xlabel('Epoch'); axes[0].set_ylabel('Accuracy')
    axes[0].legend(); axes[0].grid(True, alpha=0.3)

    axes[1].plot(history.history['loss'],     label='Train Loss', color='royalblue')
    axes[1].plot(history.history['val_loss'], label='Val Loss',   color='tomato')
    axes[1].set_title(f'{tag} — Loss')
    axes[1].set_xlabel('Epoch'); axes[1].set_ylabel('Loss')
    axes[1].legend(); axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    out = os.path.join(save_dir, f'mobilenetv2_{tag.lower().replace(" ", "_")}.png')
    plt.savefig(out, dpi=120)
    plt.close()
    logger.info('Plot saved: %s', out)


def evaluate(model, test_gen):
    logger.info('Evaluating on test set…')
    test_gen.reset()
    preds = model.predict(test_gen, verbose=1)
    y_pred = np.argmax(preds, axis=1)
    y_true = test_gen.classes
    logger.info('Classification Report:\n%s',
                classification_report(y_true, y_pred, target_names=CLASSES))
    logger.info('Confusion Matrix:\n%s', confusion_matrix(y_true, y_pred))


def main():
    check_dataset()
    os.makedirs(MODEL_DIR, exist_ok=True)

    import tensorflow as tf
    logger.info('TensorFlow version: %s', tf.__version__)

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor='val_loss', patience=4, restore_best_weights=True
        ),
        tf.keras.callbacks.ModelCheckpoint(
            MODEL_PATH, monitor='val_accuracy', save_best_only=True, verbose=1
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss', factor=0.5, patience=2, min_lr=1e-7, verbose=1
        ),
    ]

    train_gen, test_gen = build_generators()
    model, base = build_model()

    logger.info('Phase 1: Training top layers (%d epochs)…', EPOCHS)
    h1 = model.fit(train_gen, epochs=EPOCHS, validation_data=test_gen, callbacks=callbacks)
    plot_history(h1, 'Phase1 Transfer', PLOTS_DIR)

    logger.info('Phase 2: Fine-tuning last 30 layers (%d epochs)…', FINE_TUNE_EPOCHS)
    base.trainable = True
    for layer in base.layers[:-30]:
        layer.trainable = False
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=FINE_TUNE_LR),
        loss='categorical_crossentropy',
        metrics=['accuracy'],
    )
    h2 = model.fit(train_gen, epochs=FINE_TUNE_EPOCHS, validation_data=test_gen, callbacks=callbacks)
    plot_history(h2, 'Phase2 FineTune', PLOTS_DIR)

    model.save(MODEL_PATH)
    logger.info('Model saved to %s', MODEL_PATH)
    evaluate(model, test_gen)


if __name__ == '__main__':
    main()
