# Load ingredients from a file

import yaml
import os
from tabulate import tabulate
from argparse import ArgumentParser
import random

ingredient_path = os.path.join(os.path.dirname(__file__), 'pantry/ingredients.yaml')

def load_ingredients():
    file_path = ingredient_path
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

def get_unique_ingredients(recipes):
    unique_ingredients = set()
    for recipe in recipes:
        for item in recipe["ingredients"]:
            ingredient_name = item["name"]
            if ingredient_name not in unique_ingredients:
                unique_ingredients.add(ingredient_name)
    return unique_ingredients

def generate_ingredient_list():
    recipes = load_recipes()
    unique_ingredients = get_unique_ingredients(recipes)
    
    in_stock_ingredients = load_ingredients()

    for ingredient in unique_ingredients:
        if ingredient in in_stock_ingredients:
            continue
        in_stock_ingredients[ingredient] = False
    
    file_path = ingredient_path
    with open(file_path, 'w') as file:
        yaml.dump({"ingredients": in_stock_ingredients}, file)
    print("Ingredient list successfully updated and saved to file.")

def check_recipe_availability(recipe, ingredients_available):
    in_stock = []
    missing = []
    optional = []
    substitutions = []

    for item in recipe["ingredients"]:
        ingredient_name = item["name"]
        is_required = item["required"]

        if ingredients_available.get(ingredient_name):
            in_stock.append(ingredient_name)
            continue # If the ingredient is available, skip to the next one

        if not is_required:
            optional.append(ingredient_name)
            continue # If the ingredient is optional, skip to the next one

        if item.get("substitutions"):
            found_substitution = False
            for substitution in item["substitutions"]:
                if ingredients_available.get(substitution):
                    substitutions.append(substitution)
                    in_stock.append(substitution)
                    found_substitution = True
                    break
            if found_substitution:
                continue

        missing.append(ingredient_name)
    missing = list(set(missing))
    substitutions = list(set(substitutions))
    optional = list(set(optional))
    in_stock = list(set(in_stock))

    return missing, substitutions, optional, in_stock

def recipe_contains_ingredients(recipe, ingredients):
    count = 0
    for item in recipe["ingredients"]:
        ingredient_name = item["name"]
        if ingredient_name in ingredients:
            count += 1
    return True if count == len(ingredients) else False

def retrieve_recipe_availability(required_ingredients=None):
    ingredients = load_ingredients()
    recipes = load_recipes()

    recipe_status = []

    for recipe in recipes:
        if required_ingredients and not recipe_contains_ingredients(recipe, required_ingredients):
            continue # Skip recipes that don't contain the required ingredients
        missing, substitutions, optional, in_stock = check_recipe_availability(recipe, ingredients)
        recipe_status.append((
            recipe["type"],
            recipe["name"], 
            len(missing),
            "\n".join(missing),
            "\n".join(optional),
            "\n".join(substitutions),
            "\n".join(in_stock),
            ))
    headers = ["Type","Recipe Name", "M", "Missing Ingredients", "Optional Missing", "Substitutions", "In Stock"]

    # Sort the recipe status by the number of missing ingredients
    recipe_status.sort(key=lambda x: x[2])
    return recipe_status, headers

def add_ingredient_to_pantry(new_ingredients):
    pantry = load_ingredients()
    unique_ingredients = get_unique_ingredients(load_recipes())
    ingredient_to_add = []
    for new_ingredient in new_ingredients:
        if new_ingredient in pantry:
            if not pantry[new_ingredient]:
                print(f"\033[92m{new_ingredient} is now available.\033[0m")
                pantry[new_ingredient] = True

        # Ensure that only ingredients used in recipes can be added to the pantry.
        # This restriction is intentional to maintain consistency between the pantry and recipes.
        elif new_ingredient not in unique_ingredients:
            print(f"\033[91m{new_ingredient} is not a valid ingredient.\033[0m")
            continue
        else:
            ingredient_to_add.append(new_ingredient)

    # Ask the user for confirmation
    print(f"Are you sure you want to save the above changes? (y/n)")
    confirmation = input().strip().lower()
    if confirmation != 'y':
        print("Operation cancelled.")
        return
    file_path = ingredient_path
    with open(file_path, 'w') as file:
        yaml.dump({"ingredients": pantry}, file)
    print("Pantry updated.")
        
