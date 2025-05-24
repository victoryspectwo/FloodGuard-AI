import folium

# Coordinates of stops
coordinates = {
    "Depot": (1.3376, 103.7882),  
    "Beauty World MRT": (1.3415, 103.7765),
    "Bukit Timah CC": (1.3351, 103.7920),
    "Rifle Range Road": (1.3407, 103.7845),
    "Sixth Avenue MRT": (1.3293, 103.7965),
    "Jalan Kampong Chantek": (1.3256, 103.7975),
    "End": (1.3376, 103.7882),  # Ending at depot
    
    # Alternative reroute path
    "Lornie Highway": (1.3350, 103.8190),
    "Adam Road": (1.3310, 103.8140),
    "Farrer Road MRT": (1.3150, 103.8070),
    "Holland Road": (1.3155, 103.7960),
    "Rejoin Sixth Avenue": (1.3290, 103.7960)
}

# Flooded areas
flooded_locations = {
    "Bukit Timah CC",
    "Rifle Range Road",
    "Jalan Kampong Chantek"
}

# Define routes
normal_route = [
    "Depot", 
    "Beauty World MRT", 
    "Bukit Timah CC", 
    "Rifle Range Road", 
    "Jalan Kampong Chantek",
    "Sixth Avenue MRT", 
    "End"
]

rerouted_route = [
    "Depot", 
    "Beauty World MRT", 
    "Lornie Highway", 
    "Adam Road", 
    "Farrer Road MRT", 
    "Holland Road", 
    "Rejoin Sixth Avenue", 
    "Sixth Avenue MRT", 
    "End"
]

# Create map
map = folium.Map(location=[1.336, 103.79], zoom_start=13)

# Plot normal route
for location in normal_route:
    coord = coordinates[location]
    if location in flooded_locations:
        color = "red"
        icon = "cloud"
    else:
        color = "green"
        icon = "bus"
    folium.Marker(
        coord,
        popup=f"Normal: {location}",
        icon=folium.Icon(color=color, icon=icon, prefix='fa')
    ).add_to(map)

# Plot rerouted route
for location in rerouted_route:
    if location not in normal_route:
        coord = coordinates[location]
        folium.Marker(
            coord,
            popup=f"Reroute: {location}",
            icon=folium.Icon(color="orange", icon="road", prefix='fa')
        ).add_to(map)

# Draw normal route (black)
for i in range(len(normal_route) - 1):
    folium.PolyLine(
        [coordinates[normal_route[i]], coordinates[normal_route[i + 1]]],
        color="black",
        weight=5,
        opacity=0.7
    ).add_to(map)

# Draw rerouted route (red dashed)
for i in range(len(rerouted_route) - 1):
    folium.PolyLine(
        [coordinates[rerouted_route[i]], coordinates[rerouted_route[i + 1]]],
        color="red",
        weight=4,
        opacity=0.8,
        dash_array="5"
    ).add_to(map)

# Save map
map.save("floodguard_dual_route_map.html")
print("✅ Map saved as 'floodguard_dual_route_map.html'")
