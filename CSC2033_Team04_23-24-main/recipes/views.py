from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user, current_user, logout_user, login_required
from models import User, Bookmark, RecipeRating, add_recipe, get_recipe, approved_recipes_exist, get_recipes, \
    unapproved_recipes_exist, reset_recipes, mdb_split_lines, mdb_set_states, mdb_approve_recipe, mdb_delete_recipe
from extensions import db, mdb
from math import ceil

from recipes.forms import RecipeForm, RatingForm
from pymongo import DESCENDING

recipes_blueprint = Blueprint("recipes", __name__, template_folder="templates")

"""
Run search_validator on each recipe in recipes_list
If a recipe doesn't match the query, it returns {}
If a recipe matches the query, it returns {"recipe": {...}, "relevance": x}
Recipes are sorted in order of relevance (recipes with "relevance":1 are first, etc)

Returns: array of recipes that match search query

@author: Shay
"""
def search(recipes_list, query):

    results = []
    for recipe in recipes_list:
        print("Checking recipe " + str(recipe["id"]))
        validation = search_validator(recipe, query)
        if "recipe" in validation:
            results.append(validation)

    print("[DEBUG] Unordered search results: " + str(results))

    ordered_results = []
    for i in range(1, 5):
        for result in results:
            if result["relevance"] == i:
                ordered_results.append(result["recipe"])

    return ordered_results

"""
Check whether the query is within different properties of a recipe

The relevance (1 being most relevant) is whether the query is found in:
- title: relevance 1
- summary; relevance 2
- tags or category: relevance 3
- ingredients or instructions: relevance 4

Returns: {"recipe": {...}, "relevance": x} if the recipe matches the query, or {} if it doesn't

@author: Shay
"""
def search_validator(recipe, query):

    print("[DEBUG] checking recipe " + str(recipe["id"]) + " with query " + str(query))

    if query.lower() in recipe["title"].lower():
        print("[DEBUG] title = " + recipe["title"])
        return {"recipe": recipe, "relevance": 1}
    if query.lower() in recipe["summary"].lower():
        print("[DEBUG] summary = " + recipe["summary"])
        return {"recipe": recipe, "relevance": 2}
    for tag in recipe["tags"]:
        print("[DEBUG] tags = " + str(recipe["tags"]))
        if query.lower() in tag.lower():
            return {"recipe": recipe, "relevance": 3}
    if query.lower() in recipe["category"].lower():
        print("[DEBUG] category = " + recipe["category"])
        return {"recipe": recipe, "relevance": 3}
    for ingredient in recipe["ingredients"]:
        print("[DEBUG] ingredients = " + str(recipe["ingredients"]))
        if query.lower() in ingredient.lower():
            return {"recipe": recipe, "relevance": 4}
    for instruction in recipe["instructions"]:
        print("[DEBUG] instructions = " + str(recipe["instructions"]))
        if query.lower() in instruction.lower():
            return {"recipe": recipe, "relevance": 4}

    return {}  # check failed, recipe does not match query


