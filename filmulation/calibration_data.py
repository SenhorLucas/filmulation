positive_defaults = {
    "fujifilm_crystal_archive_typeii_uc": {
        "norm": {
            "dir_coupler": 0.9,
            "print_exposure": 1.0,
            "print_gamma": 1.0,
            "green_offset": 0.005,
        },
        "unorm": {
            "dir_coupler": 0.9,
            "print_exposure": 1.0,
            "print_gamma": 1.0,
            "green_offset": 0.005,
        },
    },
    "kodak_2383_uc": {
        "norm": {
            "dir_coupler": 1.0,
            "green_offset": -0.005,
            "print_exposure": 1.05,
            "print_gamma": 0.9,
        },
        "unorm": {
            "dir_coupler": 1.0,
            "green_offset": -0.005,
            "print_exposure": 0.95,
            "print_gamma": 1.0,
        },
    },
    "kodak_endura_premier_uc": {
        "norm": {
            "dir_coupler": 1.0,
            "green_offset": 0.0,
            "print_exposure": 1.0,
            "print_gamma": 0.8,
        },
        "unorm": {
            "dir_coupler": 1.0,
            "green_offset": 0.0,
            "print_exposure": 1.0,
            "print_gamma": 0.8,
        },
    },
    "kodak_supra_endura_uc": {
        "norm": {
            "dir_coupler": 1.0,
            "green_offset": 0.005,
            "print_exposure": 1.0,
            "print_gamma": 1.0,
        },
        "unorm": {
            "dir_coupler": 1.0,
            "green_offset": 0.005,
            "print_exposure": 1.0,
            "print_gamma": 1.0,
        },
    },
}

