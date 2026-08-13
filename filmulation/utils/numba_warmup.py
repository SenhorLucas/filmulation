from filmulation.utils.fast_stats import warmup_fast_stats
from filmulation.utils.lut import warmup_luts
from filmulation.utils.fast_interp import warmup_fast_interp
# from filmulation.utils.fast_gaussian_filter import warmup_fast_gaussian_filter

# precompile numba functions
def warmup():
    warmup_fast_stats()
    warmup_luts()
    warmup_fast_interp()
    # warmup_fast_gaussian_filter()
