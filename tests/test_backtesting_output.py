import pandas as pd

from backtester.analysis.cache import build_df_signature, load_cached_df, save_cached_df
from backtester.analysis.ipc_utils import load_dataframe_ipc, save_dataframe_ipc


def test_ipc_roundtrip_pickle(tmp_path):
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    path = save_dataframe_ipc(df, tmp_path, 'ipc_test', prefer_format='pickle')
    assert path is not None
    df_loaded = load_dataframe_ipc(path)
    assert df_loaded is not None
    assert df_loaded.equals(df)


def test_cache_roundtrip(tmp_path):
    df = pd.DataFrame({'x': [10, 20, 30]})
    sig = build_df_signature(df)
    saved = save_cached_df('unit_test', 'derived_metrics', df, signature=sig, cache_dir=str(tmp_path))
    assert saved is not None
    loaded = load_cached_df('unit_test', 'derived_metrics', signature=sig, cache_dir=str(tmp_path))
    assert loaded is not None
    assert loaded.equals(df)