def remove_ingredient_from_pantry(old_ingredients):
    pantry = load_ingredients()
    for old_ingredient in old_ingredients:
        if old_ingredient in pantry:
            pantry[old_ingredient] = False
        else:
            print(f"{old_ingredient} is not in the pantry.")
    file_path = ingredient_path
    with open(file_path, 'w') as file:
        yaml.dump({"ingredients": pantry}, file)
    print("Pantry updated.")

def get_optimal_recipes(recipe_status, headers):
    new_recipe_status = []
    types = set(item[0] for item in recipe_status)  # Get unique recipe types

    for recipe_type in types:
        recipes_with_type = [item for item in recipe_status if item[0] == recipe_type]
        recipes_with_type.sort(key=lambda x: x[2])
        min_missing = recipes_with_type[0][2]
        recipes_with_type = [item for item in recipes_with_type if item[2] == min_missing]

        if len(recipes_with_type) > 1:
            recipe = random.choice(recipes_with_type)
        else:
            recipe = recipes_with_type[0]
        new_recipe_status.append(recipe)

    order = ["breakfast", "lunch", "dinner", "sides", "dessert", "snacks"]
    new_recipe_status.sort(key=lambda x: order.index(x[0]) if x[0] in order else len(order))
    
    return new_recipe_status, headers

def print_recipe_availability(recipe_status, headers, print_limit):
    recipe_status.sort(key=lambda x: x[2])
    print(tabulate(recipe_status[:min(len(recipe_status), print_limit)], headers=headers, tablefmt="grid"))

def main():
    parser = ArgumentParser(description="Check recipe availability based on pantry ingredients.")
    parser.add_argument("-p", "--print_limit", type=int, default=7, help="Number of recipes to display")
    parser.add_argument("-r", "--recipe", type=str, help="Specify a recipe name to check availability")
    parser.add_argument("-i", "--ingredients", nargs="+", help="List of ingredients to check availability for.")
    parser.add_argument("-t", "--type", nargs="+", type=str, help="Specify a recipe type to check availability")
    parser.add_argument("-a", "--add", nargs="+", help="Add ingredients to the pantry")
    parser.add_argument("-d", "--delete", nargs="+", help="Remove ingredients from the pantry")
    parser.add_argument("-opt", "--optimal_recipes", action="store_true", help="Print optimal recipes")
    parser.add_argument("-gen", "--generate", action="store_true", help="Generate a list of ingredients for the entire recipe database")

    args = parser.parse_args()

    if args.add:
        add_ingredient_to_pantry(args.add)
        return
    elif args.delete:
        remove_ingredient_from_pantry(args.delete)
        return
    elif args.generate:
        generate_ingredient_list()
        return
    
    if args.ingredients:
        recipe_status, headers = retrieve_recipe_availability(args.ingredients)
    else:
        recipe_status, headers = retrieve_recipe_availability()

    if args.recipe:
        recipe_status = [item for item in recipe_status if args.recipe.lower() in item[1].lower()]

    if args.type:
        new_recipe_status = []
        for recipe_type in args.type:
            new_recipe_status += [item for item in recipe_status if recipe_type.lower() in item[0].lower()]
        recipe_status = new_recipe_status

    if args.optimal_recipes:
        recipe_status, headers = get_optimal_recipes(recipe_status, headers)
    
    print_recipe_availability(recipe_status, headers, args.print_limit)

if __name__ == "__main__":
    main()