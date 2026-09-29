from filmulation.model.stocks import Illuminants
from filmulation.model.process import generate_lut, photo_params, write_cube, FilmSim
from collections.abc import MutableMapping
import copy
import importlib.resources as pkg_resources
from itertools import product
import json
from pathlib import Path
import shutil
import sys
from typing import Any, Sequence

import numpy as np


calibration_data = None
def read_calibration_data(path: Path):
    global calibration_data
    if calibration_data is not None:
        return
    with path.open("r", encoding="utf-8") as file:
        calibration_data =  json.load(file)


def write_calibration_data(path: Path):
    # Backup if exists
    if path.is_file():
        shutil.copy2(path, path.with_name(path.name + ".bak"))

    path.write_text(
        json.dumps(calibration_data, indent=4) + "\n",
        encoding="utf-8",
    )


def get_calibration_data(path=None):
    global calibration_data
    if calibration_data is None:
        raise RuntimeError("Must read calibration data first")
    if path is None:
        return calibration_data
    current = calibration_data
    for key in path:
        if not isinstance(current, MutableMapping):
            raise TypeError(f"Cannot access key {key!r}. Current value is not a dictionary")
        if key not in current:
            raise KeyError(f"Key {key!r} not found in path {path!r}")
        current = current[key]
    return current


def set_calibration_data(path, value, create_missing=True):
    global calibration_data
    if calibration_data is None:
        raise RuntimeError("Must read calibration data first")

    if not path:
        raise ValueError("path must contain at least one key")

    current = calibration_data
    for key in path[:-1]:
        if not isinstance(current, MutableMapping):
            raise TypeError(f"Cannot access key {key!r}. Current value is not a dictionary")
        if key not in current:
            if create_missing:
                current[key] = {}
            else:
                raise KeyError(f"Key {key!r} not found in path {path!r}")
        current = current[key]
    final_key = path[-1]
    if not isinstance(current, MutableMapping):
        raise TypeError(f"Cannot set key {final_key!r}. Parent value is not a dictionary")

    current[final_key] = value


def get_calib(negative, positive, normalize, key, default):
    norm = "norm" if normalize else "unorm"
    try:
        v = get_calibration_data(path=["negative_calib", negative, norm, positive, key])
    except KeyError:
        try:
            v = get_calibration_data(path=["positive_defaults", positive, norm, key])
        except KeyError:
            v = default
    return v


def get_calib_posonly(negative, positive, normalize, key, default=None):
    """Positive-only print-balance calibration, namespaced so it never collides
    with the full-pipeline values (which are tuned for synthetic inputs).

    Lives at negative_calib[neg][norm][pos]["positive_only"][key]. Used only when
    baking a positive-only (scanned-negative inversion) LUT.
    """
    norm = "norm" if normalize else "unorm"
    try:
        return get_calibration_data(
            path=["negative_calib", negative, norm, positive, "positive_only", key])
    except (KeyError, TypeError):
        return default


