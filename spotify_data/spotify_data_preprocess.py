import pandas as pd
from constants import (
    LOCAL,
    SPOTIFY_DATA_TRACKS,
    SPOTIFY_DATA_ARTISTS,
    SPOTIFY_DATA_LISTENERS,
)


df_tracks = pd.read_csv(SPOTIFY_DATA_TRACKS)
df_artists = pd.read_csv(SPOTIFY_DATA_ARTISTS)
df_listeners = pd.read_csv(SPOTIFY_DATA_LISTENERS)


df_tracks['year'] = (
    pd.to_numeric(df_tracks['year'], errors='coerce').fillna(0).astype(int)
)
df_tracks['artists'] = (
    df_tracks['artists']
    .astype(str)
    .str.replace('[', '')
    .str.replace(']', '')
    .str.replace("'", '')
)
df_tracks = df_tracks.drop(['release_date'], axis=1)


cols_to_convert = ['Streams', 'Daily', 'As lead', 'Solo', 'As feature']
for col in cols_to_convert:
    df_artists[col] = df_artists[col].astype(str)
    df_artists[col] = df_artists[col].str.replace(',', '')
    df_artists[col] = pd.to_numeric(df_artists[col], errors='coerce')


cols = ['Listeners', 'Daily Trend', 'PkListeners']
for col in cols:
    df_listeners[col] = df_listeners[col].astype(str)
    df_listeners[col] = df_listeners[col].str.replace(',', '')
    df_listeners[col] = pd.to_numeric(df_listeners[col], errors='coerce')


output_file = LOCAL + '/data_tracks_preprocessed.csv'
output_file2 = LOCAL + '/artists_preprocessed.csv'
output_file3 = LOCAL + '/listeners_preprocessed.csv'


df_tracks.to_csv(output_file, index=False)
df_artists.to_csv(output_file2, index=False)
df_listeners.to_csv(output_file3, index=False)


print('Dados tratados das músicas do spotify salvos em:', output_file)
print('Dados tratados dos streams artistas e salvos em:', output_file2)
print('Dados tratados dos ouvintes por artistas e salvos em:', output_file3)
