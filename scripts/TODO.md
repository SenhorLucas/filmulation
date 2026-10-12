## Open threads on the film sim

**mask_frac reparameterization.** Replace `dmax0/1/2` with a fitted fraction bounded 0–1, and supply the density ratio from measurement:
```python
ratio = mask_frac * (dmax_measured / dye_peak_midscale)
```
Same degrees of freedom, dimensionally coherent, and `min=0.0` lets the fit conclude a layer is unmasked — which yellow layers usually are, and the current `cpl_amp4` floor at 0.05 forbids.

**Shelf profiles instead of Gaussians in the dmin model.** Your suspicion about scattering is plausible: `scat400` bounded at 0.62–1.0 is an enormous amount of Rayleigh loss, and it's likely absorbing shape that the symmetric Gaussians can't produce. An azo mask's absorption has a steep long-λ edge and a broad short-λ plateau, which is exactly what a λ⁻⁴ term would be recruited to fake. An erf-based shelf — and note the module already has `low_pass_filter`/`high_pass_filter` doing precisely this, from the abandoned filter models — would give that shape directly. Test: refit with shelves and see whether `scat400` drops off its lower bound.

**Amplitude floors.** Four of five `cpl_amp*` have `min=0.05`, so the fit cannot conclude an absorption is absent. Free them to zero.

**Convergence.** `max_nfev=500` against 32 parameters with a numerical Jacobian is ~15 iterations. Check `out.nfev` and `out.success`. The second smoothing spline in `shift_stretch` looks removable and is roughly half the per-evaluation cost.

**NaN asymmetry in `compute_densitometer_crosstalk_matrix`.** Numerator uses `nansum`, denominator doesn't mask — out-of-range wavelengths act as fully absorbing, inflating every density.

**`biases[0]` scales the simulation, not the residual.** Harmless at the default of 1, wrong at any other value.

**`balance_metameric_neutral` has no type guard**, and overwrites `density_midscale_neutral` with a scalar where `reconstruct_dye_density` wrote a three-element list.

**Gaussians in wavenumber rather than wavelength** — free asymmetry, no extra parameters. Lower priority than the shelf test, and partly redundant with it.

**Identifiability audit.** `report_fit(out, show_correl=True)`. Prime suspects: `cpl_amp1` vs `dye_amp1` (560nm Gaussian under magenta's peak), `cpl_amp0` vs `dye_amp2` (435nm under yellow's peak), and `base` vs `scat400`.
