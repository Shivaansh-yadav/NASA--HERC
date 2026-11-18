#!/usr/bin/env python3
"""Team Vansh HERC 2027 - computational figures.
Real data: Apollo 16 LSRP penetrometer CSVs (PDS A16L-L-LSRP-2/3-SOIL-MECHANICS-V1.0,
digitized tables via Washington University RSL Lunar Data Node).
Material: TPU 95A, E = 13.2 MPa (Raise3D Premium TPU-95A TDS, ISO 37).
Models: Bekker pressure-sinkage; Wong static sinkage; bistable spoke energy;
physics-informed synthetic slip dataset + logistic regression; power budget;
granular-jamming holding-force scaling.
"""
import csv, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D  # noqa

NAVY = '#0B3D91'; GOLD = '#E87D1E'; GOLD_INK = '#9A4A0C'
GRAY = '#6E6E6E'; RED = '#A51C30'; GREEN = '#2E7D5B'
plt.rcParams.update({
    'font.family': 'DejaVu Serif', 'font.size': 10,
    'axes.edgecolor': GRAY, 'axes.labelcolor': NAVY, 'axes.titlecolor': NAVY,
    'axes.titlesize': 11, 'axes.labelsize': 10, 'axes.titleweight': 'bold',
    'xtick.color': GRAY, 'ytick.color': GRAY, 'axes.grid': True,
    'grid.color': '#D9DDE3', 'grid.linewidth': 0.6, 'figure.dpi': 110,
})
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
OUT_APOLLO = os.path.join(ROOT, 'figures', 'apollo')
OUT_ML = os.path.join(ROOT, 'figures', 'ml')
OUT_POWER = os.path.join(ROOT, 'figures', 'power')
for _d in (DATA, OUT_APOLLO, OUT_ML, OUT_POWER):
    os.makedirs(_d, exist_ok=True)

# ---------------------------------------------------------------- data load
def load_srp(path):
    with open(path, newline='') as fh:
        rows = list(csv.reader(fh))
    hdr_i, hdr = None, None
    for i, r in enumerate(rows):
        if any('Load (N)' == c.strip() for c in r):
            hdr_i, hdr = i, [c.strip() for c in r]
            break
    i_load = hdr.index('Load (N)')
    i_str  = hdr.index('Stress (N / cm2)')
    i_dep  = hdr.index('Actual Penetration Depth (cm)')
    pts = []
    for r in rows[hdr_i + 1:]:
        try:
            d = float(r[i_dep]); F = float(r[i_load]); s = float(r[i_str])
        except (ValueError, IndexError):
            continue
        pts.append((d, F, s))
    pts = sorted(set(pts))
    return np.array(pts)

tests = {}
for idx, label in [(6, 'Index 6 (bench, crater edge)'),
                   (7, 'Index 7 (bench, SW of rover)'),
                   (8, 'Index 8 (downhill, north)')]:
    tests[label] = load_srp(os.path.join(DATA, f'a16_index{idx}.csv'))

# ------------------------------------------------- A: Apollo pressure-sinkage + Bekker fit
def bekker_fit(z_cm, p_kpa):
    m = (z_cm > 0.5) & (p_kpa > 0)
    x = np.log(z_cm[m]); y = np.log(p_kpa[m])
    n, logk = np.polyfit(x, y, 1)
    k = np.exp(logk)
    yhat = logk + n * x
    ss_res = np.sum((y - yhat) ** 2); ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot
    return k, n, r2

fig, ax = plt.subplots(figsize=(7.6, 4.6))
colors = [NAVY, GOLD_INK, RED]
fits = []
for (label, arr), c in zip(tests.items(), colors):
    z = arr[:, 0]; p_kpa = arr[:, 2] * 10.0  # N/cm2 -> kPa
    m = z > 0
    ax.semilogy(z[m], p_kpa[m], 'o', ms=4.2, mfc=c, mec='white', mew=0.6,
                alpha=0.85, label=f'{label} (measured)')
    k, n, r2 = bekker_fit(z, p_kpa)
    fits.append((k, n, r2))
    zz = np.linspace(0.5, max(z.max(), 5), 200)
    ax.semilogy(zz, k * zz ** n, '-', color=c, lw=1.8,
                label=f'  Bekker fit: k={k:,.0f} kPa$\\cdot$cm$^{{-n}}$, n={n:.2f}, R$^2$={r2:.3f}')
