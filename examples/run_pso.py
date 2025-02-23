from niapy.algorithms.basic import ParticleSwarmAlgorithm
from niapy.task import Task
from niaarmts import Dataset
from niaarmts.NiaARMTS import NiaARMTS

# Load dataset
dataset = Dataset()
dataset.load_data_from_csv('datasets/intervals.csv')

# Create an instance of NiaARMTS
niaarmts_problem = NiaARMTS(
    dimension=dataset.calculate_problem_dimension(),  # Adjust dimension dynamically
    lower=0.0,  # Lower bound of solution space
    upper=1.0,  # Upper bound of solution space
    features=dataset.get_all_features_with_metadata(),  # Pass feature metadata
    transactions=dataset.get_all_transactions(),  # Dataframe containing all transactions
    interval='true',  # Whether we're dealing with interval data
    alpha=1.0,  # Weight for support in fitness calculation
    beta=1.0,  # Weight for confidence in fitness calculation
    gamma=1.0,  # Weight for inclusion in fitness calculation # if 0.0 then inclusion metric is omitted
    delta=1.0  # Weight for amplitude in fitness calculation # if 0.0 then amplitude metric is omitted
)

# Define the optimization task
task = Task(problem=niaarmts_problem, max_iters=100)  # Run for 100 iterations

# Initialize the Particle Swarm Optimization algorithm
pso = ParticleSwarmAlgorithm(population_size=40, min_velocity=-1.0, max_velocity=1.0, c1=2.0, c2=2.0)

# Run the algorithm
best_solution = pso.run(task)

# Output the best solution and its fitness value
print(f"Best solution: {best_solution[0]}")
print(f"Fitness value: {best_solution[1]}")

# Retrieve the archive of rules that had fitness > 0.0
rule_archive = niaarmts_problem.get_rule_archive()

# Check if 'interval' is set to 'true'
is_interval = niaarmts_problem.interval == 'true'

# Print archive of rules with custom labels for interval data
print(f"\nArchive of rules with fitness > 0 (Total: {len(rule_archive)}):")
for i, rule_entry in enumerate(rule_archive, start=1):
    print(f"\nRule {i}:")
    print(f"Fitness: {rule_entry['fitness']}")

    # Format the antecedent
    antecedent_str = " AND ".join([
        f"{feature['feature']}({feature['border1']}, {feature['border2']})" if feature['type'] == 'Numerical' else f"{feature['feature']}({feature['category']})"
        for feature in rule_entry['antecedent']
    ])

    # Format the consequent
    consequent_str = " AND ".join([
        f"{feature['feature']}({feature['border1']}, {feature['border2']})" if feature['type'] == 'Numerical' else f"{feature['feature']}({feature['category']})"
        for feature in rule_entry['consequent']
    ])

    # Output the formatted rule with support, confidence, and inclusion and amplitude
    print(f"{antecedent_str} => {consequent_str}")
    print(f"Support: {rule_entry['support']:.4f}")
    print(f"Confidence: {rule_entry['confidence']:.4f}")

    if niaarmts_problem.gamma > 0.0:
        print(f"Inclusion: {rule_entry['inclusion']:.4f}")
    if niaarmts_problem.delta > 0.0:
        print(f"Amplitude: {rule_entry['amplitude']:.4f}")

    # Conditionally print 'Start Interval' and 'End Interval' based on the interval setting
    if is_interval:
        print(f"Start Interval: {rule_entry['start']}")
        print(f"End Interval: {rule_entry['end']}")
    else:
        print(f"Start timestamp: {rule_entry['start']}")
        print(f"End timestamp: {rule_entry['end']}")

# Save rules to CSV
niaarmts_problem.save_rules_to_csv("rules_archive.csv")

# Save rules to JSON
niaarmts_problem.save_rules_to_json("rules_archive.json")