def make_params(
    negative,
    positive,
    in_color_space="ProPhoto RGB",
    out_color_space=None,
    normalize=False,
    lut=True,
    positive_only=False,
    negative_only=False,
    wb_to_base=True,
    print_exposure=None,
    print_gamma=None,
    y_shift=None,
    m_shift=None,
):
    norm = "norm" if normalize else "unorm"
    if out_color_space is None:
        out_color_space = in_color_space
    params = photo_params(negative=negative, print_paper=positive)

    params.camera.auto_exposure = False
    params.camera.exposure_compensation_ev = 0.0

    params.debug.deactivate_spatial_effects = True
    params.debug.deactivate_stochastic_effects = True
    params.debug.print_timings = True if not lut else False
    params.debug.return_negative_density_cmy = False
    params.debug.return_print_density_cmy = False

    params.enlarger.m_filter_shift = get_calib(negative, positive, normalize, 'm_filter_shift', 0.0)
    params.enlarger.y_filter_shift = get_calib(negative, positive, normalize, 'y_filter_shift', 0.0)

    params.enlarger.preflash_exposure = 0.0
    params.enlarger.print_exposure = get_calib(negative, positive, normalize, 'print_exposure', 1.0)
    params.enlarger.print_exposure_compensation = False
    params.enlarger.print_illuminant = Illuminants.lamp

    params.io.compute_negative = negative_only
    params.io.compute_positive_only = positive_only
    params.io.full_image = False
    params.io.input_cctf_decoding = True
    params.io.input_color_space = in_color_space
    params.io.output_cctf_encoding = True
    params.io.output_color_space = out_color_space
    params.io.preview_resize_factor = 0.3 if not lut else 1.0
    params.io.upscale_factor = 3.0 if not lut else 1.0

    params.negative.dir_couplers.amount = get_calib(negative, positive, normalize, 'dir_coupler', 1.0)
    params.negative.dir_couplers.ratio_rgb = get_calibration_data(path=["negative_calib", negative, "ratio_rgb"])
    params.negative.dir_couplers.diffusion_size_um = 0

    params.negative.grain.active = False

    params.print_paper.data.tune.dye_density_min_factor = 0.0
    params.print_paper.data.tune.gamma_factor = get_calib(negative, positive, normalize, 'print_gamma', 1.0)
    params.print_paper.glare.active = False

    if positive_only:
        params.io.wb_to_base = wb_to_base
        if wb_to_base:
            # Base-anchored inversion: the print stage stays at its simulated
            # neutral filters; only aesthetic print_gamma/print_exposure persist.
            params.print_paper.data.tune.gamma_factor = get_calib_posonly(
                negative, positive, normalize, 'print_gamma', params.print_paper.data.tune.gamma_factor)
            params.enlarger.print_exposure = get_calib_posonly(
                negative, positive, normalize, 'print_exposure', params.enlarger.print_exposure)
        else:
            # Legacy empirical gray-world balance (namespaced apart from the
            # full-pipeline calibration), for A/B against the base-anchored path.
            params.enlarger.y_filter_shift = get_calib_posonly(
                negative, positive, normalize, 'y_filter_shift', params.enlarger.y_filter_shift)
            params.enlarger.m_filter_shift = get_calib_posonly(
                negative, positive, normalize, 'm_filter_shift', params.enlarger.m_filter_shift)
            params.enlarger.print_exposure = get_calib_posonly(
                negative, positive, normalize, 'print_exposure', params.enlarger.print_exposure)
            params.print_paper.data.tune.gamma_factor = get_calib_posonly(
                negative, positive, normalize, 'print_gamma', params.print_paper.data.tune.gamma_factor)

    # Manual overrides for print-balance experimentation (positive-only sweeps).
    # Applied only when explicitly passed, so they take precedence over the above.
    if print_exposure is not None:
        params.enlarger.print_exposure = print_exposure
    if print_gamma is not None:
        params.print_paper.data.tune.gamma_factor = print_gamma
    if y_shift is not None:
        params.enlarger.y_filter_shift = y_shift
    if m_shift is not None:
        params.enlarger.m_filter_shift = m_shift

    params.settings.lut_resolution = 32
    params.settings.rgb_to_raw_method = 'hanatos2025' #'mallett2019'  #  'hanatos2025'
    params.settings.use_camera_lut = False
    params.settings.use_fast_stats = False

    if params.debug.deactivate_spatial_effects:
        params.camera.lens_blur_um = 0.0
        params.enlarger.lens_blur = 0.0
        params.negative.dir_couplers.diffusion_size_um = 0
        params.negative.grain.blur = 0.0
        params.negative.grain.blur_dye_clouds_um = 0.0
        params.negative.halation.scattering_size_um = [0,0,0]
        params.negative.halation.size_um = [0,0,0]
        params.print_paper.glare.blur = 0
        params.scanner.lens_blur = 0.0
        params.scanner.unsharp_mask = (0.0, 0.0)

    if params.debug.deactivate_stochastic_effects:
        params.negative.glare.active = False
        params.negative.grain.active = False
        params.print_paper.glare.active = False

    params.settings.use_camera_lut = True if not lut else False
    params.settings.use_enlarger_lut = True if not lut else False
    params.settings.use_scanner_lut = True if not lut else False

    return params


