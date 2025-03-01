# Load ingredients from a file

import yaml
import os
from tabulate import tabulate
from argparse import ArgumentParser


def load_ingredients():
    file_path = os.path.join(os.path.dirname(__file__), 'db/ingredients.yaml')
    with open(file_path, 'r') as file:
        pantry = yaml.safe_load(file)
    sorted_ingredients = dict(sorted(pantry["ingredients"].items()))
    with open(file_path, 'w') as file:
        yaml.dump(pantry, file)
    return sorted_ingredients

def load_recipes():
    file_path = os.path.join(os.path.dirname(__file__), 'db/recipes.yaml')
    with open(file_path, 'r') as file:
        recipes = yaml.safe_load(file)
    sorted_recipes = sorted(recipes["recipes"], key=lambda x: x['name'])
    recipes["recipes"] = sorted_recipes
    with open(file_path, 'w') as file:
        yaml.dump(recipes, file, sort_keys=False, default_flow_style=False)
    return sorted_recipes

def check_recipe_availability(recipe, ingredients_available):
    missing = []
    optional = []
    substitutions = []

    for item in recipe["ingredients"]:
        ingredient_name = item["name"]
        is_required = item["required"]

        if ingredients_available.get(ingredient_name):
            continue # If the ingredient is available, skip to the next one

        if not is_required:
            optional.append(ingredient_name)
            continue # If the ingredient is optional, skip to the next one

        if not item.get("substitutions"):
            missing.append(ingredient_name)
            continue # If the ingredient is required and has no substitutions, mark it as missing
        
        for substitution in item["substitutions"]:
            if ingredients_available.get(substitution):
                substitutions.append(substitution)
                break

    missing = list(set(missing))
    substitutions = list(set(substitutions))
    optional = list(set(optional))

    return missing, substitutions, optional

def retrieve_recipe_availability():
    ingredients = load_ingredients()
    recipes = load_recipes()

    recipe_status = []

    for recipe in recipes:
        missing, substitutions, optional = check_recipe_availability(recipe, ingredients)
        recipe_status.append((
            recipe["type"],
            recipe["name"], 
            len(missing), 
            "\n".join(missing),
            "\n".join(optional),
            "\n".join(substitutions),
            ))
    headers = ["Type","Recipe Name", "Total Missing", "Missing Ingredients", "Optional Missing", "Substitutions"]

    # Sort the recipe status by the number of missing ingredients
    recipe_status.sort(key=lambda x: x[2])
    return recipe_status, headers

def recipe_contains_ingredients(recipe, ingredients):
    count = 0
    for item in recipe["ingredients"]:
        ingredient_name = item["name"]
        if ingredient_name in ingredients:
            count += 1
    return True if count == len(ingredients) else False

def check_recipe_availability_by_ingredients(required_ingredients):
    recipes = load_recipes()
    available_ingredients = load_ingredients()
    recipe_status = []

    for recipe in recipes:
        if recipe_contains_ingredients(recipe, required_ingredients):
            missing, substitutions, optional = check_recipe_availability(recipe
                , available_ingredients)
            recipe_status.append((
                recipe["type"],
                recipe["name"], 
                len(missing), 
                "\n".join(missing),
                "\n".join(optional),
                "\n".join(substitutions),
                ))
    headers = ["Type","Recipe Name", "Total Missing", "Missing Ingredients", "Optional Missing", "Substitutions"]

    recipe_status.sort(key=lambda x: x[2])
    return recipe_status, headers
        

def print_recipe_availability(recipe_status, headers, print_limit):
    print(tabulate(recipe_status[:min(len(recipe_status), print_limit)], headers=headers, tablefmt="grid"))

def main():
    parser = ArgumentParser(description="Check recipe availability based on pantry ingredients.")
    parser.add_argument("-p", "--print_limit", type=int, default=10, help="Number of recipes to display")
    parser.add_argument("-r", "--recipe", type=str, help="Specify a recipe name to check availability")
    parser.add_argument("-i", "--ingredients", nargs="+", help="List of ingredients to check availability for.")
    parser.add_argument("-t", "--type", type=str, help="Specify a recipe type to check availability")

    args = parser.parse_args()

    if args.ingredients:
        recipe_status, headers = check_recipe_availability_by_ingredients(args.ingredients)
    else:
        recipe_status, headers = retrieve_recipe_availability()

    if args.recipe:
        recipe_status = [item for item in recipe_status if args.recipe.lower() in item[1].lower()]

    if args.type:
        recipe_status = [item for item in recipe_status if args.type.lower() in item[0].lower()]
    
    print_recipe_availability(recipe_status, headers, args.print_limit)

if __name__ == "__main__":
    main()