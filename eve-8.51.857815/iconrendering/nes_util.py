#Embedded file name: iconrendering\nes_util.py
"""
Appropriated from a macro called AlphaCreation in the PaperDoll macro shelf.
"""
import trinity

def CreateAlpha(outPath, sourcePaths, backgroundPath = None):
    """Creates an image with alpha from 3 images with prime color backgrounds, and saves it.
    outPath: The output path to save to.
    sourcePaths: A 3-tuple with the paths for the red, green and blue images.
    backgroundPath: Optional image path to use as the background.
    """
    rBmp = trinity.Tr2HostBitmap()
    rBmp.CreateFromFile(sourcePaths[0])
    gBmp = trinity.Tr2HostBitmap()
    gBmp.CreateFromFile(sourcePaths[1])
    bBmp = trinity.Tr2HostBitmap()
    bBmp.CreateFromFile(sourcePaths[2])
    outputBmp = trinity.Tr2HostBitmap(rBmp.width, rBmp.height, 1, trinity.PIXEL_FORMAT.B8G8R8A8_UNORM)
    rTriCol = trinity.TriColor()
    gTriCol = trinity.TriColor()
    bTriCol = trinity.TriColor()
    BLACKALPHA0 = 0
    HUERANGE = 60
    REDHUE = 0
    GREENHUE = 120
    BLUEHUE = 240
    addBackground = not backgroundPath == None
    if addBackground:
        myBg = trinity.Tr2HostBitmap()
        myBg.CreateFromFile(backgroundPath)
        bgTriCol = trinity.TriColor()
    for px in range(rBmp.width):
        for py in range(rBmp.height):
            if addBackground:
                bgPixelValue = myBg.GetPixel(px, py)
                bgTriCol.FromInt(bgPixelValue)
            rPixelValue = rBmp.GetPixel(px, py)
            gPixelValue = gBmp.GetPixel(px, py)
            bPixelValue = bBmp.GetPixel(px, py)
            rTriCol.FromInt(rPixelValue)
            gTriCol.FromInt(gPixelValue)
            bTriCol.FromInt(bPixelValue)
            rh, rs, rv = rTriCol.GetHSV()
            gh, gs, gv = gTriCol.GetHSV()
            bh, bs, bv = bTriCol.GetHSV()
            if (rTriCol.r, rTriCol.g, rTriCol.b) == (1.0, 0.0, 0.0) and (gTriCol.r, gTriCol.g, gTriCol.b) == (0.0, 1.0, 0.0) and (bTriCol.r, bTriCol.g, bTriCol.b) == (0.0, 0.0, 1.0):
                if addBackground:
                    outputBmp.SetPixel(px, py, bgTriCol.AsInt())
                else:
                    outputBmp.SetPixel(px, py, BLACKALPHA0)
            elif GREENHUE - HUERANGE < gh < GREENHUE + HUERANGE and (360 - HUERANGE < rh <= 360 or REDHUE <= rh < REDHUE + HUERANGE) and BLUEHUE - HUERANGE < bh < BLUEHUE + HUERANGE:
                if gv == 1.0 and bv == 1.0 and rv == 1.0:
                    gTriCol.SetRGB(gTriCol.r, rTriCol.g, gTriCol.b, 1.0)
                    ch, cs, cv = gTriCol.GetHSV()
                    gTriCol.a = cv
                    gTriCol.r = min(1.0, gTriCol.r * 1.0 / cv)
                    gTriCol.g = min(1.0, gTriCol.g * 1.0 / cv)
                    gTriCol.b = min(1.0, gTriCol.b * 1.0 / cv)
                    outputBmp.SetPixel(px, py, gTriCol.AsInt())
                elif addBackground:
                    alpha = 1.0 - gv
                    invAlpha = 1 - alpha
                    redColor = gTriCol.r * alpha + bgTriCol.r * invAlpha
                    greenColor = rTriCol.g * alpha + bgTriCol.g * invAlpha
                    blueColor = gTriCol.b * alpha + bgTriCol.b * invAlpha
                    newAlpha = gTriCol.a * alpha + bgTriCol.a * invAlpha
                    gTriCol.SetRGB(redColor, greenColor, blueColor, newAlpha)
                else:
                    gTriCol.SetRGB(gTriCol.r, rTriCol.g, gTriCol.b, 1.0 - gv)
                    outputBmp.SetPixel(px, py, gTriCol.AsInt())
            else:
                gTriCol.a = 1.0
                outputBmp.SetPixel(px, py, gTriCol.AsInt())

    outputBmp.Save(outPath)