"""
Check through different sort orders, then run get_recipes using its built-in .sort() functionality
Except for rating sorts because they require sorting by an external value (RecipeRating.value)
Defaults to "new" if sort_order isn't another valid option

Returns: an array of recipes, sorted in the given order

@author: Shay
"""
def get_sorted_recipes(sort_order, filters={}):

    print("[DEBUG] getting sorted recipes")
    results = []
    if sort_order == "new":
        for recipe in get_recipes(filters=filters).sort("id", DESCENDING):
            results.append(recipe)
    elif sort_order == "old":
        for recipe in get_recipes(filters=filters).sort("id"):
            results.append(recipe)
    elif sort_order == "title-az":
        for recipe in get_recipes(filters=filters).sort("title"):
            results.append(recipe)
    elif sort_order == "title-za":
        for recipe in get_recipes(filters=filters).sort("title", DESCENDING):
            results.append(recipe)
    elif sort_order == "longest":
        for recipe in get_recipes(filters=filters).sort("preparation_time", DESCENDING):
            results.append(recipe)
    elif sort_order == "quickest":
        for recipe in get_recipes(filters=filters).sort("preparation_time"):
            results.append(recipe)
    elif sort_order == "most-servings":
        for recipe in get_recipes(filters=filters).sort("servings", DESCENDING):
            results.append(recipe)
    elif sort_order == "least-servings":
        for recipe in get_recipes(filters=filters).sort("servings"):
            results.append(recipe)
    elif sort_order == "most-calories":
        for recipe in get_recipes(filters=filters).sort("calories_per_serving", DESCENDING):
            results.append(recipe)
    elif sort_order == "least-calories":
        for recipe in get_recipes(filters=filters).sort("calories_per_serving"):
            results.append(recipe)
    elif sort_order == "highest-rating":
        unsorted_recipe_ratings = []
        for recipe in get_recipes(filters=filters):
            unsorted_recipe_ratings.append({"recipe": recipe, "rating": get_average_rating(recipe["id"])})
        sorted_recipe_ratings = sorted(unsorted_recipe_ratings, key=lambda r: r["rating"], reverse=True)
        for recipe_rating in sorted_recipe_ratings:
            results.append(recipe_rating["recipe"])
    elif sort_order == "lowest-rating":
        unsorted_recipe_ratings = []
        for recipe in get_recipes(filters=filters):
            unsorted_recipe_ratings.append({"recipe": recipe, "rating": get_average_rating(recipe["id"])})
        sorted_recipe_ratings = sorted(unsorted_recipe_ratings, key=lambda r: r["rating"])
        for recipe_rating in sorted_recipe_ratings:
            results.append(recipe_rating["recipe"])
    else:
        print("[DEBUG] running default")
        results = get_sorted_recipes("new", filters=filters)  # default sort order

    return results


"""
Converts a technical sort_order value to a user-friendly message

Returns: a message to display, describing how recipes are sorted

@author: Shay
"""
def get_sort_message(sort_order):

    sort_message = "Sorting by: "

    if sort_order == "old":
        sort_message += "oldest"
    elif sort_order == "highest-rating":
        sort_message += "highest average rating"
    elif sort_order == "lowest-rating":
        sort_message += "lowest average rating"
    elif sort_order == "title-az":
        sort_message += "alphabetical (A -> Z)"
    elif sort_order == "title-za":
        sort_message += "alphabetical (Z -> A)"
    elif sort_order == "quickest":
        sort_message += "quickest preparation time"
    elif sort_order == "longest":
        sort_message += "longest preparation time"
    elif sort_order == "most-servings":
        sort_message += "most servings"
    elif sort_order == "least-servings":
        sort_message += "least servings"
    elif sort_order == "most-calories":
        sort_message += "most calories per serving"
    elif sort_order == "least-calories":
        sort_message += "least calories per serving"
    else:
        sort_message += "newest"

    return sort_message

"""
Calculate an average rating based on each RecipeRating.value for a recipe (1 to 5 scale)

Returns: average rating out of 5, as a float rounded to 1 d.p. (or -1 if there are no ratings yet)

@author: Shay
"""
def get_average_rating(recipe_id):

    ratings = RecipeRating.query.filter_by(recipe_id=recipe_id).all()
    if len(ratings) == 0:
        return -1
    total = 0
    for rating in ratings:
        print("Rating: " + str(rating))
        total += rating.value
    average = total / len(ratings)
    print("Average: " + str(average))
    return round(average, 1)

"""
Display the average rating for a recipe

Returns: "{average}/5" or "No ratings yet" if no ratings exist

@author: Shay
"""
def display_rating(recipe_id):

    rating = get_average_rating(recipe_id)
    if rating <= 0:
        return "No ratings yet"
    return str(rating) + "/5"

"""
Iterate through RecipeRating rows and check if a review is included in the rating, if so add it to an array

Returns: an array of all RecpieRating rows with reviews

@author: Shay
"""
def get_reviews(recipe_id):

    ratings = RecipeRating.query.filter_by(recipe_id=recipe_id).all()
    reviews = []
    for rating in ratings:
        print("Review: " + str(rating.review))
        if rating.review:
            reviews.append(rating)
    return reviews

"""
Returns: a boolean for whether the recipe is bookmarked by the user

@author: Shay
"""
def is_bookmarked(recipe, user):

    bookmark = Bookmark.query.filter_by(recipe_id=recipe["id"],user_id=user.id).first()
    if bookmark:
        return True
    return False