MAC_PATH = "/Users/lucasviana/SynologyDrive/Resources/LUTs/filmulation"

COLOR_SPACES = {
    'dwg':      'DaVinci Wide Gamut',
    'pp':       'ProPhoto RGB',
    'srgb':     'sRGB',
    '709':      'ITU-R BT.709',
    '709g22':   'Gamma 2.2 Encoded Rec.709',
    '2020':     'ITU-R BT.2020',
    'adobe':    'Gamma 2.2 Encoded AdobeRGB',
}

NEGATIVES = {
    'fc2':   'fujifilm_c200_auc',
    'fp4':   'fujifilm_pro_400h_auc',
    'fx4':   'fujifilm_xtra_400_auc',
    'ke1':   'kodak_ektar_100_auc',
    'kg2':   'kodak_gold_200_auc',
    'kp1':   'kodak_portra_160_auc',
    'kp4':   'kodak_portra_400_auc',
    'kp8':   'kodak_portra_800_auc',
    'kp8p1': 'kodak_portra_800_push1_auc',
    'kp8p2': 'kodak_portra_800_push2_auc',
    'ku4':   'kodak_ultramax_400_auc',
    'kv5d':  'kodak_vision3_50d_uc',
    'kv25d': 'kodak_vision3_250d_uc',
    'kv2t':  'kodak_vision3_200t_uc',
    'kv5t':  'kodak_vision3_500t_uc',
}

POSITIVES = {
    'fca': 'fujifilm_crystal_archive_typeii_uc',
    'k83': 'kodak_2383_uc',
    # 'k93': 'kodak_2393_uc',
    # 'kee': 'kodak_ektacolor_edge_uc',
    'kep': 'kodak_endura_premier_uc',
    # 'kpe': 'kodak_portra_endura_uc',
    'kse': 'kodak_supra_endura_uc',
    # 'kue': 'kodak_ultra_endura_uc',
}

# Human-readable stock names, keyed by the internal stock key. Used to make the
# generated .cube self-describing (TITLE + header) so downstream tooling can
# derive profile names without a parallel mapping.
NEG_DISPLAY = {
    'fujifilm_c200_auc':            'Fujifilm C200',
    'fujifilm_pro_400h_auc':        'Fujifilm Pro 400H',
    'fujifilm_xtra_400_auc':        'Fujifilm Xtra 400',
    'kodak_ektar_100_auc':          'Kodak Ektar 100',
    'kodak_gold_200_auc':           'Kodak Gold 200',
    'kodak_portra_160_auc':         'Kodak Portra 160',
    'kodak_portra_400_auc':         'Kodak Portra 400',
    'kodak_portra_800_auc':         'Kodak Portra 800',
    'kodak_portra_800_push1_auc':   'Kodak Portra 800 Push 1',
    'kodak_portra_800_push2_auc':   'Kodak Portra 800 Push 2',
    'kodak_ultramax_400_auc':       'Kodak Ultramax 400',
    'kodak_vision3_50d_uc':         'Kodak Vision3 50D',
    'kodak_vision3_250d_uc':        'Kodak Vision3 250D',
    'kodak_vision3_200t_uc':        'Kodak Vision3 200T',
    'kodak_vision3_500t_uc':        'Kodak Vision3 500T',
}

