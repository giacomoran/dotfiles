# Stub — kaldialign is only used for WER metrics during NeMo training.
# Inference (ASRModel.transcribe) never calls any of these.

def align(*args, **kwargs):
    raise NotImplementedError("kaldialign stub: only inference is supported on this platform")

def edit_distance(*args, **kwargs):
    raise NotImplementedError("kaldialign stub: only inference is supported on this platform")