"""
Lists all public approved recipes in the database
Includes options for searching, sorting, and page navigation

@author: Shay
"""
@recipes_blueprint.route("/recipes")
@login_required
def view_recipes():

    # default values
    page = 1
    total_pages = 1
    recipes_per_page = 5
    recipes_list = []
    sort_order = "new"
    search_query = ""

    qs = str(request.query_string).lower()

    # DANGEROUS - DEVELOPING / DEBUGGING ONLY
    if "reset=yes" in qs:
        print("[DEBUG] Resetting all recipes in database")
        reset_recipes()

    # if "split=yes" in qs:
    #     print("[DEBUG] Splitting all recipe tags, ingredients, and instructions")
    #     mdb_split_lines()
    #
    # if "approve=yes" in qs:
    #     print("[DEBUG] Setting all recipe states to approved")
    #     mdb_set_states()

    if not approved_recipes_exist():
        print("[DEBUG] No recipes")
        return render_template("recipes/recipes.html", User=User, total_recipes=0,
                               recipes_list=recipes_list, recipes_per_page=recipes_per_page, page=page,
                               total_pages=total_pages, search_query=search_query, sort_order=sort_order,
                               is_bookmarked=is_bookmarked)

    if "sort=" in qs:
        try:
            sort_order = str(request.args.get("sort"))
        except KeyError:
            pass

    # get a sorted list of all approved not-private recipes
    recipes_list = get_sorted_recipes(sort_order, filters={"state": "approved", "private": False})

    if "search=" in qs:
        try:
            search_query = str(request.args.get("search"))
            print("[DEBUG] Search query = " + search_query)
            recipes_list = search(recipes_list, search_query)
        except KeyError:
            print("[DEBUG] search KeyError")
            pass

    total_recipes = len(recipes_list)
    newest_recipe_id = get_sorted_recipes("new", filters={"state": "approved", "private": False})[0]["id"]

    # if there are more recipes than 20, they will be split into separate pages
    if total_recipes > recipes_per_page:
        total_pages = max(ceil(total_recipes / recipes_per_page), 1)

        # allow page navigation using query string (e.g. "/recipes?page=1", "/recipes?page=2")
        if "page=" in qs:
            try:
                page = int(request.args.get("page"))
            except (KeyError, ValueError):
                pass  # if the page value isn't valid, continue using default page = 1

        # reduce list to only the recipes that should appear on the specified page
        first_recipe = (page - 1) * recipes_per_page
        last_recipe = min(page * recipes_per_page, total_recipes)
        recipes_list = recipes_list[first_recipe:last_recipe]


    sort_message = get_sort_message(sort_order)

    return render_template("recipes/recipes.html", User=User, total_recipes=total_recipes,
                           recipes_list=recipes_list, recipes_per_page=recipes_per_page, page=page,
                           total_pages=total_pages, newest_recipe_id=newest_recipe_id, search_query=search_query,
                           sort_order=sort_order, sort_message=sort_message, display_rating=display_rating,
                           is_bookmarked=is_bookmarked)

"""
Views a specific recipe (given as a URL like "/recipe?id=1")
This displays all of its properties, as well as reviews/ratings

@author: Shay
"""
@recipes_blueprint.route("/recipe", methods=["GET", "POST"])
@login_required
def view_recipe():
    recipe_id = 0

    qs = str(request.query_string).lower()
    if "id=" not in qs:
        return redirect(url_for("recipes.view_recipes")) # no id
    try:
        recipe_id = int(request.args.get("id"))
    except (KeyError, ValueError):
        return redirect(url_for("recipes.view_recipes"))  # invalid id

    # print("[DEBUG] Getting recipe with ID: " + str(recipe_id))
    recipe = get_recipe(recipe_id)
    if "id" not in recipe:
        return redirect(url_for("recipes.view_recipes"))  # no such recipe

    user_rating = None
    user_review = None
    user_recipe_rating = RecipeRating.query.filter_by(recipe_id=recipe_id, user_id=current_user.id).first()
    if user_recipe_rating:
        user_rating = user_recipe_rating.value
        user_review = user_recipe_rating.review
    reviews = get_reviews(recipe_id)

    form = RatingForm()
    if form.validate_on_submit():
        print("[DEBUG] FORM SUBMITTED")
        print("Form review = " + str(form.review.data))
        print("Form rating = " + str(form.rating.data))

        review = form.review.data
        if review == "":
            review = None
        value = form.rating.data
        if value < 1:
            value = 1
        if value > 5:
            value = 5

        if user_rating:
            # user has previously rated - update RecipeRating
            user_recipe_rating.value = value
            user_recipe_rating.review = review
        else:
            # user has not rated or reviewed - add new RecipeRating
            new_rating = RecipeRating(recipe_id=recipe_id,
                                      user_id=current_user.id,
                                      review=review,
                                      value=value)
            print(new_rating)
            db.session.add(new_rating)
        db.session.commit()
        return redirect(url_for("recipes.view_recipe") + "?id=" + str(recipe_id))

    bookmark = Bookmark.query.filter_by(recipe_id=recipe_id, user_id=current_user.id).first()

    return render_template("recipes/recipe.html", recipe=recipe, User=User, form=form, reviews=reviews,
                           user_review=user_review, user_rating=user_rating, display_rating=display_rating,
                           bookmark=bookmark, is_bookmarked=is_bookmarked)


