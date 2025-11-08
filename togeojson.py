import geopandas as gpd

# Read the shapefile
gdf = gpd.read_file('PD_CA_2025_EN.shp')

# Convert to GeoJSON
gdf.to_file('polling_divisions.geojson', driver='GeoJSON')