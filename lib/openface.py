from tornado import gen
import sys
import os
import logging 

OPENFACE_ROOT = os.path.abspath(os.path.join(__file__,  '../../openface'))
sys.path.append(OPENFACE_ROOT)

import openface


FORMAT = '[%(levelname)1.1s %(asctime)s %(name)s:%(lineno)d] %(message)s'
logger = logging.getLogger("lib.openface")

IMAGE_SIZE = 96
ALIGN = openface.AlignDlib(
    OPENFACE_ROOT + "/models/dlib/shape_predictor_68_face_landmarks.dat"
)
NET = None


@gen.coroutine
def hash_face(image, bb=None, alignedFace=None):
    global NET
    if NET is None:
        logging.debug("Loading openface network")
        NET = openface.TorchNeuralNet(
            OPENFACE_ROOT + "/models/openface/nn4.small2.v1.t7",
            imgDim=IMAGE_SIZE,
            cuda=False
        )

    # this function can take a while to run, so we defer to the ioloop in face
    # there are other things that need to be taken care of.  Since this
    # function is also recursive, having this yield before any work happens
    # means that we will defer to the ioloop between each step.
    yield gen.sleep(0)

    if alignedFace is not None:
        logging.debug("Hashing face")
        return NET.forward(alignedFace)

    if bb is not None:
        alignedFace = ALIGN.align(IMAGE_SIZE, image, bb,
            landmarkIndices=openface.AlignDlib.OUTER_EYES_AND_NOSE)
        if alignedFace is None:
            return None
        return (yield hash_face(image, bb=bb, alignedFace=alignedFace))

    bb = ALIGN.getLargestFaceBoundingBox(image)
    if bb is None:
        return None
    return (yield hash_face(image, bb=bb))
