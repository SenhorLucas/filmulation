import numpy as np
from matplotlib import pyplot as plt
from scipy.ndimage import gaussian_filter

from filmulation.model.density_curves import interpolate_exposure_to_density
from filmulation.model.emulsion import Film
from filmulation.profiles.io import load_profile
from filmulation.utils.fast_interp import fast_interp
from filmulation.utils.spectral_upsampling import rgb_to_raw_hanatos2025
from opt_einsum import contract


neg = load_profile("kodak_vision3_250d_uc")
dens_curves = neg.data.density_curves
density_layers = neg.data.density_curves_layers
log_exp = neg.data.log_exposure
log_sens = neg.data.log_sensitivity
wl = neg.data.wavelengths


def compute_dir_couplers_matrix(amount_rgb=[0.7,0.7,0.5], layer_diffusion=1):
    M = np.eye(3)
    M_diffused = gaussian_filter(M, layer_diffusion, mode='constant', cval=0, axes=1)
    M_diffused /= np.sum(M_diffused, axis=1)[:, None]
    M = M_diffused *np.array(amount_rgb)[:, None]
    return M


def compute_density_curves_before_dir_couplers(density_curves, log_exposure, dir_couplers_matrix, high_exposure_couplers_shift=0.0):
    d_max = np.nanmax(density_curves, axis=0)
    dc_norm = density_curves/d_max
    dc_norm_shift = dc_norm + high_exposure_couplers_shift*dc_norm**2
    couplers_amount_curves = contract('jk, km->jm', dc_norm_shift, dir_couplers_matrix)
    # plt.plot(log_exposure, couplers_amount_curves)
    # plt.show()
    x0 = log_exposure[:,None] - couplers_amount_curves
    plt.plot(x0, couplers_amount_curves)
    plt.show()
    density_curves_corrected = np.zeros_like(density_curves)
    for i in np.arange(3):
        density_curves_corrected[:,i] = np.interp(log_exposure, x0[:,i], density_curves[:,i])
    return density_curves_corrected


def compute_exposure_correction_dir_couplers(log_raw, density_cmy, density_max, dir_couplers_matrix, diffusion_size_pixel, high_exposure_couplers_shift=0.0):
    norm_density = density_cmy/density_max
    norm_density += high_exposure_couplers_shift*norm_density**2
    log_raw_correction = contract('ijk, km->ijm', norm_density, dir_couplers_matrix)
    if diffusion_size_pixel>0:
        log_raw_correction = gaussian_filter(log_raw_correction, (diffusion_size_pixel, diffusion_size_pixel, 0))
        # log_raw_correction = fast_gaussian_filter(log_raw_correction, diffusion_size_pixel)
    log_raw_corrected = log_raw - log_raw_correction
    return log_raw_corrected


def _apply_density_correction_dir_couplers(film, density_cmy, log_raw, pixel_size_um):
    # compute inhibitors matrix with super a simplified diffusion model
    dir_couplers_amount_rgb = film.dir_couplers.amount * np.array(film.dir_couplers.ratio_rgb)

    M = compute_dir_couplers_matrix(dir_couplers_amount_rgb, film.dir_couplers.diffusion_interlayer)
    print(f'{M=}')

    # compute density curves before dir couplers
    # film.dir_couplers.high_exposure_shift = 0.1
    density_curves_0 = compute_density_curves_before_dir_couplers(film.density_curves, film.log_exposure, M, film.dir_couplers.high_exposure_shift)
    # compute exposure correction
    density_max = np.nanmax(film.density_curves, axis=0)
    diffusion_size_um = film.dir_couplers.diffusion_size_um
    diffusion_size_pixel = diffusion_size_um/pixel_size_um
    log_raw_0 = compute_exposure_correction_dir_couplers(log_raw, density_cmy, density_max, M,
                                                            diffusion_size_pixel, film.dir_couplers.high_exposure_shift)
    # interpolated with corrected curves
    density_cmy = interpolate_exposure_to_density(log_raw_0, density_curves_0, film.log_exposure, film.gamma_factor)
    return density_cmy


def process():
    # film exposure in camera and chemical development
    colour_space = 'sRGB'

    rgb = np.array([[[0.5, 0.5, 0.5]]])

    sensitivity = 10**neg.data.log_sensitivity
    sensitivity = np.nan_to_num(sensitivity) # replace nans with zeros
    raw = rgb_to_raw_hanatos2025(
        rgb,
        sensitivity,
        color_space='sRGB',
        apply_cctf_decoding=True,
        reference_illuminant=neg.info.reference_illuminant
    )

    log_raw = np.log10(np.fmax(raw, 0.0) + 1e-10)

    film = Film(neg)

    # density_cmy = film.develop(
    #     log_raw, pixel_size_um=1.0, use_fast_stats=False
    # )
    # print(density_cmy)

    # # film.develop function:
    density_cmy = interpolate_exposure_to_density(log_raw, neg.data.density_curves, neg.data.log_exposure, neg.data.tune.gamma_factor)
    print(density_cmy)
    # plt.plot(log_exp, dens_curves)
    # plt.scatter(log_raw, density_cmy)
    # plt.show()

    density_cmy = film._apply_density_correction_dir_couplers(density_cmy, log_raw, pixel_size_um=1.0)
    print()
    print(f'{density_cmy=}')
    density_cmy = _apply_density_correction_dir_couplers(film, density_cmy, log_raw, pixel_size_um=1.0)
    print(f'{density_cmy=}')
    print()
    # print(density_cmy)
    # density_cmy = self._apply_grain(density_cmy, pixel_size_um, bypass_grain, use_fast_stats)


process()
