"""
ML Inference Module — DenseNet121 Pneumonia Detector.

Loads model weights at first use and caches the model in memory.
Architecture is rebuilt locally in TF 2.13 to avoid Keras 3 version incompatibilities.
"""
import os
import logging
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

CLASSES   = ['NORMAL', 'PNEUMONIA']
IMG_SIZE  = (224, 224)
THRESHOLD = 0.89   # Optimal F1 threshold found during evaluation

_model_cache: dict = {}

PRECAUTIONS = {
    'PNEUMONIA': (
        "Pneumonia detected. Recommended actions:\n"
        "1. Consult a doctor or pulmonologist immediately.\n"
        "2. Rest and stay well-hydrated.\n"
        "3. Take prescribed antibiotics or antivirals as directed.\n"
        "4. Monitor oxygen saturation levels.\n"
        "5. Avoid smoking and second-hand smoke.\n"
        "6. Follow up with a chest X-ray after treatment.\n"
        "Note: This AI result is a screening aid and does NOT replace a "
        "professional medical diagnosis."
    ),
    'NORMAL': (
        "No pneumonia detected. The chest X-ray appears normal.\n"
        "Continue regular health check-ups and maintain a healthy lifestyle.\n"
        "Note: This AI result is a screening aid and does NOT replace a "
        "professional medical diagnosis."
    ),
}


