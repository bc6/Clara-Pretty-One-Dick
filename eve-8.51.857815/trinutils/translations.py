#Embedded file name: trinutils\translations.py
import trinity

def GetTranslationValue(obj):
    """If object has a translation curve, use obj.translationCurve.value.
    Otherwise, return a zero TriVector."""
    try:
        return obj.translationCurve.value
    except AttributeError:
        return trinity.TriVectorCurve().value


def SetTranslationValue(obj, pos):
    """Sets the translationCurve value for an object,
    creating a curve if one does not already exist."""
    if hasattr(obj, 'translationCurve') and obj.translationCurve is None:
        obj.translationCurve = trinity.TriVectorCurve()
    obj.translationCurve.value = pos
