import sys
import os

OPENFACE_ROOT = os.path.abspath(os.path.join(__file__,  '../../openface'))
sys.path.append(OPENFACE_ROOT)

import openface


IMAGE_SIZE = 96
ALIGN = openface.AlignDlib(
    OPENFACE_ROOT + "/models/dlib/shape_predictor_68_face_landmarks.dat"
)
NET = None


def hash_face(image, bb=None, alignedFace=None):
    global NET
    if NET is None:
        NET = openface.TorchNeuralNet(
            OPENFACE_ROOT + "/models/openface/nn4.small2.v1.t7",
            imgDim=IMAGE_SIZE,
            cuda=False
        )
    if alignedFace is not None:
        return NET.forward(alignedFace)

    if bb is not None:
        alignedFace = ALIGN.align(IMAGE_SIZE, image, bb,
            landmarkIndices=openface.AlignDlib.OUTER_EYES_AND_NOSE)
        if alignedFace is None:
            return None
        return hash_face(image, bb=bb, alignedFace=alignedFace)

    bb = ALIGN.getLargestFaceBoundingBox(image)
    if bb is None:
        return None
    return hash_face(image, bb=bb)