"""
Toggles whether the given recipe (given as an ID like "/bookmark?id=1")
is bookmarked by the current user.

@author: Shay
"""
@recipes_blueprint.route("/bookmark")
def bookmark():
    recipe_id = 0

    qs = str(request.query_string).lower()
    if "id=" not in qs:
        return redirect(url_for("recipes.view_recipes")) # no id
    try:
        recipe_id = int(request.args.get("id"))
    except (KeyError, ValueError):
        return redirect(url_for("recipes.view_recipes"))  # invalid id

    # print("[DEBUG] Getting recipe with ID: " + str(recipe_id))
    recipe = get_recipe(recipe_id)
    if "id" not in recipe:
        return redirect(url_for("recipes.view_recipes"))  # no such recipe

    prev_bookmark = Bookmark.query.filter_by(recipe_id=recipe_id, user_id=current_user.id).first()
    if prev_bookmark:
        db.session.delete(prev_bookmark)
        db.session.commit()
        return redirect(url_for("recipes.view_recipe") + "?id=" + str(recipe_id))

    else:
        bookmark = Bookmark(recipe_id=recipe_id, user_id=current_user.id)
        db.session.add(bookmark)
        db.session.commit()
        return redirect(url_for("recipes.view_recipe") + "?id=" + str(recipe_id))

"""
Lists recipes which the current user has bookmarked

@author: Shay
"""
@recipes_blueprint.route("/bookmarked-recipes")
def view_bookmarks():
    # Retrieve all recipes from the database
    page = 1
    total_pages = 1
    recipes_per_page = 5
    recipes_list = []
    sort_order = "new"
    search_query = ""

    qs = str(request.query_string).lower()

    # DANGEROUS - DEVELOPING / DEBUGGING ONLY
    # if "reset=yes" in qs:
    #     print("[DEBUG] Resetting all recipes in database")
    #     reset_recipes()
    #
    # if "split=yes" in qs:
    #     print("[DEBUG] Splitting all recipe tags, ingredients, and instructions")
    #     mdb_split_lines()
    #
    # if "approve=yes" in qs:
    #     print("[DEBUG] Setting all recipe states to approved")
    #     mdb_set_states()

    if not approved_recipes_exist():
        print("[DEBUG] No recipes")
        return render_template("recipes/recipes.html", User=User, total_recipes=0,
                               recipes_list=recipes_list, recipes_per_page=recipes_per_page, page=page,
                               total_pages=total_pages, search_query=search_query, sort_order=sort_order)

    if "sort=" in qs:
        try:
            sort_order = str(request.args.get("sort"))
        except KeyError:
            pass

    all_recipes = get_sorted_recipes(sort_order, filters={"state": "approved", "private": False})

    if "search=" in qs:
        try:
            search_query = str(request.args.get("search"))
            print("[DEBUG] Search query = " + search_query)
            all_recipes = search(all_recipes, search_query)
        except KeyError:
            print("[DEBUG] search KeyError")
            pass

    bookmarked_recipes = []
    for recipe in all_recipes:
        if is_bookmarked(recipe, current_user):
            bookmarked_recipes.append(recipe)

    total_recipes = len(bookmarked_recipes)

    # if there are more recipes than 20, they will be split into separate pages
    if total_recipes > recipes_per_page:
        total_pages = max(ceil(total_recipes / recipes_per_page), 1)

        # allow page navigation using query string (e.g. "/recipes?page=1", "/recipes?page=2")
        if "page=" in qs:
            try:
                page = int(request.args.get("page"))
            except (KeyError, ValueError):
                pass  # if the page value isn't valid, continue using default page = 1

        # reduce list to only the recipes that should appear on the specified page
        first_recipe = (page - 1) * recipes_per_page
        last_recipe = min(page * recipes_per_page, total_recipes)
        bookmarked_recipes = bookmarked_recipes[first_recipe:last_recipe]


    sort_message = get_sort_message(sort_order)

    return render_template("recipes/bookmarked_recipes.html", User=User, recipes_list=bookmarked_recipes, page=page,
                           recipes_per_page=recipes_per_page, total_recipes=total_recipes, total_pages=total_pages,
                           search_query=search_query, sort_order=sort_order, sort_message=sort_message,
                           display_rating=display_rating)

