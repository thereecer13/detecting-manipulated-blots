"""region_match.py FIG_A x0,y0,x1,y1 FIG_B x0,y0,x1,y1 OUT.png : SIFT match of two regions (also tries mirror); writes A warped onto B beside B."""
import sys, cv2, numpy as np
fa, ba, fb, bb, out = sys.argv[1:6]; ba = list(map(int, ba.split(','))); bb = list(map(int, bb.split(',')))
A = cv2.imread(fa)[ba[1]:ba[3], ba[0]:ba[2]]; B = cv2.imread(fb)[bb[1]:bb[3], bb[0]:bb[2]]
s = cv2.SIFT_create(contrastThreshold=0.02); best = None
for mir in (0, 1):
    a = A[:, ::-1].copy() if mir else A
    ka, da = s.detectAndCompute(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), None); kb, db = s.detectAndCompute(cv2.cvtColor(B, cv2.COLOR_BGR2GRAY), None)
    if da is None or db is None: continue
    m = [x for x, y in cv2.BFMatcher().knnMatch(da, db, k=2) if x.distance < 0.75 * y.distance]
    if len(m) < 4: continue
    pa = np.float32([ka[x.queryIdx].pt for x in m]); pb = np.float32([kb[x.trainIdx].pt for x in m])
    M, inl = cv2.estimateAffinePartial2D(pa, pb, ransacReprojThreshold=3)
    if M is None: continue
    n = int(inl.sum())
    if best is None or n > best[0]: best = (n, len(m), mir, M, a)
n, tot, mir, M, a = best; sc = float(np.hypot(M[0, 0], M[1, 0])); rot = float(np.degrees(np.arctan2(M[1, 0], M[0, 0])))
W = cv2.warpAffine(a, M, (B.shape[1], B.shape[0]), borderValue=(255, 255, 255))
mask = cv2.warpAffine(np.ones(a.shape[:2], np.uint8), M, (B.shape[1], B.shape[0])) > 0
g1 = cv2.cvtColor(W, cv2.COLOR_BGR2GRAY).astype(float)[mask]; g2 = cv2.cvtColor(B, cv2.COLOR_BGR2GRAY).astype(float)[mask]
ncc = float(np.corrcoef(g1, g2)[0, 1]) if mask.sum() > 50 else -1
print(f"inliers {n}/{tot} mirrored {mir} scale {sc:.3f} rot {rot:.1f} shift {M[0,2]:.0f},{M[1,2]:.0f} overlap {mask.mean():.2f} ncc {ncc:.3f}")
f = max(1, 500 // max(B.shape[:2])); o = np.hstack([W, np.zeros((B.shape[0], 3, 3), np.uint8), B]); cv2.imwrite(out, cv2.resize(o, None, fx=f, fy=f, interpolation=cv2.INTER_CUBIC))