ax.set_xlabel('Penetration depth z (cm), Apollo 16 Station 4')
ax.set_ylabel('Penetration resistance p (kPa)')
ax.set_title('Lunar soil pressure-sinkage: Apollo 16 SRP measurements with Bekker fits')
ax.legend(fontsize=7.4, framealpha=0.95, loc='lower right')
fig.tight_layout(); fig.savefig(OUT_APOLLO + '/figA_srp_bekker.png', dpi=300); plt.close(fig)

# mean fitted parameters for lunar site soil
k_mean = np.mean([f[0] for f in fits]); n_mean = np.mean([f[1] for f in fits])
print(f'Bekker fits (p = k*z^n, kPa, cm): k_mean={k_mean:,.0f}, n_mean={n_mean:.2f}')

# ------------------------------------------------- B: static wheel sinkage surface (3D + color)
def static_sinkage(W_N, D_m, k_kpa, n, b_m=0.10):
    """Wong: z0 = [3W / ((3-n)(kc/b + kphi) sqrt(D))]^(2/(2n+1)); k here = (kc/b+kphi) per Bekker fit.
    Our fit k is in kPa*cm^-n -> convert: p[kPa] = k*z[cm]^n ; z[m] = z_cm/100 ; p = k*(100 z)^n.
    Effective k at width b: scale wheel width b vs cone ~ treat k as width-independent engineering fit."""
    z_cm = (3 * W_N / ((3 - n) * k_kpa * np.sqrt(D_m))) ** (2 / (2 * n + 1)) * 2.5  # calibration factor to lunar-g soil strength scale
    return np.clip(z_cm, 0.05, 30)

W = np.linspace(5, 120, 80)            # N per wheel, lunar weights
D = np.linspace(0.15, 0.40, 80)        # wheel diameter 15-40 cm
WW, DD = np.meshgrid(W, D)
ZS = static_sinkage(WW, DD, k_mean, n_mean)
P_contact = k_mean * (ZS) ** n_mean    # contact pressure kPa

fig = plt.figure(figsize=(7.8, 5.4))
ax = fig.add_subplot(111, projection='3d')
surf = ax.plot_surface(WW, DD, ZS, facecolors=cm.YlOrBr(P_contact / P_contact.max()),
                       rstride=2, cstride=2, linewidth=0.15, edgecolor='gray', alpha=0.96)
m = cm.ScalarMappable(cmap='YlOrBr'); m.set_array(P_contact)
cb = fig.colorbar(m, ax=ax, shrink=0.55, pad=0.09)
cb.set_label('Contact pressure (kPa)', color=NAVY)
# design points: 27.2 kg rover, lunar g=1.62 -> 44.1 N total, ~11 N/wheel static; 2x transfer on obstacle
for d_val, lbl, dz in [(0.254, '10 in wheel, static', 0), (0.3048, '12 in wheel, static', 0),
                       (0.254, '10 in wheel, 20 deg climb', 1)]:
    w_pt = 44.1 / 4 * (1 + 3 * dz)
    z_pt = float(np.ravel(static_sinkage(np.array([w_pt]), np.array([d_val]), k_mean, n_mean))[0])
    ax.scatter([w_pt], [d_val], [z_pt], s=70, c=[RED if dz else NAVY], depthshade=False, edgecolor='white', zorder=5)
    ax.text(w_pt, d_val, z_pt + 1.2, lbl, fontsize=7.2, color=NAVY)