POS_DISPLAY = {
    'fujifilm_crystal_archive_typeii_uc': 'Fujifilm Crystal Archive',
    'kodak_2383_uc':                      'Kodak 2383',
    'kodak_2393_uc':                      'Kodak 2393',
    'kodak_ektacolor_edge_uc':            'Kodak Ektacolor Edge',
    'kodak_endura_premier_uc':            'Kodak Endura Premier',
    'kodak_portra_endura_uc':             'Kodak Portra Endura',
    'kodak_supra_endura_uc':              'Kodak Endura Supra',
    'kodak_ultra_endura_uc':              'Kodak Ultra Endura',
}
def generate_lut_path(negative, positive, normalize, color_space, folder="neg-tests", dest=None,
                      positive_only=False, tag=""):
    norm = "norm" if normalize else "unorm"
    color_space = color_space.replace(" ", "_")
    base = Path(dest) if dest is not None else Path(MAC_PATH)
    location = base / folder
    location.mkdir(parents=True, exist_ok=True)
    suffix = "-posonly" if positive_only else ""
    filename = f'{negative.removesuffix("_auc").removesuffix("_uc")}-{positive.removesuffix("_uc")}-{norm}-{color_space}{suffix}{tag}.cube'
    return location / filename


def report(r, g, b, m_filter, y_filter):
    print(r, g, b)
    print(f"m_filter {m_filter}")
    print(f"y_filter {y_filter}")


def tune_printer(negative, positive, normalize):
    params = make_params(
        negative,
        positive,
        normalize=normalize,
        in_color_space='ProPhoto RGB',
        out_color_space='ProPhoto RGB',
    )
    green_offset = get_calib(negative, positive, normalize, 'green_offset', 0.0)
    params.enlarger.y_filter_shift = 0.0
    params.enlarger.m_filter_shift = 0.0

    r, g, b = generate_middle_grey_sample(params, normalize=normalize)

    # green filter calib
    entered_step_1 = False
    entered_step_2 = False
    entered_step_3 = False
    entered_step_4 = False

    while g < r - 0.005 + green_offset:
        entered_step_1 = True
        params.enlarger.m_filter_shift += 0.1
        if b > r + 0.01:
            params.enlarger.y_filter_shift -= 0.1
        if b < r - 0.01:
            params.enlarger.y_filter_shift += 0.1
        r, g, b = generate_middle_grey_sample(params, normalize=normalize)

    while g > r + green_offset:
        entered_step_2 = True
        if entered_step_1:
            print("Overshot on step 1, probably ok.")
            break
        params.enlarger.m_filter_shift -= 0.1
        if b > r + 0.01:
            params.enlarger.y_filter_shift -= 0.1
        if b < r - 0.01:
            params.enlarger.y_filter_shift += 0.1
        r, g, b = generate_middle_grey_sample(params, normalize=normalize)

    while b > g + 0.003:
        entered_step_3 = True
        params.enlarger.y_filter_shift -= 0.05
        r, g, b = generate_middle_grey_sample(params, normalize=normalize)

    while b < g - 0.003:
        entered_step_4 = True
        if entered_step_3:
            print("Overshot on step 3, probably ok.")
            break
        params.enlarger.y_filter_shift += 0.05
        r, g, b = generate_middle_grey_sample(params, normalize=normalize)

    # report(r, g, b, params.enlarger.m_filter_shift, params.enlarger.y_filter_shift)

    norm = "norm" if normalize else "unorm"
    calib = get_calibration_data(path=["negative_calib", negative, norm, positive])
    calib["m_filter_shift"] = round(params.enlarger.m_filter_shift, 1)
    calib["y_filter_shift"] = round(params.enlarger.y_filter_shift, 1)


def generate_middle_grey_sample(params, normalize=True):
    params = copy.deepcopy(params)
    photo = FilmSim(params)

    middle_gray_linear = 0.184
    middle_gray_encoded = middle_gray_linear ** (1 / 1.8)

    if normalize:
        samples = np.array(
            [
                [[0.0, 0.0, 0.0]],
                [[middle_gray_encoded, middle_gray_encoded, middle_gray_encoded]],
                [[1.0, 1.0, 1.0]],
            ],
            dtype=np.float64,
        )

        out = photo.process(samples)[..., :3]

        black = out[0, 0]
        grey = out[1, 0]
        white = out[2, 0]

        min_ = np.min(black)
        max_ = np.max(white)
        scale = max_ - min_

        grey = (grey - min_) / scale
        grey = np.clip(grey, 0.0, 1.0)

        return tuple(float(v) for v in grey)

    rgb = np.array(
        [[[middle_gray_encoded, middle_gray_encoded, middle_gray_encoded]]],
        dtype=np.float64,
    )

    out = photo.process(rgb)[0, 0, :3]
    return tuple(float(v) for v in out)