negative_calib = {
    "fujifilm_c200_auc": {
        "kodak_2383_uc": {"m_filter_shift": 3.9, "y_filter_shift": 0.4},
        "kodak_endura_premier_uc": {"m_filter_shift": 0.0, "y_filter_shift": -1.0},
        "fujifilm_crystal_archive_typeii_uc": {
            "m_filter_shift": 2.4,
            "y_filter_shift": 0.0,
        },
        "kodak_supra_endura_uc": {"m_filter_shift": 2.3, "y_filter_shift": -1.2},
    },
    "fujifilm_pro_400h_auc": {
        "kodak_2383_uc": {"m_filter_shift": 5.9, "y_filter_shift": 0.9},
        "kodak_endura_premier_uc": {"m_filter_shift": 0.0, "y_filter_shift": -1.0},
        "fujifilm_crystal_archive_typeii_uc": {
            "m_filter_shift": 3.8,
            "y_filter_shift": 0.1,
        },
        "kodak_supra_endura_uc": {"m_filter_shift": 3.3, "y_filter_shift": -1.2},
    },
    "fujifilm_xtra_400_auc": {
        "kodak_2383_uc": {"m_filter_shift": 7.0, "y_filter_shift": 0.9},
        "kodak_endura_premier_uc": {"m_filter_shift": -0.1, "y_filter_shift": -1.2},
        "fujifilm_crystal_archive_typeii_uc": {
            "m_filter_shift": 4.1,
            "y_filter_shift": 0.0,
        },
        "kodak_supra_endura_uc": {"m_filter_shift": 3.3, "y_filter_shift": -2.2},
    },
    "kodak_ektar_100_auc": {
        "kodak_2383_uc": {"m_filter_shift": 2.1, "y_filter_shift": 0.4},
        "kodak_endura_premier_uc": {"m_filter_shift": 0.1, "y_filter_shift": -0.7},
        "fujifilm_crystal_archive_typeii_uc": {
            "m_filter_shift": 1.2,
            "y_filter_shift": 0.0,
        },
        "kodak_supra_endura_uc": {"m_filter_shift": 1.8, "y_filter_shift": -1.0},
    },
    "kodak_gold_200_auc": {
        "kodak_2383_uc": {"m_filter_shift": 4.8, "y_filter_shift": 0.6},
        "kodak_endura_premier_uc": {"m_filter_shift": 0.0, "y_filter_shift": -1.0},
        "fujifilm_crystal_archive_typeii_uc": {
            "m_filter_shift": 2.5,
            "y_filter_shift": 0.0,
        },
        "kodak_supra_endura_uc": {"m_filter_shift": 1.8, "y_filter_shift": -1.6},
    },
    "kodak_portra_160_auc": {
        "kodak_2383_uc": {"m_filter_shift": 3.7, "y_filter_shift": 0.5},
        "kodak_endura_premier_uc": {"m_filter_shift": 0.1, "y_filter_shift": -0.7},
        "fujifilm_crystal_archive_typeii_uc": {
            "m_filter_shift": 2.0,
            "y_filter_shift": 0.0,
        },
        "kodak_supra_endura_uc": {"m_filter_shift": 2.8, "y_filter_shift": -1.0},
    },
    "kodak_ultramax_400_auc": {
        "kodak_2383_uc": {"m_filter_shift": 4.3, "y_filter_shift": 0.5},
        "kodak_endura_premier_uc": {"m_filter_shift": 0.1, "y_filter_shift": -1.0},
        "fujifilm_crystal_archive_typeii_uc": {
            "m_filter_shift": 2.4,
            "y_filter_shift": 0.0,
        },
        "kodak_supra_endura_uc": {"m_filter_shift": 2.2, "y_filter_shift": -1.6},
    },
    "kodak_vision3_200t_uc": {
        "kodak_2383_uc": {"m_filter_shift": 6.7, "y_filter_shift": 0.7},
        "kodak_endura_premier_uc": {"m_filter_shift": 0.0, "y_filter_shift": -1.0},
        "fujifilm_crystal_archive_typeii_uc": {
            "m_filter_shift": 5.0,
            "y_filter_shift": 0.0,
        },
        "kodak_supra_endura_uc": {"m_filter_shift": 3.7, "y_filter_shift": -1.8},
    },
    "kodak_vision3_250d_uc": {
        "kodak_2383_uc": {"m_filter_shift": 7.0, "y_filter_shift": 0.8},
        "kodak_endura_premier_uc": {"m_filter_shift": 0.0, "y_filter_shift": -1.3},
        "fujifilm_crystal_archive_typeii_uc": {
            "m_filter_shift": 5.1,
            "y_filter_shift": 0.0,
        },
        "kodak_supra_endura_uc": {"m_filter_shift": 4.2, "y_filter_shift": -2.4},
    },
    "kodak_portra_400_auc": {
        "kodak_2383_uc": {"m_filter_shift": 4.4, "y_filter_shift": 0.5},
        "kodak_endura_premier_uc": {"m_filter_shift": 0.0, "y_filter_shift": -1.2},
        "fujifilm_crystal_archive_typeii_uc": {
            "m_filter_shift": 2.4,
            "y_filter_shift": 0.0,
        },
        "kodak_supra_endura_uc": {"m_filter_shift": 3.0, "y_filter_shift": -1.4},
    },
    "kodak_portra_800_auc": {
        "kodak_2383_uc": {"m_filter_shift": 3.9, "y_filter_shift": 0.4},
        "kodak_endura_premier_uc": {"m_filter_shift": 0.0, "y_filter_shift": -0.6},
        "fujifilm_crystal_archive_typeii_uc": {
            "m_filter_shift": 2.0,
            "y_filter_shift": 0.0,
        },
        "kodak_supra_endura_uc": {"m_filter_shift": 2.3, "y_filter_shift": -1.2},
    },
    "kodak_vision3_500t_uc": {
        "ratio_rgb": (2.0, 1.0, 0.1),
        "unorm": {
            "kodak_2383_uc": {
                "m_filter_shift": 7.4,
                "y_filter_shift": 0.8,
                "dir_coupler": 1.5,
            },
            "kodak_endura_premier_uc": {
                "m_filter_shift": 0.0,
                "y_filter_shift": -1.3,
                "dir_coupler": 1.0,
            },
            "fujifilm_crystal_archive_typeii_uc": {
                "m_filter_shift": 5.4,
                "y_filter_shift": 0.0,
                "dir_coupler": 1.2,
            },
            "kodak_supra_endura_uc": {
                "m_filter_shift": 5.0,
                "y_filter_shift": -2.3,
                "dir_coupler": 1.2,
            },
        },
        "norm": {
            "kodak_2383_uc": {
                "m_filter_shift": 7.4,
                "y_filter_shift": 0.8,
                "dir_coupler": 1.5,
            },
            "kodak_endura_premier_uc": {
                "m_filter_shift": 0.0,
                "y_filter_shift": -1.3,
                "dir_coupler": 1.0,
            },
            "fujifilm_crystal_archive_typeii_uc": {
                "m_filter_shift": 5.4,
                "y_filter_shift": 0.0,
                "dir_coupler": 1.2,
            },
            "kodak_supra_endura_uc": {
                "m_filter_shift": 5.0,
                "y_filter_shift": -2.3,
                "dir_coupler": 1.2,
            },
        },
    },
    "kodak_vision3_50d_uc": {
        "kodak_2383_uc": {"m_filter_shift": 7.4, "y_filter_shift": 0.9},
        "kodak_endura_premier_uc": {"m_filter_shift": 0.0, "y_filter_shift": -1.1},
        "fujifilm_crystal_archive_typeii_uc": {
            "m_filter_shift": 5.4,
            "y_filter_shift": 0.0,
        },
        "kodak_supra_endura_uc": {"m_filter_shift": 3.4, "y_filter_shift": -2.0},
    },
}
