import os
import random

import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import box


def find_square_containing_polygons(current_gdf, num_polygons, start_size, increase_step):
    """
    Function to find the smallest square that contains a given number of polygons
    :param current_gdf:
    :param num_polygons:
    :param start_size:
    :param increase_step:
    :return:
    """
    bounds = current_gdf.total_bounds
    min_x, min_y, max_x, max_y = bounds
    while True:
        # Select random starting point for the polygon
        x_start = random.uniform(min_x, max_x)
        y_start = random.uniform(min_y, max_y)
        size = start_size
        while size < max_x - min_x and size < max_y - min_y:
            square_geom = box(
                max(min_x, x_start - size / 2),
                max(min_y, y_start - size / 2),
                min(max_x, x_start + size / 2),
                min(max_y, y_start + size / 2)
            )
            # check which polygons intersect the square
            intersecting_gdf = current_gdf[current_gdf.geometry.intersects(square_geom)]
            if len(intersecting_gdf) >= num_polygons:
                return square_geom, intersecting_gdf
            # expand the square if the number of intersecting polygons is less than the required number
            size += increase_step
    return


def explode_multipolygons(current_gdf):
    """
    Splits MultiPolygons into individual Polygons and keeps the original attributes.
    :param current_gdf:
    :return:
    """
    exploded_polygons = []
    for _, row in current_gdf.iterrows():
        geom = row.geometry
        if geom.geom_type == 'MultiPolygon':
            for part in geom.geoms:  # Iterate through each Polygon in the MultiPolygon
                new_row = row.copy()  # Copy the attributes of the current row
                new_row.geometry = part  # Update the geometry with the individual Polygon
                exploded_polygons.append(new_row)
        elif geom.geom_type == 'Polygon':  # If it's a Polygon, keep it as is
            exploded_polygons.append(row)
    return gpd.GeoDataFrame(exploded_polygons, columns=current_gdf.columns, crs=current_gdf.crs)


if __name__ == '__main__':
    # Modify the path to the shapefile to match your system
    output_path = '../output/'
    path = '../data/vg250_01-01.gk3.shape.ebenen/vg250_ebenen_0101/VG250_KRS.shp'
    if os.path.exists(path):
        gdf = gpd.read_file(path)
        print(gdf.head())
    else:
        print('No path provided')
        exit(1)
        # print size of the first polygon
    # turn all MultiPolygons into individual Polygons
    gdf = explode_multipolygons(gdf)
    # # Count the number of Polygon geometries
    # num_polygons = sum(geom.geom_type == 'Polygon' for geom in gdf.geometry)
    # num_multipolygons = sum(geom.geom_type == 'MultiPolygon' for geom in gdf.geometry)
    # print(f"Number of Polygon geometries: {num_polygons}")
    # print(f"Number of MultiPolygon geometries: {num_multipolygons}")

    # select the number of polygons to be included in the square and the start_size and increase_step
    num_of_polygons = 100
    initial_size = 1
    growth_step = 1
    square, selected_polygons = find_square_containing_polygons(gdf, num_of_polygons, initial_size,
                                                                growth_step)
    selected_polygons = selected_polygons.copy()  # Make an explicit copy to avoid the warning
    selected_polygons.loc[:, 'geometry'] = selected_polygons.geometry.intersection(square)

    # Convert all datetime fields to strings before saving
    for col in selected_polygons.columns:
        if selected_polygons[col].dtype.name == 'datetime64[ns]':
            selected_polygons[col] = selected_polygons[col].dt.strftime('%Y-%m-%d')

    selected_polygons.to_file(f'{output_path}selected_polygons_{num_of_polygons}.shp')

    base = gdf.plot(color='white', edgecolor='black')
    gpd.GeoDataFrame(geometry=[square], crs=gdf.crs).plot(ax=base, color='blue', alpha=0.3)
    selected_polygons.plot(ax=base, color='red')
    plt.savefig(f'{output_path}selected_polygons_with_surrounding_map_{num_of_polygons}.png')
    plt.close()

    modified_map = gpd.read_file(f'{output_path}selected_polygons_{num_of_polygons}.shp')
    print(modified_map)
    # plot only modified map
    modified_map.plot()
    plt.savefig(f'{output_path}modified_map{num_of_polygons}.png')
    plt.show()