def add_common(parser):
    parser.add_argument('--norm', choices=['norm', 'unorm', 'both'], default='unorm',
                         help='Normalization mode (default: unorm)')
    parser.add_argument('--color-space', choices=COLOR_SPACES, default='dwg', metavar='CS',
                         help=f'Input/output color space. Available: {stock_list(COLOR_SPACES)} (default: dwg)')
    parser.add_argument('--size', type=int, choices=[17, 32, 33, 65], default=32,
                         help='LUT grid size (default: 32)')
    parser.add_argument('--positive-only', action='store_true',
                         help='Bake only the print (positive) stage: maps scanned-negative RGB '
                              '-> positive RGB, to invert DSLR negative scans. Forces --norm unorm.')
    parser.add_argument('--negative-only', action='store_true')
    parser.add_argument('--no-wb-to-base', dest='wb_to_base', action='store_false',
                         help='Positive-only: disable base-anchored white balance (assumes the '
                              'scan is NOT WB-balanced to the film base). Falls back to the legacy '
                              'gray-world balance. Default: base-anchored.')
    parser.set_defaults(wb_to_base=True)
    # Print-balance overrides for experimentation. When set, override the values
    # pulled from calibration_data.json; the values are recorded in the .cube
    # header and filename so swept LUTs are distinguishable.
    parser.add_argument('--print-exposure', type=float, default=None,
                         help='Override baked print exposure (default: from calibration).')
    parser.add_argument('--print-gamma', type=float, default=None,
                         help='Override baked print gamma factor (default: from calibration).')
    parser.add_argument('--y-shift', type=float, default=None,
                         help='Override enlarger yellow filter shift (blue/green balance).')
    parser.add_argument('--m-shift', type=float, default=None,
                         help='Override enlarger magenta filter shift (green/red balance).')


def stock_list(d):
    return ', '.join(d)


