import folium

# Route and coordinates
route = [
    "Depot", 
    "Beauty World MRT", 
    "Sixth Avenue MRT", 
    "End"  # back to Depot or wherever you end
]

coordinates = {
    "Depot": (1.3376, 103.7882),  # Arbitrary depot location near Beauty World
    "Beauty World MRT": (1.3415, 103.7765),
    "Bukit Timah CC": (1.3351, 103.7920),
    "Rifle Range Road": (1.3407, 103.7845),
    "Sixth Avenue MRT": (1.3293, 103.7965),
    "Jalan Kampong Chantek": (1.3256, 103.7975),
    "End": (1.3376, 103.7882)  # Ending at depot
}

flooded_locations = {
    "Bukit Timah CC",
    "Rifle Range Road",
    "Jalan Kampong Chantek"
}

# Initialize map centered around Bukit Timah
map = folium.Map(location=[1.336, 103.79], zoom_start=14)

# Add all points to the map
for location in route:
    coord = coordinates[location]
    if location in flooded_locations:
        color = "red"
        icon = "cloud"
    else:
        color = "green"
        icon = "bus"
    folium.Marker(
        coord,
        popup=location,
        icon=folium.Icon(color=color, icon=icon, prefix='fa')
    ).add_to(map)

# Draw lines between the route stops
for i in range(len(route) - 1):
    folium.PolyLine(
        [coordinates[route[i]], coordinates[route[i + 1]]],
        color="blue",
        weight=5,
        opacity=0.6
    ).add_to(map)

# Save to HTML
map.save("floodguard_route_map.html")
print("✅ Map saved as 'floodguard_route_map.html'")