"""
Provides the user with a form to submit their own recipe, entering a variety of properties

@author: Shay
"""
@recipes_blueprint.route("/new-recipe", methods=["GET", "POST"])
@login_required
def new_recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        print("[DEBUG] FORM SUBMITTED")
        title = form.title.data
        summary = form.summary.data
        category = form.category.data
        raw_tags = form.tags.data
        raw_ingredients = form.ingredients.data
        raw_instructions = form.instructions.data
        preparation_time = form.preparation_time.data
        servings = form.servings.data
        calories_per_serving = form.calories_per_serving.data
        private = form.private.data
        username = current_user.username


        tags = raw_tags.split(", ")
        ingredients = raw_ingredients.split("\r\n")
        instructions = raw_instructions.split("\r\n")
        new_recipe = add_recipe(created_by=username, title=title, summary=summary, category=category, tags=tags,
                   ingredients=ingredients, instructions=instructions, preparation_time=preparation_time,
                   servings=servings, calories_per_serving=calories_per_serving, private=private)

        print("[DEBUG] added recipe")

        return redirect(url_for("recipes.view_recipe") + "?id=" + str(new_recipe["id"]))
    return render_template("recipes/submit_recipe.html", User=User, form=form)

"""
Lists all of the recipes that the current user has submitted - including private or uanpproved

@author: Shay
"""
@recipes_blueprint.route("/user-recipes")
@login_required
def user_recipes():
    # Retrieve all user recipes
    page = 1
    total_pages = 1
    recipes_per_page = 5
    recipes_list = []
    sort_order = "new"
    search_query = ""

    qs = str(request.query_string).lower()

    if not approved_recipes_exist():
        print("[DEBUG] No user recipes")
        return render_template("recipes/user_recipes.html", User=User, total_recipes=0,
                               recipes_list=recipes_list, recipes_per_page=recipes_per_page, page=page,
                               total_pages=total_pages, search_query=search_query, sort_order=sort_order)

    if "sort=" in qs:
        try:
            sort_order = str(request.args.get("sort"))
        except KeyError:
            pass

    recipes_list = get_sorted_recipes(sort_order, filters={"created_by": current_user.username})

    if "search=" in qs:
        try:
            search_query = str(request.args.get("search"))
            print("[DEBUG] Search query = " + search_query)
            recipes_list = search(recipes_list, search_query)
        except KeyError:
            print("[DEBUG] search KeyError")
            pass

    total_recipes = len(recipes_list)

    # if there are more recipes than 20, they will be split into separate pages
    if total_recipes > recipes_per_page:
        total_pages = max(ceil(total_recipes / recipes_per_page), 1)

        # allow page navigation using query string (e.g. "/recipes?page=1", "/recipes?page=2")
        if "page=" in qs:
            try:
                page = int(request.args.get("page"))
            except (KeyError, ValueError):
                pass  # if the page value isn't valid, continue using default page = 1

        # reduce list to only the recipes that should appear on the specified page
        first_recipe = (page - 1) * recipes_per_page
        last_recipe = min(page * recipes_per_page, total_recipes)
        recipes_list = recipes_list[first_recipe:last_recipe]

    sort_message = get_sort_message(sort_order)

    return render_template("recipes/user_recipes.html", User=User, total_recipes=total_recipes,
                           recipes_list=recipes_list, recipes_per_page=recipes_per_page, page=page,
                           total_pages=total_pages, search_query=search_query,
                           sort_order=sort_order, sort_message=sort_message)