def run():
    import argparse

    calib_path = Path(str(pkg_resources.files('filmulation.data.calibration').joinpath('calibration_data.json')))
    read_calibration_data(calib_path)

    # Shared stock-selection args, inherited by both subcommands via parents=
    stock_parser = argparse.ArgumentParser(add_help=False)
    stock_parser.add_argument('-n', '--negative', nargs='+', default=None, metavar='STOCK',
                              choices=NEGATIVES,
                              help=f'Negative stock(s). Available: {stock_list(NEGATIVES)}')
    stock_parser.add_argument('-p', '--positive', nargs='+', default=None, metavar='STOCK',
                              choices=POSITIVES,
                              help=f'Positive/paper stock(s). Available: {stock_list(POSITIVES)}')
    stock_parser.add_argument('--all', action='store_true',
                              help='Expand unspecified -n/-p to all available stocks')

    parser = argparse.ArgumentParser(prog='filmulation-lut', description='filmulation LUT generator')
    parser.add_argument('--dest', type=Path, default=Path(MAC_PATH),
                        help='Output directory for LUT files (default: MAC_PATH)')
    subparsers = parser.add_subparsers(dest='command', required=True)
    subparsers.add_parser('calibrate', parents=[stock_parser],
                          help='Calibrate printer parameters and write back to calibration_data.json')
    sub_gen = subparsers.add_parser('generate', parents=[stock_parser],
                                    help='Generate .cube LUT files')
    add_common(sub_gen)

    sub_pixel = subparsers.add_parser('pixel', parents=[stock_parser])
    add_common(sub_pixel)
    sub_pixel.add_argument('pixels', help='Pixels in `eval`able format')
    args = parser.parse_args()

    negatives = [NEGATIVES[n] for n in (args.negative or (list(NEGATIVES) if args.all else ['fc2']))]
    positives = [POSITIVES[p] for p in (args.positive or (list(POSITIVES) if args.all else ['fca']))]

    in_color_space = COLOR_SPACES.get(getattr(args, 'color_space', ''), 'DaVinci Wide Gamut')
    out_color_space = in_color_space

    if args.command == 'calibrate':
        for negative, positive, normalize in product(negatives, positives, [False]):
            print(f"Calibrating {negative} - {positive} - {'norm' if normalize else 'unorm'}")
            tune_printer(negative, positive, normalize)
        from pprint import pprint
        # pprint(get_calibration_data())
        write_calibration_data(calib_path)

    elif args.command == 'generate' or args.command == 'pixel':
        # A positive-only LUT's input axis is scanned-negative RGB, so the
        # black/white-corner normalization in generate_3d_lut is meaningless
        # there; always bake it unnormalized.
        if args.positive_only and args.norm != 'unorm':
            print("--positive-only forces --norm unorm")
        normalize_values = ([False] if args.positive_only else
                            {'norm': [True], 'unorm': [False], 'both': [True, False]}[args.norm])
        for negative, positive, normalize in product(negatives, positives, normalize_values):
            print(f"{negative} - {positive} - {'norm' if normalize else 'unorm'}"
                  f"{' - positive-only' if args.positive_only else ''}")
            params = make_params(
                negative,
                positive,
                in_color_space=in_color_space,
                out_color_space=out_color_space,
                normalize=normalize,
                positive_only=args.positive_only,
                negative_only=args.negative_only,
                wb_to_base=args.wb_to_base,
                print_exposure=args.print_exposure,
                print_gamma=args.print_gamma,
                y_shift=args.y_shift,
                m_shift=args.m_shift,
            )
            params.negative.dir_couplers.active = True
            params.negative.dir_couplers.diffusion_size_um = 0

            if args.command == 'pixel':
                params = copy.deepcopy(params)
                photo = FilmSim(params)
                input_pixels = np.array(eval(args.pixels), dtype=np.float64)
                if len(input_pixels.shape) == 1:
                    input_pixels = input_pixels[:, None].repeat(3, axis=1)
                out = photo.process(input_pixels, report=True)
                print(f"{out}")


            if args.command == 'generate':
                lut3d = generate_lut(
                    params,
                    size=args.size,
                    normalize=normalize,
                )

                # Tag the filename with any print-balance overrides so swept LUTs
                # don't collide and are self-identifying.
                override_tag = "".join(
                    f"-{k}{v:g}" for k, v in (
                        ("pe", args.print_exposure), ("pg", args.print_gamma),
                        ("y", args.y_shift), ("m", args.m_shift),
                    ) if v is not None
                )
                filename = generate_lut_path(
                    negative, positive, normalize, in_color_space,
                    folder=f"sim-results/{in_color_space}",
                    dest=args.dest,
                    positive_only=args.positive_only,
                    tag=override_tag,
                )

                neg_name = NEG_DISPLAY.get(negative, negative)
                pos_name = POS_DISPLAY.get(positive, positive)
                ratio_rgb = params.negative.dir_couplers.ratio_rgb
                metadata = {
                    'generator':              'filmulation',
                    'negative_key':           negative,
                    'positive_key':           positive,
                    'negative_name':          neg_name,
                    'positive_name':          pos_name,
                    'input_color_space':      in_color_space,
                    'output_color_space':     out_color_space,
                    'normalize':              'norm' if normalize else 'unorm',
                    'positive_only':          args.positive_only,
                    'wb_to_base':             args.wb_to_base if args.positive_only else False,
                    'lut_size':               args.size,
                    'dir_couplers_amount':    params.negative.dir_couplers.amount,
                    'dir_couplers_ratio_rgb': ', '.join(str(v) for v in ratio_rgb),
                    'm_filter_shift':         params.enlarger.m_filter_shift,
                    'y_filter_shift':         params.enlarger.y_filter_shift,
                    'print_exposure':         params.enlarger.print_exposure,
                    'print_gamma':            params.print_paper.data.tune.gamma_factor,
                }
                write_cube(filename, lut3d, title=f"{neg_name} - {pos_name}", metadata=metadata)