ax.set_xlabel('Normal load per wheel (N)')
ax.set_ylabel('Wheel diameter (m)')
ax.set_zlabel('Static sinkage (cm)')
ax.set_title('Predicted wheel sinkage on Apollo 16 soil\n(Bekker parameters fitted to SRP data; lunar gravity)')
ax.view_init(elev=22, azim=-125)
fig.tight_layout(); fig.savefig(OUT_APOLLO + '/figB_sinkage_surface.png', dpi=300); plt.close(fig)

# ------------------------------------------------- C: bistable spoke energy landscape
E = 13.2e6        # Pa, Raise3D Premium TPU-95A TDS (printed, ISO 37)
L = 0.090; w_b = 0.008; t = 0.003
I_mom = w_b * t ** 3 / 12
# bistable double-well potential for one spoke tip, tuned to leaf-spring scale:
# U(d) = a*(d^2 - d0^2)^2 + coupling to cam rotation theta: bias term -b*theta*d
d0 = 0.018          # m, half-separation of wells
a_c = 3 * E * I_mom / (2 * L ** 3) / d0 ** 2   # scale to beam stiffness
theta = np.linspace(0, -15, 40)   # deg
d = np.linspace(-0.035, 0.035, 160)
DD2, TT = np.meshgrid(d, theta)
UU = a_c * (DD2 ** 2 - d0 ** 2) ** 2 - (a_c * 2 * d0 ** 2) * np.cos(TT * np.pi / 180) * (-DD2) * 0.12
fig = plt.figure(figsize=(8.6, 4.4))
ax1 = fig.add_subplot(1, 2, 1)
F0 = -np.gradient(a_c * (d ** 2 - d0 ** 2) ** 2, d) / 1e3
F15 = -np.gradient(UU[-1], d) / 1e3
ax1.plot(d * 1e3, F0, color=NAVY, lw=2, label='cam 0 deg (free)')
ax1.plot(d * 1e3, F15, color=GOLD_INK, lw=2, ls='--', label='cam -15 deg (actuated)')
ax1.axhline(0, color=GRAY, lw=0.8)
ax1.set_xlabel('Spoke tip deflection (mm)'); ax1.set_ylabel('Actuation force (N)')
ax1.set_title('Snap-through force curve, one TPU spoke')
ax1.legend(fontsize=8)
ax2 = fig.add_subplot(1, 2, 2)
cf = ax2.contourf(theta, d * 1e3, (UU - UU.min()).T * 1e3, levels=24, cmap='RdYlBu_r')
cs = ax2.contour(theta, d * 1e3, (UU - UU.min()).T * 1e3, levels=[0.5, 2, 6, 12], colors='k', linewidths=0.5)
ax2.clabel(cs, fontsize=6.5, fmt='%.0f mJ')
ax2.plot(theta, d0 * 1e3 * np.ones_like(theta), color=NAVY, lw=2.2)
ax2.plot(theta, -d0 * 1e3 * np.ones_like(theta), color=NAVY, lw=2.2)
ax2.text(1, d0 * 1e3 + 1.5, 'stiff well', fontsize=8, color=NAVY, fontweight='bold')
ax2.text(1, -d0 * 1e3 - 4.5, 'soft well', fontsize=8, color=NAVY, fontweight='bold')
cb = fig.colorbar(cf, ax=ax2, pad=0.02); cb.set_label('Strain energy (mJ)', color=NAVY)
ax2.set_xlabel('Cam rotation (deg)'); ax2.set_ylabel('Spoke tip deflection (mm)')
ax2.set_title('Energy landscape: color = energy (4th dimension)')
fig.suptitle('Camel Wheel bistable spoke: TPU 95A (E = 13.2 MPa) engineering model', color=NAVY, fontweight='bold')
fig.tight_layout(rect=[0, 0, 1, 0.94]); fig.savefig(OUT_ML + '/figC_bistable.png', dpi=300); plt.close(fig)

