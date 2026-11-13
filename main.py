from drafter import *
from dataclasses import dataclass
import random
from exercise_data import exercises

set_website_title("Fitness Creator")
set_site_information(
    author="Will McKay",
    description="Create a fitness plan based on your needs.",
    sources="Drafter docs and google",
    planning=["plan.pdf", "design.pdf"],
    links=["https://github.com/WillMcKay/FitnessCreator-CISC108"]
)
hide_debug_information()
set_website_framed(False)
EQUIPMENT_GROUPS = {
    "bodyweight": ["body weight", "assisted"],
    "free weights": [
        "body weight", "assisted", "dumbbell", "barbell", "ez barbell",
        "olympic barbell", "kettlebell", "weighted", "band",
        "resistance band", "rope", "roller", "bosu ball",
    ],
}

SPLITS = {
    4: ["upper", "lower", "upper", "lower"],
    5: ["push", "pull", "legs", "upper", "lower"],
    6: ["push", "pull", "legs", "push", "pull", "legs"],
    7: ["push", "pull", "legs", "upper", "lower", "arms", "core"],
}

DAY_MUSCLES = {
    "push": ["pectorals", "delts", "triceps"],
    "pull": ["lats", "upper back", "biceps", "traps", "forearms"],
    "legs": ["quads", "glutes", "hamstrings", "calves"],
    "arms": ["biceps", "triceps", "forearms"],
    "core": ["abs", "serratus anterior", "cardiovascular system"],
}
DAY_MUSCLES["upper"] = DAY_MUSCLES["push"] + DAY_MUSCLES["pull"]
DAY_MUSCLES["lower"] = DAY_MUSCLES["legs"] + ["abs"]


@dataclass
class WorkoutData:
    name: str
    equipment: str
    category: str
    primarymuscle: str
    completed: bool = False

@dataclass
class WorkoutDay:
    name: str
    workouts: list[WorkoutData]

@dataclass
class State:
    goal: str
    equipment: str
    frequency: int
    week: list[WorkoutDay]

def filter_by_equipment(equipment: str) -> list[WorkoutData]:
    workouts = []
    for exercise in exercises:
        if equipment == "gym" or exercise["equipment"] in EQUIPMENT_GROUPS[equipment]:
            workout = WorkoutData(exercise["name"], exercise["equipment"], exercise["category"], exercise["target"])
            workouts.append(workout)

    return workouts

def fits_goal(workout: WorkoutData, goal: str) -> bool:
    if goal == "Gain Muscle":
        return workout.category != "cardio"
    if goal == "Lose Weight":
        return workout.category in ["cardio", "waist"]
    return True

def filter_by_goal(workouts: list[WorkoutData], goal: str) -> list[WorkoutData]:
    filtered = []
    for workout in workouts:
        if fits_goal(workout, goal):
            filtered.append(workout)
    return filtered

def get_day_workouts(workouts: list[WorkoutData], day: str) -> list[WorkoutData]:
    muscles = DAY_MUSCLES[day]
    matching = []
    others = []
    for workout in workouts:
        if workout.primarymuscle in muscles:
            matching.append(workout)
        else:
            others.append(workout)

    if len(matching) >= 5:
        return random.sample(matching, 5)

    needed = min(5 - len(matching), len(others))
    return matching + random.sample(others, needed)

def get_week(workouts: list[WorkoutData], frequency: int) -> list[WorkoutDay]:
    week = []
    for day in SPLITS[frequency]:
        week.append(WorkoutDay(day, get_day_workouts(workouts, day)))
    return week

@route
def create_workout(state: State) -> Page:
    workouts = filter_by_equipment(state.equipment)
    workouts = filter_by_goal(workouts, state.goal)
    state.week = get_week(workouts, state.frequency)
    return Workout(state)

@route
def set_frequency(state: State, frequency: int) -> Page:
    state.frequency = frequency
    return Goal(state)

@route
def set_goal(state: State, goal: str) -> Page:
    state.goal = goal
    return Equipment(state)

@route
def set_equipment(state: State, equipment: str) -> Page:
    state.equipment = equipment
    return create_workout(state)

@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Workout Generator"),
        "Create a new workout",
        Button("Create", "Frequency"),
        LineBreak(),
        "Load an existing workout",
        FileUpload("upload", accept=".json")
    ])

@route
def Frequency(state: State) -> Page:
    return Page(state, [
        Header("How many days a week do you want to work out?"),
        Button("4 days", "set_frequency", [Argument("frequency", 4)]),
        Button("5 days", "set_frequency", [Argument("frequency", 5)]),
        Button("6 days", "set_frequency", [Argument("frequency", 6)]),
        Button("7 days", "set_frequency", [Argument("frequency", 7)]),
    ])

@route
def Goal(state: State) -> Page:
    return Page(state, [
        Header("Select Your Goal"),
        Button("Gain Muscle", "set_goal", [Argument("goal", "Gain Muscle")]),
        Button("Lose Weight", "set_goal", [Argument("goal", "Lose Weight")]),
        Button("Stay in Shape", "set_goal", [Argument("goal", "Stay in Shape")])
    ])

@route
def Equipment(state: State) -> Page:
    return Page(state, [
        Header("What equipment do you have access to?"),
        Button("Full Gym", "set_equipment", [Argument("equipment", "gym")]),
        Button("Free Weights", "set_equipment", [Argument("equipment", "free weights")]),
        Button("Bodyweight", "set_equipment", [Argument("equipment", "bodyweight")])
    ])

@route
def Workout(state: State) -> Page:
    content = [Header("Your Workout")]
    day_number = 1
    for day in state.week:
        content.append(Header("Day " + str(day_number) + ": " + day.name.title(), 2))
        content.append(Table(day.workouts))
        day_number += 1
    content.append(Button("Back to start", "index"))
    return Page(state, content)

@route
def Save(state: State) -> Page:
    return Page(state, [
        Header("Workout Saved!")
    ])

start_server(State("", "", 0, []))