if __name__ == '__main__':
    run()

# 'ACES2065-1'
# 'ACEScc'
# 'ACEScct'
# 'ACEScg'
# 'ACESproxy'
# 'ARRI Wide Gamut 3'
# 'ARRI Wide Gamut 4'
# 'Adobe RGB (1998)'
# 'Adobe Wide Gamut RGB'
# 'Apple RGB'
# 'Best RGB'
# 'Beta RGB'
# 'Blackmagic Wide Gamut'
# 'CIE RGB'
# 'CIE XYZ-D65 - Scene-referred'
# 'Cinema Gamut'
# 'ColorMatch RGB'
# 'DCDM XYZ'
# 'DCI-P3'
# 'DCI-P3-P'
# 'DJI D-Gamut'
# 'DRAGONcolor'
# 'DRAGONcolor2'
# 'DaVinci Wide Gamut'
# 'Display P3'
# 'Don RGB 4'
# 'EBU Tech. 3213-E'
# 'ECI RGB v2'
# 'ERIMM RGB'
# 'Ekta Space PS 5'
# 'F-Gamut'
# 'F-Gamut C'
# 'FilmLight E-Gamut'
# 'FilmLight E-Gamut 2'
# 'Gamma 1.8 Encoded Rec.709'
# 'Gamma 2.2 Encoded AP1'
# 'Gamma 2.2 Encoded AdobeRGB'
# 'Gamma 2.2 Encoded Rec.709'
# 'ITU-R BT.2020'
# 'ITU-R BT.470 - 525'
# 'ITU-R BT.470 - 625'
# 'ITU-R BT.709'
# 'ITU-T H.273 - 22 Unspecified'
# 'ITU-T H.273 - Generic Film'
# 'Linear AdobeRGB'
# 'Linear P3-D65'
# 'Linear Rec.2020'
# 'Linear Rec.709 (sRGB)'
# 'Max RGB'
# 'N-Gamut'
# 'NTSC (1953)'
# 'NTSC (1987)'
# 'P3-D65'
# 'PLASA ANSI E1.54'
# 'Pal/Secam'
# 'ProPhoto RGB'
# 'Protune Native'
# 'REDWideGamutRGB'
# 'REDcolor'
# 'REDcolor2'
# 'REDcolor3'
# 'REDcolor4'
# 'RIMM RGB'
# 'ROMM RGB'
# 'Russell RGB'
# 'S-Gamut'
# 'S-Gamut3'
# 'S-Gamut3.Cine'
# 'SMPTE 240M'
# 'SMPTE C'
# 'Sharp RGB'
# 'V-Gamut'
# 'Venice S-Gamut3'
# 'Venice S-Gamut3.Cine'
# 'Xtreme RGB'
# 'sRGB'
# 'sRGB Encoded AP1'
# 'sRGB Encoded P3-D65'
# 'sRGB Encoded Rec.709 (sRGB)'
# 'aces'
# 'adobe1998'
# 'prophoto'
# 'lin_ap1_scene'
# 'lin_ap0_scene'
# 'lin_rec709_scene'
# 'lin_p3d65_scene'
# 'lin_rec2020_scene'
# 'lin_adobergb_scene'
# 'lin_ciexyzd65_scene'
# 'srgb_rec709_scene'
# 'g22_rec709_scene'
# 'g18_rec709_scene'
# 'srgb_ap1_scene'
# 'g22_ap1_scene'
# 'srgb_p3d65_scene'
# 'g22_adobergb_scene'