def _build_densenet121():
    """Rebuild ResNet50 + custom head in float32 using local TF 2.x."""
    import tensorflow as tf

    base = tf.keras.applications.ResNet50(
        weights=None,
        include_top=False,
        input_shape=(224, 224, 3),
    )
    base.trainable = False

    x = tf.keras.layers.GlobalAveragePooling2D()(base.output)

    x = tf.keras.layers.Dense(128)(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Activation('relu')(x)
    x = tf.keras.layers.Dropout(0.4)(x)

    output = tf.keras.layers.Dense(2, activation='softmax', dtype='float32')(x)

    return tf.keras.Model(inputs=base.input, outputs=output)


def _custom_objects():
    """Return custom objects that patch Keras version incompatibilities."""
    import tensorflow as tf

    class _CompatInputLayer(tf.keras.layers.InputLayer):
        def __init__(self, **kwargs):
            kwargs.pop('optional', None)
            batch_shape = kwargs.pop('batch_shape', None)
            if batch_shape is not None and 'input_shape' not in kwargs:
                kwargs['input_shape'] = tuple(batch_shape[1:])
            super().__init__(**kwargs)

    class _DTypePolicy:
        def __init__(self, name='float32'):
            self.name = name
        @classmethod
        def from_config(cls, config):
            return cls(config.get('name', 'float32'))
        def get_config(self):
            return {'name': self.name}

    return {
        'InputLayer':   _CompatInputLayer,
        'DTypePolicy':  _DTypePolicy,
    }


def load_model(model_name: str, model_dir: str):
    """
    Load model and cache it.
    Priority: .npy numpy weights (most compatible) → .weights.h5 → .h5 → .keras
    """
    if model_name in _model_cache:
        return _model_cache[model_name]

    import tensorflow as tf
    tf.keras.mixed_precision.set_global_policy('float32')

    wh5_path     = os.path.join(model_dir, f'{model_name}_weights.h5')
    pkl_path     = os.path.join(model_dir, f'{model_name}.pkl')
    npy_path     = os.path.join(model_dir, f'{model_name}.npy')
    weights_path = os.path.join(model_dir, f'{model_name}.weights.h5')
    h5_path      = os.path.join(model_dir, f'{model_name}.h5')
    keras_path   = os.path.join(model_dir, f'{model_name}.keras')

    try:
        if os.path.isfile(wh5_path):
            logger.info('Loading %s from named h5 weights: %s', model_name, wh5_path)
            import h5py
            model = _build_densenet121()
            dummy = np.zeros((1, 224, 224, 3), dtype=np.float32)
            model.predict(dummy, verbose=0)
            loaded = 0
            with h5py.File(wh5_path, 'r') as f:
                if 'n_layers' in f.attrs:
                    # Pass 1: match by layer name
                    unmatched_local  = []
                    unmatched_h5     = []
                    matched_h5_names = set()
                    for layer in model.layers:
                        if not layer.get_weights():
                            continue
                        if layer.name in f:
                            n = int(f[layer.name].attrs['n'])
                            ws = [f[layer.name][f'w{i}'][:] for i in range(n)]
                            layer.set_weights(ws)
                            matched_h5_names.add(layer.name)
                            loaded += 1
                        else:
                            unmatched_local.append(layer)
                    # Pass 2: match leftover layers by weight shapes
                    for key in f.keys():
                        if key not in matched_h5_names:
                            n  = int(f[key].attrs['n'])
                            ws = [f[key][f'w{i}'][:] for i in range(n)]
                            shapes = tuple(w.shape for w in ws)
                            for layer in unmatched_local:
                                if tuple(w.shape for w in layer.get_weights()) == shapes:
                                    layer.set_weights(ws)
                                    unmatched_local.remove(layer)
                                    loaded += 1
                                    break
                else:
                    n = int(f.attrs['n_weights'])
                    weights = [f[f'weight_{i}'][:] for i in range(n)]
                    model.set_weights(weights)
                    loaded = n
            logger.info('Model %s loaded from named h5 weights (%d layers).', model_name, loaded)

        elif os.path.isfile(pkl_path):
            logger.info('Loading %s from pickle weights: %s', model_name, pkl_path)
            import pickle
            model = _build_densenet121()
            dummy = np.zeros((1, 224, 224, 3), dtype=np.float32)
            model.predict(dummy, verbose=0)
            with open(pkl_path, 'rb') as f:
                weights = pickle.load(f)
            model.set_weights(weights)
            logger.info('Model %s loaded from pickle successfully (%d arrays).', model_name, len(weights))

        elif os.path.isfile(npy_path):
            logger.info('Loading %s from numpy weights: %s', model_name, npy_path)
            model = _build_densenet121()
            dummy = np.zeros((1, 224, 224, 3), dtype=np.float32)
            model.predict(dummy, verbose=0)
            weights = np.load(npy_path, allow_pickle=True)
            model.set_weights(weights)
            logger.info('Model %s loaded from numpy weights successfully (%d arrays).', model_name, len(weights))

        elif os.path.isfile(weights_path):
            logger.info('Loading %s from weights: %s', model_name, weights_path)
            model = _build_densenet121()
            model.load_weights(weights_path, by_name=True, skip_mismatch=True)
            logger.info('Model %s loaded from weights successfully.', model_name)

        elif os.path.isfile(h5_path):
            logger.info('Loading %s from .h5: %s', model_name, h5_path)
            model = tf.keras.models.load_model(
                h5_path, compile=False, custom_objects=_custom_objects()
            )
            logger.info('Model %s loaded from .h5 successfully.', model_name)

        elif os.path.isfile(keras_path):
            logger.info('Loading %s from .keras: %s', model_name, keras_path)
            model = tf.keras.models.load_model(
                keras_path, compile=False, custom_objects=_custom_objects()
            )
            logger.info('Model %s loaded from .keras successfully.', model_name)

        else:
            raise FileNotFoundError(
                f"No model file found for '{model_name}' in '{model_dir}'.\n"
                f"Expected one of:\n  {wh5_path}\n  {pkl_path}\n  {npy_path}\n  {weights_path}\n  {h5_path}\n  {keras_path}"
            )

        _model_cache[model_name] = model
        return model

    except FileNotFoundError:
        raise
    except Exception as exc:
        raise RuntimeError(f'Failed to load model {model_name}: {exc}') from exc


def preprocess_image(image_path: str) -> np.ndarray:
    """
    Preprocess a chest X-ray for DenseNet121 inference.
    Applies DenseNet-specific normalization (ImageNet mean/std subtraction).
    Returns shape (1, 224, 224, 3) float32.
    """
    from tensorflow.keras.applications.resnet50 import preprocess_input

    img = Image.open(image_path).convert('RGB')
    img = img.resize(IMG_SIZE, Image.LANCZOS)
    arr = np.array(img, dtype=np.float32)
    arr = preprocess_input(arr)          # scales to DenseNet expected range
    arr = np.expand_dims(arr, axis=0)    # (1, 224, 224, 3)
    return arr


def predict(image_path: str, model_name: str, model_dir: str) -> dict:
    """
    Run DenseNet121 inference on a chest X-ray image.

    Returns dict with keys:
        result, confidence, model_used, precaution_text, raw_scores
    """
    model = load_model(model_name, model_dir)
    x     = preprocess_image(image_path)

    preds  = model.predict(x, verbose=0)   # shape (1, 2)
    scores = preds[0].tolist()              # [score_PNEUMONIA, score_NORMAL] (model trained with PNEUMONIA=0)

    pneumonia_score = float(scores[0])
    class_idx  = 1 if pneumonia_score >= THRESHOLD else 0
    result     = CLASSES[class_idx]
    confidence = pneumonia_score if class_idx == 1 else float(scores[1])

    logger.info(
        'Prediction: result=%s pneumonia_score=%.4f threshold=%.2f',
        result, pneumonia_score, THRESHOLD,
    )

    return {
        'result':          result,
        'confidence':      round(confidence, 4),
        'model_used':      model_name,
        'precaution_text': PRECAUTIONS[result],
        'raw_scores':      {'PNEUMONIA': round(float(scores[0]), 4), 'NORMAL': round(float(scores[1]), 4)},
    }


def warm_up(model_name: str, model_dir: str) -> None:
    """Pre-load the active model at startup so the first prediction is fast."""
    try:
        load_model(model_name, model_dir)
    except FileNotFoundError as exc:
        logger.warning('Model warm-up skipped — file not found:\n%s', exc)
    except Exception as exc:
        logger.warning('Model warm-up failed: %s', exc)
