from drafter import *
from bakery import assert_equal
from dataclasses import dataclass
import random
import json
from exercise_data import exercises

set_website_title("Fitness Creator")
set_site_information(
    author="Will McKay",
    description="Create a fitness plan based on your needs.",
    sources="Drafter docs, LLM.txt",
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
    """
    Get all exercises that use the given equipment.
    Args:
        equipment: str
    Return: list[WorkoutData]
    """
    workouts = []
    for exercise in exercises:
        if equipment == "gym" or exercise["equipment"] in EQUIPMENT_GROUPS[equipment]:
            workout = WorkoutData(exercise["name"], exercise["equipment"], exercise["category"], exercise["target"])
            workouts.append(workout)

    return workouts

def fits_goal(workout: WorkoutData, goal: str) -> bool:
    """
    Check if a workout matches the user's goal.
    Args:
        workout: WorkoutData
        goal: str
    Return: bool
    """
    if goal == "Gain Muscle":
        return workout.category != "cardio"
    if goal == "Lose Weight":
        return workout.category in ["cardio", "waist"]
    return True

def filter_by_goal(workouts: list[WorkoutData], goal: str) -> list[WorkoutData]:
    """
    Keep only the workouts that fit the user's goal.
    Args:
        workouts: list[WorkoutData]
        goal: str
    Return: list[WorkoutData]
    """
    filtered = []
    for workout in workouts:
        if fits_goal(workout, goal):
            filtered.append(workout)
    return filtered

def get_day_workouts(workouts: list[WorkoutData], day: str) -> list[WorkoutData]:
    """
    Pick 5 workouts for one day, preferring that day's muscles.
    Args:
        workouts: list[WorkoutData]
        day: str
    Return: list[WorkoutData]
    """
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
    """
    Build a week of workout days.
    Args:
        workouts: list[WorkoutData]
        frequency: int
    Return: list[WorkoutDay]
    """
    week = []
    for day in SPLITS[frequency]:
        week.append(WorkoutDay(day, get_day_workouts(workouts, day)))
    return week

def save_workout_data(state: State) -> str:
    """
    Turn the user's week of workouts into JSON text.
    Args:
        state: State
    Return: str
    """
    workout_data = []
    for day in state.week:
        day_data = []
        for workout in day.workouts:
            day_data.append({
                "name": workout.name,
                "equipment": workout.equipment,
                "category": workout.category,
                "primarymuscle": workout.primarymuscle
            })
        workout_data.append({
            "name": day.name,
            "workouts": day_data
        })
    return json.dumps(workout_data)

@route
def create_workout(state: State) -> Page:
    """
    Generate the user's weekly plan and show it.
    Args:
        state: State
    Return: Page
    """
    workouts = filter_by_equipment(state.equipment)
    workouts = filter_by_goal(workouts, state.goal)
    state.week = get_week(workouts, state.frequency)
    return Workout(state)

@route
def set_frequency(state: State, frequency: int) -> Page:
    """
    Save how many days a week the user wants to work out.
    Args:
        state: State
        frequency: int
    Return: Page
    """
    state.frequency = frequency
    return Goal(state)

@route
def set_goal(state: State, goal: str) -> Page:
    """
    Save the user's goal.
    Args:
        state: State
        goal: str
    Return: Page
    """
    state.goal = goal
    return Equipment(state)

@route
def set_equipment(state: State, equipment: str) -> Page:
    """
    Save the user's equipment and create their workout.
    Args:
        state: State
        equipment: str
    Return: Page
    """
    state.equipment = equipment
    return create_workout(state)

@route
def index(state: State) -> Page:
    """
    Show the home page.
    Args:
        state: State
    Return: Page
    """
    return Page(state, [
        Header("Workout Generator"),
        "Create a new workout",
        Button("Create", "Frequency"),
        LineBreak(),
        "Load an existing workout",
        FileUpload("upload", accept=".json"),
        Button("Load Workout", "load_workout")
    ])

@route
def load_workout(state: State, upload: str) -> Page:
    """
    Load a saved workout from the uploaded JSON file.
    Args:
        state: State
        upload: str
    Return: Page
    """
    if upload == "":
        return index(state)
    workout_data = json.loads(upload)
    week = []
    for day in workout_data:
        workouts = []
        for workout in day["workouts"]:
            workouts.append(
                WorkoutData(
                    workout["name"],
                    workout["equipment"],
                    workout["category"],
                    workout["primarymuscle"]
                )
            )
        week.append(WorkoutDay(day["name"], workouts))
    state.week = week
    return Workout(state)

@route
def Frequency(state: State) -> Page:
    """
    Ask how many days a week the user wants to work out.
    Args:
        state: State
    Return: Page
    """
    return Page(state, [
        Header("How many days a week do you want to work out?"),
        Button("4 days", "set_frequency", [Argument("frequency", 4)]),
        Button("5 days", "set_frequency", [Argument("frequency", 5)]),
        Button("6 days", "set_frequency", [Argument("frequency", 6)]),
        Button("7 days", "set_frequency", [Argument("frequency", 7)]),
    ])

@route
def Goal(state: State) -> Page:
    """
    Ask for the user's fitness goal.
    Args:
        state: State
    Return: Page
    """
    return Page(state, [
        Header("Select Your Goal"),
        Button("Gain Muscle", "set_goal", [Argument("goal", "Gain Muscle")]),
        Button("Lose Weight", "set_goal", [Argument("goal", "Lose Weight")]),
        Button("Stay in Shape", "set_goal", [Argument("goal", "Stay in Shape")])
    ])

@route
def Equipment(state: State) -> Page:
    """
    Ask what equipment the user has.
    Args:
        state: State
    Return: Page
    """
    return Page(state, [
        Header("What equipment do you have access to?"),
        Button("Full Gym", "set_equipment", [Argument("equipment", "gym")]),
        Button("Free Weights", "set_equipment", [Argument("equipment", "free weights")]),
        Button("Bodyweight", "set_equipment", [Argument("equipment", "bodyweight")])
    ])

@route
def Workout(state: State) -> Page:
    """
    Show the weekly plan with a table for each day.
    Args:
        state: State
    Return: Page
    """
    content = [Header("Your Workout")]
    day_number = 1
    for day in state.week:
        content.append(Header("Day " + str(day_number) + ": " + day.name.title(), 2))
        rows = []
        for workout in day.workouts:
            rows.append([workout.name.title(), workout.primarymuscle.title(), workout.equipment.title()])
        content.append(Table(rows, header=["Exercise", "Muscle", "Equipment"]))
        day_number += 1
    file_text = save_workout_data(state).replace('"', "%22")
    content.append(
        Download("Save Workout", "workout.json", file_text)
    )
    content.append(Button("Back to start", "index"))
    return Page(state, content)

@route
def Save(state: State) -> Page:
    """
    Show a message that the workout was saved.
    Args:
        state: State
    Return: Page
    """
    return Page(state, [
        Header("Workout Saved!")
    ])

squat = WorkoutData("squat", "body weight", "upper legs", "quads")
run = WorkoutData("run", "body weight", "cardio", "cardiovascular system")

assert_equal(fits_goal(squat, "Gain Muscle"), True)
assert_equal(fits_goal(run, "Gain Muscle"), False)
assert_equal(fits_goal(run, "Lose Weight"), True)
assert_equal(fits_goal(squat, "Lose Weight"), False)
assert_equal(fits_goal(squat, "Stay in Shape"), True)

assert_equal(filter_by_goal([squat, run], "Gain Muscle"), [squat])
assert_equal(filter_by_goal([squat, run], "Lose Weight"), [run])
assert_equal(filter_by_goal([], "Gain Muscle"), [])

plan = State("Gain Muscle", "gym", 4, [WorkoutDay("upper", [squat])])
plan_json = ('[{"name": "upper", "workouts": [{"name": "squat", "equipment": "body weight", '
             '"category": "upper legs", "primarymuscle": "quads"}]}]')
assert_equal(save_workout_data(plan), plan_json)
assert_equal(load_workout(State("Gain Muscle", "gym", 4, []), plan_json), Workout(plan))

start_server(State("", "", 0, []))
