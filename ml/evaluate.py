"""
Model Evaluation Script
=======================
Loads a trained .h5 model and evaluates it on the test dataset,
printing classification report, confusion matrix, and ROC AUC.

Usage:
    python ml/evaluate.py --model resnet50
    python ml/evaluate.py --model mobilenetv2
"""
import os
import sys
import argparse
import logging

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

TEST_DIR   = os.path.join('DATASET', 'test')
MODEL_DIR  = 'saved_models'
IMG_HEIGHT = 224
IMG_WIDTH  = 224
BATCH_SIZE = 32
CLASSES    = ['NORMAL', 'PNEUMONIA']


def parse_args():
    parser = argparse.ArgumentParser(description='Evaluate a trained pneumonia model.')
    parser.add_argument('--model', default='resnet50',
                        choices=['resnet50', 'mobilenetv2', 'custom_cnn'],
                        help='Model name to evaluate')
    return parser.parse_args()


def main():
    args = parse_args()
    model_path = os.path.join(MODEL_DIR, f'{args.model}.h5')

    if not os.path.isfile(model_path):
        logger.error('Model not found: %s', model_path)
        sys.exit(1)
    if not os.path.isdir(TEST_DIR):
        logger.error('Test dataset not found: %s', TEST_DIR)
        sys.exit(1)

    import tensorflow as tf
    from tensorflow.keras.preprocessing.image import ImageDataGenerator
    from sklearn.metrics import (
        classification_report, confusion_matrix,
        roc_auc_score, roc_curve, cohen_kappa_score,
    )

    logger.info('Loading model: %s', model_path)
    model = tf.keras.models.load_model(model_path)

    datagen = ImageDataGenerator(rescale=1.0 / 255)
    test_gen = datagen.flow_from_directory(
        TEST_DIR,
        target_size=(IMG_HEIGHT, IMG_WIDTH),
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        classes=CLASSES,
        shuffle=False,
    )

    logger.info('Running inference on %d images…', test_gen.samples)
    preds = model.predict(test_gen, verbose=1)
    y_scores = preds[:, 1]              # probability of PNEUMONIA
    y_pred   = np.argmax(preds, axis=1)
    y_true   = test_gen.classes

    # ── Metrics ────────────────────────────────────────────────
    print('\n' + '='*60)
    print(f'Model: {args.model.upper()}')
    print('='*60)
    print(classification_report(y_true, y_pred, target_names=CLASSES))

    cm = confusion_matrix(y_true, y_pred)
    print('Confusion Matrix:')
    print(cm)

    auc = roc_auc_score(y_true, y_scores)
    kappa = cohen_kappa_score(y_true, y_pred)
    print(f'\nROC AUC  : {auc:.4f} ({auc*100:.2f}%)')
    print(f'Cohen Kappa: {kappa:.4f} ({kappa*100:.2f}%)')

    # ── ROC Curve ──────────────────────────────────────────────
    fpr, tpr, _ = roc_curve(y_true, y_scores)
    plt.figure(figsize=(7, 5))
    plt.plot(fpr, tpr, color='royalblue', lw=2,
             label=f'ROC Curve (AUC = {auc:.3f})')
    plt.plot([0, 1], [0, 1], 'k--', lw=1)
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(f'ROC Curve — {args.model.upper()}')
    plt.legend(loc='lower right')
    plt.grid(True, alpha=0.3)
    out = os.path.join(MODEL_DIR, 'plots', f'{args.model}_roc.png')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    plt.savefig(out, dpi=120)
    plt.close()
    logger.info('ROC curve saved: %s', out)


if __name__ == '__main__':
    main()