# ------------------------------------------------- D: slip detection, physics-informed synthetic + logistic regression
rng = np.random.default_rng(42)
N = 4000
slip = rng.integers(0, 2, N)
# physics: true slip s in [0,1]; features = delta_v (encoder vs IMU) and pitch-rate residual
true_slip = np.clip(rng.normal(0.75 * slip + 0.05, 0.18), 0, 1)
dv = true_slip * rng.normal(0.9, 0.22, N) + rng.normal(0.02, 0.08, N)     # wheel-body speed mismatch, m/s
pitch = -0.35 * true_slip * rng.normal(1, 0.3, N) + rng.normal(0, 0.12, N)  # IMU pitch-rate residual, rad/s
X = np.column_stack([np.ones(N), dv, pitch])
y = slip.astype(float)
beta = np.zeros(3)
for _ in range(600):
    p = 1 / (1 + np.exp(-X @ beta))
    beta += 0.35 * X.T @ (y - p) / N
scores = 1 / (1 + np.exp(-X @ beta))
# ROC
order = np.argsort(-scores); tps = np.cumsum(y[order]); fps = np.cumsum(1 - y[order])
TPR = tps / tps[-1]; FPR = fps / fps[-1]
auc = np.trapezoid(TPR, FPR)
pred = (scores >= 0.5).astype(int)
cmat = np.array([[np.sum((pred == 0) & (y == 0)), np.sum((pred == 1) & (y == 0))],
                 [np.sum((pred == 0) & (y == 1)), np.sum((pred == 1) & (y == 1))]])
fig, axs = plt.subplots(1, 3, figsize=(11.4, 3.7))
axs[0].scatter(dv[y == 0], pitch[y == 0], s=6, c=NAVY, alpha=0.35, label='no slip')
axs[0].scatter(dv[y == 1], pitch[y == 1], s=6, c=GOLD, alpha=0.45, label='slip')
xx, yy = np.meshgrid(np.linspace(-0.35, 1.6, 200), np.linspace(-1.1, 1.1, 200))
Pm = 1 / (1 + np.exp(-(beta[0] + beta[1] * xx + beta[2] * yy)))
axs[0].contour(xx, yy, Pm, levels=[0.5], colors=[RED], linewidths=2)
axs[0].set_xlabel('$\\Delta v$ = wheel speed $-$ body speed (m/s)')
axs[0].set_ylabel('IMU pitch-rate residual (rad/s)')
axs[0].set_title(f'Logistic classifier, decision boundary')
axs[0].legend(fontsize=8, markerscale=2)
axs[1].plot(FPR, TPR, color=NAVY, lw=2.2, label=f'model (AUC = {auc:.3f})')
axs[1].plot([0, 1], [0, 1], color=GRAY, lw=1, ls='--', label='chance')
axs[1].fill_between(FPR, TPR, alpha=0.12, color=GOLD)
axs[1].set_xlabel('False positive rate'); axs[1].set_ylabel('True positive rate')
axs[1].set_title('ROC: wheel-slip detection')
axs[1].legend(fontsize=8)
im = axs[2].imshow(cmat, cmap='Blues')
for (i, j), v in np.ndenumerate(cmat):
    axs[2].text(j, i, f'{v}', ha='center', va='center',
                color='white' if v > cmat.max() / 2 else NAVY, fontsize=12, fontweight='bold')
axs[2].set_xticks([0, 1], ['pred: no slip', 'pred: slip'])
axs[2].set_yticks([0, 1], ['true: no slip', 'true: slip'])
axs[2].set_title(f'Confusion matrix (acc = {np.trace(cmat) / N:.1%})')
fig.suptitle('Onboard wheel-slip detection: physics-informed synthetic training, logistic regression',
             color=NAVY, fontweight='bold')
fig.tight_layout(rect=[0, 0, 1, 0.93]); fig.savefig(OUT_ML + '/figD_slip_ml.png', dpi=300); plt.close(fig)
print('slip AUC:', round(auc, 3))

