from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def main():
    # Define location indices
    locations = {
        0: "Depot",
        1: "Beauty World MRT",
        2: "Bukit Timah CC (Flooded)",
        3: "Rifle Range Road (Flooded)",
        4: "Sixth Avenue MRT",
        5: "Jalan Kampong Chantek (Flooded)"
    }

    # Distance matrix with high cost (9999) for flood-prone routes
    distance_matrix = [
    [0, 1.2, 2.5, 9999, 4.0, 4.5],
    [1.2, 0, 1.3, 9999, 2.8, 3.3],
    [2.5, 1.3, 0, 9999, 2.0, 2.5],
    [9999, 9999, 9999, 0, 9999, 9999],
    [4.0, 2.8, 2.0, 9999, 0, 1.0],
    [4.5, 3.3, 2.5, 9999, 1.0, 0],
]


    # Create routing index manager
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), 1, 0)  # 1 vehicle, starting at node 0 (Depot)

    # Create routing model
    routing = pywrapcp.RoutingModel(manager)

    # Define cost function
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Search strategy
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Solve the problem
    solution = routing.SolveWithParameters(search_parameters)

    # Output result
    if solution:
        print("✅ Optimized rerouted path for the bus:")
        index = routing.Start(0)
        route = []
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            route.append(locations[node])
            index = solution.Value(routing.NextVar(index))
        route.append("End (Back to Depot or final stop)")
        for step in route:
            print(f"➡️  {step}")
    else:
        print("❌ No solution found.")

if __name__ == "__main__":
    main()
