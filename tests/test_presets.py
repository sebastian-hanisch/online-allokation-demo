"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; Permalink; feste Experimente."""

import ola_constants as C
import ola_evaluation as ev
import ola_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_control_ranges():
    for preset in C.PRESETS.values():
        assert preset["regel"] in C.REGELN and preset["ordnung"] in C.ORDNUNGEN and preset["n"] in C.N_OPTIONS
        assert C.D_MIN <= preset["d"] <= C.D_MAX and C.KN_MIN <= preset["kn"] <= C.KN_MAX and 0 <= preset["seed"] <= C.SEED_MAX


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**next(iter(C.PRESETS.values()))) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_every_choice_has_a_help_text_and_defaults_are_valid():
    assert set(C.REGEL_HILFE) == set(C.REGELN) and set(C.ORDNUNG_HILFE) == set(C.ORDNUNGEN)
    assert C.DEFAULT_REGEL in C.REGELN and C.DEFAULT_ORDNUNG in C.ORDNUNGEN and C.DEFAULT_N in C.N_OPTIONS and C.D_MIN <= C.DEFAULT_D <= C.D_MAX
    assert list(C.N_OPTIONS) == sorted(C.N_OPTIONS) and set(C.COLORS) == set(C.REGELN)
    assert abs((C.DEFAULT_KN - C.KN_MIN) / C.KN_STEP - round((C.DEFAULT_KN - C.KN_MIN) / C.KN_STEP)) < 1e-9


def test_experiment_grids_are_inside_the_controls():
    assert set(C.ORDER_KNS) <= {round(C.KN_MIN + i * C.KN_STEP, 1) for i in range(10)} and set(C.RESSOURCEN_DS) <= set(range(C.D_MIN, C.D_MAX + 1))
    assert list(C.GROWTH_NS) == sorted(C.GROWTH_NS) and set(C.GROWTH_NS) <= set(C.N_OPTIONS) and C.SWEEP_N in C.N_OPTIONS


def test_experiment_rows_have_the_documented_shape():
    rows = ev.order_rows(d=2, n=100)
    assert len(rows) == len(C.ORDER_KNS) * len(C.ORDNUNGEN) and all(set(C.REGELN) <= set(r) for r in rows)
    rows = ev.growth_rows()
    assert [r["n"] for r in rows] == list(C.GROWTH_NS)
    assert [r["d"] for r in ev.resource_rows(n=100)] == list(C.RESSOURCEN_DS)
    assert [r["Faktor"] for r in ev.step_rows(n=100)] == list(C.STEP_FACTORS)
    rows = ev.guarantee_rows(n=100)
    assert [r["Knappheit"] for r in rows] == list(C.GUARANTEE_KNS) and all(abs(r["Garantie"] - 0.3028) < 1e-4 for r in rows)