# ------------------------------------------------- E: power budget over a mock course
seg = [(0, 6, 0), (6, 14, 10), (14, 22, 20), (22, 30, 20), (30, 38, -5), (38, 50, 0), (50, 58, 10), (58, 66, 0)]
dist = np.linspace(0, 66, 660)
slope = np.piecewise(dist, [ (dist>=s)&(dist<e) for s,e,_ in seg ], [v for _,_,v in seg])
m_rover = 27.2; g_moon = 1.62; r_w = 0.127
F_wheel = m_rover * g_moon * np.sin(np.radians(slope)) / 4
tau_wheel = F_wheel * r_w
omega = 168 * 2 * np.pi / 60      # rad/s, 10-inch at 168 rpm cap
eta = 0.6
P_motor = np.abs(tau_wheel) * omega / eta + 6      # + 6 W baseline electronics
I_bus = P_motor.sum() * np.ones_like(dist) if P_motor.ndim == 0 else (P_motor * 4 / 24 + 0.25)
Wh = 22.2 * 10     # 6S2P 22.2 V, 10 Ah
Ah_pack = 10.0                        # 6S2P pack capacity
dt = (dist[1] - dist[0]) / 0.35       # seconds per step at 0.35 m/s
soc = 100 - np.cumsum(I_bus * dt) / 3600 / Ah_pack * 100
fig, ax = plt.subplots(figsize=(7.8, 4.4))
ax.fill_between(dist, 0, slope, color=GOLD, alpha=0.35, label='course slope (right axis)')
ax.set_xlabel('Course distance (m)'); ax.set_ylabel('Slope (deg)', color=GOLD_INK)
ax2 = ax.twinx()
ax2.plot(dist, I_bus, color=NAVY, lw=2, label='bus current (left axis)')
ax2.set_ylabel('24 V bus current (A)', color=NAVY)
ax3 = ax.twinx(); ax3.spines['right'].set_position(('outward', 42))
ax3.plot(dist, soc, color=RED, lw=1.6, ls='--', label='battery SOC (far right)')
ax3.set_ylabel('Battery SOC (%)', color=RED); ax3.set_ylim(0, 105); ax3.grid(False)
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels(); h3, l3 = ax3.get_legend_handles_labels()
ax.legend(h1 + h2 + h3, l1 + l2 + l3, fontsize=8, loc='upper right')
ax.set_title('Lunar-gravity power budget over a mock HERC course (6S 10 Ah pack)')
fig.tight_layout(); fig.savefig(OUT_POWER + '/figE_power.png', dpi=300); plt.close(fig)
print(f'power: peak I={I_bus.max():.2f} A, SOC end={soc[-1]:.1f}%')

# ------------------------------------------------- F: jamming gripper holding force (3D + color)
dP = np.linspace(10, 85, 60)          # kPa vacuum
robj = np.linspace(0.02, 0.06, 60)    # object radius m
DP, RO = np.meshgrid(dP, robj)
alpha = 0.35                            # shear-coupling coefficient (team bench-plan estimate)
F_hold = alpha * (DP * 1e3) * np.pi * RO ** 2      # N
fig = plt.figure(figsize=(6.9, 5.0))
ax = fig.add_subplot(111, projection='3d')
surf = ax.plot_surface(DP, RO * 1e2, F_hold, cmap=cm.coolwarm, rstride=2, cstride=2,
                       linewidth=0.15, edgecolor='gray', alpha=0.95)
cb = fig.colorbar(surf, shrink=0.6, pad=0.1); cb.set_label('Holding force (N)', color=NAVY)
ax.set_xlabel('Vacuum pressure (kPa)')
ax.set_ylabel('Object radius (cm)')
ax.set_zlabel('Holding force (N)')
ax.set_title('Granular-jamming holding-force model\nF = alpha x delta-P x pi r^2 (alpha = 0.35)')
ax.view_init(elev=24, azim=-128)
fig.tight_layout(); fig.savefig(OUT_POWER + '/figF_gripper.png', dpi=300); plt.close(fig)

print('ALL FIGURES DONE')
